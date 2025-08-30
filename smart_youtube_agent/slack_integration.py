#!/usr/bin/env python3
"""
Enhanced Slack Integration
Handles Slack bot interactions, video project management, and AI conversations
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from fastapi import HTTPException
from ai_brain import ai_brain
from enhanced_video_generator import enhanced_video_generator
from youtube_manager import youtube_manager

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

class SlackIntegration:
    def __init__(self):
        self.bot_token = SLACK_BOT_TOKEN
        self.signing_secret = SLACK_SIGNING_SECRET
        self.api_base_url = "https://slack.com/api"
        
    async def handle_slack_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Slack events."""
        event_type = event_data.get("type")
        
        if event_type == "url_verification":
            return {"challenge": event_data.get("challenge")}
        
        elif event_type == "event_callback":
            event = event_data.get("event", {})
            return await self.process_slack_event(event)
        
        return {"ok": True}
    
    async def process_slack_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process Slack event and generate response."""
        event_type = event.get("type")
        
        if event_type == "message":
            return await self.handle_slack_message(event)
        elif event_type == "app_mention":
            return await self.handle_app_mention(event)
        elif event_type == "reaction_added":
            return await self.handle_reaction(event)
        
        return {"ok": True}
    
    async def handle_slack_message(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle regular Slack message."""
        user_id = event.get("user")
        text = event.get("text", "")
        channel_id = event.get("channel")
        
        if not user_id or not text:
            return {"ok": True}
        
        # Ignore bot messages
        if event.get("bot_id"):
            return {"ok": True}
        
        try:
            # Process message with AI brain
            response = await ai_brain.process_message(user_id, text, platform="slack")
            
            # Send response back to Slack
            await self.send_slack_message(channel_id, response, user_id)
            
            return {"ok": True}
            
        except Exception as e:
            logger.error(f"Error handling Slack message: {e}")
            await self.send_slack_message(channel_id, "Sorry, I encountered an error. Please try again.", user_id)
            return {"ok": True}
    
    async def handle_app_mention(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle when bot is mentioned."""
        user_id = event.get("user")
        text = event.get("text", "")
        channel_id = event.get("channel")
        
        # Remove bot mention from text
        text = text.replace("<@BOT_ID>", "").strip()  # Replace with actual bot ID
        
        if not text:
            text = "Hello! How can I help you create videos today?"
        
        try:
            # Process message with AI brain
            response = await ai_brain.process_message(user_id, text, platform="slack")
            
            # Send response back to Slack
            await self.send_slack_message(channel_id, response, user_id)
            
            return {"ok": True}
            
        except Exception as e:
            logger.error(f"Error handling app mention: {e}")
            await self.send_slack_message(channel_id, "Sorry, I encountered an error. Please try again.", user_id)
            return {"ok": True}
    
    async def handle_reaction(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reaction events (for video actions)."""
        user_id = event.get("user")
        reaction = event.get("reaction")
        item = event.get("item", {})
        
        # Handle video-related reactions
        if reaction in ["video", "movie_camera", "play"]:
            await self.handle_video_reaction(user_id, reaction, item)
        
        return {"ok": True}
    
    async def handle_video_reaction(self, user_id: str, reaction: str, item: Dict[str, Any]):
        """Handle video-related reactions."""
        try:
            context = ai_brain.get_conversation_context(user_id)
            
            if reaction == "video":
                # Create new video project
                response = "What topic would you like to create a video about?"
                await self.send_slack_message(item.get("channel"), response, user_id)
            
            elif reaction == "movie_camera":
                # Show current video status
                if context.current_video_project:
                    status_response = await ai_brain.handle_get_status(context)
                    await self.send_slack_message(item.get("channel"), status_response, user_id)
                else:
                    await self.send_slack_message(item.get("channel"), "You don't have any active video projects.", user_id)
            
            elif reaction == "play":
                # Start video creation
                if context.current_video_project:
                    await self.start_video_creation(user_id, context.current_video_project)
                else:
                    await self.send_slack_message(item.get("channel"), "Please create a video project first.", user_id)
        
        except Exception as e:
            logger.error(f"Error handling video reaction: {e}")
    
    async def start_video_creation(self, user_id: str, video_project: Dict[str, Any]):
        """Start video creation process."""
        try:
            # Create video using enhanced generator
            video_data = {
                "video_id": f"slack_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "title": video_project.get("title", ""),
                "description": video_project.get("description", ""),
                "topic": video_project.get("topic", ""),
                "script": video_project.get("script", ""),
                "tags": video_project.get("tags", [])
            }
            
            # Start async video creation
            asyncio.create_task(self.create_video_async(user_id, video_data))
            
            # Send immediate response
            response = f"🎬 Starting video creation for: *{video_project.get('title', 'Your Video')}*\n\nThis will take a few minutes. I'll notify you when it's ready!"
            await self.send_slack_message_to_user(user_id, response)
            
        except Exception as e:
            logger.error(f"Error starting video creation: {e}")
            await self.send_slack_message_to_user(user_id, "Sorry, I couldn't start video creation. Please try again.")
    
    async def create_video_async(self, user_id: str, video_data: Dict[str, Any]):
        """Create video asynchronously and notify user when complete."""
        try:
            # Create video
            result = await enhanced_video_generator.create_video_project(user_id, video_data)
            
            if result["success"]:
                # Update AI brain context
                context = ai_brain.get_conversation_context(user_id)
                if context.current_video_project:
                    context.current_video_project["status"] = "video_created"
                    context.current_video_project["video_path"] = result["video_path"]
                
                # Send success notification
                success_message = f"""
✅ *Video Creation Complete!*

**Title:** {video_data.get('title', 'Your Video')}
**Duration:** {video_data.get('duration', 60)} seconds
**Status:** Ready for upload

Would you like me to:
1. Upload it to YouTube
2. Show you the video details
3. Create another video

React with :youtube: to upload to YouTube!
"""
                await self.send_slack_message_to_user(user_id, success_message)
                
            else:
                # Send error notification
                error_message = f"❌ Video creation failed: {result.get('error', 'Unknown error')}"
                await self.send_slack_message_to_user(user_id, error_message)
        
        except Exception as e:
            logger.error(f"Error in async video creation: {e}")
            await self.send_slack_message_to_user(user_id, "❌ Video creation failed. Please try again.")
    
    async def send_slack_message(self, channel_id: str, text: str, user_id: str = None) -> bool:
        """Send message to Slack channel."""
        try:
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "channel": channel_id,
                "text": text,
                "mrkdwn": True
            }
            
            if user_id:
                payload["text"] = f"<@{user_id}> {text}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/chat.postMessage",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info(f"Message sent to Slack channel {channel_id}")
                    return True
                else:
                    logger.error(f"Failed to send Slack message: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False
    
    async def send_slack_message_to_user(self, user_id: str, text: str) -> bool:
        """Send direct message to user."""
        try:
            # First, open DM with user
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            }
            
            # Open DM
            dm_payload = {"users": user_id}
            async with httpx.AsyncClient() as client:
                dm_response = await client.post(
                    f"{self.api_base_url}/conversations.open",
                    headers=headers,
                    json=dm_payload
                )
                
                if dm_response.status_code == 200:
                    dm_data = dm_response.json()
                    channel_id = dm_data.get("channel", {}).get("id")
                    
                    if channel_id:
                        return await self.send_slack_message(channel_id, text)
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending DM to user: {e}")
            return False
    
    async def send_interactive_message(self, channel_id: str, blocks: List[Dict[str, Any]], user_id: str = None) -> bool:
        """Send interactive message with blocks."""
        try:
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "channel": channel_id,
                "blocks": blocks
            }
            
            if user_id:
                payload["text"] = f"<@{user_id}>"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/chat.postMessage",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info(f"Interactive message sent to Slack channel {channel_id}")
                    return True
                else:
                    logger.error(f"Failed to send interactive message: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending interactive message: {e}")
            return False
    
    def create_video_creation_blocks(self, video_project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create Slack blocks for video creation interface."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎬 Create New Video"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Title:* {video_project.get('title', 'Untitled')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Topic:* {video_project.get('topic', 'General')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Duration:* {video_project.get('duration', 60)} seconds"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Style:* {video_project.get('style', 'Educational')}"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Create Video"
                        },
                        "value": "create_video",
                        "action_id": "create_video_btn",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Modify Script"
                        },
                        "value": "modify_script",
                        "action_id": "modify_script_btn"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Cancel"
                        },
                        "value": "cancel",
                        "action_id": "cancel_btn",
                        "style": "danger"
                    }
                ]
            }
        ]
        
        return blocks
    
    async def handle_interactive_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle interactive message responses."""
        try:
            actions = payload.get("actions", [])
            user_id = payload.get("user", {}).get("id")
            channel_id = payload.get("channel", {}).get("id")
            
            for action in actions:
                action_id = action.get("action_id")
                
                if action_id == "create_video_btn":
                    await self.handle_create_video_action(user_id, channel_id)
                elif action_id == "modify_script_btn":
                    await self.handle_modify_script_action(user_id, channel_id)
                elif action_id == "cancel_btn":
                    await self.handle_cancel_action(channel_id)
            
            return {"ok": True}
            
        except Exception as e:
            logger.error(f"Error handling interactive message: {e}")
            return {"ok": True}
    
    async def handle_create_video_action(self, user_id: str, channel_id: str):
        """Handle create video button action."""
        try:
            context = ai_brain.get_conversation_context(user_id)
            if context.current_video_project:
                await self.start_video_creation(user_id, context.current_video_project)
            else:
                await self.send_slack_message(channel_id, "Please create a video project first by typing a topic.", user_id)
        except Exception as e:
            logger.error(f"Error handling create video action: {e}")
    
    async def handle_modify_script_action(self, user_id: str, channel_id: str):
        """Handle modify script button action."""
        try:
            context = ai_brain.get_conversation_context(user_id)
            if context.current_video_project and context.current_video_project.get("script"):
                script = context.current_video_project["script"]
                await self.send_slack_message(channel_id, f"Current script:\n\n{script}\n\nReply with your modifications.", user_id)
            else:
                await self.send_slack_message(channel_id, "No script available to modify.", user_id)
        except Exception as e:
            logger.error(f"Error handling modify script action: {e}")
    
    async def handle_cancel_action(self, channel_id: str):
        """Handle cancel button action."""
        try:
            await self.send_slack_message(channel_id, "Video creation cancelled.")
        except Exception as e:
            logger.error(f"Error handling cancel action: {e}")

# Global instance
slack_integration = SlackIntegration() 