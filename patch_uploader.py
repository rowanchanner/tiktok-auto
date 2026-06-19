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
            # Screenshot interceptor — only active when discord_screenshots is ON in settings
            screenshot_interceptor = """
import time as _real_time
import os as _os
import requests as _requests

_page_ref = None
_last_ss = 0

def _intercept_sleep(seconds):
    global _last_ss, _page_ref
    # Check if screenshots are enabled
    webhook = None
    try:
        from app import app as _app
        from models import Settings as _S
        with _app.app_context():
            s = _S.query.first()
            if s and s.discord_screenshots and s.discord_webhook_url:
                webhook = s.discord_webhook_url
    except:
        pass
    
    if not webhook or not _page_ref:
        _real_time.sleep(seconds)
        return
    
    chunk = 0.5
    loops = int(seconds / chunk)
    for _ in range(loops):
        _real_time.sleep(chunk)
        now = _real_time.time()
        if now - _last_ss >= 2.0:
            _last_ss = now
            try:
                sp = "/tmp/stream.png"
                _page_ref.screenshot(path=sp)
                with open(sp, "rb") as f:
                    _requests.post(webhook, files={"file": ("stream.png", f, "image/png")}, timeout=5)
            except:
                pass
    rem = seconds % chunk
    if rem > 0:
        _real_time.sleep(rem)

time = type('_TM', (), {'sleep': _intercept_sleep, 'time': _real_time.time})
"""
            content = content.replace("import time", screenshot_interceptor)
            content = content.replace("page = context.new_page()", "page = context.new_page()\n        global _page_ref\n        _page_ref = page")
            
            with open(function_py, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully patched {function_py}")
            return

    print("Could not find tiktokautouploader in site-packages!")

if __name__ == "__main__":
    patch()
