#!/usr/bin/env python3
"""
Video Management System
Handles video creation, processing, and management for the SaaS platform
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from pydantic import BaseModel
import httpx

# Configure logging
logger = logging.getLogger(__name__)

class VideoRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    topic: str
    duration: Optional[int] = 60  # seconds
    style: Optional[str] = "educational"  # educational, entertainment, business, etc.
    language: Optional[str] = "en"
    tags: Optional[List[str]] = []
    thumbnail_prompt: Optional[str] = ""

class VideoStatus(BaseModel):
    video_id: str
    user_id: str
    status: str  # pending, processing, completed, failed, uploaded
    progress: int  # 0-100
    created_at: str
    updated_at: str
    title: str
    description: str
    youtube_id: Optional[str] = None
    youtube_url: Optional[str] = None
    local_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    error_message: Optional[str] = None

class VideoManager:
    def __init__(self):
        self.videos_dir = os.path.join(os.path.dirname(__file__), "videos")
        self.videos_file = os.path.join(os.path.dirname(__file__), "videos.json")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure necessary directories exist."""
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(os.path.join(self.videos_dir, "temp"), exist_ok=True)
        os.makedirs(os.path.join(self.videos_dir, "thumbnails"), exist_ok=True)
        os.makedirs(os.path.join(self.videos_dir, "completed"), exist_ok=True)
    
    def load_videos(self) -> Dict[str, Any]:
        """Load videos from JSON file."""
        try:
            if os.path.exists(self.videos_file):
                with open(self.videos_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading videos: {e}")
            return {}
    
    def save_videos(self, videos: Dict[str, Any]) -> None:
        """Save videos to JSON file."""
        try:
            with open(self.videos_file, "w", encoding="utf-8") as f:
                json.dump(videos, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving videos: {e}")
            raise HTTPException(status_code=500, detail="Failed to save video data")
    
    def generate_video_id(self) -> str:
        """Generate unique video ID."""
        import secrets
        return f"video_{secrets.token_hex(8)}"
    
    def create_video_request(self, user_id: str, video_data: VideoRequest) -> VideoStatus:
        """Create a new video request."""
        videos = self.load_videos()
        
        video_id = self.generate_video_id()
        now = datetime.utcnow().isoformat()
        
        video_status = VideoStatus(
            video_id=video_id,
            user_id=user_id,
            status="pending",
            progress=0,
            created_at=now,
            updated_at=now,
            title=video_data.title,
            description=video_data.description or "",
            youtube_id=None,
            youtube_url=None,
            local_path=None,
            thumbnail_path=None,
            error_message=None
        )
        
        # Store video data
        videos[video_id] = video_status.dict()
        self.save_videos(videos)
        
        # Start async processing
        asyncio.create_task(self.process_video(video_id))
        
        logger.info(f"Created video request: {video_id} for user: {user_id}")
        return video_status
    
    async def process_video(self, video_id: str) -> None:
        """Process video asynchronously."""
        try:
            videos = self.load_videos()
            if video_id not in videos:
                logger.error(f"Video {video_id} not found")
                return
            
            video = videos[video_id]
            
            # Update status to processing
            video["status"] = "processing"
            video["progress"] = 10
            video["updated_at"] = datetime.utcnow().isoformat()
            self.save_videos(videos)
            
            # Step 1: Generate script (20%)
            await self.generate_script(video_id)
            video["progress"] = 30
            video["updated_at"] = datetime.utcnow().isoformat()
            self.save_videos(videos)
            
            # Step 2: Generate audio (40%)
            await self.generate_audio(video_id)
            video["progress"] = 50
            video["updated_at"] = datetime.utcnow().isoformat()
            self.save_videos(videos)
            
            # Step 3: Generate video (70%)
            await self.generate_video_content(video_id)
            video["progress"] = 80
            video["updated_at"] = datetime.utcnow().isoformat()
            self.save_videos(videos)
            
            # Step 4: Generate thumbnail (90%)
            await self.generate_thumbnail(video_id)
            video["progress"] = 95
            video["updated_at"] = datetime.utcnow().isoformat()
            self.save_videos(videos)
            
            # Step 5: Finalize video (100%)
            await self.finalize_video(video_id)
            video["status"] = "completed"
            video["progress"] = 100
            video["updated_at"] = datetime.utcnow().isoformat()
            self.save_videos(videos)
            
            logger.info(f"Video {video_id} processing completed")
            
        except Exception as e:
            logger.error(f"Error processing video {video_id}: {e}")
            await self.mark_video_failed(video_id, str(e))
    
    async def generate_script(self, video_id: str) -> None:
        """Generate video script using AI."""
        videos = self.load_videos()
        video = videos[video_id]
        
        # Simulate script generation
        await asyncio.sleep(2)  # Simulate processing time
        
        script = f"""
Title: {video['title']}
Duration: {video.get('duration', 60)} seconds

[Opening]
Welcome to our video about {video['title']}. Today we'll explore this fascinating topic in detail.

[Main Content]
{self.generate_content_for_topic(video['title'], video.get('topic', ''))}

[Closing]
Thank you for watching! Don't forget to like and subscribe for more content like this.
        """
        
        # Save script
        script_path = os.path.join(self.videos_dir, "temp", f"{video_id}_script.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        video["script_path"] = script_path
        self.save_videos(videos)
    
    async def generate_audio(self, video_id: str) -> None:
        """Generate audio from script using TTS."""
        videos = self.load_videos()
        video = videos[video_id]
        
        # Simulate audio generation
        await asyncio.sleep(3)  # Simulate processing time
        
        # Create dummy audio file
        audio_path = os.path.join(self.videos_dir, "temp", f"{video_id}_audio.wav")
        with open(audio_path, "w") as f:
            f.write("dummy audio content")
        
        video["audio_path"] = audio_path
        self.save_videos(videos)
    
    async def generate_video_content(self, video_id: str) -> None:
        """Generate video content using AI video generation."""
        videos = self.load_videos()
        video = videos[video_id]
        
        # Simulate video generation
        await asyncio.sleep(5)  # Simulate processing time
        
        # Create dummy video file
        video_path = os.path.join(self.videos_dir, "temp", f"{video_id}_content.mp4")
        with open(video_path, "w") as f:
            f.write("dummy video content")
        
        video["video_path"] = video_path
        self.save_videos(videos)
    
    async def generate_thumbnail(self, video_id: str) -> None:
        """Generate thumbnail using AI image generation."""
        videos = self.load_videos()
        video = videos[video_id]
        
        # Simulate thumbnail generation
        await asyncio.sleep(2)  # Simulate processing time
        
        # Create dummy thumbnail
        thumbnail_path = os.path.join(self.videos_dir, "thumbnails", f"{video_id}_thumb.jpg")
        with open(thumbnail_path, "w") as f:
            f.write("dummy thumbnail content")
        
        video["thumbnail_path"] = thumbnail_path
        self.save_videos(videos)
    
    async def finalize_video(self, video_id: str) -> None:
        """Finalize video by combining audio and video."""
        videos = self.load_videos()
        video = videos[video_id]
        
        # Simulate video finalization
        await asyncio.sleep(2)  # Simulate processing time
        
        # Create final video file
        final_path = os.path.join(self.videos_dir, "completed", f"{video_id}_final.mp4")
        with open(final_path, "w") as f:
            f.write("final video content")
        
        video["local_path"] = final_path
        self.save_videos(videos)
    
    async def mark_video_failed(self, video_id: str, error_message: str) -> None:
        """Mark video as failed."""
        videos = self.load_videos()
        if video_id in videos:
            videos[video_id]["status"] = "failed"
            videos[video_id]["error_message"] = error_message
            videos[video_id]["updated_at"] = datetime.utcnow().isoformat()
            self.save_videos(videos)
    
    def get_user_videos(self, user_id: str) -> List[VideoStatus]:
        """Get all videos for a user."""
        videos = self.load_videos()
        user_videos = []
        
        for video_data in videos.values():
            if video_data["user_id"] == user_id:
                user_videos.append(VideoStatus(**video_data))
        
        return sorted(user_videos, key=lambda x: x.created_at, reverse=True)
    
    def get_video(self, video_id: str) -> Optional[VideoStatus]:
        """Get video by ID."""
        videos = self.load_videos()
        if video_id in videos:
            return VideoStatus(**videos[video_id])
        return None
    
    def update_video_status(self, video_id: str, status: str, progress: int = None, **kwargs) -> None:
        """Update video status."""
        videos = self.load_videos()
        if video_id in videos:
            videos[video_id]["status"] = status
            videos[video_id]["updated_at"] = datetime.utcnow().isoformat()
            
            if progress is not None:
                videos[video_id]["progress"] = progress
            
            for key, value in kwargs.items():
                videos[video_id][key] = value
            
            self.save_videos(videos)
    
    def delete_video(self, video_id: str, user_id: str) -> bool:
        """Delete video (only if owned by user)."""
        videos = self.load_videos()
        if video_id in videos and videos[video_id]["user_id"] == user_id:
            # Remove video files
            video = videos[video_id]
            for path_key in ["local_path", "thumbnail_path", "script_path", "audio_path", "video_path"]:
                if path_key in video and video[path_key]:
                    try:
                        os.remove(video[path_key])
                    except:
                        pass
            
            # Remove from database
            del videos[video_id]
            self.save_videos(videos)
            return True
        return False
    
    def generate_content_for_topic(self, title: str, topic: str) -> str:
        """Generate content based on topic."""
        # This would integrate with your AI system
        return f"""
This is a comprehensive overview of {title}. We'll cover the key aspects and provide valuable insights.

Key Points:
1. Understanding the fundamentals
2. Practical applications
3. Best practices and tips
4. Common challenges and solutions

This content is designed to be informative and engaging for our audience.
        """
    
    def get_video_stats(self, user_id: str) -> Dict[str, Any]:
        """Get video statistics for a user."""
        videos = self.get_user_videos(user_id)
        
        total_videos = len(videos)
        completed_videos = len([v for v in videos if v.status == "completed"])
        processing_videos = len([v for v in videos if v.status == "processing"])
        failed_videos = len([v for v in videos if v.status == "failed"])
        uploaded_videos = len([v for v in videos if v.status == "uploaded"])
        
        return {
            "total_videos": total_videos,
            "completed_videos": completed_videos,
            "processing_videos": processing_videos,
            "failed_videos": failed_videos,
            "uploaded_videos": uploaded_videos,
            "success_rate": (completed_videos / total_videos * 100) if total_videos > 0 else 0
        }
    
    def get_user_video_stats(self, user_id: str) -> Dict[str, Any]:
        """Get video statistics for a specific user."""
        try:
            videos = self.load_videos()
            user_videos = [v for v in videos.values() if v.get('user_id') == user_id]
            
            total_videos = len(user_videos)
            uploaded_videos = len([v for v in user_videos if v.get('status') == 'uploaded'])
            
            # Get recent videos (last 10)
            recent_videos = sorted(user_videos, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
            
            # Format recent videos for display
            formatted_recent = []
            for video in recent_videos:
                formatted_recent.append({
                    "id": video.get('video_id', ''),
                    "title": video.get('title', 'Untitled'),
                    "status": video.get('status', 'unknown'),
                    "views": 0,  # Will be updated from YouTube API if available
                    "created_at": video.get('created_at', '')
                })
            
            return {
                "total_videos": total_videos,
                "uploaded_videos": uploaded_videos,
                "recent_videos": formatted_recent
            }
            
        except Exception as e:
            logger.error(f"Error getting user video stats: {e}")
            return {
                "total_videos": 0,
                "uploaded_videos": 0,
                "recent_videos": []
            }

# Global instance
video_manager = VideoManager() 