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
            
            # Inject Discord Webhook Screenshot Streamer
            discord_snippet = """
        try:
            import config
            import requests
            webhook = getattr(config, "DISCORD_WEBHOOK_URL", "")
            if webhook:
                page.screenshot(path="debug_screen.png")
                with open("debug_screen.png", "rb") as f:
                    requests.post(webhook, files={"file": ("screen.png", f, "image/png")}, data={"content": "📸 Headless browser preparing to click Post!"})
        except Exception:
            pass
        page.wait_for_selector('button:has-text("Post")[aria-disabled="false"]', timeout=12000000)
"""
            content = content.replace("page.wait_for_selector('button:has-text(\"Post\")[aria-disabled=\"false\"]', timeout=12000000)", discord_snippet)
            
            with open(function_py, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully patched {function_py}")
            return

    print("Could not find tiktokautouploader in site-packages!")

if __name__ == "__main__":
    patch()
