# Smart YouTube Agent

An AI-powered YouTube video creation platform with advanced features including real-time chat, Slack integration, and automated video generation.

## Features

- 🤖 **AI-Powered Video Creation** - Generate YouTube videos using AI
- 💬 **Real-time Chat Interface** - Chat with AI assistant
- 🔗 **Slack Integration** - Connect with your Slack workspace
- 📊 **Dashboard Analytics** - Track video performance and statistics
- 🚀 **Automation Tools** - Schedule and automate video uploads
- 🎯 **SEO Optimization** - Optimize videos for better discoverability
- 🔐 **User Authentication** - Secure user management system

## Tech Stack

- **Backend**: FastAPI (Python 3.10)
- **Frontend**: HTML/CSS/JavaScript with Jinja2 templates
- **AI**: Custom AI brain for video generation
- **Database**: JSON-based storage system
- **Deployment**: Render.com ready

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/kaziashike/smart-youtube-agent.git
cd smart-youtube-agent
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python smart_youtube_agent/enhanced_main.py
```

5. Open your browser and go to `http://localhost:8000`

### Deployment on Render.com

1. Fork this repository
2. Connect your GitHub account to Render.com
3. Create a new Web Service
4. Select the repository
5. Render will automatically detect the configuration and deploy

## API Endpoints

- `GET /` - Landing page
- `GET /dashboard` - User dashboard
- `GET /chat` - Chat interface
- `GET /video-creator` - Video creation tool
- `POST /api/chat/message` - Send chat messages
- `GET /health` - Health check endpoint

## Project Structure

```
smart_youtube_agent/
├── enhanced_main.py          # Main application entry point
├── auth.py                   # Authentication system
├── ai_brain.py              # AI processing logic
├── video_routes.py          # Video creation endpoints
├── chat_interface.py        # Real-time chat system
├── slack_integration.py     # Slack bot integration
├── templates/               # HTML templates
├── static/                  # CSS, JS, and assets
└── user_memory/            # User data storage
```

## Configuration

The application uses environment variables for configuration. Create a `.env` file with:

```env
SECRET_KEY=your_secret_key_here
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_SIGNING_SECRET=your_slack_signing_secret
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue on GitHub. 