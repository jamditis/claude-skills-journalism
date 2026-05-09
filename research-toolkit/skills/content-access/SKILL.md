---
name: content-access
description: Legal methods for accessing paywalled and geo-blocked content. Use when researching behind paywalls, accessing academic papers, bypassing geographic restrictions, or finding open access alternatives. Covers Unpaywall, library databases, VPNs, and ethical access strategies for journalists and researchers.
---

# Content access methodology

Ethical and legal approaches for accessing restricted web content for journalism and research.

## Access hierarchy (most to least preferred)

```
┌─────────────────────────────────────────────────────────────────┐
│              CONTENT ACCESS DECISION HIERARCHY                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. FULLY LEGAL (Always try first)                              │
│     ├─ Library databases (PressReader, ProQuest, JSTOR)         │
│     ├─ Open access tools (Unpaywall, CORE, PubMed Central)     │
│     ├─ Author direct contact                                    │
│     └─ Interlibrary loan                                        │
│                                                                  │
│  2. LEGAL (Browser features)                                    │
│     ├─ Reader Mode (Safari, Firefox, Edge)                      │
│     ├─ Wayback Machine archives                                 │
│     └─ Google Scholar "All versions"                            │
│                                                                  │
│  3. GREY AREA (Use with caution)                               │
│     ├─ Archive.is for individual articles                       │
│     ├─ Disable JavaScript (breaks functionality)                │
│     └─ VPNs for geo-blocked content                            │
│                                                                  │
│  4. NOT RECOMMENDED                                             │
│     ├─ Credential sharing                                       │
│     ├─ Systematic scraping                                      │
│     └─ Commercial use of bypassed content                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Open access tools for academic papers

### Unpaywall browser extension

Unpaywall finds free, legal copies of 50M+ open-access academic records.

```python
# Unpaywall API (free, requires email for identification)
import requests

def find_open_access(doi: str, email: str) -> dict:
    """Find open access version of a paper using Unpaywall API.

    Args:
        doi: Digital Object Identifier (e.g., "10.1038/nature12373")
        email: Your email for API identification

    Returns:
        Dict with best open access URL if available
    """
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"

    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        return {'error': f'Status {response.status_code}'}

    data = response.json()

    if data.get('is_oa'):
        best_location = data.get('best_oa_location', {})
        return {
            'is_open_access': True,
            'oa_url': best_location.get('url_for_pdf') or best_location.get('url'),
            'oa_status': data.get('oa_status'),  # gold, green, bronze, hybrid
            'host_type': best_location.get('host_type'),  # publisher, repository
            'version': best_location.get('version')  # publishedVersion, acceptedVersion
        }

    return {
        'is_open_access': False,
        'title': data.get('title'),
        'journal': data.get('journal_name')
    }

# Usage
result = find_open_access("10.1038/nature12373", "researcher@example.com")
if result.get('is_open_access'):
    print(f"Free PDF at: {result['oa_url']}")
```

### CORE API (290M+ open-access works)

```python
# CORE API - requires free API key from https://core.ac.uk/

import requests

class CORESearch:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.core.ac.uk/v3"

    def search(self, query: str, limit: int = 10) -> list:
        """Search CORE database for open access papers."""

        headers = {'Authorization': f'Bearer {self.api_key}'}
        params = {
            'q': query,
            'limit': limit
        }

        response = requests.get(
            f"{self.base_url}/search/works",
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            return []

        data = response.json()
        results = []

        for item in data.get('results', []):
            results.append({
                'title': item.get('title'),
                'authors': [a.get('name') for a in item.get('authors', [])],
                'year': item.get('yearPublished'),
                'doi': item.get('doi'),
                'download_url': item.get('downloadUrl'),
                'abstract': item.get('abstract', '')[:500]
            })

        return results

    def get_by_doi(self, doi: str) -> dict:
        """Get paper by DOI."""
        headers = {'Authorization': f'Bearer {self.api_key}'}

        response = requests.get(
            f"{self.base_url}/works/{doi}",
            headers=headers,
            timeout=30
        )

        return response.json() if response.status_code == 200 else {}
```

### Semantic Scholar API (220M+ papers)

```python
# Semantic Scholar API - free, but request a key from
# https://www.semanticscholar.org/product/api for anything beyond
# ad-hoc calls. Unkeyed access has been tightened to a low shared
# rate limit and is no longer reliable for batch lookups.

import requests

def search_semantic_scholar(query: str, limit: int = 10) -> list:
    """Search Semantic Scholar for papers with open access links."""

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        'query': query,
        'limit': limit,
        'fields': 'title,authors,year,abstract,openAccessPdf,citationCount'
    }

    response = requests.get(url, params=params, timeout=30)

    if response.status_code != 200:
        return []

    results = []
    for paper in response.json().get('data', []):
        oa_pdf = paper.get('openAccessPdf', {})
        results.append({
            'title': paper.get('title'),
            'authors': [a.get('name') for a in paper.get('authors', [])],
            'year': paper.get('year'),
            'citations': paper.get('citationCount', 0),
            'open_access_url': oa_pdf.get('url') if oa_pdf else None,
            'abstract': paper.get('abstract', '')[:500] if paper.get('abstract') else ''
        })

    return results

def get_paper_by_doi(doi: str) -> dict:
    """Get paper details by DOI."""
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
    params = {
        'fields': 'title,authors,year,abstract,openAccessPdf,references,citations'
    }

    response = requests.get(url, params=params, timeout=30)
    return response.json() if response.status_code == 200 else {}
```

### OpenAlex API (250M+ scholarly works)

OpenAlex replaced Microsoft Academic Graph after MAG was retired and
has become the de-facto open scholarly data backbone — many tools
(Unpaywall companion data, Local Citation Network, OpenCitations)
now resolve via OpenAlex.

**Auth note (2026):** OpenAlex moved to API-key-required access on
February 13, 2026, with a credit-based rate model. Anonymous access
to the website is still free; API access via key has metered limits
that step up with paid tiers — verify the current model at
https://docs.openalex.org/. Get a free key from your OpenAlex account.

```python
# OpenAlex API client
# https://docs.openalex.org/
# Pricing & key issuance: https://openalex.org/

import requests

def search_openalex(query: str, api_key: str, limit: int = 25,
                    email: str = None) -> list:
    """Search OpenAlex for works.

    Args:
        query: free-text search string.
        api_key: OpenAlex API key (required as of 2026-02-13).
        limit: max results per page (1-200).
        email: contact email for the polite pool — recommended even
               with a key, since OpenAlex prioritizes requests with
               an identifiable sender.
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'User-Agent': f'research-toolkit ({email})' if email else 'research-toolkit',
    }
    params = {'search': query, 'per-page': limit}

    response = requests.get(
        'https://api.openalex.org/works',
        params=params,
        headers=headers,
        timeout=30,
    )
    if response.status_code != 200:
        return []

    results = []
    for work in response.json().get('results', []):
        oa = work.get('open_access') or {}
        results.append({
            'id': work.get('id'),
            'doi': work.get('doi'),
            'title': work.get('title'),
            'year': work.get('publication_year'),
            'is_oa': oa.get('is_oa', False),
            'oa_status': oa.get('oa_status'),  # gold, green, hybrid, bronze, closed
            'oa_url': oa.get('oa_url'),
            'cited_by_count': work.get('cited_by_count', 0),
        })
    return results
```

### Other open-access sources worth checking

- **DOAJ** (`doaj.org/api/v3`) — Directory of Open Access Journals; useful when you need to verify a publisher is fully OA before trusting a "journal lookup" claim.
- **EuropePMC** (`europepmc.org/RestfulWebService`) — Mirror of PubMed Central plus preprints, OA full-text search, and ORCID-aware author lookup.
- **PubMed Central** (`eutils.ncbi.nlm.nih.gov`) — NIH OA biomedical archive; required for NIH-funded papers under the 2026 OSTP Nelson Memo.

### Deliberately excluded (legally risky, likely ToS / copyright violation)

This skill does not recommend Sci-Hub, Library Genesis (LibGen), Anna's
Archive, or paywall-redirector services like 12ft.io / removepaywall.com.
These are widely used in the research community but sit in clear legal
grey-to-red zones (depending on jurisdiction) and have been targets of
DMCA takedowns, publisher lawsuits, and domain seizures. Use the
legitimate open-access paths above; if a paper truly isn't available,
the author-contact and ILL paths in this skill have very high success
rates without legal exposure.

## Browser reader mode for soft paywalls

### Activating reader mode

This bookmarklet only works for **soft / metered paywalls** where the
publisher loads the article HTML and visually overlays a subscription
prompt — the content is already in the DOM, just hidden. It does
**not** defeat hard paywalls (NYT, WSJ, FT, The Atlantic, Bloomberg,
Stratechery, etc.) where article HTML is server-side gated; on those
sites the bookmarklet simply removes overlays and reveals nothing
useful. Systematic use to read otherwise-paywalled content may
violate the publisher's ToS — use it only as a reader-mode shim for
content you legitimately have access to.

```javascript
// Bookmarklet to strip soft-paywall overlays so reader mode works
// Works on some soft paywalls that load content before blocking

javascript:(function(){
    // Try to extract article content
    var article = document.querySelector('article') ||
                  document.querySelector('[role="main"]') ||
                  document.querySelector('.article-body') ||
                  document.querySelector('.post-content');

    if (article) {
        // Remove paywall overlays
        document.querySelectorAll('[class*="paywall"], [class*="subscribe"], [id*="paywall"]')
            .forEach(el => el.remove());

        // Remove fixed position overlays
        document.querySelectorAll('*').forEach(el => {
            var style = getComputedStyle(el);
            if (style.position === 'fixed' && style.zIndex > 100) {
                el.remove();
            }
        });

        // Re-enable scrolling
        document.body.style.overflow = 'auto';
        document.documentElement.style.overflow = 'auto';

        console.log('Overlay removed. Content may now be visible.');
    }
})();
```

### Reader mode by browser

| Browser | How to Activate | Effectiveness |
|---------|-----------------|---------------|
| **Safari** | Click Reader icon in URL bar | High for soft paywalls |
| **Firefox** | Click Reader View icon (or F9) | High |
| **Edge** | Click Immersive Reader icon | Highest |
| **Chrome** | Side panel → Reading mode (stable since Chrome 114, May 2023) | Medium |

## Library database access

### Checking library access programmatically

```python
# Most library databases require authentication
# This shows how to structure library API access

class LibraryAccess:
    """Access pattern for library databases."""

    # Common library database endpoints
    DATABASES = {
        'pressreader': {
            'base': 'https://www.pressreader.com',
            'auth': 'library_card',
            'content': '7000+ newspapers/magazines'
        },
        'proquest': {
            'base': 'https://www.proquest.com',
            'auth': 'institutional',
            'content': 'news, dissertations, documents'
        },
        'jstor': {
            'base': 'https://www.jstor.org',
            'auth': 'institutional',
            'content': 'academic journals, books'
        },
        'nexis_uni': {
            'base': 'https://www.nexisuni.com',
            'auth': 'institutional',
            'content': 'legal, news, business'
        }
    }

    @staticmethod
    def get_pressreader_access_methods():
        """Ways to access PressReader through libraries."""
        return {
            'in_library': 'Connect to library WiFi, visit pressreader.com',
            'remote': 'Log in with library card credentials',
            'app': 'Download PressReader app, link library card',
            'note': 'Session length varies by library; typically requires re-authentication every 24-72 hours'
        }

# Interlibrary Loan (ILL) workflow
def request_via_ill(paper_info: dict, library_email: str) -> str:
    """Generate interlibrary loan request.

    ILL is free through most libraries and can get almost any paper.
    Turnaround: typically 3-7 days.
    """

    request = f"""
    INTERLIBRARY LOAN REQUEST

    Title: {paper_info.get('title')}
    Author(s): {paper_info.get('authors')}
    Journal: {paper_info.get('journal')}
    Year: {paper_info.get('year')}
    DOI: {paper_info.get('doi')}
    Volume/Issue: {paper_info.get('volume')}/{paper_info.get('issue')}
    Pages: {paper_info.get('pages')}

    Requested by: {library_email}
    """

    return request.strip()
```

## VPN usage for geo-blocked content

### When VPNs are appropriate

```markdown
## Legitimate VPN use cases for journalists/researchers

### APPROPRIATE:
- Accessing region-specific news sources
- Researching how content appears in other countries
- Bypassing government censorship (in some contexts)
- Protecting source communications
- Verifying geo-targeted content

### INAPPROPRIATE:
- Circumventing legitimate access controls
- Accessing content you're contractually prohibited from viewing
- Evading bans or blocks placed on your account
```

### VPN service evaluation

VPN ratings age badly — privacy claims, ownership structures, and
audit findings change yearly. Rather than maintain a stale ranked
table here (the major commercial VPNs have undergone notable
ownership consolidation: ExpressVPN by Kape Technologies, Surfshark
merging with Nord), consult an independent reviewer at point-of-use:

- **PrivacyGuides** (`privacyguides.org/en/vpn/`) — community-maintained,
  privacy-prioritized recommendations with explicit criteria.
- **Privacy Tools** historical comparisons.
- **Tor Browser** (`torproject.org`) — maximum-anonymity option,
  free, no provider trust required; slow but the right tool for
  source protection or genuinely sensitive research.

For routine geo-restriction testing (not source protection),
mainstream commercial VPNs in the $3-10/month tier are
interchangeable on speed; pick on jurisdiction (your threat model)
and recent independent audits, not marketing copy.

### Checking geo-restriction status

```python
import requests

def check_geo_access(url: str, regions: list = None) -> dict:
    """Check if URL is accessible from different regions.

    Note: This requires VPN/proxy services for actual testing.
    This function shows the concept.
    """

    regions = regions or ['US', 'UK', 'EU', 'JP', 'AU']

    results = {}

    # Direct access test
    try:
        response = requests.get(url, timeout=10)
        results['direct'] = {
            'accessible': response.status_code == 200,
            'status_code': response.status_code
        }
    except Exception as e:
        results['direct'] = {'accessible': False, 'error': str(e)}

    # Would need VPN/proxy integration for regional testing
    # results[region] = test_through_proxy(url, region)

    return results
```

## Archive-based access

### Using Archive.today for paywalled articles

```python
import requests
from urllib.parse import quote, unquote

def get_archived_article(url: str) -> str:
    """Try to get article from Archive.today.

    Archive.today often captures full article content because it
    renders JavaScript and captures the result. Legal status varies
    by jurisdiction; treat systematic use to bypass paywalls as ToS-
    violating and use only for ad-hoc research access.

    Operational notes (2026): the FBI subpoenaed archive.today's
    registrar in October 2025; Wikipedia stopped accepting it as a
    citation source in February 2026. Still useful for capturing
    JS-rendered content, but treat as secondary to Wayback Machine
    for legal/citation use.
    """
    from urllib.parse import urljoin

    # /newest/<url> 302s to the most recent snapshot or to a CAPTCHA
    # page if rate-limited. Disable redirects so we can inspect the
    # Location header explicitly. quote(unquote(url), ...) normalizes
    # any existing %xx escapes so they aren't double-encoded.
    search_url = f"https://archive.ph/newest/{quote(unquote(url), safe='')}"

    try:
        response = requests.get(
            search_url,
            timeout=30,
            allow_redirects=False,
            headers={'User-Agent': 'Mozilla/5.0 (research-archiver)'},
        )
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get('Location')
            if location:
                resolved = urljoin(response.url, location)
                # Only return if we landed on an archive page, not CAPTCHA
                if 'archive.' in resolved and '/newest/' not in resolved:
                    return resolved
        return None
    except Exception:
        return None
```

### Wayback Machine for historical access

```python
def get_wayback_article(url: str) -> str:
    """Get article from Wayback Machine.

    100% legal - the Internet Archive is a recognized library.
    May have older versions of articles (before paywall implemented).
    """

    # Check availability
    api_url = "https://archive.org/wayback/available"

    try:
        response = requests.get(api_url, params={'url': url}, timeout=10)
        data = response.json()

        snapshot = data.get('archived_snapshots', {}).get('closest', {})

        if snapshot.get('available'):
            return snapshot['url']

        return None
    except Exception:
        return None
```

## Google Scholar strategies

### Finding free versions

```python
def find_free_via_scholar(title: str) -> list:
    """Search strategies for finding free paper versions.

    Google Scholar often links to:
    - Author's personal website copies
    - Institutional repository versions
    - ResearchGate/Academia.edu uploads
    """

    strategies = [
        {
            'method': 'scholar_all_versions',
            'description': 'Click "All X versions" under result',
            'success_rate': 'Medium-High'
        },
        {
            'method': 'scholar_pdf_link',
            'description': 'Look for [PDF] link on right side',
            'success_rate': 'Medium'
        },
        {
            'method': 'title_plus_pdf',
            'description': f'Search: "{title}" filetype:pdf',
            'success_rate': 'Medium'
        },
        {
            'method': 'author_site',
            'description': 'Find author\'s academic page',
            'success_rate': 'Medium'
        },
        {
            'method': 'preprint_servers',
            'description': 'Search arXiv, SSRN, bioRxiv',
            'success_rate': 'Field-dependent'
        }
    ]

    return strategies
```

## Direct author contact

### Email template for paper requests

```python
def generate_paper_request_email(paper: dict, requester: dict) -> str:
    """Generate professional email requesting paper from author.

    Authors are typically happy to share their work.
    Success rate: Very high (70-90%).
    """

    template = f"""
Subject: Request for paper: {paper['title'][:50]}...

Dear Dr./Prof. {paper['author_last_name']},

I am a {requester['role']} at {requester['institution']}, researching
{requester['research_area']}.

I came across your paper "{paper['title']}" published in
{paper['journal']} ({paper['year']}), and I believe it would be
highly relevant to my work on {requester['specific_project']}.

Unfortunately, I don't have access through my institution. Would you
be willing to share a copy?

I would be happy to properly cite your work in any resulting publications.

Thank you for your time and for your contribution to the field.

Best regards,
{requester['name']}
{requester['title']}
{requester['institution']}
{requester['email']}
"""

    return template.strip()
```

## Access strategy by content type

### News articles

```markdown
## News article access strategies

1. **Library PressReader** - 7,000+ publications worldwide
2. **Reader Mode** - Works on ~50% of soft paywalls
3. **Archive.org** - For older articles
4. **Archive.today** - For recent articles (grey area)
5. **Google search** - Sometimes cached versions appear

## Tips:
- Some publishers offer institutional access via .edu email — check the publisher's institutional-access page rather than assuming the program still exists; most major outlets have wound these programs down.
- Press releases often contain the same factual content as the paywalled article and can be quoted directly.
- Local library cards often include digital news access via PressReader, OverDrive, or the library's own login portal.
- Some publications have free tiers (5-10 articles/month) reset by clearing cookies; mind the publisher's ToS before relying on this.
- Archive.today snapshots of news articles work for ad-hoc research access but should not be the citation in your final piece — link the original article and keep the archive as a backup, with the FBI/Wikipedia caveat noted in the archive section above.
```

### Academic papers

```markdown
## Academic paper access strategies (in order)

1. **Unpaywall extension** - Check first, automatic
2. **OpenAlex** - 250M+ works with OA links; the de-facto open scholarly data backbone since MAG was retired
3. **Google Scholar** - Click "All versions", look for [PDF]
4. **Author's website** - Check their academic page
5. **Institutional repository** - Search university library
6. **Preprint servers** - arXiv, SSRN, bioRxiv, medRxiv (note: 2026 OSTP Nelson Memo requires immediate OA for federally-funded US research)
7. **ResearchGate/Academia.edu** - Author-uploaded copies, BUT availability is uneven: both have faced publisher takedown campaigns (Elsevier/ACS lawsuits) and many entries now resolve to "request full text" rather than a PDF
8. **CORE.ac.uk** - 290M+ open access papers
9. **PubMed Central** - For biomedical papers
10. **Contact author directly** - High success rate (70-90%)
11. **Interlibrary Loan** - Free, gets almost anything
```

### Books and reports

```markdown
## Book/report access strategies

1. **Library digital lending** - Internet Archive, OverDrive
2. **Google Books** - Often has preview or full text
3. **HathiTrust** - Academic library consortium
4. **Project Gutenberg** - Public domain books
5. **OpenLibrary** - Internet Archive's book lending
6. **Publisher open access** - Some chapters/reports free
7. **Author/organization website** - Reports often available
8. **Interlibrary Loan** - Physical books, scanned chapters
```

## Legal and ethical framework

### Fair use considerations (US)

```markdown
## Fair Use Factors (17 U.S.C. § 107)

1. **Purpose and character of use**
   - Transformative use (commentary, criticism) favored
   - Non-commercial/educational use favored
   - Journalism generally protected

2. **Nature of copyrighted work**
   - Factual works (news, research) - broader fair use
   - Creative works (fiction, art) - narrower fair use

3. **Amount used relative to whole**
   - Using only necessary portions favored
   - Heart of the work disfavored

4. **Effect on market**
   - Not replacing purchase disfavored
   - No market impact favored

## Journalism privilege:
News reporting is explicitly listed as fair use purpose.
However, wholesale copying of entire articles still problematic.
```

### Best practices for researchers

```markdown
## Ethical content access guidelines

### DO:
- Use library resources first (supports the ecosystem)
- Try open access tools before circumvention
- Contact authors directly (they want citations)
- Cite properly regardless of how you accessed content
- Budget for subscriptions to frequently-used sources

### DON'T:
- Share login credentials
- Systematically download entire databases
- Use bypassed content for commercial purposes
- Redistribute paywalled content
- Rely solely on bypass methods
```
