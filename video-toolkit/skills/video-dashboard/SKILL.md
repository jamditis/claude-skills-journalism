---
name: video-dashboard
description: This skill should be used when the user asks to "build a dashboard", "create a video analysis dashboard", "generate content analysis", "run topic analysis on transcripts", "analyze sentiment", "compare cross-platform messaging", or needs to aggregate transcript and frame data into an interactive web dashboard.
argument-hint: "[optional: path to project directory]"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Agent", "AskUserQuestion"]
---

# Content analysis and interactive dashboard

Aggregate transcripts and frame analysis data into structured analysis JSONs, then generate an interactive single-page web dashboard for exploring the results.

## Prerequisites

- Transcripts in `transcripts/{platform}/{id}.txt` (from /video-transcribe)
- Optionally: frame analysis in `frame-analysis/{platform}/{id}.json` (from /video-frames)
- `metadata.json` with video entries

## Workflow

### Step 1: Ask which sections to include

Present the user with section options:

| Section | Description | Data needed |
|---------|-------------|-------------|
| Overview stats | Video count, platforms, total minutes, words | metadata.json |
| Video catalog | Filterable grid with transcript accordion | metadata.json + transcripts |
| Transcript search | Full-text search with highlighted excerpts | transcripts |
| Topic analysis | Keyword frequency chart with topic pills | transcripts |
| Sentiment analysis | Positive/negative/urgent tone breakdown | transcripts |
| Cross-platform comparison | Side-by-side platform metrics + top words | transcripts + metadata |

All sections are recommended. The user can deselect any they don't want.

### Step 2: Configure topic keywords

Topic analysis uses keyword matching against transcripts. The default categories are generic:

```python
TOPIC_KEYWORDS = {
    "politics": ["government", "policy", "legislation", "law", "vote"],
    "economy": ["job", "business", "economy", "wage", "worker", "tax"],
    "health": ["health", "hospital", "mental health", "doctor", "care"],
    "education": ["school", "student", "teacher", "education", "university"],
    "environment": ["climate", "green", "pollution", "sustainability"],
    "technology": ["tech", "digital", "software", "AI", "data"],
    "community": ["community", "neighborhood", "local", "together"],
    "safety": ["crime", "police", "safety", "violence", "security"],
}
```

Ask the user: "Want to customize the topic categories for this subject, or use the defaults?" If the subject is a politician, suggest political topic categories (housing, transit, budget, immigration, etc.).

### Step 3: Run content analysis

Generate four JSON files in `analysis/`:

**topics.json** — keyword frequency per video, per platform, and overall:
```json
{
  "overall": {"topic": count, ...},
  "per_platform": {"twitter": {"topic": count}, ...},
  "per_video": {"video_id": {"title": "...", "platform": "...", "topics": {...}}}
}
```

**sentiment.json** — positive/negative/urgent scoring per video:
```json
{
  "per_video": {"video_id": {"raw_counts": {...}, "dominant_tone": "urgent"}},
  "per_platform": {"twitter": {"positive": N, "negative": N, "urgent": N, "count": N}}
}
```

**cross-platform.json** — platform comparison metrics:
```json
{
  "platforms": {
    "twitter": {
      "video_count": N, "total_words": N, "avg_duration_seconds": N,
      "avg_words_per_video": N, "top_words": {"word": count, ...}
    }
  }
}
```

**summary.json** — high-level overview stats:
```json
{
  "total_videos": N, "total_duration_minutes": N, "total_words": N,
  "platforms": [...], "top_topics": [...],
  "dominant_tone_distribution": {"urgent": N, "positive": N, ...}
}
```

### Step 4: Generate the dashboard

Build a single HTML file at `web/index.html` with:

- **Zero-build architecture:** CDN-loaded Chart.js and Google Fonts, all CSS/JS inline
- **Inline SVG favicon** (no external files needed)
- **Dark theme** with editorial typography
- **Platform color-coding:** Twitter blue, TikTok pink, YouTube red, Instagram gradient, Facebook blue
- **Data loading:** Fetch JSON from relative paths (`../analysis/*.json`, `../metadata.json`)
- **Graceful degradation:** Show "data not yet available" for missing sections

**Data normalization layer:** The dashboard should normalize field names on load to handle variations in analysis script output. Map common patterns:
- `overall` / `frequencies` (topics)
- `per_video` / `by_video`
- `per_platform` / `by_platform`

**Dashboard sections (based on user selection):**
- Overview stats with large monospace numbers
- Filterable video grid with platform badges and transcript accordion
- Full-text transcript search with debounced input and highlighted matches
- Topic frequency horizontal bar chart (Chart.js) with clickable topic pills
- Sentiment doughnut chart + per-platform stacked bars
- Cross-platform comparison panels with top word lists

### Step 5: Test the dashboard

Start a local server and verify:

```bash
cd {project-dir} && python -m http.server 8888
# Open http://localhost:8888/web/index.html
```

Check: charts render, video grid populates, search works, platform filters work across sections.

### Step 6: Commit and report

Commit the analysis script, JSON outputs, and dashboard. Report key findings:
- Top topics with counts
- Dominant tone distribution
- Cross-platform patterns (which platform has longest videos, most words, etc.)

## Key lessons

- **Field name normalization is critical:** If the analysis script and dashboard are written separately (or by different subagents), field names will diverge. Add a normalization layer in the dashboard's data loading step.
- **total_words not automatic:** The analysis script may not calculate total word count. Add it to summary.json by counting words across all transcript .txt files.
- **Cross-platform top_words format:** The analysis script may output `{"word": count}` objects, but the dashboard may expect `[{word, count}]` arrays. Normalize on load.
- **Stopword filtering matters:** Remove common English stopwords from cross-platform top words, or the lists will be useless (all "the", "is", "and").
