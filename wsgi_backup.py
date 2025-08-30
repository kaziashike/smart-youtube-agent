#!/usr/bin/env python3
"""
WSGI entry point for Smart YouTube Agent
This file ensures compatibility with Render.com's auto-detection
"""

import os
import sys

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Import the FastAPI app
from smart_youtube_agent.main_standalone import app

# WSGI application object
application = app

# For direct execution
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
