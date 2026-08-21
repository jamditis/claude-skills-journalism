## Building a verification trail

### Documentation template

```markdown
## Verification record

**Claim being verified:**
[State the specific claim]

**Source of claim:**
- Name/account:
- Platform:
- Date first seen:
- URL (archived):

**Verification steps taken:**

### Step 1: [Description]
- Action taken:
- Tool/method used:
- Result:
- Screenshot/evidence saved: [filename]

### Step 2: [Description]
- Action taken:
- Tool/method used:
- Result:
- Screenshot/evidence saved: [filename]

[Continue for each step]

**Corroborating sources:**
1. [Source 1] - [What it confirms]
2. [Source 2] - [What it confirms]
3. [Source 3] - [What it confirms]

**Contradicting information:**
1. [Source] - [What it contradicts]

**Confidence assessment:**
- [ ] Verified true
- [ ] Likely true (high confidence)
- [ ] Unverified (insufficient evidence)
- [ ] Likely false (contradicting evidence)
- [ ] Verified false

**Reasoning:**
[Explain your conclusion based on evidence]

**Verification completed by:**
**Date:**
```

## Archiving evidence

### Web archiving best practices

For full archiving workflows (rate limits, batch jobs, recovery from broken archives), use the **web-archiving** skill. The snippet here covers the minimum journalist-usable pattern: archive the same URL to Wayback Machine and Archive.today simultaneously so a single archive going down doesn't lose the evidence.

```python
import requests
from urllib.parse import quote

def archive_url(url: str, perma_cc_api_key: str | None = None) -> dict:
    """Archive a URL to Wayback Machine and Archive.today.

    Returns a dict with the archived URL (or error) for each service.
    Pass perma_cc_api_key to also archive to Perma.cc (requires an account).
    """
    results = {}

    # Internet Archive Wayback Machine
    try:
        response = requests.get(
            f'https://web.archive.org/save/{quote(url, safe="")}',
            timeout=60,
            allow_redirects=True,
        )
        if response.status_code == 200:
            results['wayback'] = response.url
        else:
            results['wayback_error'] = f'HTTP {response.status_code}'
    except requests.RequestException as e:
        results['wayback_error'] = str(e)

    # Archive.today, POST to /submit/, the archived URL appears in the
    # Refresh header (or the Location header on a 302).
    try:
        response = requests.post(
            'https://archive.ph/submit/',
            data={'url': url},
            timeout=120,
            allow_redirects=False,
            headers={'User-Agent': 'Mozilla/5.0 (verification archive bot)'},
        )
        archived = response.headers.get('Refresh', '').split('url=')[-1] \
            or response.headers.get('Location', '')
        if archived:
            results['archive_today'] = archived
        else:
            results['archive_today_error'] = f'no archived URL returned (HTTP {response.status_code})'
    except requests.RequestException as e:
        results['archive_today_error'] = str(e)

    # Perma.cc (optional, requires API key from a Perma account)
    if perma_cc_api_key:
        try:
            response = requests.post(
                'https://api.perma.cc/v1/archives/',
                json={'url': url},
                headers={'Authorization': f'ApiKey {perma_cc_api_key}'},
                timeout=60,
            )
            if response.status_code == 201:
                results['perma_cc'] = f"https://perma.cc/{response.json()['guid']}"
            else:
                results['perma_cc_error'] = f'HTTP {response.status_code}'
        except requests.RequestException as e:
            results['perma_cc_error'] = str(e)

    return results
```

Run on every primary-source URL the moment you decide it might appear in the story. Pages disappear, get edited, or go behind paywalls. An archive captured at the moment of reporting is the difference between a defensible quote and one that evaporates before publication.

### Screenshot documentation

```markdown
## Screenshot best practices

1. **Full page capture**: Use browser extensions for full-page screenshots
2. **Include URL bar**: Shows the source URL
3. **Include timestamp**: System clock visible or add manually
4. **Save metadata**: Note when and how captured
5. **Multiple formats**: Save as PNG (lossless) and PDF
6. **Secure storage**: Hash files and store securely

Recommended tools:
- Hunchly (hunch.ly) - automatic capture and logging
- Screenpresso - full page with annotations
- Browser print-to-PDF - includes URL and date
```
