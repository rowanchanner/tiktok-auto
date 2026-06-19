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
    discord_webhook_url = db.Column(db.String(255), default="")
    discord_screenshots = db.Column(db.Boolean, default=False)
    use_peak_hours = db.Column(db.Boolean, default=False)
    peak_hours = db.Column(db.Text, default="")  # comma-separated hours like "9,12,18,21"
    youtube_enabled = db.Column(db.Boolean, default=False)
    youtube_only = db.Column(db.Boolean, default=False)
    youtube_token = db.Column(db.Text, default="")  # JSON OAuth token for YouTube API
    watermark_enabled = db.Column(db.Boolean, default=False)
    watermark_text = db.Column(db.Text, default='Follow [username] for more!')
    watermark_position = db.Column(db.String(20), default='bottom-center')  # top-left, top-center, top-right, bottom-left, bottom-center, bottom-right
    watermark_font_size = db.Column(db.Integer, default=24)
    watermark_opacity = db.Column(db.Float, default=0.8)
    watermark_color = db.Column(db.String(7), default='#ffffff')

class Proxy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proxy_url = db.Column(db.String(255), nullable=False)

class PostHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(50), nullable=False)
    video_url = db.Column(db.String(255))
    uploaded_url = db.Column(db.String(255), default='')  # link to the post on user's TikTok
    youtube_url = db.Column(db.String(255), default='')   # link to YouTube Short
    description = db.Column(db.Text)
    hashtags = db.Column(db.Text)
    account = db.Column(db.String(100), default='rowanoutdoors')
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)

class TikTokAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    cookie_file = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    search_hashtags = db.Column(db.Text, default='')  # blank = use global
    extra_hashtags = db.Column(db.Text, default='')    # blank = use global
    max_posts_per_day = db.Column(db.Integer, default=0)  # 0 = use global
    post_to = db.Column(db.String(20), default='tiktok')  # tiktok, both, youtube
    watermark_text = db.Column(db.Text, default='')  # blank = use global watermark
