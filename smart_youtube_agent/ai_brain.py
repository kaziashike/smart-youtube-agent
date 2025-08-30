#!/usr/bin/env python3
"""
AI Brain - Intelligent Conversation and Video Generation System
Handles AI conversations, script generation, and video planning
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import httpx
from pydantic import BaseModel
from openrouter_utils import send_to_openrouter
from ai_memory_system import memory_system

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

KIMI_API_KEY = os.getenv("KIMI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class ConversationContext(BaseModel):
    user_id: str
    conversation_history: List[Dict[str, Any]] = []
    current_video_project: Optional[Dict[str, Any]] = None
    user_preferences: Dict[str, Any] = {}
    last_interaction: str = ""

class VideoProject(BaseModel):
    title: str
    description: str
    topic: str
    target_audience: str
    duration: int = 60
    style: str = "educational"
    language: str = "en"
    tags: List[str] = []
    script: Optional[str] = None
    status: str = "planning"  # planning, script_generated, video_created, uploaded

class AIBrain:
    def __init__(self):
        self.conversations: Dict[str, ConversationContext] = {}
        self.video_projects: Dict[str, VideoProject] = {}
    
    def get_conversation_context(self, user_id: str) -> ConversationContext:
        """Get or create conversation context for user with memory integration."""
        if user_id not in self.conversations:
            # Load conversation history from memory system
            recent_conversations = memory_system.get_conversation_history(user_id, limit=5)
            conversation_history = []
            
            for conv in recent_conversations:
                conversation_history.extend([
                    {"role": "user", "content": conv["message"], "timestamp": conv["created_at"]},
                    {"role": "assistant", "content": conv["response"], "timestamp": conv["created_at"]}
                ])
            
            # Get user preferences from memory
            user_preferences = memory_system.get_user_preferences(user_id)
            
            self.conversations[user_id] = ConversationContext(
                user_id=user_id,
                conversation_history=conversation_history,
                user_preferences=user_preferences
            )
        
        return self.conversations[user_id]
    
    async def process_message(self, user_id: str, message: str, platform: str = "web") -> str:
        """Process user message and return intelligent response."""
        context = self.get_conversation_context(user_id)
        
        # Add message to history
        context.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": platform
        })
        
        # Get relevant memories for context
        relevant_memories = memory_system.retrieve_memories(user_id, message, limit=3)
        
        # Analyze intent and generate response with memory context
        intent = await self.analyze_intent(message, context, relevant_memories)
        response = await self.generate_response(message, intent, context, relevant_memories)
        
        # Store conversation in memory system
        memory_system.store_conversation(
            user_id, 
            message, 
            response, 
            intent.get("intent", "general"),
            intent.get("parameters", {})
        )
        
        # Store important information as memories
        if intent.get("intent") in ["create_video", "modify_script", "user_preference"]:
            importance = 0.8 if intent.get("intent") == "create_video" else 0.6
            memory_system.store_memory(
                user_id,
                intent.get("intent"),
                f"User: {message}\nAssistant: {response}",
                {"intent": intent, "platform": platform},
                importance=importance
            )
        
        # Add response to history
        context.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": platform
        })
        
        context.last_interaction = datetime.utcnow().isoformat()
        return response
    
    async def analyze_intent(self, message: str, context: ConversationContext, memories: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze user intent using AI."""
        # Include memory context in prompt
        memory_context = ""
        if memories:
            memory_context = "Relevant past interactions:\n"
            for memory in memories[:3]:  # Limit to top 3 memories
                memory_context += f"- {memory['content'][:100]}...\n"
        
        intent_prompt = f"""
You are an AI assistant for a YouTube video creation platform. Analyze the user's intent and return a JSON response with:
- intent: The main intent (create_video, modify_script, get_status, upload_video, help, etc.)
- parameters: Relevant parameters extracted from the message
- confidence: Confidence score (0-1)
- suggested_actions: List of suggested next actions

User message: {message}
Current context: {context.current_video_project.dict() if context.current_video_project else "No active project"}
User preferences: {context.user_preferences}

{memory_context}

Return only valid JSON.
"""
        
        try:
            response = await send_to_openrouter(message, system_prompt=intent_prompt)
            if response:
                return json.loads(response)
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
        
        # Fallback intent analysis
        message_lower = message.lower()
        if any(word in message_lower for word in ["create", "make", "generate", "new video"]):
            return {"intent": "create_video", "confidence": 0.8, "parameters": {}, "suggested_actions": ["ask_for_topic"]}
        elif any(word in message_lower for word in ["script", "modify", "change", "edit"]):
            return {"intent": "modify_script", "confidence": 0.7, "parameters": {}, "suggested_actions": ["show_current_script"]}
        elif any(word in message_lower for word in ["status", "progress", "how"]):
            return {"intent": "get_status", "confidence": 0.9, "parameters": {}, "suggested_actions": ["show_status"]}
        elif any(word in message_lower for word in ["upload", "youtube", "publish"]):
            return {"intent": "upload_video", "confidence": 0.8, "parameters": {}, "suggested_actions": ["check_ready_to_upload"]}
        else:
            return {"intent": "general_chat", "confidence": 0.5, "parameters": {}, "suggested_actions": ["provide_help"]}
    
    async def generate_response(self, message: str, intent: Dict[str, Any], context: ConversationContext, memories: List[Dict[str, Any]] = None) -> str:
        """Generate intelligent response based on intent."""
        intent_type = intent.get("intent", "general_chat")
        
        if intent_type == "create_video":
            return await self.handle_create_video(message, context)
        elif intent_type == "modify_script":
            return await self.handle_modify_script(message, context)
        elif intent_type == "get_status":
            return await self.handle_get_status(context)
        elif intent_type == "upload_video":
            return await self.handle_upload_video(context)
        elif intent_type == "help":
            return await self.handle_help_request()
        else:
            return await self.handle_general_chat(message, context)
    
    async def handle_create_video(self, message: str, context: ConversationContext) -> str:
        """Handle video creation request."""
        if context.current_video_project:
            return "You already have an active video project. Would you like to modify it or start a new one?"
        
        # Extract video parameters from message
        video_params = await self.extract_video_parameters(message)
        
        # Create new video project
        project = VideoProject(**video_params)
        context.current_video_project = project
        
        # Generate initial script
        script = await self.generate_script(project)
        project.script = script
        project.status = "script_generated"
        
        return f"""
🎬 *New Video Project Created!*

**Title:** {project.title}
**Topic:** {project.topic}
**Duration:** {project.duration} seconds
**Style:** {project.style}

I've generated an initial script for your video. Would you like me to:
1. Show you the script for review
2. Start creating the video immediately
3. Modify the script first
4. Add more details to the project

What would you prefer?
"""
    
    async def handle_modify_script(self, message: str, context: ConversationContext) -> str:
        """Handle script modification request."""
        if not context.current_video_project:
            return "You don't have an active video project. Let's create one first!"
        
        project = context.current_video_project
        
        # Extract modification instructions
        modification_prompt = f"""
The user wants to modify the script for their video project.
Current script: {project.script}
User's modification request: {message}

Please provide the updated script based on the user's request.
"""
        
        try:
            updated_script = await send_to_openrouter(message, system_prompt=modification_prompt)
            if updated_script:
                project.script = updated_script
                return f"✅ Script updated successfully! Here's your modified script:\n\n{updated_script}\n\nWould you like to start creating the video now?"
        except Exception as e:
            logger.error(f"Error modifying script: {e}")
        
        return "I couldn't modify the script at the moment. Please try again or provide more specific instructions."
    
    async def handle_get_status(self, context: ConversationContext) -> str:
        """Handle status inquiry."""
        if not context.current_video_project:
            return "You don't have any active video projects. Let's create one!"
        
        project = context.current_video_project
        return f"""
📊 *Current Project Status*

**Title:** {project.title}
**Status:** {project.status}
**Topic:** {project.topic}
**Duration:** {project.duration} seconds

**Progress:**
- ✅ Project created
- {'✅' if project.script else '⏳'} Script generated
- {'✅' if project.status == 'video_created' else '⏳'} Video created
- {'✅' if project.status == 'uploaded' else '⏳'} Uploaded to YouTube

What would you like to do next?
"""
    
    async def handle_upload_video(self, context: ConversationContext) -> str:
        """Handle upload request."""
        if not context.current_video_project:
            return "You don't have a video to upload. Let's create one first!"
        
        project = context.current_video_project
        if project.status != "video_created":
            return f"Your video is still being created (status: {project.status}). Please wait for it to complete before uploading."
        
        return "🎬 Your video is ready for upload! I'll help you upload it to YouTube with optimized SEO settings."
    
    async def handle_help_request(self) -> str:
        """Handle help request."""
        return """
🤖 *Smart YouTube Agent Help*

I can help you with:

🎬 **Video Creation**
- Create new videos from topics
- Generate scripts automatically
- Modify scripts based on your feedback

📊 **Project Management**
- Check video creation status
- Track progress of your projects
- Manage multiple video projects

📤 **YouTube Integration**
- Upload videos to your YouTube channel
- Optimize SEO settings automatically
- Schedule uploads

💬 **Conversation**
- Chat naturally about your projects
- Get suggestions and recommendations
- Ask questions about video creation

**Commands:**
- "Create a video about [topic]"
- "Show me the script"
- "What's the status?"
- "Upload to YouTube"
- "Help" or "What can you do?"

What would you like to do?
"""
    
    async def handle_general_chat(self, message: str, context: ConversationContext) -> str:
        """Handle general conversation."""
        chat_prompt = f"""
You are a helpful AI assistant for a YouTube video creation platform. The user is having a general conversation with you.

User message: {message}
Current context: {context.current_video_project.dict() if context.current_video_project else "No active project"}

Respond naturally and helpfully. If they seem interested in creating videos, gently guide them toward that.
"""
        
        try:
            response = await send_to_openrouter(message, system_prompt=chat_prompt)
            if response:
                return response
        except Exception as e:
            logger.error(f"Error in general chat: {e}")
        
        return "I'm here to help you create amazing YouTube videos! What would you like to work on today?"
    
    async def extract_video_parameters(self, message: str) -> Dict[str, Any]:
        """Extract video parameters from user message."""
        extraction_prompt = f"""
Extract video creation parameters from the user's message and return a JSON object with:
- title: Video title
- topic: Main topic
- description: Video description
- target_audience: Target audience
- duration: Duration in seconds (default 60)
- style: Video style (educational, entertainment, business, etc.)
- language: Language code (default "en")
- tags: List of relevant tags

User message: {message}

Return only valid JSON.
"""
        
        try:
            response = await send_to_openrouter(message, system_prompt=extraction_prompt)
            if response:
                params = json.loads(response)
                # Set defaults for missing parameters
                params.setdefault("duration", 60)
                params.setdefault("style", "educational")
                params.setdefault("language", "en")
                params.setdefault("tags", [])
                return params
        except Exception as e:
            logger.error(f"Error extracting parameters: {e}")
        
        # Fallback parameter extraction
        return {
            "title": f"Video about {message.split()[:3]}",
            "topic": message,
            "description": f"A video about {message}",
            "target_audience": "general",
            "duration": 60,
            "style": "educational",
            "language": "en",
            "tags": []
        }
    
    async def generate_script(self, project: VideoProject) -> str:
        """Generate video script using AI."""
        script_prompt = f"""
Create an engaging video script for YouTube with the following parameters:

Title: {project.title}
Topic: {project.topic}
Description: {project.description}
Target Audience: {project.target_audience}
Duration: {project.duration} seconds

Language: {project.language}

Create a YouTube video script that is:
- Written in natural, fluent plain text (not in script-style brackets or labels like [Opening] or [Closing])
- Uses markdown formatting or hint comments only when needed
- Engaging and attention-grabbing from the very first sentence
- Well-structured with a logical flow, but without labeling sections with headers or brackets
- Optimized for a total duration of around 90 seconds
- Suitable for a general audience, beginner-friendly but insightful
- Includes a strong, conversational opening
- Ends with a clear, natural call-to-action (like subscribe, like, etc.) without sounding robotic
- Avoids any technical markers like `[scene]`, `[music]`, `[duration]`, or `[segment]`


Return the script in a natural, conversational format.
"""
        
        try:
            script = await send_to_openrouter(project.topic, system_prompt=script_prompt)
            if script:
                return script
        except Exception as e:
            logger.error(f"Error generating script: {e}")
        
        # Fallback script
        return f"""
Welcome to our video about {project.topic}!

In this {project.duration}-second video, we'll explore {project.topic} in detail.

[Main content would be generated here based on the topic]

Thank you for watching! Don't forget to like and subscribe for more content like this.
"""

# Global instance
ai_brain = AIBrain() 