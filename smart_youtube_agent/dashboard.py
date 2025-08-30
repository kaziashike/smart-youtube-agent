#!/usr/bin/env python3
"""
Dashboard System
Provides admin dashboard for monitoring user activity and system status
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

# Configure logging
logger = logging.getLogger(__name__)

# Setup Jinja2 environment
template_dir = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(template_dir))

# Memory directory
MEMORY_DIR = os.path.join(os.path.dirname(__file__), "user_memory")

router = APIRouter()

def get_dashboard_secret() -> Optional[str]:
    """Get dashboard access secret from environment."""
    return os.getenv("DASHBOARD_SECRET")

def validate_token(token: str) -> None:
    """Validate dashboard access token."""
    secret = get_dashboard_secret()
    if not secret or token != secret:
        logger.warning(f"Invalid dashboard token attempt: {token[:10]}...")
        raise HTTPException(status_code=403, detail="Invalid dashboard token.")

def get_system_uptime() -> str:
    """Calculate system uptime from stored startup timestamp."""
    try:
        uptime_path = os.path.join(os.path.dirname(__file__), "uptime.txt")
        if not os.path.exists(uptime_path):
            with open(uptime_path, "w") as f:
                f.write(str(datetime.utcnow().timestamp()))
        
        with open(uptime_path, "r") as f:
            start_ts = float(f.read().strip())
        
        delta = datetime.utcnow() - datetime.fromtimestamp(start_ts)
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except Exception as e:
        logger.error(f"Error calculating uptime: {e}")
        return "Unknown"

def safe_load_user_memory(user_id: str, file_path: str) -> Optional[Dict[str, Any]]:
    """Safely load user memory file with error handling."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Corrupted JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def get_all_user_memory() -> List[Tuple[str, Dict[str, Any]]]:
    """Get all user memory data with error handling."""
    users = []
    if not os.path.exists(MEMORY_DIR):
        logger.warning(f"Memory directory does not exist: {MEMORY_DIR}")
        return users
    
    try:
        for fname in os.listdir(MEMORY_DIR):
            if fname.endswith(".json"):
                user_id = fname[:-5]
                file_path = os.path.join(MEMORY_DIR, fname)
                data = safe_load_user_memory(user_id, file_path)
                if data is not None:
                    users.append((user_id, data))
                else:
                    logger.warning(f"Skipping corrupted user file: {fname}")
    except Exception as e:
        logger.error(f"Error reading memory directory: {e}")
    
    return users

def get_global_stats(users: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
    """Calculate global system statistics."""
    try:
        total_users = len(users)
        total_videos = sum(len(u[1].get("videos", [])) for u in users)
        
        # Videos generated this month
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_videos = 0
        
        for _, data in users:
            for video in data.get("videos", []):
                if "created" in video:
                    try:
                        dt = datetime.fromisoformat(video["created"])
                        if dt >= month_start:
                            month_videos += 1
                    except (ValueError, TypeError):
                        continue
        
        # Model in use
        model = os.getenv("OPENROUTER_MODEL", "Unknown")
        
        # Auto mode status
        auto_mode_users = sum(1 for u in users if u[1].get("auto_mode_enabled", False))
        auto_mode_status = "ON" if auto_mode_users > 0 else "OFF"
        
        uptime = get_system_uptime()
        
        return {
            "total_users": total_users,
            "total_videos": total_videos,
            "month_videos": month_videos,
            "model": model,
            "auto_mode": auto_mode_status,
            "auto_mode_users": auto_mode_users,
            "uptime": uptime
        }
    except Exception as e:
        logger.error(f"Error calculating global stats: {e}")
        return {
            "total_users": 0,
            "total_videos": 0,
            "month_videos": 0,
            "model": "Unknown",
            "auto_mode": "Unknown",
            "auto_mode_users": 0,
            "uptime": "Unknown"
        }

def format_date(date_str: str) -> str:
    """Format date string for display."""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return date_str

def get_user_summary(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate user summary for dashboard display."""
    try:
        plan = data.get("subscription_tier", "Free").capitalize()
        videos = data.get("videos", [])
        
        # Get last 3 videos
        recent_videos = videos[-3:] if videos else []
        last_video = videos[-1] if videos else None
        
        last_title = last_video.get("title", "No videos") if last_video else "No videos"
        last_date = format_date(last_video.get("created", "")) if last_video else "N/A"
        yt_id = last_video.get("youtube_id") if last_video else None
        yt_link = f"https://youtube.com/watch?v={yt_id}" if yt_id else ""
        status = last_video.get("status", "Unknown") if last_video else "N/A"
        auto_mode = "ON" if data.get("auto_mode_enabled", False) else "OFF"
        thumbnail = last_video.get("thumbnail") if last_video else None
        
        # Video count
        video_count = len(videos)
        
        # Recent video summaries
        recent_video_summaries = []
        for video in recent_videos:
            video_summary = {
                "title": video.get("title", "Untitled"),
                "created": format_date(video.get("created", "")),
                "status": video.get("status", "Unknown"),
                "youtube_id": video.get("youtube_id"),
                "youtube_link": f"https://youtube.com/watch?v={video.get('youtube_id')}" if video.get("youtube_id") else None,
                "thumbnail": video.get("thumbnail"),
                "views": video.get("views", "N/A")
            }
            recent_video_summaries.append(video_summary)
        
        return {
            "user_id": user_id,
            "plan": plan,
            "video_count": video_count,
            "last_title": last_title,
            "last_date": last_date,
            "yt_link": yt_link,
            "status": status,
            "auto_mode": auto_mode,
            "thumbnail": thumbnail,
            "recent_videos": recent_video_summaries
        }
    except Exception as e:
        logger.error(f"Error generating user summary for {user_id}: {e}")
        return {
            "user_id": user_id,
            "plan": "Unknown",
            "video_count": 0,
            "last_title": "Error",
            "last_date": "N/A",
            "yt_link": "",
            "status": "Error",
            "auto_mode": "OFF",
            "thumbnail": None,
            "recent_videos": []
        }

def get_user_analytics(user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate user analytics data."""
    try:
        videos = user_data.get("videos", [])
        analytics = []
        
        for video in videos[-5:]:  # Last 5 videos
            analytics.append({
                "title": video.get("title", "Untitled"),
                "created": format_date(video.get("created", "")),
                "status": video.get("status", "Unknown"),
                "views": video.get("views", "N/A"),
                "youtube_id": video.get("youtube_id")
            })
        
        return analytics
    except Exception as e:
        logger.error(f"Error generating user analytics: {e}")
        return []

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    token: str = Query(..., description="Dashboard access token")
):
    """Main dashboard view showing system overview and user summaries."""
    try:
        validate_token(token)
        
        # Load user data
        users = get_all_user_memory()
        global_stats = get_global_stats(users)
        
        # Generate user summaries
        user_rows = []
        for user_id, data in users:
            summary = get_user_summary(user_id, data)
            user_rows.append(summary)
        
        # Sort users by last activity (most recent first)
        user_rows.sort(key=lambda x: x["last_date"], reverse=True)
        
        template = env.get_template("dashboard.html")
        return template.render(
            request=request,
            global_stats=global_stats,
            user_rows=user_rows,
            user_detail=None,
            llm_msgs=[],
            video_history=[],
            analytics=[],
            current_user_id=None
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        raise HTTPException(status_code=500, detail="Dashboard error")

@router.get("/dashboard/{user_id}", response_class=HTMLResponse)
async def dashboard_user(
    request: Request, 
    user_id: str,
    token: str = Query(..., description="Dashboard access token")
):
    """Individual user dashboard showing detailed analytics and memory dump."""
    try:
        validate_token(token)
        
        # Load all users for global stats
        users = get_all_user_memory()
        global_stats = get_global_stats(users)
        
        # Find specific user
        user_detail = None
        for uid, data in users:
            if uid == user_id:
                user_detail = data
                break
        
        if not user_detail:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Extract recent LLM messages
        llm_msgs = []
        try:
            interactions = user_detail.get("interactions", [])
            llm_msgs = [
                {
                    "intent": i.get("intent", "Unknown"),
                    "text": i.get("text", ""),
                    "timestamp": format_date(i.get("timestamp", "")) if "timestamp" in i else "N/A"
                }
                for i in interactions[-20:]  # Last 20 interactions
                if "intent" in i
            ]
        except Exception as e:
            logger.error(f"Error processing LLM messages for {user_id}: {e}")
        
        # Video history
        video_history = []
        try:
            videos = user_detail.get("videos", [])
            video_history = [
                {
                    "title": v.get("title", "Untitled"),
                    "created": format_date(v.get("created", "")),
                    "status": v.get("status", "Unknown"),
                    "youtube_id": v.get("youtube_id"),
                    "youtube_link": f"https://youtube.com/watch?v={v.get('youtube_id')}" if v.get("youtube_id") else None,
                    "thumbnail": v.get("thumbnail")
                }
                for v in videos[-10:]  # Last 10 videos
            ]
        except Exception as e:
            logger.error(f"Error processing video history for {user_id}: {e}")
        
        # Analytics
        analytics = get_user_analytics(user_detail)
        
        template = env.get_template("dashboard.html")
        return template.render(
            request=request,
            global_stats=global_stats,
            user_rows=[],
            user_detail=user_detail,
            llm_msgs=llm_msgs,
            video_history=video_history,
            analytics=analytics,
            current_user_id=user_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rendering user dashboard: {e}")
        raise HTTPException(status_code=500, detail="User dashboard error")
