"""
Auto TikTok Poster — Duplicate Tracker
========================================
Tracks which videos have been posted to avoid duplicates.
Stores data in a JSON file at data/posted.json.
"""

import json
import os
import logging
from datetime import datetime, timezone

import config

logger = logging.getLogger(__name__)


def _ensure_data_dir():
    """Create the data directory if it doesn't exist."""
    os.makedirs(config.DATA_DIR, exist_ok=True)


def _load_posted() -> list[dict]:
    """Load the list of previously posted videos from disk."""
    if not os.path.exists(config.POSTED_LOG):
        return []
    try:
        with open(config.POSTED_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read posted log, starting fresh: {e}")
        return []


def _save_posted(entries: list[dict]):
    """Save the posted log to disk."""
    _ensure_data_dir()
    with open(config.POSTED_LOG, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def is_posted(video_id: str) -> bool:
    """Check if a video ID has already been posted."""
    entries = _load_posted()
    posted_ids = {entry["video_id"] for entry in entries}
    return video_id in posted_ids


def mark_posted(video_id: str, video_url: str, description: str = "", hashtags: list[str] = None):
    """Record a video as posted with timestamp and metadata."""
    entries = _load_posted()
    entry = {
        "video_id": video_id,
        "video_url": video_url,
        "description": description[:200] if description else "",
        "hashtags": hashtags or [],
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)
    _save_posted(entries)
    logger.info(f"✅ Marked video {video_id} as posted")


def get_posted_count_today() -> int:
    """Count how many videos have been posted today (UTC)."""
    entries = _load_posted()
    today = datetime.now(timezone.utc).date().isoformat()
    count = 0
    for entry in entries:
        posted_date = entry.get("posted_at", "")[:10]  # Extract YYYY-MM-DD
        if posted_date == today:
            count += 1
    return count


def get_all_posted_ids() -> set[str]:
    """Return a set of all previously posted video IDs."""
    entries = _load_posted()
    return {entry["video_id"] for entry in entries}


def get_post_history(limit: int = 20) -> list[dict]:
    """Return the most recent posted entries."""
    entries = _load_posted()
    return entries[-limit:]
