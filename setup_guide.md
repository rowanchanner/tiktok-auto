# 🎬 Auto TikTok Poster — Setup Guide

## Prerequisites

- **Python 3.10+** installed and on your PATH
- **FFmpeg** installed and on your PATH (needed by yt-dlp for video processing)
- A **TikTok account** you want to post to

---

## Step 1: Install Python Dependencies

Open a terminal in this folder and run:

```bash
pip install -r requirements.txt
```

This installs:
- `yt-dlp` — downloads TikTok videos without watermarks
- `tiktokautouploader` — uploads videos to TikTok via stealth browser
- `requests` — API calls to discover videos
- `schedule` — job scheduling for auto mode
- `playwright` — browser automation engine

---

## Step 2: Install Playwright Browsers

After installing the Python packages, install the browser engines:

```bash
playwright install
```

This downloads Chromium (and optionally Firefox/WebKit) for browser automation.

---

## Step 3: Install FFmpeg

FFmpeg is required by yt-dlp for optimal video downloading.

### Windows:
1. Download from https://ffmpeg.org/download.html (get the "essentials" build)
2. Extract to a folder like `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH
4. Verify: `ffmpeg -version`

### Alternative (via winget):
```bash
winget install ffmpeg
```

### Alternative (via choco):
```bash
choco install ffmpeg
```

---

## Step 4: Export Your TikTok Cookies

The uploader needs your TikTok login cookies to authenticate.

### Method: "Get cookies.txt LOCALLY" Browser Extension

1. Install the **"Get cookies.txt LOCALLY"** extension:
   - [Chrome](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. Log in to **TikTok** in your browser (make sure you're fully logged in)

3. While on `tiktok.com`, click the extension icon

4. Click **"Export"** to download `cookies.txt`

5. Move the `cookies.txt` file into this project folder:
   ```
   C:\Users\churc\OneDrive\Desktop\nope\cookies.txt
   ```

> ⚠️ **Security Warning**: Your cookies file contains your login session. Never share it with anyone or commit it to version control.

> 💡 **Tip**: If your uploads start failing with auth errors, your cookies may have expired. Re-export them following the steps above.

---

## Step 5: Configure Settings (Optional)

Edit `config.py` to customize:

| Setting | Default | Description |
|---|---|---|
| `HASHTAGS` | Movie clip tags | Which hashtags to search |
| `MIN_VIEWS` | 500,000 | Minimum views to consider "viral" |
| `MAX_DURATION_SECONDS` | 180 | Skip videos longer than this |
| `POST_INTERVAL_HOURS` | 4 | Hours between auto-posts |
| `MAX_POSTS_PER_DAY` | 5 | Daily safety limit |
| `EXTRA_HASHTAGS` | `[]` | Additional hashtags for every post |
| `CLEANUP_AFTER_UPLOAD` | `True` | Delete video file after uploading |

---

## Usage

### Test Without Uploading (Recommended First Step)
```bash
python main.py --dry-run
```
This will discover a video, download it, and show you what *would* be posted — without actually uploading anything.

### Post One Video
```bash
python main.py
```

### Auto Mode (Scheduled Posting)
```bash
python main.py --auto
```
Posts a video immediately, then every N hours (configured in `config.py`).

### Auto Mode + Dry Run (Test Scheduling)
```bash
python main.py --auto --dry-run
```

### View Post History
```bash
python main.py --history
```

### Debug Mode (Verbose Logging)
```bash
python main.py --dry-run --debug
```

---

## Troubleshooting

### "yt-dlp download failed"
- Update yt-dlp: `pip install -U yt-dlp`
- Make sure FFmpeg is installed and on PATH
- TikTok may be rate-limiting — wait a few minutes

### "Cookies file not found"
- Make sure `cookies.txt` is in the project root folder
- Re-export cookies if they expired

### "Upload failed" / "Something went wrong"
- Re-export cookies (they expire)
- Try running without `--headless` to see what's happening in the browser
- TikTok may have updated their UI — check for package updates: `pip install -U tiktokautouploader`

### "No eligible videos found"
- Lower `MIN_VIEWS` in `config.py`
- Add more hashtags to `HASHTAGS` list
- Increase `FETCH_COUNT`

---

## ⚠️ Disclaimer

This tool is for educational purposes only. Re-posting copyrighted content (movie clips) without authorization violates copyright law and TikTok's Terms of Service. Use at your own risk. The author is not responsible for any consequences including account bans, DMCA takedowns, or legal action.
