---
name: social-media-intelligence
description: Social media monitoring, narrative tracking, and open-source intelligence for journalists. Use when tracking viral content spread, analyzing coordinated campaigns, monitoring breaking news on social platforms, investigating accounts for authenticity, or detecting misinformation patterns. Essential for reporters covering online narratives and digital investigations.
---

# Social media intelligence

Systematic approaches for monitoring, analyzing, and investigating social media for journalism.

## When to activate

- Tracking how a story spreads across platforms
- Investigating potential coordinated inauthentic behavior
- Monitoring breaking news across social platforms
- Analyzing account networks and relationships
- Detecting bot activity or manipulation campaigns
- Building evidence trails for digital investigations
- Archiving social content before deletion

## Real-time monitoring

### Multi-platform tracker

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum
import hashlib

class Platform(Enum):
    TWITTER = "twitter"  # X since 2023; "twitter" retained for legacy data
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    THREADS = "threads"
    BLUESKY = "bluesky"
    MASTODON = "mastodon"
    TELEGRAM = "telegram"

@dataclass
class SocialPost:
    platform: Platform
    post_id: str
    author: str
    content: str
    timestamp: datetime
    url: str
    engagement: Dict[str, int] = field(default_factory=dict)
    media_urls: List[str] = field(default_factory=list)
    archived_urls: List[str] = field(default_factory=list)
    content_hash: str = ""

    def __post_init__(self):
        # Hash content for duplicate detection
        self.content_hash = hashlib.md5(
            f"{self.platform.value}:{self.content}".encode()
        ).hexdigest()

@dataclass
class MonitoringQuery:
    keywords: List[str]
    platforms: List[Platform]
    accounts: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    exclude_terms: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None

    def to_search_string(self, platform: Platform) -> str:
        """Generate platform-specific search query."""
        parts = []

        # Keywords
        if self.keywords:
            parts.append(' OR '.join(f'"{k}"' for k in self.keywords))

        # Hashtags
        if self.hashtags:
            parts.append(' OR '.join(f'#{h}' for h in self.hashtags))

        # Exclusions
        if self.exclude_terms:
            parts.append(' '.join(f'-{t}' for t in self.exclude_terms))

        return ' '.join(parts)
```

### Breaking news monitor

```python
from collections import defaultdict
from datetime import datetime, timedelta

class BreakingNewsDetector:
    """Detect sudden spikes in keyword mentions."""

    def __init__(self, baseline_window_hours: int = 24):
        self.baseline_window = timedelta(hours=baseline_window_hours)
        self.mention_history = defaultdict(list)

    def add_mention(self, keyword: str, timestamp: datetime):
        """Record a mention of a keyword."""
        self.mention_history[keyword].append(timestamp)
        # Prune old data
        cutoff = datetime.now() - self.baseline_window * 2
        self.mention_history[keyword] = [
            t for t in self.mention_history[keyword] if t > cutoff
        ]

    def is_spiking(self, keyword: str, threshold_multiplier: float = 3.0) -> bool:
        """Check if keyword is spiking above baseline."""
        now = datetime.now()
        recent = sum(1 for t in self.mention_history[keyword]
                    if t > now - timedelta(hours=1))

        baseline_hourly = len([
            t for t in self.mention_history[keyword]
            if t > now - self.baseline_window
        ]) / self.baseline_window.total_seconds() * 3600

        if baseline_hourly == 0:
            return recent > 10  # Arbitrary threshold for new topics

        return recent > baseline_hourly * threshold_multiplier

    def get_trending(self, top_n: int = 10) -> List[tuple]:
        """Get keywords sorted by spike intensity."""
        spikes = []
        for keyword in self.mention_history:
            if self.is_spiking(keyword):
                recent = sum(1 for t in self.mention_history[keyword]
                           if t > datetime.now() - timedelta(hours=1))
                spikes.append((keyword, recent))

        return sorted(spikes, key=lambda x: x[1], reverse=True)[:top_n]
```

## Account analysis

### Authenticity indicators

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class AccountAnalysis:
    username: str
    platform: Platform
    created_date: Optional[datetime] = None
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0

    # Authenticity signals
    profile_photo_is_stock: Optional[bool] = None
    bio_contains_keywords: List[str] = field(default_factory=list)
    posts_primarily_reshares: Optional[bool] = None
    posting_pattern_irregular: Optional[bool] = None
    engagement_ratio_suspicious: Optional[bool] = None

    def calculate_red_flags(self) -> dict:
        """Score account authenticity."""
        flags = {}

        # Account age
        if self.created_date:
            age_days = (datetime.now() - self.created_date).days
            if age_days < 30:
                flags['new_account'] = f"Created {age_days} days ago"

        # Follower ratio
        if self.following_count > 0:
            ratio = self.follower_count / self.following_count
            if ratio < 0.1:
                flags['low_follower_ratio'] = f"Ratio: {ratio:.2f}"

        # Posting frequency
        if self.created_date and self.post_count > 0:
            age_days = max(1, (datetime.now() - self.created_date).days)
            posts_per_day = self.post_count / age_days
            if posts_per_day > 50:
                flags['excessive_posting'] = f"{posts_per_day:.0f} posts/day"

        # Stock photo check
        if self.profile_photo_is_stock:
            flags['stock_profile_photo'] = "Profile appears to be stock image"

        return flags

    def authenticity_score(self) -> int:
        """0-100 score, higher = more likely authentic."""
        score = 100
        flags = self.calculate_red_flags()

        penalty_per_flag = 20
        score -= len(flags) * penalty_per_flag

        return max(0, score)
```

### Network mapping

```python
from collections import defaultdict
from typing import Set, Dict

class AccountNetwork:
    """Map relationships between accounts."""

    def __init__(self):
        self.interactions = defaultdict(lambda: defaultdict(int))
        self.accounts = {}

    def add_interaction(self, from_account: str, to_account: str,
                       interaction_type: str = "mention"):
        """Record an interaction between accounts."""
        self.interactions[from_account][to_account] += 1

    def find_clusters(self, min_interactions: int = 3) -> List[Set[str]]:
        """Find groups of accounts that frequently interact."""
        # Build adjacency with minimum threshold
        adjacency = defaultdict(set)
        for from_acc, targets in self.interactions.items():
            for to_acc, count in targets.items():
                if count >= min_interactions:
                    adjacency[from_acc].add(to_acc)
                    adjacency[to_acc].add(from_acc)

        # Find connected components
        visited = set()
        clusters = []

        for account in adjacency:
            if account in visited:
                continue

            cluster = set()
            stack = [account]

            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                cluster.add(current)
                stack.extend(adjacency[current] - visited)

            if len(cluster) > 1:
                clusters.append(cluster)

        return sorted(clusters, key=len, reverse=True)

    def coordination_score(self, accounts: Set[str]) -> float:
        """Score how coordinated a group of accounts appears."""
        if len(accounts) < 2:
            return 0.0

        total_possible = len(accounts) * (len(accounts) - 1)
        actual_connections = 0

        for acc in accounts:
            for other in accounts:
                if acc != other and self.interactions[acc][other] > 0:
                    actual_connections += 1

        return actual_connections / total_possible if total_possible > 0 else 0
```

## Narrative tracking

### Claim propagation tracker

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

@dataclass
class Claim:
    text: str
    first_seen: datetime
    first_seen_url: str
    variations: List[str] = field(default_factory=list)
    appearances: List[Dict] = field(default_factory=list)

    def add_appearance(self, url: str, platform: Platform,
                       timestamp: datetime, author: str):
        """Track where this claim has appeared."""
        self.appearances.append({
            'url': url,
            'platform': platform.value,
            'timestamp': timestamp,
            'author': author
        })

    def spread_timeline(self) -> List[Dict]:
        """Get chronological spread of the claim."""
        return sorted(self.appearances, key=lambda x: x['timestamp'])

    def platforms_reached(self) -> Dict[str, int]:
        """Count appearances by platform."""
        counts = defaultdict(int)
        for app in self.appearances:
            counts[app['platform']] += 1
        return dict(counts)

    def velocity(self, window_hours: int = 24) -> float:
        """Calculate spread rate in appearances per hour."""
        if not self.appearances:
            return 0.0

        recent = [
            a for a in self.appearances
            if a['timestamp'] > datetime.now() - timedelta(hours=window_hours)
        ]
        return len(recent) / window_hours
```

### Hashtag analysis

```python
from collections import Counter
from datetime import datetime, timedelta

class HashtagAnalyzer:
    """Analyze hashtag usage patterns."""

    def __init__(self):
        self.hashtag_posts = defaultdict(list)

    def add_post(self, hashtags: List[str], post: SocialPost):
        """Record a post's hashtags."""
        for tag in hashtags:
            self.hashtag_posts[tag.lower()].append(post)

    def co_occurrence(self, hashtag: str, top_n: int = 10) -> List[tuple]:
        """Find hashtags that commonly appear with this one."""
        co_tags = Counter()

        for post in self.hashtag_posts.get(hashtag.lower(), []):
            # Extract hashtags from post content
            tags = [
                word.lower() for word in post.content.split()
                if word.startswith('#')
            ]
            for tag in tags:
                if tag != f'#{hashtag.lower()}':
                    co_tags[tag] += 1

        return co_tags.most_common(top_n)

    def posting_pattern(self, hashtag: str) -> Dict:
        """Analyze when posts with this hashtag appear."""
        posts = self.hashtag_posts.get(hashtag.lower(), [])

        hour_counts = Counter(p.timestamp.hour for p in posts)
        day_counts = Counter(p.timestamp.strftime('%A') for p in posts)

        return {
            'by_hour': dict(hour_counts),
            'by_day': dict(day_counts),
            'total_posts': len(posts),
            'unique_authors': len(set(p.author for p in posts))
        }
```

## Evidence preservation

### Archive before it disappears

For full archiving workflows (rate limits, batch jobs, recovery from broken archive UIs), see the **web-archiving** skill.

```python
import re
import requests
from datetime import datetime
from typing import Optional
from urllib.parse import quote, urljoin

class SocialArchiver:
    """Archive social content before deletion."""

    def __init__(self):
        self.archived = {}

    def archive_to_wayback(self, url: str) -> Optional[str]:
        """Submit URL to Internet Archive.

        Anonymous saves are rate-limited at roughly 15/minute and silently drop
        some paywalled or heavily JS-rendered pages. For high-volume archiving,
        register an Internet Archive S3 key and add an Authorization header.
        """
        try:
            save_url = f"https://web.archive.org/save/{quote(url, safe='')}"
            response = requests.get(save_url, timeout=30)
            if response.status_code == 200:
                archived_url = response.url
                self.archived[url] = {
                    'wayback': archived_url,
                    'archived_at': datetime.now().isoformat(),
                }
                return archived_url
        except Exception as e:
            print(f"Wayback archive failed: {e}")
        return None

    def archive_to_archive_today(self, url: str) -> Optional[str]:
        """Submit URL to archive.today.

        Operational notes (2026): the FBI subpoenaed archive.today's registrar
        in October 2025 to identify the operator; Wikipedia voted in February
        2026 to stop accepting it as a citation source after the site shipped
        DDoS-attack code in January 2026. The service is still useful for
        capturing content the Wayback Machine can't render, but treat it as
        secondary to the Internet Archive and document any reliance on it.
        It also rate-limits aggressively and serves CAPTCHAs to scrapers.
        """
        try:
            response = requests.post(
                'https://archive.today/submit/',
                data={'url': url, 'anyway': '1'},
                timeout=60,
                allow_redirects=False,
                headers={'User-Agent': 'Mozilla/5.0 (verification archive bot)'},
            )
            # archive.today returns the snapshot URL in one of two shapes:
            #   - 30x with Location: https://archive.today/<snapshot_id>
            #   - 200 with Refresh: 0;url=https://archive.today/<snapshot_id>
            # Following redirects silently can land on /wip/ pages or hide the
            # canonical snapshot URL, so handle both headers explicitly.
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get('Location')
                if location:
                    # Location MAY be relative per RFC 7231; resolve against request URL.
                    return urljoin(response.url, location)
            if response.status_code == 200:
                refresh = response.headers.get('Refresh', '')
                # Refresh keyword is case-insensitive per HTML spec; values may
                # contain ;-separated params. Match the url= directive itself.
                m = re.search(r'\burl\s*=\s*(.+)', refresh, re.IGNORECASE)
                if m:
                    target = m.group(1).strip().strip('\'"')
                    return urljoin(response.url, target)
        except Exception as e:
            print(f"archive.today failed: {e}")
        return None

    def full_archive(self, url: str) -> dict:
        """Archive to multiple services for redundancy."""
        results = {
            'original_url': url,
            'archived_at': datetime.now().isoformat(),
            'archives': {},
        }

        wayback = self.archive_to_wayback(url)
        if wayback:
            results['archives']['wayback'] = wayback

        archive_today = self.archive_to_archive_today(url)
        if archive_today:
            results['archives']['archive_today'] = archive_today

        return results
```

## Coordination detection

### Behavioral signals checklist

```markdown
## Coordinated inauthentic behavior indicators

### Timing patterns
- [ ] Multiple accounts posting same content within minutes
- [ ] Synchronized posting times across accounts
- [ ] Burst activity followed by dormancy
- [ ] Posts appear faster than human typing speed

### Content patterns
- [ ] Identical or near-identical text across accounts
- [ ] Same images/media shared by multiple accounts
- [ ] Identical typos or formatting errors
- [ ] Copy-paste artifacts visible

### Account patterns
- [ ] Accounts created around same time
- [ ] Similar naming conventions (name + numbers)
- [ ] Generic or stock profile photos
- [ ] Minimal personal content, mostly shares
- [ ] Follow the same accounts
- [ ] Engage with each other disproportionately

### Network patterns
- [ ] Form dense clusters in network analysis
- [ ] Amplify same external sources
- [ ] Target same accounts or hashtags
- [ ] Cross-platform coordination visible
```

### Automated coordination scoring

```python
def coordination_likelihood(posts: List[SocialPost]) -> dict:
    """Score how likely posts represent coordinated activity."""

    if len(posts) < 2:
        return {'score': 0, 'signals': []}

    signals = []
    score = 0

    # Check for identical content
    contents = [p.content for p in posts]
    unique_contents = set(contents)
    if len(unique_contents) < len(contents) * 0.5:
        signals.append("High content duplication")
        score += 30

    # Check timing clusters
    timestamps = sorted(p.timestamp for p in posts)
    rapid_posts = 0
    for i in range(1, len(timestamps)):
        if (timestamps[i] - timestamps[i-1]).seconds < 60:
            rapid_posts += 1

    if rapid_posts > len(posts) * 0.3:
        signals.append("Suspicious timing clusters")
        score += 25

    # Check unique authors
    authors = set(p.author for p in posts)
    if len(authors) > 5 and len(contents) / len(authors) > 2:
        signals.append("Few authors, many similar posts")
        score += 20

    return {
        'score': min(100, score),
        'signals': signals,
        'posts_analyzed': len(posts),
        'unique_authors': len(authors)
    }
```

## Platform-specific tools

Status as of 2026. Platform APIs change rapidly — verify pricing and access before designing a project around any one path.

| Platform | Research access | Notes |
|----------|-----------------|-------|
| X (Twitter) | Pay-per-use developer API (developer.x.com); X Pro Search (consumer-facing, behind X Premium+); Brandwatch / Sprinklr (paid third-party) | Free academic/research tier ended early 2023. The 2024 Basic and Pro subscription tiers were replaced in Feb 2026 with a pay-per-use model — billed by API call, no monthly subscription. Verify current per-call rates and any rate-limit caps in the developer portal before scoping a project. Post-2023 ToS explicitly prohibits scraping. |
| Facebook / Instagram | Meta Content Library + Library API (research access); Junkipedia (free, journalist-friendly); NewsWhip (paid) | CrowdTangle was shut down on Aug 14, 2024 — it does not exist in any form. Meta Content Library replaced it. As of Dec 8, 2025, applications go through Meta's portal directly (previously routed via University of Michigan ICPSR). Eligibility favors academic and nonprofit researchers; most working journalists qualify only through institutional affiliation. SOMAR and other secure enclaves remain typical execution environments. |
| TikTok | Research API (qualifying academic and nonprofit researchers; DSA-vetted researchers in the EU); Exolyt, Pentos (paid) | Apply at developers.tiktok.com. Eligible organizations are typically academic institutions and nonprofit research entities; EU-based researchers have stronger access via DSA Article 40. Playlist Info and Commercial Content endpoints expanded in 2026. |
| YouTube | YouTube Data API v3 | 10,000 units per day default (search costs 100 units = ~100 searches/day); higher quota by application, multi-week review. No journalist-specific tier. |
| Reddit | Reddit API (free for non-commercial research); Arctic Shift (Pushshift successor, free dumps via Academic Torrents) | Pushshift restricted to verified moderators since 2023 — it is no longer a journalist-research path. Arctic Shift is the active successor. |
| Bluesky | Jetstream (filtered JSON over WebSocket, no auth required) or raw firehose | Public-by-default. Jetstream is the journalist-friendly entrypoint at ~850 MB/day filtered; raw firehose is 4-8 GB/hour and requires you to build archives yourself. |
| Threads (Meta) | Threads API (publishing/embedding); Meta Content Library (research) | Public profile discovery threshold lowered to 100 followers in March 2026. Bulk historical research routes through Meta Content Library, with the same academic-only restriction. |
| Mastodon / Fediverse | Public-timeline API (per-instance); cross-instance search at search.noc.social or fediverse.info | Many instances now set `DISALLOW_UNAUTHENTICATED_API_ACCESS`; admin-controlled. Cross-instance search is fragmented. |
| Telegram | Bot API + MTProto + public previews at `t.me/s/<channel>`; Bellingcat tools (Telegago, Telepathy, TelegramDB) | Public-channel scraping is legal in most jurisdictions; private groups are off-limits. |

### EU DSA Article 40 access

The EU Digital Services Act gives EU-based researchers stronger access rights than US researchers on TikTok and the Meta platforms. US journalists may need EU institutional partners (a university, a vetted research nonprofit) to qualify for the Research API tiers on those platforms. This is a real path, not a workaround.

## OSINT tooling

The custom Python heuristics above are starting points for monitoring and pattern surfacing. For production OSINT work, the canonical external tools are:

### Account authenticity and coordination

- **Botometer X** (osome.iu.edu) — academic standard for Twitter bot likelihood; archival mode only since June 2023, so it cannot score accounts created or active after May 31, 2023.
- **Hoaxy / Hoaxy2** (osome.iu.edu) — operational; Hoaxy2 added Mastodon search, Bluesky real-time monitoring, and a Facebook News Bridge. Bot scores were removed when the Twitter API died.
- **OSoMe Coordiscope** — coordinated-network visualizer, free.
- **CooRTweet** (R package) — successor to CooRnet for coordinated inauthentic behavior analysis. CooRnet was discontinued alongside CrowdTangle in August 2024.
- **Bot Sentinel** (botsentinel.com) — was offline through 2025 with relaunch announced for 2026; verify operational status before citing in reporting.

### Reverse image and forensic verification

- **TinEye** — canonical exact-match and first-appearance reverse-image search.
- **Yandex Images** — strong for face and region matching, especially Russia and Eastern Europe.
- **Google Lens** — successor to the deprecated legacy Google reverse-image search.
- **Forensically** (29a.ch) and **FotoForensics** — image manipulation analysis (error level analysis, clone detection, metadata).
- **InVID-WeVerify plugin** — operational under the EU vera.ai project; new beta synthetic-image and voice-clone detectors added in 2025. Some Twitter-era features broke after the API change.

### Network analysis

- **Gephi** — free, open-source; the ICIJ Panama Papers tool of record.
- **Maltego CE** — Community Edition free with registration; paid tiers expanded in 2025.
- **NodeXL** — Excel add-on, basic free / Pro paid; legacy but functional.

### Methodology authorities (current, 2026)

- **Bellingcat Online Investigation Toolkit** ([bellingcat.gitbook.io/toolkit](https://bellingcat.gitbook.io/toolkit)) — community-maintained "Toolkit 2.0," updated continuously.
- **Information Futures Lab** at Brown SPH — successor to First Draft News (which closed June 2022); Claire Wardle co-directs.
- **WITNESS Deepfakes Rapid Response Force** ([gen-ai.witness.org](https://www.gen-ai.witness.org/deepfakes-rapid-response-force/)) — pairs reporters with media-forensics experts on deadline.
- **CJR Tow Center** — non-technical 2025 deepfake-detection guide for journalists.
- Note: **Stanford Internet Observatory** was effectively dismantled in June 2024; the election-research mantle moved to the **Stanford Social Media Lab** (Hancock) and the **NYU Stern Center for Business and Human Rights**.

## Ethical guidelines

- Archive public content only.
- Don't create fake accounts for monitoring.
- Respect platform terms of service. X's post-2023 ToS explicitly prohibits scraping even of public posts; rely on the API or licensed data brokers. Don't reuse research-access tokens for non-research purposes — Meta and TikTok terminate access for ToS drift.
- Protect sources who share social content.
- Verify before publishing claims about coordination — coordination scoring is a hypothesis, not a finding.
- Consider context before amplifying harmful content.

## Related skills

- **source-verification** — Verify accounts and claims found on social
- **web-archiving** — Full archiving workflows beyond the wrappers shown above
- **web-scraping** — Programmatic collection of public content
- **data-journalism** — Analyze social data for patterns and produce charts
- **crisis-communications** — Time-pressure verification during breaking news

---

## Skill metadata

| Field | Value |
|-------|-------|
| version | 1.1.0 |
| created | 2025-12-26 |
| updated | 2026-05-08 |
| author | Joe Amditis |
| domain | journalism, osint |
| complexity | advanced |
