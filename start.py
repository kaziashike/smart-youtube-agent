#!/usr/bin/env python3
"""
Main entry point for Smart YouTube Agent
This file bypasses Render.com's auto-detection
"""

import os
import sys
import subprocess

def main():
    """Main entry point that starts the application."""
    print("🚀 Smart YouTube Agent Starting...")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"Port: {os.environ.get('PORT', '8000')}")
    
    # Add the current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    try:
        # Import and start the FastAPI app
        from smart_youtube_agent.main_standalone import app
        import uvicorn
        
        port = int(os.environ.get("PORT", 8000))
        print(f"Starting uvicorn server on port {port}")
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port, 
            workers=1,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Trying alternative import...")
        
        # Try alternative import path
        try:
            sys.path.insert(0, os.path.join(current_dir, "smart_youtube_agent"))
            from main_standalone import app
            import uvicorn
            
            port = int(os.environ.get("PORT", 8000))
            print(f"Starting uvicorn server on port {port}")
            
            uvicorn.run(
                app, 
                host="0.0.0.0", 
                port=port, 
                workers=1,
                log_level="info"
            )
            
        except Exception as e2:
            print(f"Alternative import failed: {e2}")
            print("Starting fallback server...")
            
            # Fallback: start a simple HTTP server
            import http.server
            import socketserver
            
            port = int(os.environ.get("PORT", 8000))
            handler = http.server.SimpleHTTPRequestHandler
            
            with socketserver.TCPServer(("", port), handler) as httpd:
                print(f"Fallback server running on port {port}")
                httpd.serve_forever()

if __name__ == "__main__":
    main()
