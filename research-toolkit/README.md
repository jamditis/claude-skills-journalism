# research-toolkit

Five skills for research, source preservation, and academic workflows. Built for journalists, researchers, librarians, and academics who need to find, preserve, and analyze evidence across the web.

## What's in this plugin

| Skill | Purpose |
|---|---|
| **academic-writing** | Research methodology, scholarly communication, literature reviews, grant proposals, citation management, and peer-review preparation |
| **content-access** | Legal access to paywalled and geo-blocked content via Unpaywall, library databases, open-access alternatives, and ethical access strategies |
| **digital-archive** | AI-enriched digital archive construction with entity extraction, knowledge graphs, and multi-source ingestion (patterns from the Jay Rosen Digital Archive project) |
| **page-monitoring** | Web page change detection, availability tracking, and content-update alerts via Visualping, ChangeTower, Distill.io, and self-hosted monitoring |
| **web-archiving** | Page archiving and retrieval from Wayback Machine, Archive.today, ArchiveBox, and evidence preservation tools — including legal-evidence chain-of-custody patterns |

## Installation

Install via the `claude-skills-journalism` Marketplace:

```
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install research-toolkit@claude-skills-journalism
```

Or install individual skills directly into `~/.claude/skills/` if you prefer not to use the plugin system — see the project README.

## Cross-references to skills outside this bundle

A few skills here interact with siblings in the `journalism-core` bundle. References are advisory ("see also") — the skills work standalone if `journalism-core` is not installed:

- **web-archiving** is referenced from `journalism-core/source-verification` (full archiving workflows) and `journalism-core/interview-prep` (recovering deleted social-media content)
- **content-access** complements `journalism-core/foia-requests` for primary-source acquisition

## Maintenance

Skills are maintained for currency on a rolling basis. Notable currency notes:

- **content-access** — paywall services and academic-access tools change frequently; verify URLs and pricing before relying on a referenced source
- **page-monitoring** — third-party monitoring services have shifted free-tier limits in 2024-2026
- **web-archiving** — archive.today underwent operational changes in late 2025 (FBI subpoena to registrar, Wikipedia citation policy shift); see notes in the skill itself
