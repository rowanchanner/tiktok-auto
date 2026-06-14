import os
import site

def patch():
    # Get all possible site-packages directories
    site_packages = site.getsitepackages()
    if hasattr(site, 'getusersitepackages'):
        site_packages.append(site.getusersitepackages())
        
    for sp in site_packages:
        function_py = os.path.join(sp, 'tiktokautouploader', 'function.py')
        if os.path.exists(function_py):
            with open(function_py, 'r', encoding='utf-8') as f:
                content = f.read()
            if "_intercept_sleep" in content:
                print(f"Already patched {function_py}")
                return
            
            # Fix Playwright strict mode violation for Cancel buttons
            content = content.replace('"button:has-text(\'Cancel\')"', '"button:has-text(\'Cancel\') >> nth=0"')
            content = content.replace("'button:has-text(\\'Cancel\\')'", "'button:has-text(\\'Cancel\\') >> nth=0'")
            
            # Force click the 'Got it' button since the cookie banner intercepts it on Render
            content = content.replace('page.click("button:has-text(\'Got it\')")', 'page.click("button:has-text(\'Got it\')", force=True)')
            
            # Force click all Post buttons just to be completely immune to the cookie banner
            # Force click all Post buttons just to be completely immune to the cookie banner
            content = content.replace('page.click(\'button:has-text("Post")[data-e2e="post_video_button"]\', timeout=2000)', 'page.click(\'button:has-text("Post")[data-e2e="post_video_button"]\', timeout=2000, force=True)')
            content = content.replace('page.click(\'button:has-text("Post")[aria-disabled="false"]\', timeout=2000)', 'page.click(\'button:has-text("Post")[aria-disabled="false"]\', timeout=2000, force=True)')
            content = content.replace('page.locator(\'button:has-text("Post now")\').click(timeout=3000)', 'page.locator(\'button:has-text("Post now")\').click(timeout=3000, force=True)')
            
            # Hide TikTok Joyride tutorial overlays globally so they never block clicks
            content = content.replace("page.wait_for_selector('div[data-contents=\"true\"]')", "page.add_style_tag(content='.react-joyride__overlay, #react-joyride-portal { display: none !important; }'); page.wait_for_selector('div[data-contents=\"true\"]')")
            
            # Prevent the library from cancelling proxy uploads mid-flight if the network is slow
            content = content.replace("timeout=2000", "timeout=60000")
            content = content.replace("timeout=3000", "timeout=60000")
            content = content.replace("timeout=5000", "timeout=60000")
            
            # Intercept time.sleep to send screenshots every 2 seconds
            screenshot_interceptor = """
import time as builtin_time
import config
import requests
import os

_last_screenshot = 0
_page_ref = None
_webhook_cache = None

def _intercept_sleep(seconds):
    global _last_screenshot, _page_ref, _webhook_cache
    
    if _webhook_cache is None:
        try:
            from app import app
            from models import Settings
            with app.app_context():
                s = Settings.query.first()
                if s and s.discord_webhook_url:
                    _webhook_cache = s.discord_webhook_url
                    print(f"WEBHOOK INITIALIZED: {_webhook_cache}", flush=True)
                else:
                    _webhook_cache = "EMPTY"
                    print("CRITICAL: DISCORD WEBHOOK IS EMPTY IN DATABASE!", flush=True)
        except Exception as e:
            print(f"WEBHOOK DB FETCH ERROR: {e}", flush=True)
            _webhook_cache = "EMPTY"

    if _webhook_cache == "EMPTY" or not _page_ref:
        builtin_time.sleep(seconds)
        return

    # Sleep in small chunks so we can send screenshots exactly every 2 seconds
    chunk = 0.5
    loops = int(seconds / chunk)
    remainder = seconds % chunk
    
    for _ in range(loops):
        builtin_time.sleep(chunk)
        now = builtin_time.time()
        if now - _last_screenshot >= 2.0:
            _last_screenshot = now
            try:
                screen_path = os.path.join(config.BASE_DIR, "stream.png")
                _page_ref.screenshot(path=screen_path)
                with open(screen_path, "rb") as f:
                    resp = requests.post(_webhook_cache, files={"file": ("stream.png", f, "image/png")})
                    if resp.status_code >= 400:
                        print(f"WEBHOOK POST ERROR: {resp.status_code} - {resp.text}", flush=True)
            except Exception as e:
                print(f"WEBHOOK EXEC ERROR: {e}", flush=True)
                pass
                
    if remainder > 0:
        builtin_time.sleep(remainder)

time = type('TimeMock', (), {'sleep': _intercept_sleep, 'time': builtin_time.time})
"""
            # Inject interceptor right after `import time`
            content = content.replace("import time", screenshot_interceptor)
            
            # Capture the `page` object reference when it's created
            content = content.replace("page = context.new_page()", "page = context.new_page()\n        global _page_ref\n        _page_ref = page")
            with open(function_py, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully patched {function_py}")
            return

    print("Could not find tiktokautouploader in site-packages!")

if __name__ == "__main__":
    patch()
