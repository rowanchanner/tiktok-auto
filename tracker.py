from models import db, PostHistory, Settings
from datetime import datetime

def get_posted_count_today():
    today = datetime.utcnow().date()
    # Count how many posts happened today
    # We query all and filter in Python for SQLite compatibility, or use SQLAlchemy func
    posts = PostHistory.query.all()
    count = 0
    for p in posts:
        if p.posted_at and p.posted_at.date() == today:
            count += 1
    return count

def mark_posted(video_id, video_url="", description="", hashtags=[]):
    new_post = PostHistory(
        video_id=video_id,
        video_url=video_url,
        description=description,
        hashtags=",".join(hashtags) if hashtags else ""
    )
    db.session.add(new_post)
    db.session.commit()

def has_been_posted(video_id):
    post = PostHistory.query.filter_by(video_id=video_id).first()
    return post is not None

def get_all_posted_ids():
    posts = PostHistory.query.all()
    return [p.video_id for p in posts]

def get_post_history(limit=20):
    posts = PostHistory.query.order_by(PostHistory.posted_at.desc()).limit(limit).all()
    return [
        {
            "video_id": p.video_id,
            "video_url": p.video_url,
            "description": p.description,
            "hashtags": p.hashtags.split(",") if p.hashtags else [],
            "posted_at": p.posted_at.isoformat()
        } for p in posts
    ]
