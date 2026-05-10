---
name: free-apis-catalog
description: Use when suggesting APIs for a project, looking for free data sources, building weekend projects that need external data, or when the user needs weather, news, finance, sports, ML, or entertainment data without paid subscriptions
---

# Free APIs catalog (journalism-curated)

A short list of free APIs that work for journalism, research, and weekend projects under current free-tier conditions. The value here is curation under verified 2026 free-tier limits — not coverage. For breadth, defer to the canonical aggregator below.

## Canonical breadth reference

For a near-complete inventory of free public APIs across every category (1000+ entries, actively maintained), use:

- **public-apis/public-apis on GitHub** — https://github.com/public-apis/public-apis

Not archived, last commit verified 2026-05-09, 4,600+ commits, 6,000+ merged PRs. When you need an API outside the categories below, search there first.

This skill curates the journalism-relevant subset.

## Recently sunset / changed (don't use)

| API | Status | What to use instead |
|---|---|---|
| **IEX Cloud** | Fully retired 2024-08-31. https://iexcloud.org/ | Alpha Vantage, Tiingo IEX, Financial Modeling Prep, Polygon |
| **CrowdTangle** | Sunset 2024-08-14 | Meta Content Library (academic/non-profit-research only — most journalists ineligible). https://transparency.meta.com/researchtools/meta-content-library/ |
| **ProPublica Congress API** | Retired 2024-07-10, repo archived. https://www.propublica.org/nerds/congress-api-update | api.congress.gov (Library of Congress, free with api.data.gov key) |
| **X / Twitter API free tier** | Effectively eliminated for new developers as of Feb 2026; pay-per-use only. Uncertain on exact figures (provider pricing page returned 402). Treat as paid. | No free replacement; closest free alternatives are Bluesky Jetstream + Mastodon |
| **Reddit API** | Free for research/non-commercial only since June 2023; paid for commercial use. https://www.reddit.com/wiki/api/ | (Same — usable for journalism research, prohibited for monetized products) |
| **Hugging Face Inference API** | Rebranded to Inference Providers (router across 20+ providers). Free users now get $0.10/month in credits, down from previous unmetered free tier for many models. https://huggingface.co/docs/inference-providers/pricing | Free tier still works for low-volume / embeddings; paid for production |

## Journalism-curated short list

All entries below verified against provider pages on 2026-05-09 unless marked **uncertain**. Always confirm rate limits against the provider's live developer docs before depending on them in production.

### News monitoring

| API | Free tier | Notes |
|---|---|---|
| [GDELT 2.0](https://gdeltproject.org/data.html) | Fully free, no auth | Global news + knowledge graph, updates every 15 min, BigQuery-mirrored. Strong for cross-border / longitudinal monitoring. |
| [NewsAPI](https://newsapi.org/pricing) | 100 req/day, 24h delay, 1mo window, dev-only | Commercial use prohibited on free tier. Not usable in shipped products. |
| [GNews](https://gnews.io/#pricing) | 100 req/day, 30d window, 12h delay, non-commercial | 10 articles/request cap. |
| [Mediastack](https://mediastack.com/pricing) | 100 req/month, 30-min delay | Functionally a demo. |
| [NYT Article Search / Top Stories](https://developer.nytimes.com/) | Free with key, daily cap (uncertain — verify) | Solid for archival queries. |

### Social platforms (post-API-monetization landscape)

| API | Free tier | Notes |
|---|---|---|
| [Bluesky Jetstream](https://docs.bsky.app/blog/jetstream) | Public WebSocket firehose, no auth | Real-time public-post stream. 4 official instances. Caveat: not formally part of AT Protocol — no long-term stability commitment. |
| [Bluesky AppView](https://docs.bsky.app/docs/advanced-guides/rate-limits) | Public read endpoints, 3000 req / 5min IP-based | Auth needed for write ops. Profiles, posts, search. |
| [Mastodon](https://docs.joinmastodon.org/api/) | Per-instance, OAuth, public endpoints often unauth-readable | Federated — coverage is server-by-server. |
| [Threads (Meta)](https://developers.facebook.com/docs/threads) | Free pricing not surfaced on docs page (uncertain — verify) | Read/post/reply/search/insights/webhooks. |
| [Reddit](https://www.reddit.com/wiki/api/) | 100 QPM authenticated, 10 QPM unauthenticated, non-commercial only | Adequate for OSINT/research, prohibited for monetized products. |
| [Meta Content Library](https://transparency.meta.com/researchtools/meta-content-library/) | Academic / non-profit researchers only | Most journalists need a university partner to qualify. |
| [TikTok Research API](https://developers.tiktok.com/products/research-api/) | Academic-affiliated researchers only | Same eligibility gate as MCL. |

### Government / public records (US)

| API | Free tier | Notes |
|---|---|---|
| [api.data.gov umbrella key](https://api.data.gov/) | One key for 25+ federal agencies, 450+ APIs | Gateway for NASA, NPS, NIH, USGS, FDA, EPA, LoC, etc. Use this first. |
| [api.congress.gov](https://api.congress.gov/) | Free with api.data.gov key | Official Library of Congress legislative data. Replaces ProPublica Congress API. |
| [GovInfo (GPO)](https://www.govinfo.gov/developers) | Uses api.data.gov key | Federal-publication search and full-text. New MCP server in public preview for LLM workflows. |
| [OpenFEC](https://api.open.fec.gov/developers/) | Free, api.data.gov key | Campaign finance. (Page ECONNREFUSED on verification day — confirm rate limits live.) |
| [Census API](https://api.census.gov/data.html) | Free, no documented rate limits | Demographic / economic data. |
| [BLS](https://www.bls.gov/developers/) | 500 queries/day, 25 series/query with key (**uncertain** — page 403'd; verify) | Labor statistics. |
| [BEA](https://apps.bea.gov/api/signup/) | Free with key | National income & product accounts. |
| [EPA Envirofacts](https://www.epa.gov/enviro/envirofacts-data-service-api) | Free, no auth | TRI, Superfund, ECHO, RCRAInfo, SDWIS, GHG, RadNet, FRS — ~20 EPA programs. |
| [USGS earthquakes](https://earthquake.usgs.gov/fdsnws/event/1/) | Free, no auth | Real-time + historical earthquake events. GeoJSON / QuakeML / CSV. |

### Weather / climate

| API | Free tier | Notes |
|---|---|---|
| [NWS api.weather.gov](https://www.weather.gov/documentation/services-web-api) | Fully free, no key, just User-Agent header | "Generous" rate limit. Forecasts, alerts, observations, gridpoints. US only. |
| [Open-Meteo](https://open-meteo.com/en/pricing) | Free non-commercial: 600/min, 10k/day, 300k/month, no key | CC BY 4.0 attribution required. Global. Commercial use requires paid. |
| [OpenWeather](https://openweathermap.org/price) | 60 calls/min, 1M calls/mo on free tier | Historical weather, 30-day forecasts, Bulk Download, Weather History API are paid. Students get historical via student program. |

### Financial / economic

| API | Free tier | Notes |
|---|---|---|
| [FRED (St. Louis Fed)](https://fred.stlouisfed.org/docs/api/fred/) | Free with key (**uncertain** — page 403'd; verify limits) | Primary reference for US macro data. |
| [CoinGecko Demo](https://www.coingecko.com/en/api/pricing) | 10k calls/mo, 30/min, free with key | Attribution required. |
| [Alpha Vantage](https://www.alphavantage.co/support/#api-key) | 25 requests/day | Free tier is now a demo, not a usable journalism data source. Migration target for IEX Cloud users — but expect to need a paid tier for any real workload. |
| [Financial Modeling Prep](https://site.financialmodelingprep.com/) | Free tier exists, paid for production | IEX Cloud successor. |

### Archive / preservation

| API | Free tier | Notes |
|---|---|---|
| [Wayback Machine](https://archive.org/help/wayback_api.php) | Free | Availability JSON, Memento, CDX server. Save Page Now exposes programmatic submit. |
| archive.today | Programmatic submit available; no public API docs (uncertain — WebFetch blocked) | Useful for redundancy alongside Wayback. Verify endpoint by direct curl. |

### AI / ML

| API | Free tier | Notes |
|---|---|---|
| [Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/pricing) | $0.10/month free credit, then pay-as-you-go | 2024 rebrand from "Inference API." Plain HF Inference now mostly CPU-only (embeddings, BERT-class). PRO users get $2/month. |
| [Cohere](https://docs.cohere.com/reference/about) | Free trial key for development, rate-limited | Paid for production. |

### Sports

| API | Free tier | Notes |
|---|---|---|
| [TheSportsDB](https://www.thesportsdb.com/free_sports_api) | Free at point of access | $9/mo premium for production key. |
| [football-data.org](https://www.football-data.org/coverage) | Free tier covers 12 major competitions | UCL, Premier League, La Liga, Serie A, Bundesliga, Ligue 1, etc. |

## Evaluating APIs from the catalog

When picking an API for a journalism project, check three things on the provider's developer docs:

| Field | What to check |
|-------|---------------|
| **Auth** | "No auth" = no registration. "Key required" = sign up + manage the key. OAuth = per-user flow. |
| **Free-tier limits** | Daily / monthly request caps, rate limits per minute, article delay (often 12–24h on free tiers), recency window. |
| **Commercial restriction** | Many "free" APIs prohibit commercial use. Even an internal newsroom tool that supports paid coverage may count. Read the ToS. |
| **CORS** | Matters for browser frontends, irrelevant for backend scripts and cron jobs. |
| **Stability commitment** | Some "free firehose" APIs (e.g., Bluesky Jetstream) have no long-term stability commitment. Don't depend on them in production without a fallback. |

## Weekend project ideas

- **News alerts:** GDELT or NewsAPI + keyword filter + Telegram bot (2–3 hours)
- **Sentiment signal:** News feed + Hugging Face sentiment model + score from −1 to +1 (note free-tier credit cap)
- **Weather dashboard:** Open-Meteo + historical data + forecast for target city
- **Earthquake monitor:** USGS FDSN feed + threshold filter + Slack notification
- **Federal dataset explorer:** api.data.gov key + cycle through agencies + index findings to a project digital archive

## Usage tip

For any new project needing external data: check the journalism-curated list above first. If nothing fits, search public-apis/public-apis. Feed candidate API docs to an agent along with your specific use case — it'll spot rate-limit / commercial-use traps that a casual read would miss.

## Last currency sweep

2026-05-09. Verified directly against provider pages where reachable; uncertain entries marked inline with the specific provider page that failed verification (403, ECONNREFUSED, login-walled). Re-verify rate-limit numbers before depending on them in production.

---

*Curation under current free-tier conditions is what paid alternatives like RapidAPI's directory don't provide. Coverage is what public-apis/public-apis is for.*
