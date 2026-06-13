import os
from flask import Flask, render_template, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

from models import db, Settings, PostHistory
import main as bot_main

load_dotenv()

app = Flask(__name__)
# Fix for Render's reverse proxy to ensure HTTPS URLs are generated
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-default-key")

# Database setup
# Use DATABASE_URL for Render PostgreSQL, otherwise fallback to local SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///bot.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Google OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)

ALLOWED_EMAIL = "rowanchanner2@gmail.com"

# APScheduler Setup
scheduler = BackgroundScheduler()

def bot_job():
    with app.app_context():
        # Check if bot is enabled in settings
        settings = Settings.query.first()
        if settings and not settings.is_running:
            return
        # Run the bot pipeline
        bot_main.run_pipeline(dry_run=False, db_session=db.session)

@app.before_request
def initialize_db():
    # Setup DB on first request if it doesn't exist
    app.before_request_funcs[None].remove(initialize_db)
    db.create_all()
    if not Settings.query.first():
        db.session.add(Settings())
        db.session.commit()
    
    # Start scheduler if not running
    if not scheduler.running:
        settings = Settings.query.first()
        interval = settings.post_interval_hours if settings else 3
        scheduler.add_job(bot_job, 'interval', hours=interval, id='tiktok_job')
        scheduler.start()

# --- Auth Middleware ---
@app.before_request
def require_login():
    allowed_routes = ['login', 'authorize', 'static']
    if request.endpoint not in allowed_routes and 'user' not in session:
        return redirect(url_for('login'))

# --- Routes ---

@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/google_login')
def google_login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    
    if user_info.get('email') != ALLOWED_EMAIL:
        return "Unauthorized. This dashboard is locked to a specific account.", 403
        
    session['user'] = user_info
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    settings = Settings.query.first()
    recent_posts = PostHistory.query.order_by(PostHistory.posted_at.desc()).limit(5).all()
    
    # Get next run time
    job = scheduler.get_job('tiktok_job')
    next_run = job.next_run_time if job else None
    
    return render_template('dashboard.html', user=session['user'], settings=settings, next_run=next_run, recent_posts=recent_posts)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    settings_obj = Settings.query.first()
    if request.method == 'POST':
        settings_obj.post_interval_hours = int(request.form.get('interval', 3))
        settings_obj.max_posts_per_day = int(request.form.get('max_posts', 15))
        settings_obj.hashtags = request.form.get('hashtags', '')
        settings_obj.extra_hashtags = request.form.get('extra_hashtags', '')
        settings_obj.min_views = int(request.form.get('min_views', 500000))
        settings_obj.is_running = 'is_running' in request.form
        
        db.session.commit()
        
        # Reschedule job with new interval
        scheduler.reschedule_job('tiktok_job', trigger='interval', hours=settings_obj.post_interval_hours)
        
        return redirect(url_for('settings'))
        
    return render_template('settings.html', settings=settings_obj, user=session['user'])

@app.route('/history')
def history():
    posts = PostHistory.query.order_by(PostHistory.posted_at.desc()).all()
    return render_template('history.html', posts=posts, user=session['user'])

@app.route('/run_now', methods=['POST'])
def run_now():
    # Trigger a run immediately
    scheduler.get_job('tiktok_job').modify(next_run_time=datetime.now())
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)
