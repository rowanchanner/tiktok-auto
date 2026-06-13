"""
Auto TikTok Poster — Video Discovery
======================================
Finds trending/viral movie clip TikToks using the TikWM API.
"""

import random
import logging
import requests
import urllib3

import config
import tracker

# Suppress SSL warnings (this machine has SSL cert verification issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def _fetch_videos_by_hashtag(hashtag: str) -> list[dict]:
    """
    Fetch videos for a given hashtag from the TikWM API.
    
    Returns a list of video data dicts with keys like:
      - id, title, play, wmplay, duration, play_count, etc.
    """
    url = f"{config.TIKWM_API_BASE}/feed/search"
    params = {
        "keywords": f"#{hashtag}",
        "count": config.FETCH_COUNT,
        "cursor": 0,
        "HD": 1,
    }

    try:
        logger.debug(f"Fetching videos for #{hashtag}...")
        response = requests.get(url, params=params, timeout=15, verify=False)
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0:
            logger.warning(f"TikWM API returned error for #{hashtag}: {data.get('msg', 'Unknown error')}")
            return []

        videos = data.get("data", {}).get("videos", [])
        if not videos:
            logger.warning(f"No videos found for #{hashtag}")
            return []

        logger.info(f"Found {len(videos)} videos for #{hashtag}")
        return videos

    except requests.RequestException as e:
        logger.error(f"Request failed for #{hashtag}: {e}")
        return []
    except (ValueError, KeyError) as e:
        logger.error(f"Failed to parse TikWM response for #{hashtag}: {e}")
        return []


def _extract_hashtags_from_title(title: str) -> list[str]:
    """Extract hashtags from a video title/description string."""
    if not title:
        return []
    words = title.split()
    hashtags = [word for word in words if word.startswith("#")]
    return hashtags


def _filter_videos(videos: list[dict]) -> list[dict]:
    """
    Filter videos by:
      - Minimum view count (viral threshold)
      - Maximum duration
      - Not already posted
    """
    posted_ids = tracker.get_all_posted_ids()
    filtered = []

    for video in videos:
        video_id = str(video.get("video_id", video.get("id", "")))
        play_count = video.get("play_count", 0)
        duration = video.get("duration", 0)

        # Skip already posted
        if video_id in posted_ids:
            logger.debug(f"Skipping {video_id} — already posted")
            continue

        # Skip low-view videos
        if play_count < config.MIN_VIEWS:
            logger.debug(f"Skipping {video_id} — only {play_count:,} views (min: {config.MIN_VIEWS:,})")
            continue

        # Skip videos that are too long
        if duration > config.MAX_DURATION_SECONDS:
            logger.debug(f"Skipping {video_id} — {duration}s exceeds max {config.MAX_DURATION_SECONDS}s")
            continue

        filtered.append(video)

    logger.info(f"Filtered to {len(filtered)} eligible videos (from {len(videos)} total)")
    return filtered


def discover_video() -> dict | None:
    """
    Main discovery function. Searches random hashtags for viral movie clips
    and returns a single video dict ready for download.
    
    Returns a dict with:
        - video_id: str
        - video_url: str (TikTok URL)
        - download_url: str (direct MP4 URL, no watermark)
        - title: str (description text)
        - hashtags: list[str]
        - author: str
        - play_count: int
        - duration: int
        
    Returns None if no eligible video is found.
    """
    # Shuffle hashtags so we get variety
    hashtags = config.HASHTAGS.copy()
    random.shuffle(hashtags)

    all_candidates = []

    for hashtag in hashtags:
        videos = _fetch_videos_by_hashtag(hashtag)
        filtered = _filter_videos(videos)
        all_candidates.extend(filtered)

        # If we have enough candidates, stop searching
        if len(all_candidates) >= 10:
            break

    if not all_candidates:
        logger.warning("❌ No eligible videos found across all hashtags")
        return None

    # Sort by views (most viral first) and pick randomly from top 10
    all_candidates.sort(key=lambda v: v.get("play_count", 0), reverse=True)
    top_picks = all_candidates[:10]
    chosen = random.choice(top_picks)

    video_id = str(chosen.get("video_id", chosen.get("id", "")))
    title = chosen.get("title", "")
    author_info = chosen.get("author", {})
    author_name = author_info.get("unique_id", author_info.get("nickname", "unknown")) if isinstance(author_info, dict) else str(author_info)

    result = {
        "video_id": video_id,
        "video_url": f"https://www.tiktok.com/@{author_name}/video/{video_id}",
        "download_url": chosen.get("play", ""),  # No-watermark URL from TikWM
        "title": title,
        "hashtags": _extract_hashtags_from_title(title),
        "author": author_name,
        "play_count": chosen.get("play_count", 0),
        "duration": chosen.get("duration", 0),
    }

    logger.info(
        f"🎬 Selected: {result['video_url']}\n"
        f"   Author: @{result['author']}\n"
        f"   Views: {result['play_count']:,}\n"
        f"   Duration: {result['duration']}s\n"
        f"   Description: {result['title'][:80]}..."
    )

    return result
