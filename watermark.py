"""
Video Watermark Processor
==========================
Applies text watermarks to videos using ffmpeg before uploading.
"""

import os
import logging
import subprocess

logger = logging.getLogger(__name__)

# Position to ffmpeg drawtext coordinate mapping
POSITION_MAP = {
    'top-left':      'x=20:y=40',
    'top-center':    'x=(w-text_w)/2:y=40',
    'top-right':     'x=w-text_w-20:y=40',
    'bottom-left':   'x=20:y=h-text_h-40',
    'bottom-center': 'x=(w-text_w)/2:y=h-text_h-40',
    'bottom-right':  'x=w-text_w-20:y=h-text_h-40',
}


def hex_to_ffmpeg_color(hex_color, opacity=1.0):
    """Convert #RRGGBB + opacity to ffmpeg color format."""
    hex_color = hex_color.lstrip('#')
    alpha = int(opacity * 255)
    return f"#{hex_color}{alpha:02X}"


def apply_watermark(video_path: str, account_name: str) -> str:
    """
    Apply watermark to a video file.
    
    Args:
        video_path: Path to the input video
        account_name: TikTok username (for [username] replacement)
    
    Returns:
        Path to watermarked video, or original path if watermark is disabled/failed
    """
    try:
        from models import Settings, TikTokAccount
        from app import app
        
        with app.app_context():
            settings = Settings.query.first()
            if not settings or not settings.watermark_enabled:
                return video_path
            
            # Get watermark text (per-account override or global)
            watermark_text = settings.watermark_text or 'Follow [username] for more!'
            acc = TikTokAccount.query.filter_by(username=account_name).first()
            if acc and acc.watermark_text and acc.watermark_text.strip():
                watermark_text = acc.watermark_text
            
            # Replace [username] placeholder
            watermark_text = watermark_text.replace('[username]', f'@{account_name}')
            
            position = settings.watermark_position or 'bottom-center'
            font_size = settings.watermark_font_size or 24
            opacity = settings.watermark_opacity or 0.8
            color = settings.watermark_color or '#ffffff'
        
        # Build output path
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_watermarked{ext}"
        
        # Build ffmpeg drawtext filter
        pos_coords = POSITION_MAP.get(position, POSITION_MAP['bottom-center'])
        ffmpeg_color = hex_to_ffmpeg_color(color, opacity)
        
        # Escape special characters for ffmpeg drawtext
        escaped_text = watermark_text.replace("'", "'\\''").replace(":", "\\:")
        
        drawtext = (
            f"drawtext=text='{escaped_text}'"
            f":fontsize={font_size}"
            f":fontcolor={ffmpeg_color}"
            f":{pos_coords}"
            f":shadowcolor=black@0.7:shadowx=2:shadowy=2"
        )
        
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vf', drawtext,
            '-codec:a', 'copy',
            '-preset', 'ultrafast',
            output_path
        ]
        
        logger.info(f"💧 Applying watermark: \"{watermark_text}\"")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            logger.error(f"ffmpeg watermark failed: {result.stderr[-500:]}")
            return video_path  # Return original on failure
        
        # Replace original with watermarked version
        os.remove(video_path)
        os.rename(output_path, video_path)
        logger.info("💧 Watermark applied successfully!")
        return video_path
        
    except Exception as e:
        logger.error(f"Watermark error: {e}")
        return video_path  # Return original on any failure
