#!/usr/bin/env python3
"""
Enhanced Smart YouTube Agent - Main Application
Complete SaaS platform with AI-powered video creation, chat interface, and Slack integration
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import logging
import os
import json
from typing import Dict, Any, Optional
import asyncio

# Import all modules
from .auth import get_current_user, create_access_token
from .enhanced_auth_routes import router as auth_router
from .saas_routes import router as saas_router
from .dashboard import router as dashboard_router
from .video_routes import router as video_router
from .ai_brain import ai_brain
from .enhanced_video_generator import enhanced_video_generator
from .slack_integration import slack_integration
from .chat_interface import chat_manager, websocket_endpoint, get_chat_html
from .video_manager import video_manager
from .automation_manager import automation_manager
from .seo_optimizer import seo_optimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Smart YouTube Agent",
    description="AI-powered YouTube video creation platform",
    version="2.0.0"
)

# Include existing routers
app.include_router(auth_router, tags=["Authentication"])  # No prefix so /api/login works
app.include_router(saas_router, prefix="/api", tags=["SaaS"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(video_router, tags=["Video Creation"])

# Enhanced routes

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page with enhanced features."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart YouTube Agent</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .feature { margin: 10px 0; padding: 10px; background: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>Smart YouTube Agent</h1>
        <p>AI-powered YouTube video creation platform</p>
        <div class="feature">AI-powered video creation</div>
        <div class="feature">Real-time chat with AI assistant</div>
        <div class="feature">Slack integration</div>
        <div class="feature">YouTube automation</div>
        <div class="feature">SEO optimization</div>
        <div class="feature">Multi-platform support</div>
        <p><a href="/dashboard">Go to Dashboard</a></p>
        <p><a href="/chat">Chat with AI</a></p>
    </body>
    </html>
    """)

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Chat interface page."""
    return HTMLResponse(content=get_chat_html())

@app.get("/video-creator", response_class=HTMLResponse)
async def video_creator_page(request: Request):
    """Video creator page."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Creator - Smart YouTube Agent</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .form-group { margin: 15px 0; }
            input, textarea { width: 100%; padding: 8px; margin: 5px 0; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; }
        </style>
    </head>
    <body>
        <h1>Video Creator</h1>
        <form>
            <div class="form-group">
                <label>Video Topic:</label>
                <input type="text" placeholder="Enter your video topic">
            </div>
            <div class="form-group">
                <label>Description:</label>
                <textarea placeholder="Describe your video"></textarea>
            </div>
            <button type="submit">Create Video with AI</button>
        </form>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """)

@app.websocket("/ws/{user_id}")
async def websocket_handler(websocket: WebSocket, user_id: str):
    """WebSocket handler for real-time chat."""
    await websocket_endpoint(websocket, user_id)

# Enhanced API routes

@app.post("/api/chat/message")
async def send_chat_message(
    message: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Send message through chat API."""
    try:
        user_id = current_user["user_id"]
        content = message.get("content", "")
        
        # Process with AI brain
        response = await ai_brain.process_message(user_id, content, platform="api")
        
        return {
            "success": True,
            "response": response,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

# Video creation routes are handled by video_routes.py

@app.get("/api/ai/conversation")
async def get_conversation_history(current_user: dict = Depends(get_current_user)):
    """Get conversation history for the current user."""
    try:
        user_id = current_user["user_id"]
        conversation = await ai_brain.get_conversation_history(user_id)
        return {"conversation": conversation}
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation history")

@app.post("/api/ai/clear-conversation")
async def clear_conversation(current_user: dict = Depends(get_current_user)):
    """Clear conversation history for user."""
    try:
        user_id = current_user["user_id"]
        context = ai_brain.get_conversation_context(user_id)
        context.conversation_history = []
        context.current_video_project = None
        
        return {
            "success": True,
            "message": "Conversation cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear conversation")

# Enhanced Slack integration

@app.post("/slack/events")
async def slack_events_handler(request: Request):
    """Enhanced Slack events handler."""
    try:
        body = await request.json()
        return await slack_integration.handle_slack_event(body)
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        return {"ok": True}

@app.post("/slack/interactive")
async def slack_interactive_handler(request: Request):
    """Handle Slack interactive messages."""
    try:
        form_data = await request.form()
        payload = json.loads(form_data.get("payload", "{}"))
        return await slack_integration.handle_interactive_message(payload)
    except Exception as e:
        logger.error(f"Error handling Slack interactive: {e}")
        return {"ok": True}

# Enhanced video management

@app.get("/api/videos/status/{video_id}")
async def get_video_status(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed video status."""
    try:
        status = enhanced_video_generator.get_video_status(video_id)
        
        # Add user-specific information
        user_id = current_user["user_id"]
        context = ai_brain.get_conversation_context(user_id)
        
        if context.current_video_project and context.current_video_project.video_id == video_id:
            status["ai_context"] = context.current_video_project.dict()
        
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting video status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video status")

@app.post("/api/videos/{video_id}/upload-to-youtube")
async def upload_video_to_youtube(
    video_id: str,
    upload_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Upload video to YouTube with SEO optimization."""
    try:
        user_id = current_user["user_id"]
        
        # Get video status
        status = enhanced_video_generator.get_video_status(video_id)
        
        if not status["video_exists"]:
            raise HTTPException(status_code=400, detail="Video not found or not ready")
        
        # Optimize for YouTube
        seo_data = await enhanced_video_generator.optimize_for_youtube(
            status["video_path"],
            upload_data.get("title", ""),
            upload_data.get("description", ""),
            upload_data.get("tags", [])
        )
        
        if not seo_data["success"]:
            raise HTTPException(status_code=500, detail="Failed to optimize video")
        
        # Upload to YouTube
        from youtube_manager import youtube_manager
        upload_result = youtube_manager.upload_video(user_id, {
            "title": seo_data["youtube_title"],
            "description": seo_data["youtube_description"],
            "tags": seo_data["youtube_tags"],
            "category": seo_data["youtube_category"],
            "privacy": seo_data["youtube_privacy"],
            "video_file": status["video_path"]
        })
        
        return {
            "success": True,
            "message": "Video uploaded to YouTube successfully",
            "data": {
                "youtube_url": upload_result["video_url"],
                "seo_data": seo_data
            }
        }
        
    except Exception as e:
        logger.error(f"Error uploading to YouTube: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload to YouTube")

# Dashboard enhancements

@app.get("/api/dashboard/ai-stats")
async def get_ai_stats(current_user: dict = Depends(get_current_user)):
    """Get AI-related statistics for dashboard."""
    try:
        user_id = current_user["user_id"]
        context = ai_brain.get_conversation_context(user_id)
        
        # Get chat session info
        chat_session = chat_manager.get_user_session(user_id)
        
        stats = {
            "conversation_count": len(context.conversation_history),
            "current_project": context.current_video_project.dict() if context.current_video_project else None,
            "chat_session": chat_session,
            "connected_users": len(chat_manager.get_connected_users()),
            "ai_ready": True
        }
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting AI stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI stats")

@app.get("/api/dashboard/quick-actions")
async def get_quick_actions(current_user: dict = Depends(get_current_user)):
    """Get quick action suggestions based on user context."""
    try:
        user_id = current_user["user_id"]
        context = ai_brain.get_conversation_context(user_id)
        
        actions = []
        
        if not context.current_video_project:
            actions.append({
                "id": "create_video",
                "title": "Create New Video",
                "description": "Start creating a new YouTube video",
                "icon": "🎬",
                "action": "chat:create_video"
            })
        else:
            actions.append({
                "id": "view_project",
                "title": "View Current Project",
                "description": "Check status of current video project",
                "icon": "📊",
                "action": "chat:view_project"
            })
            
            if context.current_video_project.status == "script_generated":
                actions.append({
                    "id": "start_creation",
                    "title": "Start Video Creation",
                    "description": "Begin creating the video",
                    "icon": "▶️",
                    "action": "chat:start_creation"
                })
            
            if context.current_video_project.status == "video_created":
                actions.append({
                    "id": "upload_youtube",
                    "title": "Upload to YouTube",
                    "description": "Upload video to YouTube",
                "icon": "📤",
                "action": "chat:upload_youtube"
            })
        
        actions.extend([
            {
                "id": "chat_ai",
                "title": "Chat with AI",
                "description": "Start a conversation with the AI assistant",
                "icon": "🤖",
                "action": "navigate:/chat"
            },
            {
                "id": "connect_slack",
                "title": "Connect Slack",
                "description": "Set up Slack integration",
                "icon": "💬",
                "action": "navigate:/settings/integrations"
            }
        ])
        
        return {
            "success": True,
            "data": actions
        }
    except Exception as e:
        logger.error(f"Error getting quick actions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quick actions")

# Health check and monitoring

@app.get("/health")
async def health_check():
    """Enhanced health check."""
    try:
        # Check AI brain
        ai_status = "healthy"
        try:
            # Test AI brain functionality
            test_response = await ai_brain.process_message("health_check", "test", platform="health")
            ai_status = "healthy" if test_response else "degraded"
        except Exception as e:
            ai_status = "unhealthy"
            logger.error(f"AI brain health check failed: {e}")
        
        # Check video generator
        video_status = "healthy"
        try:
            # Test video generator
            test_status = enhanced_video_generator.get_video_status("test")
            video_status = "healthy"
        except Exception as e:
            video_status = "unhealthy"
            logger.error(f"Video generator health check failed: {e}")
        
        # Check chat manager
        chat_status = "healthy"
        try:
            connected_users = chat_manager.get_connected_users()
            chat_status = "healthy"
        except Exception as e:
            chat_status = "unhealthy"
            logger.error(f"Chat manager health check failed: {e}")
        
        return {
            "status": "ok",
            "timestamp": asyncio.get_event_loop().time(),
            "components": {
                "ai_brain": ai_status,
                "video_generator": video_status,
                "chat_manager": chat_status,
                "slack_integration": "healthy" if slack_integration.bot_token else "not_configured"
            },
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }

@app.get("/api/user/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get user statistics for dashboard."""
    try:
        # Get real user statistics from video manager and YouTube
        user_id = current_user["user_id"]
        
        # Get video statistics with error handling
        try:
            video_stats = video_manager.get_user_video_stats(user_id)
        except Exception as e:
            logger.error(f"Error getting video stats: {e}")
            video_stats = {
                "total_videos": 0,
                "uploaded_videos": 0,
                "recent_videos": []
            }
        
        # Get YouTube statistics if connected
        youtube_stats = {"total_views": 0, "total_subscribers": 0}
        try:
            from youtube_manager import youtube_manager
            channel_info = youtube_manager.get_channel_info(user_id)
            if channel_info and not channel_info.get('channel_id', '').startswith('demo_'):
                youtube_stats = {
                    "total_views": int(channel_info.get('view_count', 0)),
                    "total_subscribers": int(channel_info.get('subscriber_count', 0))
                }
        except Exception as e:
            logger.warning(f"Could not get YouTube stats: {e}")
        
        stats = {
            "videos_created": video_stats.get("total_videos", 0),
            "videos_uploaded": video_stats.get("uploaded_videos", 0),
            "total_views": youtube_stats.get("total_views", 0),
            "total_subscribers": youtube_stats.get("total_subscribers", 0),
            "recent_videos": video_stats.get("recent_videos", [])
        }
        
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to get user stats")

@app.post("/api/slack/setup")
async def setup_slack_integration(
    slack_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Setup Slack integration for user."""
    try:
        # This would integrate with Slack API
        # For now, return success
        return {
            "success": True,
            "message": "Slack integration setup initiated",
            "bot_invite_url": "https://slack.com/oauth/v2/authorize?client_id=demo&scope=chat:write,commands"
        }
    except Exception as e:
        logger.error(f"Error setting up Slack: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup Slack integration")

@app.get("/api/analytics/{video_id}")
async def get_video_analytics(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get real analytics for a specific video."""
    try:
        user_id = current_user["user_id"]
        
        # Get real analytics from YouTube API
        from youtube_manager import youtube_manager
        analytics = youtube_manager.get_video_analytics(user_id, video_id)
        
        if analytics:
            return {"success": True, "data": analytics}
        else:
            raise HTTPException(status_code=404, detail="Video not found or no analytics available")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video analytics")

# Automation API endpoints
@app.get("/api/automation/settings")
async def get_automation_settings(current_user: dict = Depends(get_current_user)):
    """Get automation settings for the current user."""
    try:
        user_id = current_user["user_id"]
        settings = automation_manager.get_user_settings(user_id)
        return settings
    except Exception as e:
        logger.error(f"Error getting automation settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get automation settings")

@app.post("/api/automation/settings")
async def save_automation_settings(
    settings: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Save automation settings for the current user."""
    try:
        user_id = current_user["user_id"]
        result = automation_manager.save_user_settings(user_id, settings)
        return result
    except Exception as e:
        logger.error(f"Error saving automation settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save automation settings")

@app.get("/api/automation/next-upload")
async def get_next_upload(current_user: dict = Depends(get_current_user)):
    """Get the next scheduled upload time."""
    try:
        user_id = current_user["user_id"]
        next_upload = automation_manager.get_next_upload(user_id)
        return {"next_upload": next_upload}
    except Exception as e:
        logger.error(f"Error getting next upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to get next upload")

@app.post("/api/automation/toggle")
async def toggle_automation(
    payload: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Enable or disable automation for the current user."""
    try:
        user_id = current_user["user_id"]
        enabled = bool(payload.get("enabled"))
        updated = automation_manager.set_enabled(user_id, enabled)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling automation: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle automation")

# SEO optimization routes are handled by video_routes.py

# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Smart YouTube Agent starting up...")
    
    # Initialize AI brain
    logger.info("Initializing AI brain...")
    
    # Initialize video generator
    logger.info("Initializing video generator...")
    
    # Initialize chat manager
    logger.info("Initializing chat manager...")
    
    # Initialize Slack integration
    logger.info("Initializing Slack integration...")
    
    # Start automation scheduler
    logger.info("Starting automation scheduler...")
    automation_manager.start_scheduler()
    
    logger.info("Smart YouTube Agent startup complete!")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Smart YouTube Agent shutting down...")
    
    # Clean up connections
    for user_id in list(chat_manager.active_connections.keys()):
        chat_manager.disconnect(user_id)
    
    logger.info("Smart YouTube Agent shutdown complete!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 