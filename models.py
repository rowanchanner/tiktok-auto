from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_interval_hours = db.Column(db.Integer, default=3)
    max_posts_per_day = db.Column(db.Integer, default=15)
    hashtags = db.Column(db.Text, default="movieclips,moviescenes,filmtok,cinemascenes,movietok,filmclips,moviemoments")
    extra_hashtags = db.Column(db.Text, default="")
    min_views = db.Column(db.Integer, default=500000)
    is_running = db.Column(db.Boolean, default=True)

class PostHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(50), nullable=False)
    video_url = db.Column(db.String(255))
    description = db.Column(db.Text)
    hashtags = db.Column(db.Text)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)

class TikTokAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    cookie_file = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
