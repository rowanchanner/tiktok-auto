"""
Auto TikTok Poster — Account Setup
=====================================
Run this ONCE to accept cookies and log into TikTok.
After this, the auto poster will work without issues.

Usage: python setup_account.py
"""

import time
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def setup():
    try:
        from phantomwright.sync_api import sync_playwright
    except ImportError:
        from playwright.sync_api import sync_playwright

    print("\n  === TikTok Account Setup ===\n")
    print("  A browser will open. You need to:")
    print("  1. Click 'Accept All Cookies' if the popup appears")
    print("  2. Log into your TikTok account")
    print("  3. Once logged in, come back here and press Enter")
    print()

    with sync_playwright() as p:
        # Use persistent context so cookies are saved
        import os
        cookie_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")
        os.makedirs(cookie_dir, exist_ok=True)

        browser = p.chromium.launch_persistent_context(
            user_data_dir=cookie_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
        )

        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded")

        # Try to click cookie consent buttons
        time.sleep(3)
        try:
            # Common TikTok cookie consent selectors
            for selector in [
                'button:has-text("Accept all")',
                'button:has-text("Accept All")', 
                'button:has-text("Accept all cookies")',
                'button:has-text("Allow all")',
                'button:has-text("Allow All")',
                '[data-testid="cookie-banner-accept"]',
                'button.cookie-banner-accept',
            ]:
                btn = page.query_selector(selector)
                if btn:
                    btn.click()
                    print("  [OK] Clicked cookie consent button!")
                    time.sleep(1)
                    break
            else:
                print("  [INFO] No cookie popup found (may already be accepted)")
        except Exception as e:
            print(f"  [INFO] Cookie handling: {e}")

        print()
        print("  >>> Log into your TikTok account in the browser <<<")
        print()
        input("  Press Enter here AFTER you've logged in successfully... ")

        # Save cookies for tiktokautouploader
        cookies = page.context.cookies()
        
        # Save as cookies.txt in Netscape format
        import config
        with open(config.COOKIES_FILE, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies:
                secure = "TRUE" if c.get("secure") else "FALSE"
                domain = c.get("domain", "")
                http_only = "TRUE" if c.get("httpOnly") else "FALSE"
                path = c.get("path", "/")
                expires = str(int(c.get("expires", 0)))
                name = c.get("name", "")
                value = c.get("value", "")
                dot_domain = "TRUE" if domain.startswith(".") else "FALSE"
                f.write(f"{domain}\t{dot_domain}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

        # Also save as JSON for tiktokautouploader
        import json
        json_cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"CookieFile{config.TIKTOK_ACCOUNT}.json")
        with open(json_cookie_path, "w") as f:
            json.dump(cookies, f, indent=2)
        
        print(f"\n  [OK] Cookies saved!")
        print(f"  [OK] Saved {len(cookies)} cookies for account '{config.TIKTOK_ACCOUNT}'")
        
        browser.close()

    print("\n  Setup complete! You can now run: python main.py")
    print()


if __name__ == "__main__":
    setup()
