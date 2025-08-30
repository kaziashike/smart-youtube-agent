#!/usr/bin/env python3
"""
Minimal Smart YouTube Agent - Zero Dependencies
Can run even if package installation fails
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class SmartYouTubeAgentHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/" or path == "":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_landing_page().encode('utf-8'))
            
        elif path == "/dashboard":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_dashboard_page().encode('utf-8'))
            
        elif path == "/chat":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_chat_page().encode('utf-8'))
            
        elif path == "/video-creator":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_video_creator_page().encode('utf-8'))
            
        elif path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "Smart YouTube Agent",
                "version": "2.0.0",
                "deployment": "minimal",
                "message": "Running with zero external dependencies"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_404_page().encode('utf-8'))
    
    def get_landing_page(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Smart YouTube Agent</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .hero { text-align: center; color: white; margin: 60px 0; }
                .hero h1 { font-size: 3.5rem; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
                .hero p { font-size: 1.3rem; margin-bottom: 40px; opacity: 0.9; }
                .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin: 60px 0; }
                .feature-card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; transition: transform 0.3s ease; }
                .feature-card:hover { transform: translateY(-5px); }
                .feature-icon { font-size: 3rem; margin-bottom: 20px; }
                .feature-card h3 { color: #333; margin-bottom: 15px; font-size: 1.5rem; }
                .feature-card p { color: #666; line-height: 1.6; }
                .cta-buttons { text-align: center; margin: 60px 0; }
                .btn { display: inline-block; padding: 15px 30px; margin: 10px; background: #ff6b6b; color: white; text-decoration: none; border-radius: 50px; font-weight: bold; transition: all 0.3s ease; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
                .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }
                .btn.secondary { background: transparent; border: 2px solid white; }
                .btn.secondary:hover { background: white; color: #667eea; }
                .status-badge { background: #28a745; color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem; margin-bottom: 20px; display: inline-block; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="hero">
                    <div class="status-badge">✅ Deployed Successfully</div>
                    <h1>🚀 Smart YouTube Agent</h1>
                    <p>AI-powered YouTube video creation platform that revolutionizes content creation</p>
                </div>
                
                <div class="features">
                    <div class="feature-card">
                        <div class="feature-icon">🤖</div>
                        <h3>AI-Powered Creation</h3>
                        <p>Generate engaging video scripts and content using advanced AI technology</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">💬</div>
                        <h3>Smart Chat Assistant</h3>
                        <p>Get real-time help and guidance from our intelligent AI assistant</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🔗</div>
                        <h3>Slack Integration</h3>
                        <p>Create videos directly from your Slack workspace</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📤</div>
                        <h3>YouTube Automation</h3>
                        <p>Schedule and automate video uploads to YouTube</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🎯</div>
                        <h3>SEO Optimization</h3>
                        <p>Optimize your videos for better discoverability and ranking</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📱</div>
                        <h3>Multi-Platform</h3>
                        <p>Access your dashboard from anywhere, anytime</p>
                    </div>
                </div>
                
                <div class="cta-buttons">
                    <a href="/dashboard" class="btn">📊 Go to Dashboard</a>
                    <a href="/chat" class="btn secondary">💬 Chat with AI</a>
                    <a href="/video-creator" class="btn">🎬 Create Video</a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def get_dashboard_page(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Smart YouTube Agent</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }
                .header { background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header h1 { color: #333; text-align: center; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 25px; margin: 40px 0; }
                .stat-card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); text-align: center; border-left: 5px solid #667eea; }
                .stat-number { font-size: 3rem; font-weight: bold; color: #667eea; margin-bottom: 10px; }
                .stat-label { color: #666; font-size: 1.1rem; }
                .actions { text-align: center; margin: 40px 0; }
                .btn { display: inline-block; padding: 15px 30px; margin: 10px; background: #667eea; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; transition: all 0.3s ease; }
                .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
                .btn.secondary { background: #ff6b6b; }
                .recent-activity { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); margin: 40px 0; }
                .activity-item { padding: 15px 0; border-bottom: 1px solid #eee; display: flex; align-items: center; }
                .activity-item:last-child { border-bottom: none; }
                .activity-icon { font-size: 1.5rem; margin-right: 15px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Smart YouTube Agent Dashboard</h1>
            </div>
            
            <div class="container">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">0</div>
                        <div class="stat-label">Videos Created</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">0</div>
                        <div class="stat-label">Videos Uploaded</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">0</div>
                        <div class="stat-label">Total Views</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">0</div>
                        <div class="stat-label">Subscribers</div>
                    </div>
                </div>
                
                <div class="recent-activity">
                    <h2 style="margin-bottom: 20px; color: #333;">Recent Activity</h2>
                    <div class="activity-item">
                        <div class="activity-icon">🎉</div>
                        <div>Welcome to Smart YouTube Agent! Start creating your first video.</div>
                    </div>
                </div>
                
                <div class="actions">
                    <a href="/video-creator" class="btn">🎬 Create New Video</a>
                    <a href="/chat" class="btn secondary">💬 Chat with AI</a>
                    <a href="/" class="btn">🏠 Back to Home</a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def get_chat_page(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Chat - Smart YouTube Agent</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }
                .header { background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header h1 { color: #333; text-align: center; }
                .container { max-width: 800px; margin: 0 auto; padding: 20px; }
                .chat-container { background: white; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); overflow: hidden; }
                .chat-header { background: #667eea; color: white; padding: 20px; text-align: center; }
                .chat-box { height: 400px; padding: 20px; overflow-y: auto; background: #f8f9fa; }
                .message { margin: 15px 0; padding: 15px; border-radius: 10px; max-width: 80%; }
                .message.user { background: #667eea; color: white; margin-left: auto; }
                .message.ai { background: white; color: #333; border: 1px solid #e9ecef; }
                .input-area { padding: 20px; background: white; border-top: 1px solid #e9ecef; }
                .input-group { display: flex; gap: 10px; }
                input[type="text"] { flex: 1; padding: 15px; border: 2px solid #e9ecef; border-radius: 10px; font-size: 16px; outline: none; }
                input[type="text"]:focus { border-color: #667eea; }
                .send-btn { padding: 15px 25px; background: #667eea; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 16px; font-weight: bold; }
                .send-btn:hover { background: #5a6fd8; }
                .back-btn { display: inline-block; padding: 15px 30px; margin: 20px 0; background: #ff6b6b; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 AI Chat Assistant</h1>
            </div>
            
            <div class="container">
                <div class="chat-container">
                    <div class="chat-header">
                        <h2>Chat with AI to create amazing videos!</h2>
                    </div>
                    
                    <div class="chat-box" id="chatBox">
                        <div class="message ai">
                            <strong>AI Assistant:</strong> Hello! I'm here to help you create amazing YouTube videos. What would you like to create today?
                        </div>
                    </div>
                    
                    <div class="input-area">
                        <div class="input-group">
                            <input type="text" id="messageInput" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
                            <button class="send-btn" onclick="sendMessage()">Send</button>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <a href="/" class="back-btn">🏠 Back to Home</a>
                </div>
            </div>
            
            <script>
                function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (message) {
                        addMessage('You', message, 'user');
                        input.value = '';
                        
                        // Simulate AI response
                        setTimeout(() => {
                            const responses = [
                                "That's a great idea! Let me help you plan that video.",
                                "I can definitely help you create content about that topic!",
                                "Excellent choice! Here are some tips for your video...",
                                "I love that concept! Let's make it engaging and informative.",
                                "Perfect! I'll help you structure that video for maximum impact."
                            ];
                            const randomResponse = responses[Math.floor(Math.random() * responses.length)];
                            addMessage('AI Assistant', randomResponse, 'ai');
                        }, 1000);
                    }
                }
                
                function addMessage(sender, text, type) {
                    const chatBox = document.getElementById('chatBox');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${type}`;
                    messageDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
                    chatBox.appendChild(messageDiv);
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
                
                function handleKeyPress(event) {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                }
            </script>
        </body>
        </html>
        """
    
    def get_video_creator_page(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Video Creator - Smart YouTube Agent</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }
                .header { background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header h1 { color: #333; text-align: center; }
                .container { max-width: 800px; margin: 0 auto; padding: 20px; }
                .form-container { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); }
                .form-group { margin: 25px 0; }
                label { display: block; margin-bottom: 8px; font-weight: bold; color: #333; }
                input, textarea, select { width: 100%; padding: 15px; border: 2px solid #e9ecef; border-radius: 10px; font-size: 16px; outline: none; transition: border-color 0.3s ease; }
                input:focus, textarea:focus, select:focus { border-color: #667eea; }
                .submit-btn { width: 100%; padding: 20px; background: #667eea; color: white; border: none; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer; margin-top: 20px; transition: background 0.3s ease; }
                .submit-btn:hover { background: #5a6fd8; }
                .back-btn { display: inline-block; padding: 15px 30px; margin: 20px 0; background: #ff6b6b; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎬 Video Creator</h1>
            </div>
            
            <div class="container">
                <div class="form-container">
                    <form onsubmit="handleSubmit(event)">
                        <div class="form-group">
                            <label>Video Topic:</label>
                            <input type="text" placeholder="e.g., How to make the perfect pizza" required>
                        </div>
                        
                        <div class="form-group">
                            <label>Video Style:</label>
                            <select required>
                                <option value="">Select a style</option>
                                <option value="tutorial">Educational Tutorial</option>
                                <option value="entertainment">Entertainment</option>
                                <option value="review">Product Review</option>
                                <option value="vlog">Vlog</option>
                                <option value="news">News/Updates</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Target Duration:</label>
                            <select required>
                                <option value="">Select duration</option>
                                <option value="short">Short (1-3 minutes)</option>
                                <option value="medium">Medium (5-10 minutes)</option>
                                <option value="long">Long (15+ minutes)</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Description:</label>
                            <textarea rows="4" placeholder="Describe what you want in your video..." required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label>Tags (comma separated):</label>
                            <input type="text" placeholder="e.g., tutorial, how-to, tips">
                        </div>
                        
                        <button type="submit" class="submit-btn">🚀 Create Video with AI</button>
                    </form>
                </div>
                
                <div style="text-align: center;">
                    <a href="/" class="back-btn">🏠 Back to Home</a>
                    <a href="/dashboard" class="back-btn" style="background: #28a745;">📊 Go to Dashboard</a>
                </div>
            </div>
            
            <script>
                function handleSubmit(event) {
                    event.preventDefault();
                    alert('🎉 Video creation request submitted! Our AI is now working on your video. You\'ll receive a notification when it\'s ready.');
                }
            </script>
        </body>
        </html>
        """
    
    def get_404_page(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Page Not Found - Smart YouTube Agent</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f7fa; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); }
                h1 { color: #667eea; margin-bottom: 20px; }
                .btn { display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 10px; margin: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>404 - Page Not Found</h1>
                <p>The page you're looking for doesn't exist.</p>
                <a href="/" class="btn">🏠 Go Home</a>
            </div>
        </body>
        </html>
        """
    
    def log_message(self, format, *args):
        # Suppress log messages for cleaner output
        pass

def run_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), SmartYouTubeAgentHandler)
    print(f"🚀 Smart YouTube Agent running on port {port}")
    print(f"📱 Open your browser and go to: http://localhost:{port}")
    print("✅ Zero external dependencies - running with built-in Python HTTP server")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
