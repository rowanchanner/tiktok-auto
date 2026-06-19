"""
Auto TikTok Poster — Main Entry Point
=======================================
Orchestrates the full pipeline: discover → download → upload.

Usage:
    python main.py              # Find, download, and post one video
    python main.py --auto       # Run on a schedule (every N hours)
    python main.py --dry-run    # Find and download but don't upload
    python main.py --history    # Show recent post history
"""

import argparse
import logging
import sys
import time
import io
import os
import random
from datetime import datetime, timezone

# Fix Windows console encoding for emoji/unicode in log messages
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except AttributeError:
    pass  # In WSGI environments (like Gunicorn), stdout might not have a .buffer attribute

import schedule as schedule_lib

import config
import tracker
from discover import discover_video
from downloader import download_video
from uploader import upload_video, cleanup_video

# ─── Logging Setup ───────────────────────────────────────────────────────────

def setup_logging(level: str = None):
    """Configure logging with colored-ish console output and file output."""
    log_level = getattr(logging, (level or config.LOG_LEVEL).upper(), logging.INFO)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-7s │ %(name)-12s │ %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File Handler for Live Web Logs
    log_file = os.path.join(config.BASE_DIR, "bot.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Clear existing handlers to prevent duplicates if called multiple times
    root_logger.handlers = []
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Quiet down noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("yt_dlp").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


logger = logging.getLogger("main")

# Initialize logging when module is imported
setup_logging()

# ─── Global Objects ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(dry_run: bool = False, active_accounts: list = None) -> bool:
    """Run the complete discovery -> download -> upload pipeline for ALL accounts sequentially."""
    logger.info("============================================================")
    
    if not active_accounts:
        active_accounts = [getattr(config, "TIKTOK_ACCOUNT", "rowanoutdoors")]
        
    posts_today = tracker.get_posted_count_today()
    max_posts = getattr(config, "MAX_POSTS_PER_DAY", 15)
    
    logger.info(f"📊 Posts today: {posts_today}/{max_posts}")
    if posts_today >= max_posts:
        logger.info("Reached maximum posts for today. Sleeping until tomorrow.")
        return False

    any_success = False
    
    for account_name in active_accounts:
        logger.info("")
        logger.info(f"━━━ Processing account: @{account_name} ━━━")
        
        # Check daily limit before each account
        posts_today = tracker.get_posted_count_today()
        if posts_today >= max_posts:
            logger.info("Reached daily limit. Stopping.")
            break
        
        # Step 1: Discover
        logger.info("─── Step 1: Discovering viral movie clips ───")
        video_info = discover_video()
        if not video_info:
            logger.warning(f"No eligible videos found for @{account_name}. Skipping.")
            continue

        # Step 2: Download
        logger.info("─── Step 2: Downloading video ───")
        download_result = download_video(video_info)
        if not download_result:
            logger.error(f"Download failed for @{account_name}. Skipping.")
            continue

        # Step 3: Upload
        logger.info(f"─── Step 3: Uploading to @{account_name} ───")
        import gc
        gc.collect()
        
        success = upload_video(download_result, account_name=account_name, dry_run=dry_run)
        
        if success:
            tracker.mark_posted(
                video_id=download_result["video_id"],
                video_url=download_result.get("video_url", ""),
                description=download_result.get("description", ""),
                hashtags=download_result.get("hashtags", []),
                account=account_name,
            )
            if not dry_run:
                cleanup_video(download_result["file_path"])
            
            logger.info(f"🎉 Posted to @{account_name}!")
            any_success = True
            
            # Discord notification
            if not dry_run:
                try:
                    webhook_url = getattr(config, "DISCORD_WEBHOOK_URL", "")
                    if webhook_url:
                        import requests
                        desc = download_result.get("description", "")[:200]
                        tags = " ".join(download_result.get("hashtags", [])[:5])
                        profile = f"https://www.tiktok.com/@{account_name}"
                        requests.post(webhook_url, json={
                            "content": f"✅ **Posted to @{account_name}!**\n📝 {desc}\n🏷️ {tags}\n🔗 {profile}"
                        }, timeout=10)
                except Exception as e:
                    logger.warning(f"Discord webhook failed: {e}")
        else:
            logger.error(f"❌ Upload failed for @{account_name}")
            cleanup_video(download_result["file_path"])
        
        # Brief pause between accounts
        if account_name != active_accounts[-1]:
            logger.info("⏳ Waiting 30s before next account...")
            time.sleep(30)
    
    return any_success


# ─── Scheduled Mode ──────────────────────────────────────────────────────────

def run_auto_mode(dry_run: bool = False):
    """Run the pipeline on a recurring schedule."""
    interval_hours = config.POST_INTERVAL_HOURS
    
    logger.info(f"🔄 Auto mode enabled — posting every {interval_hours} hours")
    logger.info(f"   Max posts per day: {config.MAX_POSTS_PER_DAY}")
    logger.info(f"   Dry run: {dry_run}")
    logger.info(f"   Press Ctrl+C to stop")
    logger.info("")

    # Run immediately on start
    run_pipeline(dry_run=dry_run)

    # Schedule recurring runs
    schedule_lib.every(interval_hours).hours.do(run_pipeline, dry_run=dry_run)

    try:
        while True:
            schedule_lib.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\n⏹️  Auto mode stopped by user")


# ─── History ──────────────────────────────────────────────────────────────────

def show_history():
    """Display recent post history."""
    history = tracker.get_post_history(limit=20)
    
    if not history:
        print("\n📭 No posts yet.\n")
        return

    print(f"\n📜 Recent Post History ({len(history)} entries):")
    print("─" * 80)
    
    for i, entry in enumerate(reversed(history), 1):
        posted_at = entry.get("posted_at", "?")[:19].replace("T", " ")
        video_id = entry.get("video_id", "?")
        desc = entry.get("description", "")[:60]
        tags = " ".join(entry.get("hashtags", [])[:5])
        
        print(f"  {i:2d}. [{posted_at}] ID: {video_id}")
        print(f"      {desc}...")
        if tags:
            print(f"      {tags}")
        print()

    posts_today = tracker.get_posted_count_today()
    print(f"📊 Posts today: {posts_today}/{config.MAX_POSTS_PER_DAY}")
    print()


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🎬 Auto TikTok Poster — Repost viral movie clips automatically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    Post one video now
  python main.py --dry-run          Test without uploading
  python main.py --auto             Run on schedule (every 4 hours)
  python main.py --auto --dry-run   Schedule dry runs for testing
  python main.py --history          View post history
        """,
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help=f"Run on a schedule (every {config.POST_INTERVAL_HOURS} hours)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover and download but skip the actual upload",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show recent post history and exit",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging("DEBUG" if args.debug else None)

    # We need a Flask app context to use the database locally
    from app import app, db
    app.app_context().push()
    db.create_all()

    # Print banner
    print()
    print("  +==========================================+")
    print("  |       Auto TikTok Poster                |")
    print("  |         Movie Clips Edition              |")
    print("  +==========================================+")
    print()

    if args.history:
        show_history()
        return

    if args.auto:
        run_auto_mode(dry_run=args.dry_run)
    else:
        success = run_pipeline(dry_run=args.dry_run)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
