#!/usr/bin/env python3
"""
YouTube Channel Management
Handles YouTube channel connection and API operations
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httpx

# Configure logging
logger = logging.getLogger(__name__)

# YouTube API configuration
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

class YouTubeManager:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.client_secrets_file = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE")
        
    def get_web_auth_url(self, user_id: str) -> str:
        """Generate web-based OAuth2 authorization URL for YouTube."""
        try:
            # Check if we have OAuth credentials configured
            client_id = os.getenv("YOUTUBE_WEB_CLIENT_ID")
            client_secret = os.getenv("YOUTUBE_WEB_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                raise HTTPException(
                    status_code=501, 
                    detail="YouTube integration not configured. Please set YOUTUBE_WEB_CLIENT_ID and YOUTUBE_WEB_CLIENT_SECRET environment variables."
                )
            
            # Create OAuth2 flow for web application
            flow = InstalledAppFlow.from_client_config({
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:8000/auth/youtube/callback"]
                }
            }, SCOPES)
            
            # Set redirect URI - prioritize Cloudflare tunnel URL
            redirect_uris = ["http://localhost:8000/auth/youtube/callback"]
            cloudflare_uri = next((uri for uri in redirect_uris if 'trycloudflare.com' in uri), None)
            flow.redirect_uri = cloudflare_uri or redirect_uris[0]
            
            # Generate authorization URL
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id,  # Pass user_id as state parameter
                prompt='consent'  # Always show consent screen
            )
            
            logger.info(f"Generated YouTube OAuth URL for user {user_id}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating YouTube auth URL: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate YouTube authorization URL")
    

    
    def handle_web_auth_callback(self, code: str, user_id: str) -> Dict[str, Any]:
        """Handle web-based OAuth2 callback and save credentials."""
        try:
            if not code:
                raise HTTPException(status_code=400, detail="Authorization code not received")
            
            # Exchange code for tokens
            client_id = os.getenv("YOUTUBE_WEB_CLIENT_ID")
            client_secret = os.getenv("YOUTUBE_WEB_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                raise HTTPException(status_code=501, detail="YouTube integration not configured")
            
            # Create OAuth2 flow
            flow = InstalledAppFlow.from_client_config({
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:8000/auth/youtube/callback"]
                }
            }, SCOPES)
            
            # Set redirect URI - prioritize Cloudflare tunnel URL
            redirect_uris = ["http://localhost:8000/auth/youtube/callback"]
            cloudflare_uri = next((uri for uri in redirect_uris if 'trycloudflare.com' in uri), None)
            flow.redirect_uri = cloudflare_uri or redirect_uris[0]
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=code)
            
            # Get credentials
            credentials = flow.credentials
            
            # Save credentials for user
            self.save_user_credentials(user_id, credentials)
            
            # Get channel info
            channel_info = self.get_channel_info_with_credentials(credentials)
            
            if not channel_info:
                raise HTTPException(status_code=400, detail="No YouTube channel found for this account")
            
            return {
                "success": True,
                "message": "YouTube channel connected successfully",
                "channel_info": channel_info
            }
            
        except Exception as e:
            logger.error(f"Error handling web auth callback: {e}")
            raise HTTPException(status_code=500, detail="Failed to complete YouTube authorization")
    

    
    def save_user_credentials(self, user_id: str, credentials: Credentials) -> None:
        """Save user credentials securely."""
        try:
            credentials_file = os.path.join(os.path.dirname(__file__), "user_credentials", f"{user_id}_youtube.json")
            os.makedirs(os.path.dirname(credentials_file), exist_ok=True)
            
            credentials_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes
            }
            
            with open(credentials_file, 'w') as f:
                json.dump(credentials_data, f)
                
            logger.info(f"Saved credentials for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
    

    
    def load_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Load user credentials."""
        try:
            credentials_file = os.path.join(os.path.dirname(__file__), "user_credentials", f"{user_id}_youtube.json")
            
            if not os.path.exists(credentials_file):
                return None
            
            with open(credentials_file, 'r') as f:
                credentials_data = json.load(f)
            

            
            credentials = Credentials(
                token=credentials_data["token"],
                refresh_token=credentials_data["refresh_token"],
                token_uri=credentials_data["token_uri"],
                client_id=credentials_data["client_id"],
                client_secret=credentials_data["client_secret"],
                scopes=credentials_data["scopes"]
            )
            
            return credentials
            
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return None
    
    def get_channel_info_with_credentials(self, credentials: Credentials) -> Optional[Dict[str, Any]]:
        """Get channel info using credentials."""
        try:
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Get channel info
            channels_response = youtube.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            if channels_response['items']:
                channel = channels_response['items'][0]
                return {
                    "channel_id": channel['id'],
                    "title": channel['snippet']['title'],
                    "description": channel['snippet']['description'],
                    "subscriber_count": int(channel['statistics'].get('subscriberCount', 0)),
                    "view_count": int(channel['statistics'].get('viewCount', 0)),
                    "video_count": int(channel['statistics'].get('videoCount', 0))
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None

    def get_auth_url(self, user_id: str) -> str:
        """Generate OAuth2 authorization URL for YouTube."""
        try:
            # Check if client secrets file exists and is valid
            if not self.client_secrets_file:
                logger.error("YouTube client secrets not configured.")
                raise HTTPException(
                    status_code=500, 
                    detail="YouTube integration not configured. Please run: python setup_youtube_api.py"
                )
            
            if not os.path.exists(self.client_secrets_file):
                logger.error(f"Client secrets file not found: {self.client_secrets_file}")
                raise HTTPException(
                    status_code=500, 
                    detail="YouTube credentials file not found. Please run: python setup_youtube_api.py"
                )
            
            # Validate client secrets file
            try:
                with open(self.client_secrets_file, 'r') as f:
                    secrets = json.load(f)
                    
                if 'web' not in secrets or 'client_id' not in secrets['web']:
                    raise ValueError("Invalid client secrets format")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Invalid client secrets file: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail="Invalid YouTube credentials file. Please run: python setup_youtube_api.py"
                )
            
            # Create OAuth2 flow with real credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file, SCOPES
            )
            
            # Set redirect URI - prioritize Cloudflare tunnel URL
            redirect_uris = ["http://127.0.0.1:8000/auth/youtube/callback"]
            cloudflare_uri = next((uri for uri in redirect_uris if 'trycloudflare.com' in uri), None)
            flow.redirect_uri = cloudflare_uri or redirect_uris[0]
            
            # Generate authorization URL
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id  # Pass user_id as state parameter
            )
            
            logger.info(f"Generated real YouTube OAuth URL for user {user_id}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating YouTube auth URL: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate YouTube authorization URL")
    
    def handle_auth_callback(self, code: str, user_id: str) -> Dict[str, Any]:
        """Handle OAuth2 callback and save credentials."""
        try:
            if not self.client_secrets_file:
                raise HTTPException(
                    status_code=500, 
                    detail="YouTube client secrets file not configured"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file, SCOPES
            )
            # Set redirect URI - prioritize Cloudflare tunnel URL
            redirect_uris = ["http://127.0.0.1:8000/auth/youtube/callback"]
            cloudflare_uri = next((uri for uri in redirect_uris if 'trycloudflare.com' in uri), None)
            flow.redirect_uri = (cloudflare_uri or redirect_uris[0]) + f"?user_id={user_id}"
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=code)
            
            # Get credentials
            credentials = flow.credentials
            
            # Save credentials for user
            self.save_user_credentials(user_id, credentials)
            
            # Get channel info
            channel_info = self.get_channel_info_with_credentials(credentials)
            
            return {
                "success": True,
                "message": "YouTube channel connected successfully",
                "channel_info": channel_info
            }
            
        except Exception as e:
            logger.error(f"Error handling auth callback: {e}")
            raise HTTPException(status_code=500, detail="Failed to complete YouTube authorization")

    def get_channel_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get channel info for user."""
        try:
            # Try to load user credentials
            credentials = self.load_user_credentials(user_id)
            
            if credentials:
                return self.get_channel_info_with_credentials(credentials)
            
            # No credentials found - user hasn't connected YouTube
            return None
            
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None
    
    def disconnect_channel(self, user_id: str) -> bool:
        """Disconnect YouTube channel for user."""
        try:
            credentials_file = os.path.join(os.path.dirname(__file__), "user_credentials", f"{user_id}_youtube.json")
            
            if os.path.exists(credentials_file):
                os.remove(credentials_file)
                logger.info(f"Disconnected YouTube channel for user {user_id}")
                return True
            
            return True  # Return True even if file doesn't exist
            
        except Exception as e:
            logger.error(f"Error disconnecting YouTube channel: {e}")
            return False
    
    def upload_video(self, user_id: str, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload video to YouTube channel with SEO optimization."""
        try:
            # Get user's YouTube credentials
            channel_info = self.get_channel_info(user_id)
            if not channel_info or not channel_info.get('credentials'):
                raise HTTPException(status_code=400, detail="YouTube channel not connected")
            
            # Ensure we have valid credentials
            if not channel_info.get('credentials'):
                raise HTTPException(status_code=400, detail="Invalid YouTube channel credentials")
            
            creds_data = channel_info['credentials']
            credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data['refresh_token'],
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes']
            )
            
            # Build YouTube service
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Generate SEO-optimized metadata
            optimized_data = self._optimize_video_metadata(video_data)
            
            # Prepare video metadata
            video_metadata = {
                'snippet': {
                    'title': optimized_data.get('title', 'Untitled Video'),
                    'description': optimized_data.get('description', ''),
                    'tags': optimized_data.get('tags', []),
                    'categoryId': optimized_data.get('category_id', '22'),  # People & Blogs
                    'defaultLanguage': 'en',
                    'defaultAudioLanguage': 'en'
                },
                'status': {
                    'privacyStatus': video_data.get('privacy', 'public'),
                    'publishAt': video_data.get('publish_at'),
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Upload video file
            video_file = video_data.get('file_path')
            if not video_file or not os.path.exists(video_file):
                raise HTTPException(status_code=400, detail="Video file not found")
            
            logger.info(f"Starting real YouTube upload: {video_file}")
            from googleapiclient.http import MediaFileUpload
            media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
            
            insert_request = youtube.videos().insert(
                part=','.join(video_metadata.keys()),
                body=video_metadata,
                media_body=media
            )
            
            # Execute upload
            response = insert_request.execute()
            video_id = response['id']
            logger.info(f"Real YouTube video uploaded successfully: {video_id}")
            
            return {
                "success": True,
                "video_id": video_id,
                "title": response['snippet']['title'],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "message": "Video uploaded successfully with SEO optimization!"
            }
            
        except HttpError as e:
            logger.error(f"YouTube upload error: {e}")
            raise HTTPException(status_code=400, detail=f"Upload failed: {e}")
        except Exception as e:
            logger.error(f"Error uploading video: {e}")
            raise HTTPException(status_code=500, detail="Video upload failed")
    

    
    def _optimize_video_metadata(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply SEO optimization to video metadata."""
        title = video_data.get('title', '')
        description = video_data.get('description', '')
        tags = video_data.get('tags', [])
        
        # Optimize title (max 100 characters for best SEO)
        optimized_title = title[:97] + "..." if len(title) > 100 else title
        
        # Enhance description with SEO elements
        optimized_description = self._enhance_description(description, title, tags)
        
        # Optimize tags
        optimized_tags = self._optimize_tags(tags, title)
        
        return {
            'title': optimized_title,
            'description': optimized_description,
            'tags': optimized_tags,
            'category_id': self._determine_category(title, description)
        }
    
    def _enhance_description(self, description: str, title: str, tags: List[str]) -> str:
        """Enhance video description for better SEO."""
        enhanced = description
        
        # Add hashtags from tags
        if tags:
            hashtags = " ".join([f"#{tag.replace(' ', '')}" for tag in tags[:3]])
            enhanced = f"{enhanced}\n\n{hashtags}"
        
        # Add call-to-action
        cta = "\n\n👍 Like this video if it helped you!\n🔔 Subscribe for more AI-powered content!\n💬 Comment below with your thoughts!"
        enhanced = f"{enhanced}{cta}"
        
        return enhanced[:5000]  # YouTube description limit
    
    def _optimize_tags(self, tags: List[str], title: str) -> List[str]:
        """Optimize tags for better discoverability."""
        optimized_tags = list(tags)
        
        # Add title words as tags
        title_words = [word.lower() for word in title.split() if len(word) > 3]
        for word in title_words[:3]:  # Add first 3 meaningful words
            if word not in [tag.lower() for tag in optimized_tags]:
                optimized_tags.append(word)
        
        # Add common YouTube keywords
        common_tags = ["AI", "tutorial", "how to", "guide", "tips", "2024"]
        for tag in common_tags:
            if tag.lower() not in [t.lower() for t in optimized_tags] and len(optimized_tags) < 10:
                optimized_tags.append(tag)
        
        return optimized_tags[:15]  # Limit to 15 tags
    
    def _determine_category(self, title: str, description: str) -> str:
        """Determine the best YouTube category based on content."""
        content = f"{title} {description}".lower()
        
        # Category mapping
        categories = {
            'education': '27',
            'howto': '26', 
            'tech': '28',
            'gaming': '20',
            'music': '10',
            'comedy': '23',
            'entertainment': '24',
            'news': '25',
            'sports': '17'
        }
        
        for keyword, category_id in categories.items():
            if keyword in content:
                return category_id
        
        return '22'  # Default: People & Blogs
    
    def get_video_analytics(self, user_id: str, video_id: str) -> Dict[str, Any]:
        """Get analytics for a specific video."""
        try:
            channel_info = self.get_channel_info(user_id)
            if not channel_info:
                raise HTTPException(status_code=400, detail="YouTube channel not connected")
            
            credentials = Credentials(**channel_info['credentials'])
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Get video statistics
            video_response = youtube.videos().list(
                part='statistics,snippet',
                id=video_id
            ).execute()
            
            if not video_response.get('items'):
                raise HTTPException(status_code=404, detail="Video not found")
            
            video = video_response['items'][0]
            stats = video['statistics']
            
            analytics = {
                'video_id': video_id,
                'title': video['snippet']['title'],
                'views': stats.get('viewCount', '0'),
                'likes': stats.get('likeCount', '0'),
                'comments': stats.get('commentCount', '0'),
                'published_at': video['snippet']['publishedAt']
            }
            
            return analytics
            
        except HttpError as e:
            logger.error(f"YouTube analytics error: {e}")
            raise HTTPException(status_code=400, detail=f"YouTube API error: {e}")
        except Exception as e:
            logger.error(f"Error getting video analytics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get video analytics")
    
    def disconnect_channel(self, user_id: str) -> Dict[str, Any]:
        """Disconnect YouTube channel from user account."""
        try:
            from auth import update_user_profile
            update_user_profile(user_id, {"youtube_channel": None})
            
            logger.info(f"YouTube channel disconnected for user {user_id}")
            
            return {
                "success": True,
                "message": "YouTube channel disconnected successfully"
            }
            
        except Exception as e:
            logger.error(f"Error disconnecting channel: {e}")
            raise HTTPException(status_code=500, detail="Failed to disconnect channel")

# Global instance
youtube_manager = YouTubeManager() 