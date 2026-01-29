---
name: archive-reminder
description: Remind to archive URLs when citing web sources in journalism content
event: PostToolUse
tools: [Write, Edit]
---

# Archive reminder hook

After writing content with URLs, remind to archive web sources for permanence and evidence preservation.

## When this hook fires

- After `Write` tool creates content with URLs
- After `Edit` tool adds web citations
- When content includes links to external websites

## Why archive?

- **Link rot**: ~25% of web links break within 2 years
- **Content changes**: Pages are edited, sometimes to remove information
- **Evidence**: Archives provide timestamped proof of what was published
- **Legal**: Courts increasingly accept archived pages as evidence

## What to flag

### News article citations

```
⚠️ Archive: https://example.com/news/article
   → Save to Wayback Machine and Archive.today
```

### Social media posts

```
⚠️ Archive: https://twitter.com/user/status/123
   → High deletion risk - archive immediately
```

### Government pages

```
⚠️ Archive: https://agency.gov/data/report.pdf
   → Government sites change with administrations
```

### Corporate statements

```
⚠️ Archive: https://company.com/press-release
   → Companies often remove old statements
```

## Archive services

Suggest multiple archives for redundancy:

| Service | URL | Best for |
|---------|-----|----------|
| Wayback Machine | web.archive.org | General web pages |
| Archive.today | archive.today | Dynamic content, JS sites |
| Perma.cc | perma.cc | Legal/academic (requires account) |
| Ghost Archive | ghostarchive.org | Social media |

## Output format

```
⚠️ Archive reminder:

URLs in this content should be archived:

- [URL 1]: [archive status if known]
- [URL 2]: Not yet archived

Quick archive links:
- Wayback: https://web.archive.org/save/[URL]
- Archive.today: https://archive.today/?run=1&url=[URL]

Archived versions protect against link rot and content changes.
```

## Archive citation format

When archived, cite both:

```markdown
Original: https://example.com/article
Archived: https://web.archive.org/web/20260129/https://example.com/article
```

Or inline:

```markdown
According to [the report](https://example.com/report) ([archived](https://archive.today/AbCdE))...
```

## Priority levels

| Source type | Archive priority |
|-------------|------------------|
| Social media | **Immediate** - high deletion risk |
| Government | **High** - changes with administrations |
| News sites | **Medium** - paywalls may block later |
| Academic | **Low** - usually stable (DOIs preferred) |
| Wikipedia | **Skip** - use permalink instead |

## Integration with web-archiving skill

This hook pairs with the web-archiving skill, which provides detailed archiving workflows. The hook reminds; the skill provides methods.

## Non-blocking

This hook suggests archiving but doesn't require it. Breaking news may not allow time for archiving—that's okay, archive when possible.

## Skip conditions

Skip archive reminders for:

- Internal links (same domain)
- Known permanent identifiers (DOIs, ISBNs)
- Wikipedia (use permanent links instead)
- Already-archived URLs (archive.org, archive.today domains)
- Code repositories (GitHub, GitLab - generally stable)
