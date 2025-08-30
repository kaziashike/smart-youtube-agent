#!/usr/bin/env python3
"""
Simplified Smart YouTube Agent - Main Application
Optimized for Render.com deployment
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Smart YouTube Agent",
    description="AI-powered YouTube video creation platform",
    version="2.0.0"
)

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart YouTube Agent</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .feature { margin: 15px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff; }
            .btn { display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
            .btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Smart YouTube Agent</h1>
            <p>AI-powered YouTube video creation platform</p>
            
            <div class="feature">
                <strong>🤖 AI-powered video creation</strong> - Generate engaging videos with AI assistance
            </div>
            <div class="feature">
                <strong>💬 Real-time chat with AI assistant</strong> - Get help and guidance instantly
            </div>
            <div class="feature">
                <strong>🔗 Slack integration</strong> - Create videos directly from Slack
            </div>
            <div class="feature">
                <strong>📤 YouTube automation</strong> - Schedule and automate uploads
            </div>
            <div class="feature">
                <strong>🎯 SEO optimization</strong> - Optimize videos for better discoverability
            </div>
            <div class="feature">
                <strong>📱 Multi-platform support</strong> - Access from anywhere
            </div>
            
            <div style="margin-top: 30px;">
                <a href="/dashboard" class="btn">Go to Dashboard</a>
                <a href="/chat" class="btn">Chat with AI</a>
                <a href="/video-creator" class="btn">Create Video</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Smart YouTube Agent</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
            .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #e9ecef; }
            .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
            .btn { display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Dashboard</h1>
            <p>Welcome to your Smart YouTube Agent dashboard</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">0</div>
                    <div>Videos Created</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">0</div>
                    <div>Videos Uploaded</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">0</div>
                    <div>Total Views</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">0</div>
                    <div>Subscribers</div>
                </div>
            </div>
            
            <div style="margin-top: 30px;">
                <a href="/video-creator" class="btn">Create New Video</a>
                <a href="/chat" class="btn">Chat with AI</a>
                <a href="/" class="btn">Back to Home</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Chat interface page."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Chat - Smart YouTube Agent</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .chat-box { height: 400px; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 20px 0; background: #f8f9fa; overflow-y: auto; }
            .input-group { display: flex; gap: 10px; }
            input[type="text"] { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 5px; }
            .btn { padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Chat Assistant</h1>
            <p>Chat with our AI to create videos, get help, and more!</p>
            
            <div class="chat-box" id="chatBox">
                <div style="color: #666; text-align: center; margin-top: 150px;">
                    Start chatting with AI to create your first video!
                </div>
            </div>
            
            <div class="input-group">
                <input type="text" id="messageInput" placeholder="Type your message here...">
                <button class="btn" onclick="sendMessage()">Send</button>
            </div>
            
            <div style="margin-top: 20px;">
                <a href="/" class="btn" style="text-decoration: none;">Back to Home</a>
            </div>
        </div>
        
        <script>
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (message) {
                    const chatBox = document.getElementById('chatBox');
                    chatBox.innerHTML += '<div style="margin: 10px 0;"><strong>You:</strong> ' + message + '</div>';
                    chatBox.innerHTML += '<div style="margin: 10px 0; color: #007bff;"><strong>AI:</strong> Thanks for your message! I\'m here to help you create amazing videos.</div>';
                    input.value = '';
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
            }
            
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """)

@app.get("/video-creator", response_class=HTMLResponse)
async def video_creator_page(request: Request):
    """Video creator page."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Creator - Smart YouTube Agent</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
            .btn { padding: 15px 30px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 10px 5px; }
            .btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Video Creator</h1>
            <p>Create amazing YouTube videos with AI assistance</p>
            
            <form>
                <div class="form-group">
                    <label>Video Topic:</label>
                    <input type="text" placeholder="e.g., How to make the perfect pizza" required>
                </div>
                
                <div class="form-group">
                    <label>Video Style:</label>
                    <select>
                        <option>Educational Tutorial</option>
                        <option>Entertainment</option>
                        <option>Product Review</option>
                        <option>Vlog</option>
                        <option>News/Updates</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Target Duration:</label>
                    <select>
                        <option>Short (1-3 minutes)</option>
                        <option>Medium (5-10 minutes)</option>
                        <option>Long (15+ minutes)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Description:</label>
                    <textarea rows="4" placeholder="Describe what you want in your video..."></textarea>
                </div>
                
                <div class="form-group">
                    <label>Tags (comma separated):</label>
                    <input type="text" placeholder="e.g., tutorial, how-to, tips">
                </div>
                
                <button type="submit" class="btn">🚀 Create Video with AI</button>
            </form>
            
            <div style="margin-top: 30px;">
                <a href="/" class="btn" style="text-decoration: none;">Back to Home</a>
                <a href="/dashboard" class="btn" style="text-decoration: none;">Go to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Smart YouTube Agent",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
