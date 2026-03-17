# Security policy

## Reporting a vulnerability

If you find a security issue in any skill, hook, or plugin in this collection, please report it responsibly.

**Email:** jamditis@gmail.com

**What to include:**
- Which skill, hook, or plugin is affected
- Description of the vulnerability
- Steps to reproduce
- Potential impact

**Response time:** I'll acknowledge reports within 48 hours and provide a fix timeline within a week.

## Scope

This collection contains instruction files (markdown) and some helper scripts. Security concerns most likely involve:

- **Scripts** in `scripts/` directories that execute shell commands
- **Hooks** that run automatically and could have unintended side effects
- **Plugin configurations** that could expose data or credentials
- **Templates** that generate code — injection risks in generated output

## Supported versions

Only the latest version on the `master` branch is supported. There are no backported security fixes to older versions.
