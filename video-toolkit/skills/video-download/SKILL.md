---
name: video-download
description: This skill should be used when the user asks to "download videos", "scrape videos from social media", "pull videos from Twitter/TikTok/YouTube/Instagram/Facebook", "download someone's social media videos", or needs to collect video content from public social media accounts for analysis.
argument-hint: "[optional: subject name or platform URLs]"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Agent", "AskUserQuestion", "mcp__plugin_playwright_playwright__*"]
---

# Video download from social media

Download videos from public social media accounts using yt-dlp with Playwright browser automation as a fallback for platforms where yt-dlp's playlist extractors fail.

## Prerequisites

Verify these tools are installed before starting:

```bash
yt-dlp --version    # Video downloader
ffmpeg -version     # Media processing (needed by yt-dlp for merging)
```

If either is missing, install via: `pip install yt-dlp` and `choco install ffmpeg` (Windows) or `brew install ffmpeg` (macOS).

## Workflow

### Step 1: Gather target information

If not provided as arguments, ask the user interactively:

1. **Subject name** — who are we downloading from?
2. **Platform URLs** — which social media profile pages? Support: Twitter/X, TikTok, YouTube, Instagram, Facebook
3. **Video count** — how many recent videos per platform? Default: 15
4. **Output directory** — where to save? Default: `{subject-name}-video-analysis/downloads/{platform}/`

### Step 2: Create project structure

```bash
mkdir -p {project-dir}/downloads/{twitter,tiktok,youtube,instagram,facebook}
```

Create `metadata.json` at the project root with:
```json
{
  "project": "{subject-name}-video-analysis",
  "created": "{ISO-date}",
  "sources": { "platform": "url", ... },
  "videos": []
}
```

### Step 3: Check yt-dlp extractor status

Before downloading, check which extractors are functional:

```bash
yt-dlp --list-extractors | grep -iE "twitter|tiktok|youtube|instagram|facebook"
```

Look for "(CURRENTLY BROKEN)" flags. Platforms marked broken will need the Playwright fallback.

### Step 4: Download — yt-dlp first

For each platform, attempt yt-dlp first:

```bash
yt-dlp --playlist-items 1:{count} \
  -f "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b" \
  --merge-output-format mp4 \
  -o "{downloads_dir}/{platform}/%(id)s.%(ext)s" \
  --write-info-json --no-write-playlist-metafiles \
  --no-overwrites --ignore-errors --print-json \
  "{url}"
```

Parse `--print-json` output to extract metadata (id, title, upload_date, duration, source_url).

**Platform reliability order:** YouTube (most reliable) > TikTok > Twitter/X > Facebook > Instagram (often broken).

Run platforms one at a time, starting with the most reliable.

### Step 5: Fallback — Playwright URL extraction

For platforms where yt-dlp fails (common for Instagram, Facebook, sometimes Twitter), use Playwright browser automation:

1. Navigate to the profile/media page
2. Scroll to load content
3. Extract individual video URLs via JavaScript:
   - **Twitter/X media tab:** Find elements with duration text (e.g., "0:45") and walk up to the parent `<a>` link
   - **Instagram reels tab:** Collect `a[href*="/reel/"]` links
   - **Facebook reels tab:** Collect `a[href*="/reel/"]` links
4. Save URLs to `{project-dir}/{platform}_urls.txt`
5. Download each URL individually with yt-dlp

The user may need to log in via Playwright first. Open login pages and let them authenticate before extracting URLs.

### Step 6: Update metadata.json

After all downloads, read the `.info.json` sidecar files and populate `metadata.json`:

```python
# Per video entry in metadata.json:
{
  "id": "video_id",
  "title": "video title",
  "upload_date": "YYYY-MM-DD",
  "duration": 123,  # seconds
  "source_url": "https://...",
  "platform": "twitter",
  "local_path": "downloads/twitter/video_id.mp4",
  "description": "video description"
}
```

Sort videos by upload_date descending. Deduplicate by video ID.

### Step 7: Verify and report

Print a summary table showing per-platform download counts and any failures. Commit the download script and metadata.json (not the video files — those should be gitignored).

## Key lessons

- **Windows encoding:** TikTok titles often contain emoji/Unicode that crashes Windows console output. Encode print output as ASCII with replacement characters.
- **Chrome cookies:** `--cookies-from-browser chrome` often fails on Windows with a DPAPI error. Try without cookies first — public accounts usually work.
- **Instagram user extractor:** Frequently broken in yt-dlp. Always plan for the Playwright fallback.
- **Timeout handling:** Set generous timeouts (10+ minutes per platform) for large video downloads.
