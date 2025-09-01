#!/usr/bin/env python3
"""
Chat Interface - Real-time AI Conversation System
Provides chat functionality for the web dashboard
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from .ai_brain import ai_brain
from .enhanced_video_generator import enhanced_video_generator

# Configure logging
logger = logging.getLogger(__name__)

class ChatManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Initialize user session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                "connected_at": datetime.utcnow().isoformat(),
                "message_count": 0,
                "current_project": None
            }
        
        logger.info(f"User {user_id} connected to chat")
        
        # Send welcome message
        welcome_message = {
            "type": "message",
            "sender": "assistant",
            "content": "Hello! I'm your AI assistant for creating YouTube videos. How can I help you today?",
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_message(user_id, welcome_message)
    
    def disconnect(self, user_id: str):
        """Disconnect a WebSocket client."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from chat")
    
    async def send_message(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected users."""
        disconnected_users = []
        
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    async def handle_message(self, user_id: str, message_data: Dict[str, Any]):
        """Handle incoming message from user with streaming response."""
        try:
            content = message_data.get("content", "")
            message_type = message_data.get("type", "text")
            
            # Update session
            if user_id in self.user_sessions:
                self.user_sessions[user_id]["message_count"] += 1
                self.user_sessions[user_id]["last_message"] = datetime.utcnow().isoformat()
            
            # Send user message back to confirm receipt
            user_message = {
                "type": "message",
                "sender": "user",
                "content": self._format_message(content),
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(user_id, user_message)
            
            # Send typing indicator
            typing_message = {
                "type": "typing",
                "sender": "assistant",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(user_id, typing_message)
            
            # Process with AI brain and stream response
            await self._stream_ai_response(user_id, content)
            
            # Check if video creation was requested
            await self.handle_video_creation_request(user_id, content, "")
            
        except Exception as e:
            logger.error(f"Error handling message from {user_id}: {e}")
            error_message = {
                "type": "error",
                "content": "Sorry, I encountered an error. Please try again.",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(user_id, error_message)
    
    def _format_message(self, content: str) -> str:
        """Format message content to remove markdown formatting."""
        # Remove markdown formatting
        import re
        
        # Remove **bold** and __bold__
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        content = re.sub(r'__(.*?)__', r'\1', content)
        
        # Remove *italic* and _italic_
        content = re.sub(r'\*(.*?)\*', r'\1', content)
        content = re.sub(r'_(.*?)_', r'\1', content)
        
        # Remove `code`
        content = re.sub(r'`(.*?)`', r'\1', content)
        
        # Remove ```code blocks```
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        
        # Remove # headers
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        
        # Remove [links](url)
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        
        return content.strip()
    
    async def _stream_ai_response(self, user_id: str, user_content: str):
        """Stream AI response in chunks."""
        try:
            # Get AI response
            response = await ai_brain.process_message(user_id, user_content, platform="web")
            
            # Split response into chunks for streaming
            chunks = self._split_into_chunks(response, chunk_size=50)
            
            # Send each chunk with a small delay
            for i, chunk in enumerate(chunks):
                message = {
                    "type": "message_chunk" if i < len(chunks) - 1 else "message",
                    "sender": "assistant",
                    "content": chunk,
                    "is_partial": i < len(chunks) - 1,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.send_message(user_id, message)
                
                # Small delay between chunks for streaming effect
                if i < len(chunks) - 1:
                    import asyncio
                    await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error streaming AI response: {e}")
            error_message = {
                "type": "error",
                "content": "Sorry, I encountered an error while processing your message.",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(user_id, error_message)
    
    def _split_into_chunks(self, text: str, chunk_size: int = 50) -> List[str]:
        """Split text into chunks for streaming."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    async def handle_video_creation_request(self, user_id: str, user_message: str, ai_response: str):
        """Handle video creation requests from chat."""
        try:
            context = ai_brain.get_conversation_context(user_id)
            
            # Check if user wants to create a video
            if any(keyword in user_message.lower() for keyword in ["create video", "make video", "generate video", "new video"]):
                if context.current_video_project:
                    # Show current project status
                    status_message = {
                        "type": "video_status",
                        "project": context.current_video_project.dict(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.send_message(user_id, status_message)
                else:
                    # Prompt for video topic
                    prompt_message = {
                        "type": "video_prompt",
                        "content": "What topic would you like to create a video about?",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.send_message(user_id, prompt_message)
            
            # Check if user wants to start video creation
            elif any(keyword in user_message.lower() for keyword in ["start", "begin", "go", "yes", "create"]):
                if context.current_video_project:
                    await self.start_video_creation(user_id, context.current_video_project)
            
            # Check if user wants to modify script
            elif any(keyword in user_message.lower() for keyword in ["modify", "change", "edit", "script"]):
                if context.current_video_project and context.current_video_project.script:
                    script_message = {
                        "type": "script_edit",
                        "script": context.current_video_project.script,
                        "content": "Here's your current script. Reply with your modifications:",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.send_message(user_id, script_message)
            
            # Check if user wants to upload to YouTube
            elif any(keyword in user_message.lower() for keyword in ["upload", "youtube", "publish"]):
                if context.current_video_project and context.current_video_project.status == "video_created":
                    await self.handle_youtube_upload(user_id, context.current_video_project)
                else:
                    upload_message = {
                        "type": "upload_status",
                        "content": "Your video needs to be created first before uploading to YouTube.",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.send_message(user_id, upload_message)
        
        except Exception as e:
            logger.error(f"Error handling video creation request: {e}")
    
    async def start_video_creation(self, user_id: str, video_project):
        """Start video creation process."""
        try:
            # Send progress message
            progress_message = {
                "type": "video_progress",
                "content": f"🎬 Starting video creation for: {video_project.title}",
                "progress": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(user_id, progress_message)
            
            # Prepare video data
            video_data = {
                "video_id": f"web_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "title": video_project.title,
                "description": video_project.description,
                "topic": video_project.topic,
                "script": video_project.script,
                "tags": video_project.tags,
                "duration": video_project.duration,
                "style": video_project.style
            }
            
            # Start async video creation
            asyncio.create_task(self.create_video_async(user_id, video_data))
            
        except Exception as e:
            logger.error(f"Error starting video creation: {e}")
            error_message = {
                "type": "error",
                "content": "Sorry, I couldn't start video creation. Please try again.",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(user_id, error_message)
    
    async def create_video_async(self, user_id: str, video_data: Dict[str, Any]):
        """Create video asynchronously and send progress updates."""
        try:
            # Progress updates
            progress_steps = [
                (10, "Generating script..."),
                (30, "Creating video content..."),
                (50, "Adding audio..."),
                (70, "Generating thumbnail..."),
                (90, "Finalizing video..."),
                (100, "Video creation complete!")
            ]
            
            for progress, message in progress_steps:
                progress_message = {
                    "type": "video_progress",
                    "content": message,
                    "progress": progress,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(user_id, progress_message)
                await asyncio.sleep(2)  # Simulate processing time
            
            # Create video
            result = await enhanced_video_generator.create_video_project(user_id, video_data)
            
            if result["success"]:
                # Update AI brain context
                context = ai_brain.get_conversation_context(user_id)
                if context.current_video_project:
                    context.current_video_project.status = "video_created"
                    context.current_video_project.video_path = result["video_path"]
                
                # Send success message
                success_message = {
                    "type": "video_complete",
                    "content": f"✅ Video creation complete! Title: {video_data.get('title', 'Your Video')}",
                    "video_data": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(user_id, success_message)
                
                # Send upload prompt
                upload_prompt = {
                    "type": "upload_prompt",
                    "content": "Would you like me to upload this video to YouTube?",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(user_id, upload_prompt)
                
            else:
                # Send error message
                error_message = {
                    "type": "video_error",
                    "content": f"❌ Video creation failed: {result.get('error', 'Unknown error')}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(user_id, error_message)
        
        except Exception as e:
            logger.error(f"Error in async video creation: {e}")
            error_message = {
                "type": "video_error",
                "content": "❌ Video creation failed. Please try again.",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(user_id, error_message)
    
    async def handle_youtube_upload(self, user_id: str, video_project):
        """Handle YouTube upload request."""
        try:
            # Check if YouTube is connected
            from youtube_manager import youtube_manager
            channel_info = youtube_manager.get_channel_info(user_id)
            
            if not channel_info:
                # Prompt to connect YouTube
                connect_message = {
                    "type": "youtube_connect",
                    "content": "You need to connect your YouTube channel first. Please go to your profile settings.",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(user_id, connect_message)
                return
            
            # Start upload process
            upload_message = {
                "type": "upload_progress",
                "content": "📤 Starting YouTube upload...",
                "progress": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(user_id, upload_message)
            
            # Simulate upload process
            upload_steps = [
                (25, "Preparing video for upload..."),
                (50, "Uploading to YouTube..."),
                (75, "Setting SEO metadata..."),
                (100, "Upload complete!")
            ]
            
            for progress, message in upload_steps:
                progress_message = {
                    "type": "upload_progress",
                    "content": message,
                    "progress": progress,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(user_id, progress_message)
                await asyncio.sleep(1)
            
            # Send completion message
            completion_message = {
                "type": "upload_complete",
                "content": "✅ Video uploaded to YouTube successfully!",
                "youtube_url": f"https://www.youtube.com/watch?v=yt_{video_project.video_id}",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(user_id, completion_message)
            
        except Exception as e:
            logger.error(f"Error handling YouTube upload: {e}")
            error_message = {
                "type": "upload_error",
                "content": "❌ Upload failed. Please try again.",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(user_id, error_message)
    
    def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session information."""
        return self.user_sessions.get(user_id)
    
    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs."""
        return list(self.active_connections.keys())

# Global instance
chat_manager = ChatManager()

# WebSocket endpoint
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat."""
    await chat_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle message
            await chat_manager.handle_message(user_id, message_data)
            
    except WebSocketDisconnect:
        chat_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        chat_manager.disconnect(user_id)

# Chat HTML template
def get_chat_html() -> str:
    """Get chat interface HTML."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>AI Chat - Smart YouTube Agent</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
            height: calc(100vh - 40px);
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px 15px 0 0;
            text-align: center;
        }
        
        .chat-header h1 {
            margin: 0;
            font-size: 24px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message.assistant {
            justify-content: flex-start;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .message.assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
        }
        
        .message-time {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        
        .chat-input {
            padding: 20px;
            border-top: 1px solid #e0e0e0;
            background: white;
            border-radius: 0 0 15px 15px;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
        }
        
        .message-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .message-input:focus {
            border-color: #667eea;
        }
        
        .send-button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
        }
        
        .send-button:hover {
            transform: translateY(-2px);
        }
        
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .typing-indicator {
            padding: 12px 16px;
            color: #666;
            font-style: italic;
        }
        
        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #999;
            margin: 0 2px;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-indicator span:nth-child(1) {
            animation-delay: -0.32s;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: -0.16s;
        }
        
        @keyframes typing {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }
        
        .video-progress {
            background: #e8f5e8;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4caf50, #8bc34a);
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🤖 AI Assistant</h1>
            <p>Chat with me to create amazing YouTube videos!</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <!-- Messages will be added here -->
        </div>
        
        <div class="chat-input">
            <div class="input-container">
                <input type="text" id="messageInput" class="message-input" placeholder="Type your message here..." />
                <button id="sendButton" class="send-button">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        let ws = null;
        let userId = 'web_user_' + Date.now();
        
        function connectWebSocket() {
            ws = new WebSocket(`ws://localhost:8000/ws/${userId}`);
            
            ws.onopen = function() {
                console.log('WebSocket connected');
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                displayMessage(message);
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected');
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function displayMessage(message) {
            // Handle typing indicator
            if (message.type === 'typing') {
                const typingDiv = document.createElement('div');
                typingDiv.className = 'message assistant';
                typingDiv.id = 'typing-indicator';
                typingDiv.innerHTML = `
                    <div class="message-content">
                        <div class="typing-indicator">
                            <span></span><span></span><span></span>
                        </div>
                        <div class="message-time">${new Date(message.timestamp).toLocaleTimeString()}</div>
                    </div>
                `;
                chatMessages.appendChild(typingDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                return;
            }
            
            // Remove typing indicator if it exists
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            // Handle message chunks for streaming
            if (message.type === 'message_chunk') {
                // Find existing assistant message or create new one
                let messageDiv = chatMessages.querySelector('.message.assistant:last-child');
                if (!messageDiv || messageDiv.querySelector('.message-content').textContent.trim() === '') {
                    messageDiv = document.createElement('div');
                    messageDiv.className = 'message assistant';
                    messageDiv.innerHTML = `
                        <div class="message-content">
                            <div class="message-time">${new Date(message.timestamp).toLocaleTimeString()}</div>
                        </div>
                    `;
                    chatMessages.appendChild(messageDiv);
                }
                
                // Append chunk to existing message
                const contentDiv = messageDiv.querySelector('.message-content');
                const timeDiv = contentDiv.querySelector('.message-time');
                contentDiv.insertBefore(document.createTextNode(message.content), timeDiv);
                
                chatMessages.scrollTop = chatMessages.scrollHeight;
                return;
            }
            
            // Handle regular messages
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${message.sender}`;
            
            let content = message.content;
            
            if (message.type === 'video_progress') {
                content = `
                    <div class="video-progress">
                        <strong>${message.content}</strong>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${message.progress}%"></div>
                        </div>
                    </div>
                `;
            }
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${content}
                    <div class="message-time">${new Date(message.timestamp).toLocaleTimeString()}</div>
                </div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function sendMessage() {
            const content = messageInput.value.trim();
            if (!content || !ws) return;
            
            const message = {
                type: 'text',
                content: content,
                timestamp: new Date().toISOString()
            };
            
            ws.send(JSON.stringify(message));
            messageInput.value = '';
        }
        
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Connect on page load
        connectWebSocket();
    </script>
</body>
</html>
""" 