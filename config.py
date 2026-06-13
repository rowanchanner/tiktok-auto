"""
Auto TikTok Poster — Configuration
====================================
"""

import os

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
DATA_DIR = os.path.join(BASE_DIR, "data")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
POSTED_LOG = os.path.join(DATA_DIR, "posted.json")

# ─── Constants ───────────────────────────────────────────────────────────────
TIKTOK_ACCOUNT = "rowanoutdoors"
MAX_DURATION_SECONDS = 180
FETCH_COUNT = 30
CLEANUP_AFTER_UPLOAD = True
TIKWM_API_BASE = "https://www.tikwm.com/api"
LOG_LEVEL = "INFO"

# ─── Dynamic DB Settings ─────────────────────────────────────────────────────
# We use Python's module-level __getattr__ to dynamically fetch these from the database
# when they are accessed, so that UI changes take effect immediately without restarting.

def __getattr__(name):
    try:
        from models import Settings
        from flask import current_app
        # If we have an active app context, query the DB
        if current_app:
            s = Settings.query.first()
            if not s:
                raise ValueError("No settings found")
            
            if name == "POST_INTERVAL_HOURS":
                return s.post_interval_hours
            elif name == "MAX_POSTS_PER_DAY":
                return s.max_posts_per_day
            elif name == "HASHTAGS":
                return [h.strip() for h in s.hashtags.split(',')] if s.hashtags else []
            elif name == "EXTRA_HASHTAGS":
                return [h.strip() for h in s.extra_hashtags.split(',')] if s.extra_hashtags else []
            elif name == "MIN_VIEWS":
                return s.min_views
            elif name == "PROXY_URL":
                return s.proxy_url
            elif name == "DISCORD_WEBHOOK_URL":
                return s.discord_webhook_url
    except Exception:
        pass # Fallback to defaults if no DB or no app context

    # Defaults
    if name == "POST_INTERVAL_HOURS":
        return 3
    elif name == "MAX_POSTS_PER_DAY":
        return 15
    elif name == "HASHTAGS":
        return ["movieclips", "moviescenes", "filmtok", "cinemascenes", "movietok", "filmclips", "moviemoments"]
    elif name == "EXTRA_HASHTAGS":
        return []
    elif name == "MIN_VIEWS":
        return 500000
    elif name == "PROXY_URL":
        return ""
    elif name == "DISCORD_WEBHOOK_URL":
        return ""

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
