---
name: python-pipeline
description: Python data processing pipelines with modular architecture. Use when building content processing workflows, implementing dispatcher patterns, integrating Google Sheets/Drive APIs, or creating batch processing systems. Covers patterns from rosen-scraper, image-analyzer, and social-scraper projects.
---

# Python data pipeline development

Patterns for building production-quality data processing pipelines with Python.

**Targeted at Python 3.11+** for `asyncio.TaskGroup` and exception groups; Python 3.12+ for the lighter `type X = ...` syntax. Pin a 3.13+ runtime if you want the JIT or experimental free-threading; the patterns here don't depend on either.

## Choosing a DataFrame engine: pandas vs polars vs DuckDB

For a long time pandas was the default for any tabular work in Python. As of 2026 the default has shifted: **polars** is the right pick for multi-GB pipelines on a single machine, **DuckDB** is the right pick when SQL or larger-than-RAM scans are involved, and **pandas** stays useful for small data and the ML/notebook ecosystem (scikit-learn, statsmodels, plotnine all speak it natively).

| Tool | When | Why |
|---|---|---|
| pandas | < ~1 GB data, ML interop, single-threaded familiarity | Mature, ubiquitous, eager DataFrame model. Slowest in benchmarks but most ecosystem support. |
| polars | 1 GB - tens of GB on one box, performance-critical pipelines | Multithreaded by default, lazy query engine, Arrow-native. ~5x speedup over pandas on filter / aggregate at 100M rows. |
| DuckDB | SQL workflows, larger-than-RAM, parquet/CSV scanning, joins across many files | Vectorized + pipelined execution, cost-based optimizer, streaming scans. Works great as a thin wrapper over a directory of parquet files. |

All three speak Apache Arrow, so zero-copy interop between them is the pragmatic answer most of the time:

```python
import polars as pl
import duckdb

# Polars: read a directory of CSVs, filter, group
df = (
    pl.scan_csv('data/articles_*.csv')
      .filter(pl.col('published_at') >= '2026-01-01')
      .group_by('source')
      .agg(pl.len().alias('count'), pl.col('word_count').mean())
      .collect()
)

# DuckDB: same shape with SQL, no intermediate copy
con = duckdb.connect()
df = con.execute("""
    SELECT source, COUNT(*) AS count, AVG(word_count) AS avg_wc
    FROM 'data/articles_*.csv'
    WHERE published_at >= '2026-01-01'
    GROUP BY source
""").pl()  # returns a Polars DataFrame; use .df() for pandas

# Hand off to pandas only at the boundary that needs it (e.g. scikit-learn)
import pandas as pd
pdf = df.to_pandas()
```

If your pipeline already uses pandas everywhere, don't pre-emptively rewrite. Migrate the bottleneck stages first — typically the CSV-load + filter step.

## Architecture patterns

### Modular processor architecture
```
src/
├── workflow.py              # Main orchestrator
├── dispatcher.py            # Content-type router
├── processors/
│   ├── __init__.py
│   ├── base.py             # Abstract base class
│   ├── article_processor.py
│   ├── video_processor.py
│   └── audio_processor.py
├── services/
│   ├── sheets_service.py   # Google Sheets integration
│   ├── drive_service.py    # Google Drive integration
│   └── ai_service.py       # Gemini API wrapper
├── utils/
│   ├── logger.py
│   └── rate_limiter.py
└── config.py               # Environment configuration
```

### Dispatcher pattern

```python
from typing import Protocol
from urllib.parse import urlparse

class Processor(Protocol):
    def can_process(self, url: str) -> bool: ...
    def process(self, url: str, metadata: dict) -> dict: ...

class Dispatcher:
    def __init__(self):
        self.processors: list[Processor] = [
            ArticleProcessor(),
            VideoProcessor(),
            AudioProcessor(),
            SocialProcessor(),
        ]

    def dispatch(self, url: str, metadata: dict) -> dict:
        for processor in self.processors:
            if processor.can_process(url):
                return processor.process(url, metadata)
        raise ValueError(f"No processor found for URL: {url}")

# Pattern-based routing
class ArticleProcessor:
    DOMAINS = ['nytimes.com', 'washingtonpost.com', 'medium.com']

    def can_process(self, url: str) -> bool:
        domain = urlparse(url).netloc.replace('www.', '')
        return any(d in domain for d in self.DOMAINS)
```

### CSV-based pipeline workflow

```python
import csv
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Iterator

@dataclass
class Record:
    id: str
    url: str
    title: str | None = None
    content: str | None = None
    status: str = 'pending'

def read_input(path: Path) -> Iterator[Record]:
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield Record(**{k: v for k, v in row.items() if k in Record.__annotations__})

def write_output(records: list[Record], path: Path):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(Record.__annotations__.keys()))
        writer.writeheader()
        writer.writerows(asdict(r) for r in records)

def process_batch(input_path: Path, output_path: Path):
    dispatcher = Dispatcher()
    results = []

    for record in read_input(input_path):
        try:
            processed = dispatcher.dispatch(record.url, asdict(record))
            record.status = 'completed'
            record.title = processed.get('title')
            record.content = processed.get('content')
        except Exception as e:
            record.status = f'failed: {e}'
        results.append(record)

    write_output(results, output_path)
```

## Google Sheets integration

```python
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class SheetsService:
    def __init__(self, credentials_path: str):
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        self.client = gspread.authorize(creds)

    def get_worksheet(self, spreadsheet_id: str, sheet_name: str):
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        return spreadsheet.worksheet(sheet_name)

    def read_all(self, worksheet) -> list[dict]:
        return worksheet.get_all_records()

    def append_row(self, worksheet, row: list):
        worksheet.append_row(row, value_input_option='USER_ENTERED')

    def batch_update(self, worksheet, updates: list[dict]):
        """Update multiple cells efficiently."""
        # Format: [{'range': 'A1', 'values': [[value]]}]
        worksheet.batch_update(updates, value_input_option='USER_ENTERED')

    def find_row_by_id(self, worksheet, id_value: str, id_column: int = 1) -> int | None:
        """Find row number by ID value."""
        try:
            cell = worksheet.find(id_value, in_column=id_column)
            return cell.row
        except gspread.CellNotFound:
            return None
```

## Rate limiting

```python
import time
from functools import wraps
from ratelimit import limits, sleep_and_retry

# Simple rate limiter
@sleep_and_retry
@limits(calls=10, period=60)  # 10 calls per minute
def rate_limited_api_call(url: str):
    return requests.get(url)

# Custom rate limiter with backoff
class RateLimiter:
    def __init__(self, calls_per_minute: int = 10):
        self.delay = 60 / calls_per_minute
        self.last_call = 0

    def wait(self):
        elapsed = time.time() - self.last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_call = time.time()

# Usage
limiter = RateLimiter(calls_per_minute=10)

def fetch_with_rate_limit(url: str):
    limiter.wait()
    return requests.get(url)
```

## Concurrent fetching with asyncio.TaskGroup (3.11+)

For I/O-bound stages (HTTP fetches, API calls), `asyncio.TaskGroup` plus `httpx.AsyncClient` runs many requests in parallel without the boilerplate of `asyncio.gather`. TaskGroup's structured-concurrency model means an exception in one task cancels the rest and surfaces as an `ExceptionGroup` — easier to reason about than `gather(return_exceptions=True)`.

```python
import asyncio
import httpx

async def fetch_one(client: httpx.AsyncClient, url: str) -> tuple[str, str | Exception]:
    try:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        return (url, response.text)
    except Exception as e:
        return (url, e)

async def fetch_many(urls: list[str], concurrency: int = 10) -> dict[str, str | Exception]:
    results: dict[str, str | Exception] = {}
    sem = asyncio.Semaphore(concurrency)

    async def _bounded(client: httpx.AsyncClient, url: str):
        async with sem:
            url, body = await fetch_one(client, url)
            results[url] = body

    async with httpx.AsyncClient(http2=True, timeout=30) as client:
        async with asyncio.TaskGroup() as tg:
            for url in urls:
                tg.create_task(_bounded(client, url))

    return results

# Usage
urls = ['https://example.com/a', 'https://example.com/b', ...]
data = asyncio.run(fetch_many(urls, concurrency=20))
```

Pair with `aiolimiter` if you need a true requests-per-second cap (semaphore alone bounds concurrency, not rate). For exponential-backoff retries, wrap `fetch_one` with `tenacity.AsyncRetrying`.

## Progress tracking with resume capability

```python
import json
from pathlib import Path

class ProgressTracker:
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.state = self._load()

    def _load(self) -> dict:
        if self.progress_file.exists():
            return json.loads(self.progress_file.read_text())
        return {'processed_ids': [], 'last_row': 0, 'errors': []}

    def save(self):
        self.progress_file.write_text(json.dumps(self.state, indent=2))

    def mark_processed(self, record_id: str):
        self.state['processed_ids'].append(record_id)
        self.save()

    def is_processed(self, record_id: str) -> bool:
        return record_id in self.state['processed_ids']

    def log_error(self, record_id: str, error: str):
        self.state['errors'].append({'id': record_id, 'error': error})
        self.save()

# Usage in workflow
tracker = ProgressTracker(Path('progress.json'))

for record in records:
    if tracker.is_processed(record.id):
        continue  # Skip already processed

    try:
        process(record)
        tracker.mark_processed(record.id)
    except Exception as e:
        tracker.log_error(record.id, str(e))
```

## Gemini AI integration

The `google-generativeai` package was deprecated August 31, 2025 and the unified `google-genai` SDK replaced it. New code should target `google-genai`:

```bash
pip install google-genai
```

```python
import os
import json
from google import genai
from google.genai import types

# Client carries config (API key, project, location). Reuse across calls.
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

# Pick a current model. Names drift; check ai.google.dev/gemini-api/docs/models
# for the active list. gemini-2.5-flash is a reasonable cost-efficient default.
DEFAULT_MODEL = 'gemini-2.5-flash'

class AIService:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def categorize(self, text: str, taxonomy: dict) -> dict:
        prompt = f"""Analyze this content and categorize it.

Content:
{text[:10000]}

Taxonomy:
{json.dumps(taxonomy, indent=2)}

Respond with JSON containing:
- category: one of the taxonomy categories
- tags: list of relevant tags
- summary: 2-3 sentence summary
"""
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json'),
        )
        return json.loads(response.text)

    def extract_entities(self, text: str) -> list[dict]:
        prompt = f"""Extract named entities from this text.

Text:
{text[:10000]}

For each entity, provide:
- name: entity name
- type: Person, Organization, Location, Event, Work, or Concept
- prominence: 1-10 score based on importance in text

Respond with JSON array of entities.
"""
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json'),
        )
        return json.loads(response.text)

# Batch processing with token-usage tracking (cost varies by model and time;
# look up live pricing rather than hardcoding a per-1k figure).
class BatchAIProcessor:
    def __init__(self, ai_service: AIService):
        self.ai = ai_service
        self.input_tokens = 0
        self.output_tokens = 0

    def process_batch(
        self, items: list[str], prompt_template: str
    ) -> list[dict]:
        """Render each item into prompt_template via .format(item=...).
        prompt_template must instruct the model to return JSON, since this
        method enforces response_mime_type='application/json'.
        """
        results = []
        for item in items:
            response = client.models.generate_content(
                model=self.ai.model,
                contents=prompt_template.format(item=item),
                config=types.GenerateContentConfig(
                    response_mime_type='application/json'
                ),
            )
            usage = response.usage_metadata
            self.input_tokens += usage.prompt_token_count or 0
            self.output_tokens += usage.candidates_token_count or 0
            results.append(json.loads(response.text))
        return results
```

`response.usage_metadata` carries the actual token counts, which is more accurate than length heuristics. Without `response_mime_type='application/json'`, Gemini returns prose (often wrapped in markdown fences) and `json.loads` fails — every JSON-returning call needs both the config flag and a JSON-shaped prompt. For multimodal calls, pass content as a list (text + parts), not a single string.

## Image classification with Gemini Vision

```python
from google import genai
from google.genai import types
from PIL import Image
from pathlib import Path

client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

def classify_image(image_path: Path, categories: list[str]) -> dict:
    image = Image.open(image_path)

    prompt = f"""Analyze this image and classify it.

Available categories: {', '.join(categories)}

Respond with JSON:
{{
  "category": "category name",
  "description": "brief description",
  "suggested_filename": "descriptive-filename-with-dashes",
  "tags": ["tag1", "tag2", "tag3"]
}}
"""
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[prompt, image],
        config=types.GenerateContentConfig(response_mime_type='application/json'),
    )
    return json.loads(response.text)

# pathlib.Path.glob does NOT support brace expansion (`*.{jpg,png,webp}`);
# iterate the extensions explicitly.
IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.webp')

def organize_images(source_dir: Path, output_dir: Path):
    categories = ['Nature', 'People', 'Architecture', 'Art', 'Technology', 'Other']

    image_paths = (
        p for p in source_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )

    for image_path in image_paths:
        try:
            result = classify_image(image_path, categories)
            category_dir = output_dir / result['category']
            category_dir.mkdir(parents=True, exist_ok=True)

            new_name = f"{result['suggested_filename']}{image_path.suffix.lower()}"
            image_path.rename(category_dir / new_name)
        except Exception as e:
            failures = output_dir / 'failures'
            failures.mkdir(parents=True, exist_ok=True)
            image_path.rename(failures / image_path.name)
```

## Environment configuration

```python
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # API Keys
    GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
    GOOGLE_SHEET_ID = os.environ['GOOGLE_SHEET_ID']

    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / 'data'
    OUTPUT_DIR = PROJECT_ROOT / 'output'
    CREDENTIALS_PATH = PROJECT_ROOT / 'google_credentials.json'

    # Rate limits
    API_CALLS_PER_MINUTE = 10
    BATCH_SIZE = 50

    @classmethod
    def ensure_dirs(cls):
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
```

## Logging setup

```python
import logging
from pathlib import Path
from datetime import datetime

def setup_logging(log_dir: Path, name: str = 'pipeline') -> logging.Logger:
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler (INFO+)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    # File handler (DEBUG+)
    log_file = log_dir / f"{name}_{datetime.now():%Y%m%d_%H%M%S}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    logger.addHandler(console)
    logger.addHandler(file_handler)

    return logger
```

## Common pitfalls

**Google Sheets cell limits:**
```python
MAX_CELL_LENGTH = 50000

def truncate_for_sheets(text: str) -> str:
    if len(text) > MAX_CELL_LENGTH:
        return text[:MAX_CELL_LENGTH - 20] + '... [truncated]'
    return text
```

**CSV encoding issues:**
```python
# Always specify encoding
with open(path, 'r', encoding='utf-8-sig') as f:  # BOM handling
    reader = csv.reader(f)
```

**API quota management:**
```python
# Cache API responses
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_api_call(url: str) -> dict:
    return api_client.fetch(url)
```
