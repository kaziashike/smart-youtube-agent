#!/usr/bin/env python3
"""
Automation Manager - Handles scheduled video creation and uploads
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import HTTPException
import schedule
import time
import threading

# Configure logging
logger = logging.getLogger(__name__)

class AutomationManager:
    def __init__(self):
        self.settings_file = Path(__file__).parent / "automation_settings.json"
        self.scheduler = schedule.Scheduler()
        self.running = False
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load automation settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading automation settings: {e}")
            return {}
    
    def _save_settings(self):
        """Save automation settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving automation settings: {e}")
    
    def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """Get automation settings for a specific user."""
        return self.settings.get(user_id, {
            "enabled": False,
            "niche": "",
            "frequency": "weekly",
            "upload_days": [],
            "upload_time": "09:00",
            "last_upload": None,
            "next_upload": None
        })
    
    def save_user_settings(self, user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Save automation settings for a user."""
        try:
            # Validate settings
            if not settings.get("niche"):
                raise HTTPException(status_code=400, detail="Video niche is required")
            
            if not settings.get("upload_days"):
                raise HTTPException(status_code=400, detail="At least one upload day is required")
            
            # Update settings
            self.settings[user_id] = {
                "enabled": settings.get("enabled", True),
                "niche": settings["niche"],
                "frequency": settings.get("frequency", "weekly"),
                "upload_days": settings["upload_days"],
                "upload_time": settings.get("upload_time", "09:00"),
                "last_upload": None,
                "next_upload": self._calculate_next_upload(settings)
            }
            
            self._save_settings()
            
            # Schedule job if enabled
            if settings.get("enabled"):
                self._schedule_user_job(user_id)
            
            return self.settings[user_id]
            
        except Exception as e:
            logger.error(f"Error saving automation settings for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to save automation settings")
    
    def _calculate_next_upload(self, settings: Dict[str, Any]) -> Optional[str]:
        """Calculate the next upload time based on settings."""
        try:
            upload_days = settings.get("upload_days", [])
            upload_time = settings.get("upload_time", "09:00")
            
            if not upload_days:
                return None
            
            now = datetime.now()
            current_day = now.strftime("%A").lower()
            
            # Find next upload day
            days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            current_day_index = days_of_week.index(current_day)
            
            next_upload_day = None
            for day in upload_days:
                day_index = days_of_week.index(day)
                if day_index > current_day_index:
                    next_upload_day = day
                    break
            
            if not next_upload_day:
                # If no day found this week, use the first day next week
                next_upload_day = upload_days[0]
            
            # Calculate next upload date
            target_day_index = days_of_week.index(next_upload_day)
            days_ahead = (target_day_index - current_day_index) % 7
            if days_ahead == 0 and now.time() >= datetime.strptime(upload_time, "%H:%M").time():
                days_ahead = 7
            
            next_upload_date = now + timedelta(days=days_ahead)
            next_upload_datetime = datetime.combine(
                next_upload_date.date(),
                datetime.strptime(upload_time, "%H:%M").time()
            )
            
            return next_upload_datetime.isoformat()
            
        except Exception as e:
            logger.error(f"Error calculating next upload: {e}")
            return None
    
    def _schedule_user_job(self, user_id: str):
        """Schedule automation job for a user."""
        try:
            settings = self.settings.get(user_id)
            if not settings or not settings.get("enabled"):
                return
            
            # Clear existing job for this user
            self.scheduler.clear(user_id)
            
            # Schedule job for each upload day
            for day in settings.get("upload_days", []):
                upload_time = settings.get("upload_time", "09:00")
                
                # Map day names to schedule library format
                day_map = {
                    "monday": schedule.every().monday,
                    "tuesday": schedule.every().tuesday,
                    "wednesday": schedule.every().wednesday,
                    "thursday": schedule.every().thursday,
                    "friday": schedule.every().friday,
                    "saturday": schedule.every().saturday,
                    "sunday": schedule.every().sunday
                }
                
                if day in day_map:
                    job = day_map[day].at(upload_time).do(self._create_automated_video, user_id)
                    job.tag(user_id)
                    
            logger.info(f"Scheduled automation jobs for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error scheduling job for user {user_id}: {e}")
    
    def _create_automated_video(self, user_id: str):
        """Create an automated video for a user and persist as 'prepared' (no auto-upload)."""
        try:
            settings = self.settings.get(user_id)
            if not settings:
                return
            
            logger.info(f"Creating automated video for user {user_id}")
            
            # Import here to avoid circular imports
            from enhanced_video_generator import enhanced_video_generator
            
            # Build video data
            niche = settings.get("niche", "general")
            title = f"Automated {niche.title()} Video"
            description = f"Automated video about {niche} topics"
            video_data = {
                "title": title,
                "topic": f"Latest trends in {niche}",
                "description": description,
                "duration": 60,
                "style": "educational",
                "tags": [niche, "automated", "trending"]
            }
            
            # Run the async generator in a local event loop
            try:
                result = asyncio.run(enhanced_video_generator.create_video_project(user_id, video_data))
            except RuntimeError:
                # If already in an event loop, create a new loop in thread-safe way
                loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(enhanced_video_generator.create_video_project(user_id, video_data))
                finally:
                    try:
                        loop.close()
                    except Exception:
                        pass
            
            if not result.get("success"):
                logger.error(f"Automated video generation failed for user {user_id}: {result}")
                return
            
            # Normalize paths relative to project root for streaming
            video_path_abs = Path(result.get("video_path", "")).resolve()
            project_root = Path.cwd().resolve()
            try:
                rel_video_path = str(video_path_abs.relative_to(project_root)).replace("\\", "/")
            except Exception:
                # Fallback: place under videos/ if absolute
                if "videos" in video_path_abs.parts:
                    idx = video_path_abs.parts.index("videos")
                    rel_video_path = "/".join(video_path_abs.parts[idx:])
                else:
                    rel_video_path = f"videos/{video_path_abs.name}"
            
            thumbnail_path = result.get("thumbnail_path")
            if thumbnail_path:
                thumb_abs = Path(thumbnail_path).resolve()
                try:
                    rel_thumb_path = str(thumb_abs.relative_to(project_root)).replace("\\", "/")
                except Exception:
                    if "videos" in thumb_abs.parts:
                        idx = thumb_abs.parts.index("videos")
                        rel_thumb_path = "/".join(thumb_abs.parts[idx:])
                    else:
                        rel_thumb_path = f"videos/thumbnails/{thumb_abs.name}"
            else:
                rel_thumb_path = None
            
            seo = result.get("seo_data", {})
            
            # Persist prepared record in user_data/<user_id>/videos.json
            user_videos_file = Path(f"user_data/{user_id}/videos.json")
            user_videos_file.parent.mkdir(parents=True, exist_ok=True)
            videos: list = []
            if user_videos_file.exists():
                try:
                    with open(user_videos_file, 'r', encoding='utf-8') as f:
                        videos = json.load(f)
                except Exception:
                    videos = []
            
            import uuid as _uuid
            video_id = str(_uuid.uuid4())
            prepared_record = {
                "id": video_id,
                "user_id": user_id,
                "title": seo.get("youtube_title") or title,
                "description": seo.get("youtube_description") or description,
                "script": result.get("script", ""),
                "style": video_data["style"],
                "duration": video_data["duration"],
                "status": "prepared",
                "created_at": datetime.now().isoformat(),
                "file_path": rel_video_path,
                "thumbnail_path": rel_thumb_path,
                "tags": seo.get("youtube_tags") or video_data.get("tags", []),
                "category_id": seo.get("youtube_category") or "22",
                "privacy_status": seo.get("youtube_privacy") or "public",
                "seo": seo
            }
            videos.append(prepared_record)
            with open(user_videos_file, 'w', encoding='utf-8') as f:
                json.dump(videos, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Prepared video saved for user {user_id}: {prepared_record['id']}")
            
            # Update upload times
            self.settings[user_id]["last_upload"] = datetime.now().isoformat()
            self.settings[user_id]["next_upload"] = self._calculate_next_upload(settings)
            self._save_settings()
            
        except Exception as e:
            logger.error(f"Error creating automated video for user {user_id}: {e}")
    
    def start_scheduler(self):
        """Start the automation scheduler."""
        if self.running:
            return
        
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Automation scheduler started")
    
    def stop_scheduler(self):
        """Stop the automation scheduler."""
        self.running = False
        logger.info("Automation scheduler stopped")
    
    def get_next_upload(self, user_id: str) -> Optional[str]:
        """Get the next scheduled upload time for a user."""
        settings = self.settings.get(user_id)
        if not settings or not settings.get("enabled"):
            return None
        
        return settings.get("next_upload")

    def set_enabled(self, user_id: str, enabled: bool) -> Dict[str, Any]:
        """Enable or disable automation for a user, persisting and updating schedules."""
        try:
            current = self.get_user_settings(user_id)
            # If enabling but no niche/days configured, require configuration first
            if enabled and (not current.get("niche") or not current.get("upload_days")):
                raise HTTPException(status_code=400, detail="Please configure niche, days and time before enabling automation")
            # Ensure user settings entry exists
            self.settings[user_id] = {
                **current,
                "enabled": enabled,
            }
            if not enabled:
                # Clear schedule and next upload
                try:
                    self.scheduler.clear(user_id)
                except Exception:
                    pass
                self.settings[user_id]["next_upload"] = None
            else:
                # Recalculate next upload and schedule jobs
                self.settings[user_id]["next_upload"] = self._calculate_next_upload(self.settings[user_id])
                self._schedule_user_job(user_id)
            self._save_settings()
            return self.settings[user_id]
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error setting automation enabled for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update automation status")

# Global instance
automation_manager = AutomationManager() 