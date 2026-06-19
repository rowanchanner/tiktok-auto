"""
YouTube Shorts Uploader
========================
Uploads videos to YouTube as Shorts using the YouTube Data API v3.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)


def upload_to_youtube(video_path: str, title: str, description: str, hashtags: list = None):
    """
    Upload a video to YouTube as a Short.
    
    Returns:
        video_id string if successful, None otherwise
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
                return None
            if not settings.youtube_token:
                logger.warning("⚠️  YouTube token not set — connect your YouTube account in Settings")
                return None
            
            token_data = json.loads(settings.youtube_token)
        
        # Check video duration — Shorts MUST be under 60 seconds
        try:
            import subprocess
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
                capture_output=True, text=True, timeout=10
            )
            duration = float(result.stdout.strip())
            if duration > 60:
                logger.warning(f"⚠️  Video is {duration:.0f}s — too long for YouTube Shorts (max 60s). Skipping.")
                return None
            logger.info(f"📐 Video duration: {duration:.0f}s (valid for Shorts)")
        except Exception as e:
            logger.warning(f"Could not check duration: {e} — uploading anyway")
        
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
        
        # CRITICAL: Add #Shorts to title — YouTube uses this to classify as Short
        if '#Shorts' not in title and '#shorts' not in title:
            max_title_len = 100 - len(' #Shorts') 
            if len(title) > max_title_len:
                title = title[:max_title_len - 3] + '...'
            title = f"{title} #Shorts"
        
        body = {
            'snippet': {
                'title': title,
                'description': full_description,
                'tags': [t.lstrip('#') for t in (hashtags or [])][:15] + ['Shorts'],
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
        
        logger.info(f"📺 Uploading to YouTube Shorts: \"{title}\"")
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response.get('id')
        logger.info(f"✅ YouTube Short uploaded! https://youtube.com/shorts/{video_id}")
        return video_id
        
    except Exception as e:
        logger.error(f"❌ YouTube upload failed: {e}")
        return None
