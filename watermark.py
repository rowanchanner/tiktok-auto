"""
Video Watermark Processor
==========================
Applies text watermarks to videos using ffmpeg before uploading.
Supports: static, DVD bounce, scroll, and pulse animations.
"""

import os
import logging
import subprocess

logger = logging.getLogger(__name__)


def hex_to_ffmpeg_color(hex_color, opacity=1.0):
    """Convert #RRGGBB + opacity to ffmpeg color format."""
    hex_color = hex_color.lstrip('#')
    alpha = int(opacity * 255)
    return f"#{hex_color}{alpha:02X}"


def _build_drawtext(text, font_size, color, opacity, position, animation):
    """Build the ffmpeg drawtext filter string based on animation type."""
    escaped = text.replace("'", "'\\''").replace(":", "\\:").replace("%", "%%")
    ffmpeg_color = hex_to_ffmpeg_color(color, opacity)
    shadow = "shadowcolor=black@0.7:shadowx=2:shadowy=2"
    
    if animation == 'bounce':
        # DVD-style bounce — text bounces off all edges
        # Speed: ~80px/s horizontal, ~60px/s vertical (slightly different so it doesn't loop)
        return (
            f"drawtext=text='{escaped}'"
            f":fontsize={font_size}"
            f":fontcolor={ffmpeg_color}"
            f":x='abs(mod(t*80\\,2*(w-text_w))-(w-text_w))'"
            f":y='abs(mod(t*60\\,2*(h-text_h))-(h-text_h))'"
            f":{shadow}"
        )
    
    elif animation == 'scroll':
        # Scrolls from right to left across the bottom
        y_pos = 'h-text_h-40' if 'bottom' in position else '40'
        return (
            f"drawtext=text='{escaped}'"
            f":fontsize={font_size}"
            f":fontcolor={ffmpeg_color}"
            f":x='w-mod(t*120\\,w+text_w)'"
            f":y={y_pos}"
            f":{shadow}"
        )
    
    elif animation == 'pulse':
        # Fades in and out at fixed position
        pos_map = {
            'top-left':      'x=20:y=40',
            'top-center':    'x=(w-text_w)/2:y=40',
            'top-right':     'x=w-text_w-20:y=40',
            'bottom-left':   'x=20:y=h-text_h-40',
            'bottom-center': 'x=(w-text_w)/2:y=h-text_h-40',
            'bottom-right':  'x=w-text_w-20:y=h-text_h-40',
        }
        coords = pos_map.get(position, pos_map['bottom-center'])
        # Alpha pulses between 0.3 and 1.0
        alpha_expr = f"0.3+0.7*abs(sin(t*2))"
        return (
            f"drawtext=text='{escaped}'"
            f":fontsize={font_size}"
            f":fontcolor={color}"
            f":alpha='{alpha_expr}'"
            f":{coords}"
            f":{shadow}"
        )
    
    else:  # static
        pos_map = {
            'top-left':      'x=20:y=40',
            'top-center':    'x=(w-text_w)/2:y=40',
            'top-right':     'x=w-text_w-20:y=40',
            'bottom-left':   'x=20:y=h-text_h-40',
            'bottom-center': 'x=(w-text_w)/2:y=h-text_h-40',
            'bottom-right':  'x=w-text_w-20:y=h-text_h-40',
        }
        coords = pos_map.get(position, pos_map['bottom-center'])
        return (
            f"drawtext=text='{escaped}'"
            f":fontsize={font_size}"
            f":fontcolor={ffmpeg_color}"
            f":{coords}"
            f":{shadow}"
        )


def apply_watermark(video_path: str, account_name: str) -> str:
    """
    Apply watermark to a video file.
    
    Returns:
        Path to watermarked video, or original path if disabled/failed
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
            animation = settings.watermark_animation or 'static'
        
        # Build output path
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_watermarked{ext}"
        
        # Build ffmpeg filter
        drawtext = _build_drawtext(watermark_text, font_size, color, opacity, position, animation)
        
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vf', drawtext,
            '-codec:a', 'copy',
            '-preset', 'ultrafast',
            output_path
        ]
        
        anim_label = f" ({animation})" if animation != 'static' else ''
        logger.info(f"💧 Applying watermark{anim_label}: \"{watermark_text}\"")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            logger.error(f"ffmpeg watermark failed: {result.stderr[-500:]}")
            return video_path
        
        # Replace original with watermarked version
        os.remove(video_path)
        os.rename(output_path, video_path)
        logger.info("💧 Watermark applied successfully!")
        return video_path
        
    except Exception as e:
        logger.error(f"Watermark error: {e}")
        return video_path
