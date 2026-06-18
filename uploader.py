"""
Auto TikTok Poster — Video Uploader
=====================================
Uploads videos to TikTok using tiktokautouploader (stealth browser automation).
"""

import os
import logging

import config

logger = logging.getLogger(__name__)

# --- MONKEY PATCH TIKTOKAUTOUPLOADER DOCKER FLAGS ---
try:
    import tiktokautouploader.function as tf
    original_make_stealth_context = tf._make_stealth_context

    def patched_make_stealth_context(p, headless, proxy):
        stealth = tf.Stealth(navigator_languages_override=("en-US", "en"))
        browser = p.chromium.launch(
            headless=headless,
            proxy=proxy,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",             # <--- MANDATORY FOR DOCKER
                "--disable-dev-shm-usage",  # <--- MANDATORY FOR DOCKER
            ],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
        )
        stealth.apply_stealth_sync(context)
        return browser, context

    tf._make_stealth_context = patched_make_stealth_context
except ImportError:
    pass
# -----------------------------------------------


def _build_caption(description: str, hashtags: list[str]) -> str:
    """
    Build the upload caption from original description and hashtags.
    Adds any extra hashtags from config.
    """
    # Start with the original description
    caption = description.strip() if description else ""

    # Collect all hashtags (original + extras from config)
    all_hashtags = set()
    for tag in hashtags:
        # Normalize: ensure # prefix
        tag = tag.strip()
        if tag and not tag.startswith("#"):
            tag = f"#{tag}"
        if tag:
            all_hashtags.add(tag)

    for tag in config.EXTRA_HASHTAGS:
        tag = tag.strip()
        if tag and not tag.startswith("#"):
            tag = f"#{tag}"
        if tag:
            all_hashtags.add(tag)

    # Check which hashtags are already in the description
    existing_in_desc = {word for word in caption.split() if word.startswith("#")}
    new_tags = all_hashtags - existing_in_desc

    # Append new hashtags to the caption
    if new_tags:
        tag_string = " ".join(sorted(new_tags))
        if caption:
            caption = f"{caption} {tag_string}"
        else:
            caption = tag_string

    # TikTok caption limit is 2200 characters
    if len(caption) > 2200:
        caption = caption[:2197] + "..."

    return caption


def upload_video(video_info: dict, account_name: str = None, dry_run: bool = False) -> bool:
    """
    Upload a video to TikTok using tiktokautouploader.
    
    Args:
        video_info (dict): The result from download_video()
        account_name (str): The account username to use for cookies.
        dry_run (bool): If True, skip the actual upload.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    if not video_info:
        logger.error("No video info provided for upload")
        return False
        
    if not account_name:
        account_name = getattr(config, "TIKTOK_ACCOUNT", "rowanoutdoors")

    video_path = video_info.get('file_path')
    description = video_info.get('description', '')
    hashtags = video_info.get("hashtags", [])

    # Validate file exists
    if not os.path.exists(video_path):
        logger.error(f"❌ Video file not found: {video_path}")
        return False

    # Build caption (description without hashtags — hashtags are passed separately)
    caption = _build_caption(description, hashtags)
    
    # Separate hashtags from description text for the API
    desc_words = caption.split()
    clean_desc = " ".join(w for w in desc_words if not w.startswith("#"))
    tag_list = [w.lstrip("#") for w in desc_words if w.startswith("#")]
    
    logger.info(f"📝 Caption: {clean_desc[:200]}")
    logger.info(f"🏷️  Hashtags: {tag_list}")

    if dry_run:
        logger.info("🏃 DRY RUN — skipping actual upload")
        logger.info(f"   Would upload: {video_path}")
        return True

    try:
        # Import here to avoid import errors if package isn't installed yet
        from tiktokautouploader import upload_tiktok

        logger.info(f"📤 Uploading to TikTok...")
        
        # Pull a single burner proxy from the database
        from models import Proxy
        from app import app, db
        
        proxy_dict = None
        with app.app_context():
            burner = Proxy.query.first()
            if burner:
                raw_proxy = burner.proxy_url
                # Clean up any http:// or https:// prefixes
                if raw_proxy.startswith('http://'):
                    raw_proxy = raw_proxy[7:]
                elif raw_proxy.startswith('https://'):
                    raw_proxy = raw_proxy[8:]
                    
                # Parse user:pass@host:port format expected by the library
                if '@' in raw_proxy:
                    creds, hostport = raw_proxy.split('@', 1)
                    if ':' in creds:
                        user, pwd = creds.split(':', 1)
                        proxy_dict = {
                            "server": hostport,
                            "username": user,
                            "password": pwd
                        }
                    else:
                        proxy_dict = {"server": hostport}
                else:
                    proxy_dict = {"server": raw_proxy}
                    
                logger.info(f"🛡️  Using burner proxy: {proxy_dict['server']}")
                db.session.delete(burner)
                db.session.commit()
                logger.info(f"🔥 Burner proxy deleted from pool. {Proxy.query.count()} remaining.")
            else:
                logger.warning("⚠️  Burner Proxy Pool is EMPTY! Proceeding with naked IP...")

        result = upload_tiktok(
            video=video_path,
            description=clean_desc,
            accountname=account_name,
            hashtags=tag_list if tag_list else None,
            proxy=proxy_dict,
            copyrightcheck=False,
            headless=True,  # Always headless on Render
            suppressprint=False,
            stealth=True,
        )

        # The library returns "Error" if it can't confirm the upload
        if result and "error" in str(result).lower():
            logger.warning(f"⚠️  Upload uncertain — library returned: {result}")
            logger.warning("   Check your TikTok account to see if it posted.")
            return True  # Still mark as posted to avoid duplicates
        
        logger.info(f"✅ Upload successful! Result: {result}")
        return True

    except ImportError:
        logger.error(
            "❌ tiktokautouploader is not installed.\n"
            "   Run: pip install tiktokautouploader\n"
            "   Then: playwright install"
        )
        return False
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        return False


def cleanup_video(file_path: str):
    """Delete the downloaded video file after successful upload."""
    if config.CLEANUP_AFTER_UPLOAD and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"🗑️  Cleaned up: {file_path}")
        except OSError as e:
            logger.warning(f"Could not delete {file_path}: {e}")
