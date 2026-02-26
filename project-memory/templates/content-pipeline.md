# CLAUDE.md - [Project name]

> Template for: Content pipelines (publishing workflows, content automation)

## Project overview

[One sentence: What content this pipeline processes and where it publishes]

**Content types:** [Articles, newsletters, social posts, etc.]
**Sources:** [CMS, Google Docs, RSS, etc.]
**Destinations:** [Website, email, social platforms]
**Frequency:** [Daily, weekly, on-demand]

## Tech stack

**Language:** [Python, Node.js, etc.]
**Automation:** [GitHub Actions, cron, Zapier, etc.]
**Storage:** [Database, cloud storage, etc.]
**APIs:** [CMS, social platforms, email service]

## Commands

```bash
# Run full pipeline
[command to process and publish content]

# Preview without publishing
[command for dry run]

# Process single item
[command to process one piece of content]

# Check pipeline status
[command to view queue/status]
```

## Content flow

```
[Source] --> [Ingest] --> [Transform] --> [Enrich] --> [Publish]
                              │
                              └--> [Review Queue] (if needed)
```

## Content schema

**Input format:**
```yaml
title: ""
body: ""
author: ""
date: ""
tags: []
status: draft|review|approved
```

**Output transformations:**
- [HTML formatting]
- [Image optimization]
- [SEO metadata generation]

## File structure

```
project-root/
├── src/
│   ├── ingest/         # Content ingestion
│   ├── transform/      # Format conversion
│   ├── enrich/         # AI enhancement, metadata
│   ├── publish/        # Platform publishers
│   └── utils/          # Shared utilities
├── templates/          # Output templates
├── config/             # Platform configs
└── queue/              # Processing queue
```

## Platform integrations

**[Platform A]:**
- API credentials location
- Rate limits
- Publishing rules

**[Platform B]:**
- Authentication method
- Content requirements
- Scheduling capabilities

## AI enrichment

- [Summarization: model and prompts]
- [Tagging: automated categorization]
- [SEO: title/description generation]
- [Human review: when required]

## Quality gates

- [ ] Spell check / grammar
- [ ] Link validation
- [ ] Image alt text
- [ ] SEO requirements
- [ ] Editorial approval (if required)

## Error handling

- [Failed publish retry strategy]
- [Notification on failure]
- [Manual intervention process]

## Things to avoid

- Don't publish without preview
- Avoid duplicate posts to same platform
- Don't skip quality gates for "urgent" content

---

*Update when adding new content types or platforms.*
