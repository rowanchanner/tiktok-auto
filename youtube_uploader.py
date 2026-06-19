"""
YouTube Shorts Uploader
========================
Uploads videos to YouTube as Shorts using the YouTube Data API v3.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)


def upload_to_youtube(video_path: str, title: str, description: str, hashtags: list = None) -> bool:
    """
    Upload a video to YouTube as a Short.
    
    Args:
        video_path: Path to the video file
        title: Video title
        description: Video description
        hashtags: List of hashtags to add
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
        from models import Settings
        from app import app
        
        # Get the stored YouTube token
        with app.app_context():
            settings = Settings.query.first()
            if not settings or not settings.youtube_enabled:
                logger.debug("YouTube upload disabled in settings")
                return False
            if not settings.youtube_token:
                logger.warning("⚠️  YouTube token not set — connect your YouTube account in Settings")
                return False
            
            token_data = json.loads(settings.youtube_token)
        
        # Build credentials from stored token
        creds = Credentials(
            token=token_data.get('access_token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        )
        
        # Build YouTube API client
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Build the description with hashtags
        tag_string = ""
        if hashtags:
            tag_string = " " + " ".join(f"#{t.lstrip('#')}" for t in hashtags[:10])
        
        full_description = f"{description}{tag_string}\n\n#Shorts"
        
        # Truncate title to 100 chars (YouTube limit)
        if len(title) > 100:
            title = title[:97] + "..."
        
        body = {
            'snippet': {
                'title': title,
                'description': full_description,
                'tags': [t.lstrip('#') for t in (hashtags or [])][:15],
                'categoryId': '22',  # People & Blogs
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False,
            }
        }
        
        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True,
            chunksize=1024 * 1024  # 1MB chunks
        )
        
        logger.info("📺 Uploading to YouTube Shorts...")
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response.get('id')
        logger.info(f"✅ YouTube Short uploaded! https://youtube.com/shorts/{video_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ YouTube upload failed: {e}")
        return False
