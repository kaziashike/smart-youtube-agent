#!/usr/bin/env python3
"""
Enhanced Video Generator
Integrates AI script generation with automated video creation using CapCut
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import subprocess
import sys
from pathlib import Path

# Import the existing Video_agent
from Video_agent import run as run_capcut_video

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedVideoGenerator:
    def __init__(self):
        self.videos_dir = os.path.join(os.path.dirname(__file__), "videos")
        self.temp_dir = os.path.join(self.videos_dir, "temp")
        self.completed_dir = os.path.join(self.videos_dir, "completed")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure necessary directories exist."""
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.completed_dir, exist_ok=True)
    
    async def generate_video_from_script(self, script: str, video_id: str, user_id: str) -> Dict[str, Any]:
        """Generate video from script using CapCut automation."""
        try:
            logger.info(f"Starting video generation for {video_id}")
            
            # Save script to file
            script_path = os.path.join(self.temp_dir, f"{video_id}_script.txt")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script)
            
            # Run CapCut automation
            video_path = await self.run_capcut_automation(script, video_id)
            
            if video_path and os.path.exists(video_path):
                return {
                    "success": True,
                    "video_path": video_path,
                    "script_path": script_path,
                    "status": "completed"
                }
            else:
                return {
                    "success": False,
                    "error": "Video generation failed",
                    "status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }
    
    async def run_capcut_automation(self, script: str, video_id: str) -> Optional[str]:
        """Run CapCut automation using the robust video generation service."""
        try:
            from video_generation_service import video_generation_service
            
            logger.info(f"Using video generation service for video {video_id}")
            
            # Use the robust video generation service
            result_path = await video_generation_service.generate_video(script, video_id)
            
            if result_path and os.path.exists(result_path):
                logger.info(f"Video generation completed successfully: {result_path}")
                return result_path
            else:
                logger.error("Video generation service returned no valid path")
                return None
            
        except Exception as e:
            logger.error(f"Error in CapCut automation service: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def generate_thumbnail(self, video_id: str, title: str, description: str) -> Optional[str]:
        """Generate thumbnail using AI image generation."""
        try:
            # Import thumbnail generator
            from thumbnail_generator import generate_thumbnail
            
            thumbnail_path = os.path.join(self.videos_dir, "thumbnails", f"{video_id}_thumb.jpg")
            
            # Generate thumbnail
            success = await generate_thumbnail(title, description, thumbnail_path)
            
            if success:
                return thumbnail_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None
    
    async def optimize_for_youtube(self, video_path: str, title: str, description: str, tags: List[str]) -> Dict[str, Any]:
        """Optimize video metadata for YouTube SEO."""
        try:
            # Generate SEO-optimized title and description
            seo_data = await self.generate_seo_optimization(title, description, tags)
            
            return {
                "success": True,
                "youtube_title": seo_data.get("title", title),
                "youtube_description": seo_data.get("description", description),
                "youtube_tags": seo_data.get("tags", tags),
                "youtube_category": seo_data.get("category", "22"),  # People & Blogs
                "youtube_privacy": "private"  # Start as private for review
            }
            
        except Exception as e:
            logger.error(f"Error optimizing for YouTube: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_seo_optimization(self, title: str, description: str, tags: List[str]) -> Dict[str, Any]:
        """Generate SEO-optimized metadata using AI."""
        from openrouter_utils import send_to_openrouter
        
        seo_prompt = f"""
Optimize this YouTube video metadata for maximum SEO performance:

Original Title: {title}
Original Description: {description}
Original Tags: {', '.join(tags)}

Generate optimized:
1. Title (under 60 characters, engaging, keyword-rich)
2. Description (under 5000 characters, includes keywords, call-to-action)
3. Tags (relevant keywords, trending topics)
4. Category (YouTube category ID)

Return as JSON:
{{
    "title": "optimized title",
    "description": "optimized description",
    "tags": ["tag1", "tag2", "tag3"],
    "category": "22"
}}
"""
        
        try:
            response = await send_to_openrouter(title, system_prompt=seo_prompt)
            if response:
                return json.loads(response)
        except Exception as e:
            logger.error(f"Error generating SEO optimization: {e}")
        
        # Fallback optimization
        return {
            "title": f"{title} - Complete Guide 2024",
            "description": f"{description}\n\n🔔 Subscribe for more content!\n👍 Like if this helped!\n💬 Comment your thoughts below!\n\n#youtube #content #viral",
            "tags": tags + ["youtube", "content", "viral", "trending"],
            "category": "22"
        }
    
    async def create_video_project(self, user_id: str, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a complete video project with AI-generated content."""
        try:
            video_id = video_data.get("video_id", f"video_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            
            # Step 1: Generate or use provided script
            script = video_data.get("script")
            if not script:
                script = await self.generate_script_from_topic(video_data.get("topic", ""))
            
            # Step 2: Generate video
            video_result = await self.generate_video_from_script(script, video_id, user_id)
            
            if not video_result["success"]:
                return video_result
            
            # Step 3: Generate thumbnail
            thumbnail_path = await self.generate_thumbnail(
                video_id, 
                video_data.get("title", ""), 
                video_data.get("description", "")
            )
            
            # Step 4: Optimize for YouTube
            seo_data = await self.optimize_for_youtube(
                video_result["video_path"],
                video_data.get("title", ""),
                video_data.get("description", ""),
                video_data.get("tags", [])
            )
            
            return {
                "success": True,
                "video_id": video_id,
                "video_path": video_result["video_path"],
                "thumbnail_path": thumbnail_path,
                "script": script,
                "seo_data": seo_data,
                "status": "completed",
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating video project: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }
    
    async def generate_script_from_topic(self, topic: str) -> str:
        """Generate script from topic using AI."""
        from openrouter_utils import send_to_openrouter
        
        script_prompt = f"""
Create an engaging YouTube video script about: {topic}

Requirements:
- Duration: 60-90 seconds
- Engaging opening hook
- Clear structure with main points
- Call-to-action at the end
- Natural, conversational tone
- Include relevant keywords

Make it entertaining and informative for a general audience.
"""
        
        try:
            script = await send_to_openrouter(topic, system_prompt=script_prompt)
            if script:
                return script
        except Exception as e:
            logger.error(f"Error generating script: {e}")
        
        # Fallback script
        return f"""
Welcome to our video about {topic}!

In this video, we'll explore everything you need to know about {topic}.

[Main content about {topic}]

Key takeaways:
1. Important point about {topic}
2. Another crucial aspect
3. Final thoughts

Thanks for watching! Don't forget to like and subscribe for more content like this.
"""
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Get current status of video generation."""
        video_path = os.path.join(self.completed_dir, f"{video_id}_final.mp4")
        thumbnail_path = os.path.join(self.videos_dir, "thumbnails", f"{video_id}_thumb.jpg")
        
        status = {
            "video_id": video_id,
            "video_exists": os.path.exists(video_path),
            "thumbnail_exists": os.path.exists(thumbnail_path),
            "video_path": video_path if os.path.exists(video_path) else None,
            "thumbnail_path": thumbnail_path if os.path.exists(thumbnail_path) else None,
            "status": "completed" if os.path.exists(video_path) else "processing"
        }
        
        return status

# Global instance
enhanced_video_generator = EnhancedVideoGenerator() 