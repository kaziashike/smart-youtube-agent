#!/usr/bin/env python3
"""
Enhanced Authentication API Routes
Handles user signup, login, and profile management with improved YouTube integration
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from auth import (
    UserSignup, UserLogin, signup_user, login_user, 
    get_current_user, update_user_profile, get_user_profile
)
from enhanced_youtube_manager import enhanced_youtube_manager
from pathlib import Path
import json

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Setup Jinja2 templates
import os
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page."""
    return templates.TemplateResponse("enhanced_landing.html", {"request": request})

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page."""
    return templates.TemplateResponse("signup.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """User profile page."""
    return templates.TemplateResponse("enhanced_profile.html", {
        "request": request,
        "user": None  # Will be loaded via JavaScript
    })

@router.get("/integrations/youtube", response_class=HTMLResponse)
async def youtube_integration_page(request: Request):
    """YouTube integration setup page."""
    return templates.TemplateResponse("enhanced_youtube_integration.html", {"request": request})

@router.get("/integrations/slack", response_class=HTMLResponse)
async def slack_integration_page(request: Request):
    """Slack integration setup page."""
    return templates.TemplateResponse("slack_integration.html", {"request": request})

@router.post("/api/signup")
async def api_signup(user_data: UserSignup):
    """API endpoint for user signup."""
    try:
        result = signup_user(user_data)
        return {
            "success": True,
            "message": "User registered successfully",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/api/login")
async def api_login(login_data: UserLogin):
    """API endpoint for user login."""
    try:
        result = login_user(login_data)
        return {
            "success": True,
            "message": "Login successful",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/api/profile")
async def api_get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return {
        "success": True,
        "data": {
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "name": current_user["name"],
            "company": current_user.get("company"),
            "subscription_tier": current_user.get("subscription_tier", "Free"),
            "created_at": current_user.get("created_at"),
            "youtube_channel": current_user.get("youtube_channel")
        }
    }

@router.put("/api/profile")
async def api_update_profile(
    updates: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile."""
    try:
        result = update_user_profile(current_user["user_id"], updates)
        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

@router.get("/api/youtube/auth")
async def youtube_auth_url(current_user: dict = Depends(get_current_user)):
    """Get YouTube OAuth authorization URL."""
    try:
        auth_url = enhanced_youtube_manager.get_web_auth_url(current_user["user_id"])
        return {
            "success": True,
            "auth_url": auth_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube auth URL error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate auth URL")

@router.get("/auth/youtube/callback")
async def youtube_auth_callback(
    request: Request,
    code: str = None,
    state: str = None,
    user_id: str = None,
    error: str = None,
    demo: str = None
):
    """Handle YouTube OAuth callback with enhanced error handling."""
    try:
        # Handle OAuth errors
        if error:
            logger.error(f"YouTube OAuth error: {error}")
            return RedirectResponse(
                url=f"/profile?error=youtube_failed&message=OAuth authorization denied",
                status_code=302
            )
        
        # Handle demo mode
        if demo == "true":
            user_id = user_id or state
            if not user_id:
                raise HTTPException(status_code=400, detail="Missing user ID for demo mode")
            
            result = enhanced_youtube_manager._handle_demo_callback(user_id)
            channel_name = result.get('channel_info', {}).get('title', 'Demo Channel')
            return RedirectResponse(
                url=f"/profile?success=youtube_connected&channel={channel_name}&demo=true",
                status_code=302
            )
        
        # Get user_id from state parameter (for real OAuth) or query parameter (for demo)
        actual_user_id = state or user_id
        
        if not code or not actual_user_id:
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        logger.info(f"Processing YouTube OAuth callback for user {actual_user_id}")
        result = enhanced_youtube_manager.handle_web_auth_callback(code, actual_user_id)
        
        # Redirect to profile page with success message
        channel_name = result.get('channel_info', {}).get('title', 'Unknown Channel')
        return RedirectResponse(
            url=f"/profile?success=youtube_connected&channel={channel_name}",
            status_code=302
        )
    except HTTPException as e:
        logger.error(f"YouTube callback error: {e.detail}")
        # Redirect to profile page with error message
        return RedirectResponse(
            url=f"/profile?error=youtube_failed&message={e.detail}",
            status_code=302
        )
    except Exception as e:
        logger.error(f"Unexpected error in YouTube callback: {e}")
        return RedirectResponse(
            url=f"/profile?error=youtube_failed&message=Connection failed",
            status_code=302
        )

@router.get("/api/youtube/channel")
async def get_youtube_channel(current_user: dict = Depends(get_current_user)):
    """Get connected YouTube channel info."""
    try:
        channel_info = enhanced_youtube_manager.get_channel_info(current_user["user_id"])
        return {
            "success": True,
            "data": channel_info
        }
    except Exception as e:
        logger.error(f"Get channel info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get channel info")

@router.delete("/api/youtube/disconnect")
async def disconnect_youtube(current_user: dict = Depends(get_current_user)):
    """Disconnect YouTube channel."""
    try:
        result = enhanced_youtube_manager.disconnect_channel(current_user["user_id"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Disconnect channel error: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect channel")

@router.get("/api/youtube/analytics/{video_id}")
async def get_video_analytics(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get video analytics."""
    try:
        analytics = enhanced_youtube_manager.get_video_analytics(current_user["user_id"], video_id)
        return {
            "success": True,
            "data": analytics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video analytics")

@router.get("/api/youtube/status")
async def get_youtube_status(current_user: dict = Depends(get_current_user)):
    """Get YouTube connection status."""
    try:
        channel_info = enhanced_youtube_manager.get_channel_info(current_user["user_id"])
        
        if channel_info:
            return {
                "success": True,
                "connected": True,
                "channel_info": channel_info,
                "demo_mode": enhanced_youtube_manager.is_demo_mode()
            }
        else:
            return {
                "success": True,
                "connected": False,
                "channel_info": None,
                "demo_mode": enhanced_youtube_manager.is_demo_mode()
            }
    except Exception as e:
        logger.error(f"Get YouTube status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get YouTube status")

@router.post("/api/youtube/upload")
async def upload_youtube_video(
    video_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Upload video to YouTube."""
    try:
        result = enhanced_youtube_manager.upload_video(current_user["user_id"], video_data)
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload video error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload video")

@router.post("/api/youtube/save-credentials")
async def save_youtube_credentials(
    credentials_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Save YouTube credentials from file upload or manual input."""
    try:
        client_id = credentials_data.get("client_id")
        client_secret = credentials_data.get("client_secret")
        project_id = credentials_data.get("project_id")
        
        if not client_id or not client_secret:
            raise HTTPException(status_code=400, detail="Client ID and Client Secret are required")
        
        # Create credentials structure
        credentials = {
            "web": {
                "client_id": client_id,
                "project_id": project_id or "youtube-project",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": [
                    "http://localhost:8000/auth/youtube/callback",
                    "http://127.0.0.1:8000/auth/youtube/callback"
                ]
            }
        }
        
        # Save to client_secrets.json
        credentials_file = Path(__file__).parent / "client_secrets.json"
        with open(credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)
        
        # Update environment variables
        env_file = Path(__file__).parent.parent / ".env"
        env_lines = []
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_lines = f.readlines()
        
        # Remove existing YouTube variables
        env_lines = [line for line in env_lines if not line.startswith(("YOUTUBE_", "DEMO_MODE="))]
        
        # Add new variables
        youtube_vars = {
            "YOUTUBE_WEB_CLIENT_ID": client_id,
            "YOUTUBE_WEB_CLIENT_SECRET": client_secret,
            "DEMO_MODE": "false"
        }
        
        for key, value in youtube_vars.items():
            env_lines.append(f"{key}={value}\n")
        
        # Write updated .env file
        with open(env_file, 'w') as f:
            f.writelines(env_lines)
        
        logger.info(f"Saved YouTube credentials for user {current_user['user_id']}")
        
        return {
            "success": True,
            "message": "YouTube credentials saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error saving YouTube credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to save credentials")

@router.get("/api/youtube/setup-status")
async def get_youtube_setup_status():
    """Get YouTube setup status for the application."""
    try:
        demo_mode = enhanced_youtube_manager.is_demo_mode()
        
        # Check if client_secrets.json exists and has valid credentials
        client_secrets_file = Path(__file__).parent / "client_secrets.json"
        setup_complete = False
        
        if client_secrets_file.exists():
            try:
                with open(client_secrets_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                web_config = config.get('web', {})
                if web_config.get('client_id') and web_config.get('client_secret'):
                    setup_complete = True
            except Exception as e:
                logger.error(f"Error reading client_secrets.json: {e}")
        
        if demo_mode:
            return {
                "success": True,
                "setup_complete": True,
                "demo_mode": True,
                "message": "Demo mode is active - all features available for testing"
            }
        elif setup_complete:
            return {
                "success": True,
                "setup_complete": True,
                "demo_mode": False,
                "message": "Real YouTube API is configured"
            }
        else:
            return {
                "success": True,
                "setup_complete": False,
                "demo_mode": False,
                "message": "YouTube API not configured - please add your client_secrets.json file"
            }
    except Exception as e:
        logger.error(f"Get setup status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get setup status") 