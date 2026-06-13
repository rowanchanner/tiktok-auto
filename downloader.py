"""
Auto TikTok Poster — Video Downloader
=======================================
Downloads TikTok videos without watermarks using yt-dlp.
Falls back to direct URL download via TikWM if yt-dlp fails.
"""

import os
import logging
import requests
import yt_dlp

import config

logger = logging.getLogger(__name__)


def _ensure_download_dir():
    """Create the downloads directory if it doesn't exist."""
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)


def _download_with_ytdlp(video_url: str, video_id: str) -> str | None:
    """
    Download a TikTok video using yt-dlp (removes watermark automatically).
    
    Returns the path to the downloaded file, or None on failure.
    """
    output_path = os.path.join(config.DOWNLOAD_DIR, f"{video_id}.mp4")

    ydl_opts = {
        "format": "best",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "socket_timeout": 30,
        "retries": 3,
        # Merge to mp4 if needed
        "merge_output_format": "mp4",
    }

    try:
        logger.info(f"⬇️  Downloading with yt-dlp: {video_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ Downloaded: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
            return output_path
        else:
            logger.warning("yt-dlp completed but output file not found")
            return None

    except Exception as e:
        logger.warning(f"yt-dlp download failed: {e}")
        return None


def _download_with_direct_url(download_url: str, video_id: str) -> str | None:
    """
    Download a video directly from the TikWM no-watermark URL.
    Fallback method if yt-dlp fails.
    
    Returns the path to the downloaded file, or None on failure.
    """
    if not download_url:
        logger.warning("No direct download URL available")
        return None

    output_path = os.path.join(config.DOWNLOAD_DIR, f"{video_id}.mp4")

    try:
        logger.info(f"⬇️  Downloading via direct URL (fallback)...")
        response = requests.get(download_url, timeout=60, stream=True, verify=False)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(output_path)
        if file_size < 10_000:  # Less than 10KB is probably an error page
            logger.warning(f"Downloaded file is suspiciously small ({file_size} bytes), likely invalid")
            os.remove(output_path)
            return None

        logger.info(f"✅ Downloaded: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
        return output_path

    except Exception as e:
        logger.error(f"Direct download failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None


def extract_metadata_with_ytdlp(video_url: str) -> dict:
    """
    Extract rich metadata from a TikTok video URL using yt-dlp.
    Does NOT download the video — metadata only.
    
    Returns a dict with description, hashtags, uploader, music info, etc.
    """
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            description = info.get("description", "") or info.get("title", "")
            
            # Extract hashtags from description
            hashtags = []
            if description:
                hashtags = [word for word in description.split() if word.startswith("#")]

            return {
                "description": description,
                "hashtags": hashtags,
                "uploader": info.get("uploader", ""),
                "uploader_id": info.get("uploader_id", ""),
                "track": info.get("track", ""),
                "artist": info.get("artist", ""),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "comment_count": info.get("comment_count", 0),
                "duration": info.get("duration", 0),
            }
    except Exception as e:
        logger.warning(f"yt-dlp metadata extraction failed: {e}")
        return {}


def download_video(video_data: dict) -> dict | None:
    """
    Main download function. Attempts yt-dlp first, falls back to direct URL.
    
    Args:
        video_data: Dict from discover.discover_video() containing:
            - video_id, video_url, download_url, title, hashtags, etc.
    
    Returns a dict with:
        - file_path: str (path to downloaded MP4)
        - video_id: str
        - description: str
        - hashtags: list[str]
        - author: str
        
    Returns None if download fails completely.
    """
    _ensure_download_dir()

    video_id = video_data["video_id"]
    video_url = video_data["video_url"]
    download_url = video_data.get("download_url", "")

    # Try yt-dlp first (most reliable, auto-removes watermark)
    file_path = _download_with_ytdlp(video_url, video_id)

    # Fallback to direct TikWM URL
    if not file_path:
        logger.info("Trying fallback download method...")
        file_path = _download_with_direct_url(download_url, video_id)

    if not file_path:
        logger.error(f"❌ All download methods failed for {video_id}")
        return None

    # Try to get richer metadata from yt-dlp
    metadata = extract_metadata_with_ytdlp(video_url)

    # Merge: prefer yt-dlp metadata, fall back to TikWM data
    description = metadata.get("description") or video_data.get("title", "")
    hashtags = metadata.get("hashtags") or video_data.get("hashtags", [])

    result = {
        "file_path": file_path,
        "video_id": video_id,
        "video_url": video_url,
        "description": description,
        "hashtags": hashtags,
        "author": metadata.get("uploader") or video_data.get("author", ""),
        "track": metadata.get("track", ""),
        "artist": metadata.get("artist", ""),
    }

    logger.info(
        f"📋 Metadata extracted:\n"
        f"   Description: {result['description'][:100]}...\n"
        f"   Hashtags: {' '.join(result['hashtags'][:10])}\n"
        f"   Music: {result['track']} — {result['artist']}"
    )

    return result
