#!/usr/bin/env python3
"""
SaaS Platform Routes
Main routes for video creation, subscription management, and user dashboard
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .auth import get_current_user
from .video_manager import video_manager, VideoRequest
from .subscription_manager import subscription_manager
from .youtube_manager import YouTubeManager
from datetime import datetime

# Create YouTube manager instance
youtube_manager = YouTubeManager()

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Setup Jinja2 templates
import os
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@router.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard(request: Request, current_user: dict = Depends(get_current_user)):
    """User dashboard page."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user
    })

@router.get("/videos", response_class=HTMLResponse)
async def videos_page(request: Request, current_user: dict = Depends(get_current_user)):
    """Videos management page."""
    return templates.TemplateResponse("videos.html", {
        "request": request,
        "user": current_user
    })

@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Pricing page."""
    return templates.TemplateResponse("pricing.html", {
        "request": request,
        "tiers": subscription_manager.get_all_tiers()
    })

@router.get("/billing", response_class=HTMLResponse)
async def billing_page(request: Request, current_user: dict = Depends(get_current_user)):
    """Billing page."""
    return templates.TemplateResponse("billing.html", {
        "request": request,
        "user": current_user
    })

# API Routes

@router.post("/api/videos/create")
async def create_video(
    video_data: VideoRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new video."""
    try:
        # Check subscription limits
        if not subscription_manager.check_video_limit(current_user["user_id"]):
            raise HTTPException(status_code=403, detail="Video limit reached for your subscription tier")
        
        # Create video
        video_status = video_manager.create_video_request(current_user["user_id"], video_data)
        
        # Update usage metrics
        subscription_manager.update_usage_metrics(current_user["user_id"], "videos_created")
        
        return {
            "success": True,
            "message": "Video creation started",
            "data": video_status.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating video: {e}")
        raise HTTPException(status_code=500, detail="Failed to create video")

@router.get("/api/videos")
async def get_user_videos(current_user: dict = Depends(get_current_user)):
    """Get user's videos."""
    try:
        videos = video_manager.get_user_videos(current_user["user_id"])
        return {
            "success": True,
            "data": [video.dict() for video in videos]
        }
    except Exception as e:
        logger.error(f"Error getting videos: {e}")
        raise HTTPException(status_code=500, detail="Failed to get videos")

@router.get("/api/videos/{video_id}")
async def get_video(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific video."""
    try:
        video = video_manager.get_video(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        if video.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "success": True,
            "data": video.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video")

@router.delete("/api/videos/{video_id}")
async def delete_video(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete video."""
    try:
        success = video_manager.delete_video(video_id, current_user["user_id"])
        if not success:
            raise HTTPException(status_code=404, detail="Video not found or access denied")
        
        return {
            "success": True,
            "message": "Video deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete video")

@router.post("/api/videos/{video_id}/upload")
async def upload_video_to_youtube(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Upload video to YouTube."""
    try:
        video = video_manager.get_video(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        if video.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if video.status != "completed":
            raise HTTPException(status_code=400, detail="Video not ready for upload")
        
        # Check if YouTube channel is connected
        channel_info = youtube_manager.get_channel_info(current_user["user_id"])
        if not channel_info:
            raise HTTPException(status_code=400, detail="YouTube channel not connected")
        
        # Simulate upload (in real implementation, this would upload the actual video)
        video_manager.update_video_status(
            video_id, 
            "uploaded", 
            youtube_id=f"yt_{video_id}",
            youtube_url=f"https://www.youtube.com/watch?v=yt_{video_id}"
        )
        
        # Update usage metrics
        subscription_manager.update_usage_metrics(current_user["user_id"], "videos_uploaded")
        
        return {
            "success": True,
            "message": "Video uploaded to YouTube successfully",
            "data": {
                "youtube_id": f"yt_{video_id}",
                "youtube_url": f"https://www.youtube.com/watch?v=yt_{video_id}"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload video")

@router.get("/api/subscription")
async def get_user_subscription(current_user: dict = Depends(get_current_user)):
    """Get user subscription."""
    try:
        subscription = subscription_manager.get_subscription(current_user["user_id"])
        if not subscription:
            # Create free subscription for new users
            subscription = subscription_manager.create_free_subscription(current_user["user_id"])
        
        tier_info = subscription_manager.get_tier_info(subscription.tier)
        
        return {
            "success": True,
            "data": {
                "subscription": subscription.dict(),
                "tier_info": tier_info.dict() if tier_info else None
            }
        }
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")

@router.post("/api/subscription/upgrade")
async def upgrade_subscription(
    tier: str,
    billing_cycle: str = "monthly",
    current_user: dict = Depends(get_current_user)
):
    """Upgrade user subscription."""
    try:
        subscription = subscription_manager.upgrade_subscription(
            current_user["user_id"], 
            tier, 
            billing_cycle
        )
        
        return {
            "success": True,
            "message": f"Upgraded to {tier} successfully",
            "data": subscription.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to upgrade subscription")

@router.post("/api/subscription/cancel")
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    """Cancel user subscription."""
    try:
        subscription = subscription_manager.cancel_subscription(current_user["user_id"])
        
        return {
            "success": True,
            "message": "Subscription cancelled successfully",
            "data": subscription.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@router.get("/api/billing/history")
async def get_billing_history(current_user: dict = Depends(get_current_user)):
    """Get user billing history."""
    try:
        billing_history = subscription_manager.get_billing_history(current_user["user_id"])
        
        return {
            "success": True,
            "data": [record.dict() for record in billing_history]
        }
    except Exception as e:
        logger.error(f"Error getting billing history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get billing history")

@router.get("/api/usage")
async def get_usage_metrics(current_user: dict = Depends(get_current_user)):
    """Get user usage metrics."""
    try:
        current_month = datetime.utcnow().strftime("%Y-%m")
        usage = subscription_manager.get_usage_metrics(current_user["user_id"], current_month)
        all_usage = subscription_manager.get_all_usage_metrics(current_user["user_id"])
        
        return {
            "success": True,
            "data": {
                "current_month": usage.dict() if usage else None,
                "all_months": [u.dict() for u in all_usage]
            }
        }
    except Exception as e:
        logger.error(f"Error getting usage metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get usage metrics")

@router.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics."""
    try:
        # Get video stats
        video_stats = video_manager.get_video_stats(current_user["user_id"])
        
        # Get subscription info
        subscription = subscription_manager.get_subscription(current_user["user_id"])
        tier_info = subscription_manager.get_tier_info(subscription.tier) if subscription else None
        
        # Get usage metrics
        current_month = datetime.utcnow().strftime("%Y-%m")
        usage = subscription_manager.get_usage_metrics(current_user["user_id"], current_month)
        
        # Get YouTube channel info
        channel_info = youtube_manager.get_channel_info(current_user["user_id"])
        
        return {
            "success": True,
            "data": {
                "video_stats": video_stats,
                "subscription": subscription.dict() if subscription else None,
                "tier_info": tier_info.dict() if tier_info else None,
                "usage": usage.dict() if usage else None,
                "youtube_channel": channel_info
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")

@router.get("/api/pricing/tiers")
async def get_pricing_tiers():
    """Get all pricing tiers."""
    try:
        tiers = subscription_manager.get_all_tiers()
        return {
            "success": True,
            "data": {name: tier.dict() for name, tier in tiers.items()}
        }
    except Exception as e:
        logger.error(f"Error getting pricing tiers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pricing tiers")

# YouTube Integration Routes

@router.get("/api/youtube/auth")
async def get_youtube_auth_url(current_user: dict = Depends(get_current_user)):
    """Get YouTube OAuth authorization URL."""
    try:
        user_id = current_user["user_id"]
        
        # Generate OAuth URL
        auth_url = youtube_manager.get_web_auth_url(user_id)
        
        logger.info(f"Generated YouTube auth URL for user {user_id}: {auth_url}")
        
        return {
            "success": True,
            "auth_url": auth_url,
            "message": "Click the link to connect your YouTube channel"
        }
    except HTTPException as e:
        logger.error(f"HTTP error getting YouTube auth URL: {e}")
        raise e
    except Exception as e:
        logger.error(f"Error getting YouTube auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate YouTube authorization URL")

@router.get("/api/youtube/status")
async def get_youtube_status(current_user: dict = Depends(get_current_user)):
    """Get YouTube connection status."""
    try:
        user_id = current_user["user_id"]
        channel_info = youtube_manager.get_channel_info(user_id)
        
        if channel_info:
            return {
                "success": True,
                "connected": True,
                "channel_info": channel_info,
                "demo_mode": channel_info.get("demo_mode", False)
            }
        else:
            return {
                "success": True,
                "connected": False,
                "channel_info": None
            }
    except Exception as e:
        logger.error(f"Error getting YouTube status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get YouTube status")

@router.get("/auth/youtube/callback")
async def youtube_auth_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None
):
    """Handle YouTube OAuth callback."""
    try:
        logger.info(f"YouTube callback received: code={code}, state={state}, error={error}")
        
        if error:
            return templates.TemplateResponse("youtube_callback.html", {
                "request": request,
                "success": False,
                "error": error,
                "message": "YouTube authorization was cancelled or failed"
            })
        
        if not state:
            return templates.TemplateResponse("youtube_callback.html", {
                "request": request,
                "success": False,
                "error": "Missing user state",
                "message": "Authorization state not received"
            })
        
        # Handle the callback
        result = youtube_manager.handle_web_auth_callback(code, state)
        
        if result["success"]:
            return templates.TemplateResponse("youtube_callback.html", {
                "request": request,
                "success": True,
                "message": result["message"],
                "channel_info": result.get("channel_info", {})
            })
        else:
            return templates.TemplateResponse("youtube_callback.html", {
                "request": request,
                "success": False,
                "error": "Connection failed",
                "message": "Failed to connect YouTube channel"
            })
            
    except Exception as e:
        logger.error(f"Error handling YouTube callback: {e}")
        return templates.TemplateResponse("youtube_callback.html", {
            "request": request,
            "success": False,
            "error": str(e),
            "message": "An error occurred during YouTube authorization"
        })

@router.post("/api/youtube/disconnect")
async def disconnect_youtube(current_user: dict = Depends(get_current_user)):
    """Disconnect YouTube channel."""
    try:
        user_id = current_user["user_id"]
        result = youtube_manager.disconnect_channel(user_id)
        
        return {
            "success": True,
            "message": "YouTube channel disconnected successfully"
        }
    except Exception as e:
        logger.error(f"Error disconnecting YouTube: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect YouTube channel")

@router.get("/settings")
async def settings_page(request: Request, current_user: dict = Depends(get_current_user)):
    """Settings page."""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": current_user
    })

@router.get("/integrations/youtube")
async def youtube_integration_page(request: Request, current_user: dict = Depends(get_current_user)):
    """YouTube integration setup page - redirect to settings."""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": current_user
    }) 