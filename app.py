import os
from flask import Flask, render_template, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

from models import db, Settings, PostHistory, TikTokAccount, Proxy
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
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

ALLOWED_EMAIL = "rowanchanner2@gmail.com"

# APScheduler Setup
scheduler = BackgroundScheduler()

def bot_job():
    with app.app_context():
        import logging
        logger = logging.getLogger("bot")
        logger.info("⚡ Run Now triggered! Checking settings...")
        try:
            # Check if bot is enabled in settings
            settings = Settings.query.first()
            if settings and not settings.is_running:
                logger.warning("Bot is PAUSED in Settings! Skipping run.")
                return
            
            logger.info("Bot is ENABLED. Starting pipeline...")
            # Fetch active accounts
            from models import TikTokAccount
            active_accounts = [acc.username for acc in TikTokAccount.query.filter_by(is_active=True).all()]
            
            if not active_accounts:
                logger.error("No active TikTok accounts found! Add one in Settings.")
            else:
                logger.info(f"Found active accounts: {active_accounts}")
            
            # Run the bot pipeline
            bot_main.run_pipeline(dry_run=False, active_accounts=active_accounts)
        except Exception as e:
            import traceback
            logger.error(f"Error in background bot job: {str(e)}")
            logger.error(traceback.format_exc())

@app.before_request
def initialize_db():
    # Setup DB on first request if it doesn't exist
    app.before_request_funcs[None].remove(initialize_db)
    db.create_all()
    
    # Auto-migrate: Add discord_webhook_url column if it doesn't exist
    from sqlalchemy import text
    try:
        db.session.execute(text('ALTER TABLE settings ADD COLUMN discord_webhook_url VARCHAR(255) DEFAULT ""'))
        db.session.commit()
    except:
        db.session.rollback()
    
    # Restore cookies from persistent disk on Render
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    if os.path.exists(data_dir):
        import shutil
        for f in os.listdir(data_dir):
            if f.startswith("CookieFile") and f.endswith(".json"):
                shutil.copy(os.path.join(data_dir, f), os.path.join(base_dir, f))
                
    # Add default account if none exist
    if TikTokAccount.query.count() == 0:
        default_acc = TikTokAccount(username="rowanoutdoors", cookie_file="CookieFilerowanoutdoors.json", is_active=True)
        db.session.add(default_acc)
        db.session.commit()
    
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
    
    # Force enabled by default
    settings.is_running = True
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
    allowed_routes = ['login', 'google_login', 'authorize', 'static']
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
    try:
        # Force HTTPS redirect URI unless testing locally
        scheme = 'http' if request.host.startswith('localhost') or request.host.startswith('127.0.0.1') else 'https'
        redirect_uri = url_for('authorize', _external=True, _scheme=scheme)
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        return f"Error during Google Login: {str(e)}", 500

@app.route('/authorize')
def authorize():
    try:
        token = google.authorize_access_token()
        # With OpenID Connect, userinfo might be inside the token
        user_info = token.get('userinfo')
        
        if not user_info:
            # Fallback using absolute URL since api_base_url was removed
            resp = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
            user_info = resp.json()
            
        if user_info.get('email') != ALLOWED_EMAIL:
            return "Unauthorized. This dashboard is locked to a specific account.", 403
            
        session['user'] = user_info
        return redirect(url_for('dashboard'))
    except Exception as e:
        import traceback
        return f"Error during authorization: {str(e)}<br><br>Traceback:<br><pre>{traceback.format_exc()}</pre>", 500

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
        
    try:
        settings = Settings.query.first()
        recent_posts = PostHistory.query.order_by(PostHistory.posted_at.desc()).limit(5).all()
        
        # Get next run time
        job = scheduler.get_job('tiktok_job')
        next_run = job.next_run_time if job else None
        
        return render_template('dashboard.html', user=user, settings=settings, next_run=next_run, recent_posts=recent_posts)
    except Exception as e:
        import traceback
        return f"CRASH IN DASHBOARD:<br><br>{str(e)}<br><pre>{traceback.format_exc()}</pre>", 500

from werkzeug.utils import secure_filename

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
        
    try:
        settings_obj = Settings.query.first()
        accounts = TikTokAccount.query.all()
        
        if request.method == 'POST':
            if 'upload_cookie' in request.form:
                # Handle cookie upload
                file = request.files.get('cookie_file')
                username = request.form.get('account_username')
                if file and username and file.filename.endswith('.json'):
                    filename = f"CookieFile{username}.json"
                    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
                    file.save(file_path)
                    
                    # Also save to persistent disk if it exists
                    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
                    if os.path.exists(data_dir):
                        import shutil
                        shutil.copy(file_path, os.path.join(data_dir, filename))
                    
                    # Update or create account in DB
                    account = TikTokAccount.query.filter_by(username=username).first()
                    if not account:
                        account = TikTokAccount(username=username, cookie_file=filename, is_active=True)
                        db.session.add(account)
                    db.session.commit()
            elif 'delete_account' in request.form:
                account_id = request.form.get('account_id')
                account = TikTokAccount.query.get(account_id)
                if account:
                    try:
                        base_dir = os.path.dirname(os.path.abspath(__file__))
                        os.remove(os.path.join(base_dir, account.cookie_file))
                        data_dir = os.path.join(base_dir, 'data')
                        if os.path.exists(data_dir):
                            os.remove(os.path.join(data_dir, account.cookie_file))
                    except:
                        pass
                    db.session.delete(account)
                    db.session.commit()
            elif 'toggle_account' in request.form:
                account_id = request.form.get('account_id')
                account = TikTokAccount.query.get(account_id)
                if account:
                    account.is_active = not account.is_active
                    db.session.commit()
            elif 'add_proxies' in request.form:
                bulk = request.form.get('bulk_proxies', '')
                for line in bulk.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    if not line.startswith('http'):
                        line = f"http://{line}"
                    db.session.add(Proxy(proxy_url=line))
                db.session.commit()
            elif 'clear_proxies' in request.form:
                Proxy.query.delete()
                db.session.commit()
            else:
                settings_obj.post_interval_hours = int(request.form.get('interval', 3))
                settings_obj.max_posts_per_day = int(request.form.get('max_posts', 15))
                settings_obj.hashtags = request.form.get('hashtags', '')
                settings_obj.extra_hashtags = request.form.get('extra_hashtags', '')
                settings_obj.min_views = int(request.form.get('min_views', 500000))
                settings_obj.is_running = 'is_running' in request.form
                # Removed proxy_url from settings since it's now in the Proxy table
                settings_obj.discord_webhook_url = request.form.get('discord_webhook_url', '')
                
                db.session.commit()
                
                # Reschedule job with new interval
                scheduler.reschedule_job('tiktok_job', trigger='interval', hours=settings_obj.post_interval_hours)
            
            return redirect(url_for('settings'))
            
        proxy_count = Proxy.query.count()
        return render_template('settings.html', settings=settings_obj, user=user, accounts=accounts, proxy_count=proxy_count)
    except Exception as e:
        import traceback
        return f"CRASH IN SETTINGS:<br><br>{str(e)}<br><pre>{traceback.format_exc()}</pre>", 500

@app.route('/history')
def history():
    try:
        user = session.get('user')
        if not user:
            return redirect(url_for('login'))
        posts = PostHistory.query.order_by(PostHistory.posted_at.desc()).all()
        return render_template('history.html', posts=posts, user=user)
    except Exception as e:
        import traceback
        return f"CRASH IN HISTORY:<br><br>{str(e)}<br><pre>{traceback.format_exc()}</pre>", 500

@app.route('/run_now', methods=['POST'])
def run_now():
    try:
        user = session.get('user')
        if not user:
            return redirect(url_for('login'))
            
        from datetime import timezone
        job = scheduler.get_job('tiktok_job')
        if job:
            job.modify(next_run_time=datetime.now(timezone.utc))
            
        return redirect(url_for('dashboard'))
    except Exception as e:
        import traceback
        return f"CRASH IN RUN_NOW:<br><br>{str(e)}<br><pre>{traceback.format_exc()}</pre>", 500

@app.route('/logs_api')
def logs_api():
    user = session.get('user')
    if not user:
        return "Unauthorized", 401
    
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.log")
    if not os.path.exists(log_file):
        return "Log file not found... Waiting for bot to run.\n"
        
    try:
        # Read the last 100 lines of the log file
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return "".join(lines[-100:])
    except Exception as e:
        return f"Error reading logs: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)
