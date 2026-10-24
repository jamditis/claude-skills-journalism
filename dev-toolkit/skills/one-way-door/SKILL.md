---
name: one-way-door
description: Flags irreversible decisions before commit. Use for data models, infra, auth boundaries, API contracts, event schemas, CI/CD.
---

# One-way door check

Some decisions are easy to reverse, you can change a UI component, rename a variable, or swap a utility function with no lasting consequences. These are **two-way doors**: walk through, and if it's wrong, walk back.

Other decisions create gravity. Once traffic, users, or other code depends on them, changing course gets expensive. A database schema migration after launch. An API contract that external consumers rely on. An auth boundary that shapes your entire permission model. These are **one-way doors**.

The most expensive mistakes in software aren't bugs. They're irreversible architectural decisions made too quickly.

## What gets flagged

### Data models and database schemas

Files matching: `schema.prisma`, `schema.graphql`, `*.sql`, `migration*`, `models.py`, `models.ts`, `entities.py`, `entities.ts`

Data models are the hardest decisions to reverse. Once your database has rows, every schema change requires a migration. Column renames break queries. Relationship changes cascade through your entire application.

**Questions to ask:**
- Have you mapped all the relationships between entities?
- Will this schema support the queries you need without N+1 problems?
- Are you normalizing appropriately for your read/write patterns?

### Infrastructure and deployment configs

Files matching: `docker-compose*`, `Dockerfile`, `*.tf`, `terraform*`, `pulumi*`, `cdk*`, `cloudformation*`, `k8s*`, `kubernetes*`, `helm*`

Infrastructure choices constrain everything built on top of them. Switching from ECS to Kubernetes, or from Lambda to containers, affects deployment pipelines, monitoring, scaling, and team knowledge.

**Questions to ask:**
- Is this the simplest infrastructure that meets your needs?
- What's your team's operational experience with this stack?
- What does failure recovery look like?

### Authentication and authorization

Files matching: `auth.{ts,js,py}`, `firestore.rules`, `storage.rules`, `*.rules`, `security.{ts,js,py,json,rules,yaml,yml}`, `rbac.{ts,js,py,json}`, `permissions.{ts,js,py,json}`

These patterns are extension-qualified on purpose: an unrelated file that merely contains the word `security` or `permissions` (a note, a doc, a test) does not trip the check.

Auth boundaries are load-bearing walls. Session vs JWT, role-based vs attribute-based, single-tenant vs multi-tenant, each choice shapes your security model, user experience, and compliance posture.

**Questions to ask:**
- Does this cover all your user types and access patterns?
- How will you handle token refresh, session expiry, and revocation?
- Are you building for single-tenant or multi-tenant from the start?

### API contracts and service interfaces

Files matching: `openapi*`, `swagger*`, `*.proto`, `*.graphql`, `api-schema*`, `routes.ts`, `routes.js`, `routes.py`

Published APIs are promises to consumers. Breaking changes require versioning, deprecation periods, and migration guides. Internal APIs between services create coupling that's hard to unwind.

**Questions to ask:**
- Who will consume this API? Internal services, external developers, or both?
- How will you version breaking changes?
- Are you exposing implementation details that should stay private?

### Event systems and message buses

Files matching: `events.ts`, `eventbus.ts`, `eventemitter.py`, `eventhandler.py`, `pubsub*`, `queue*`, `kafka*`, `rabbit*`

Event schemas are contracts between producers and consumers. Once multiple services subscribe to an event, changing its shape requires coordinated deploys. Event ordering assumptions become architectural constraints.

**Questions to ask:**
- Have you defined the event schema, including required vs optional fields?
- What happens when a consumer fails to process an event?
- Do you need ordering guarantees?

### CI/CD pipelines

Files in: `.github/`, `.gitlab/`, `.circleci/`, or matching `Jenkinsfile`, `.travis.yml`, `cloudbuild*`

CI/CD pipelines become the backbone of your release process. Teams build muscle memory around deploy workflows. Changing pipeline structure means retraining, and broken deploys during the transition can block your entire team.

**Questions to ask:**
- Does this pipeline support your branching strategy?
- What's the rollback procedure if a deploy fails?
- Are secrets handled securely?

### Dependency and package configs

Files matching: `package.json`, `Cargo.toml`, `go.mod`, `requirements.txt`, `pyproject.toml`, `Gemfile`

Framework and dependency choices ripple through your entire codebase. Switching from React to Vue, or from Express to Fastify, means rewriting large portions of your application.

**Questions to ask:**
- Is this dependency actively maintained?
- Does it handle your scale requirements?
- What's the migration path if you need to switch?

### Cloud service configs

Files matching: `firebase.json`, `.firebaserc`, `firestore.indexes*`

Cloud service configs lock you into specific providers and architectures. Firestore indexes determine query performance. Firebase rules define your security boundary.

**Questions to ask:**
- Are you comfortable with this provider for the long term?
- Have you tested these indexes against your actual query patterns?
- What's the exit strategy if you need to migrate?

## Two-way doors (what passes through)

These file types are safe to decide quickly and change later:

- **UI components**, React/Vue/Svelte components, CSS, templates
- **Utility functions**, Helpers, formatters, validators
- **Test files**, Test infrastructure can be refactored freely
- **Documentation**, README, guides, comments
- **Logging and monitoring**, Log formats, metric names
- **Configuration files**, `.env`, feature flags, app config
- **Static assets**, Images, fonts, icons

### Enforced safelist

The optional Claude Code hook has an early-exit safelist before any pattern
check. Tests, fixtures, mocks, Markdown, and documentation or plan text files
pass even when a filename contains a word such as `auth` or `security`.

The shared skill does not depend on this hook. Apply the same safelist when you
review a proposed file manually.

## How to implement

### Shared project instruction

Add this rule to the project's canonical instruction file. Use `AGENTS.md` for
Codex or `CLAUDE.md` for Claude Code. If one imports the other, edit the
canonical file.

```markdown
### One-way door check

Before creating a file that represents an architectural decision, ask which
parts would be difficult to reverse. One-way doors include data models, service
communication patterns, authentication boundaries, tenancy models, and
infrastructure configuration. If a decision is a one-way door, ask the user and
wait for an explicit answer. Use the client's structured question tool when it
has one. Explain the trade-offs and at least two alternatives before asking
whether to proceed. Two-way doors, such as UI components, utilities, and
styling, can be changed quickly.
```

This manual workflow is the portable behavior. It works without automatic
hooks:

1. Identify the one-way-door file before writing it.
2. Explain what becomes difficult to reverse.
3. Present at least two alternatives with trade-offs.
4. Ask the user and wait for an explicit answer. Use the client's structured
   question tool when it has one.
5. Write only after the user approves the specific decision.

### Optional Claude Code enforcement

Claude Code users may install the repository's `one-way-door-check` hook for
automatic pre-write blocking. The hook and its approval promoter are optional
Claude Code enforcement, not shared Agent Skills behavior. The adapter keeps a
session-scoped pending and approved ledger so an approved file can be retried
without a loop.

PowerShell ports, `one-way-door-check.ps1` and
`one-way-door-approve.ps1`, are included in this skill directory. The
[hook documentation](https://github.com/jamditis/claude-skills-journalism/blob/master/hooks/one-way-door-check.md)
contains the POSIX implementation, the ledger rules, and the Claude Code wiring. Clients without this adapter must use the manual workflow
above. Do not treat the absence of automatic enforcement as approval.

## The three questions

Before committing to any one-way door, ask:

1. **What am I committing to?**, What does this decision constrain? What becomes harder to change?
2. **What are the alternatives?**, Is there a simpler approach? A more reversible one?
3. **What's the migration path?**, If this turns out to be wrong, how do we change course?

If you can't answer these questions clearly, you're not ready to walk through the door.
