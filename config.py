"""
Auto TikTok Poster — Configuration
====================================
Edit these settings to customize behavior.
"""

import os

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
DATA_DIR = os.path.join(BASE_DIR, "data")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
POSTED_LOG = os.path.join(DATA_DIR, "posted.json")

# ─── TikTok Account ─────────────────────────────────────────────────────────
# Your TikTok username (without the @ symbol)
TIKTOK_ACCOUNT = "rowanoutdoors"

# ─── Discovery ───────────────────────────────────────────────────────────────
# Hashtags to search for movie clips (without the # symbol)
HASHTAGS = [
    "movieclips",
    "moviescenes",
    "filmtok",
    "cinemascenes",
    "movietok",
    "filmclips",
    "moviemoments",
]

# Minimum view count to consider a video "viral"
MIN_VIEWS = 500_000

# Maximum video duration in seconds (TikTok allows up to 10 min, but shorter clips repost better)
MAX_DURATION_SECONDS = 180

# Number of videos to fetch per hashtag search
FETCH_COUNT = 30

# ─── Posting ─────────────────────────────────────────────────────────────────
# Interval between auto-posts in hours (only used with --auto flag)
POST_INTERVAL_HOURS = 3

# Maximum posts per day (safety limit)
MAX_POSTS_PER_DAY = 15

# ─── Upload Settings ────────────────────────────────────────────────────────
# Add extra hashtags to every post (in addition to the original ones)
EXTRA_HASHTAGS = []  # e.g., ["#fyp", "#viral", "#foryou"]

# Whether to delete the downloaded video after successful upload
CLEANUP_AFTER_UPLOAD = True

# ─── TikWM API ───────────────────────────────────────────────────────────────
TIKWM_API_BASE = "https://www.tikwm.com/api"

# ─── Logging ─────────────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
