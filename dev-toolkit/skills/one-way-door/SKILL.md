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

### Enforced safelist (the hook)

The CLAUDE.md rule leans on judgement, but the automated hook hard-codes an early-exit safelist that runs before any pattern check. These classes always pass, even when the filename contains a keyword like `auth` or `security`, because they're the common false positives:

- Test files by naming convention, `test_*.py`, `*_test.py`, `*.test.{ts,tsx,js,jsx}`, `*.spec.{ts,tsx,js,jsx}`
- Anything under a `tests/`, `__tests__/`, `fixtures/`, `mocks/`, or `__mocks__/` directory
- All Markdown (`*.md`)
- `*.txt` / `*.rst` under a `plans/`, `docs/`, `notes/`, or `superpowers` directory

## How to implement

### Option 1: CLAUDE.md rule

Add this to your project's `CLAUDE.md`:

```markdown
### One-way door check
Before creating new files that represent architectural decisions, ask: "Which of these decisions would be difficult to reverse?" One-way doors include data models, service communication patterns, auth boundaries, tenancy models, and infrastructure configs. These create gravity, once traffic, users, or other code depends on them, changing course gets expensive. If a decision is a one-way door, pause and discuss the trade-offs before committing. Two-way doors (UI components, utilities, styling) can be decided quickly and changed later.
```

### Option 2: PreToolUse hook (automated enforcement)

The automated version is two hooks that share a session-scoped approval ledger:

- **`one-way-door-check.sh`** runs on `PreToolUse:Write`. It blocks the first write to a one-way-door file and records that file as pending.
- **`one-way-door-approve.sh`** runs on `PostToolUse:AskUserQuestion`. When you answer any `AskUserQuestion`, normally the one the check told Claude to ask, it promotes every pending file to approved, so Claude's retried write passes.

Without the ledger the check would be stateless and re-block the same file on every retry, the "use `AskUserQuestion`, then retry" instruction would loop forever. The ledger makes the loop terminate: answer once, and every file currently pending, usually just the one the check told Claude to ask about, stays open for the rest of the session. A one-way-door file you have not tried to write yet is not pending, so it still blocks the first time Claude attempts it.

The promoter keys on the `AskUserQuestion` event itself, not on which question was answered: it approves the whole pending set at once, so if two one-way-door files are blocked before Claude asks, or it asks an unrelated question while a file is pending, they are all approved together. The block-then-discuss prompt is the real guardrail; the ledger only keeps an already-discussed file from re-blocking.

Add both hooks to your Claude Code `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/one-way-door-check.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "AskUserQuestion",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/one-way-door-approve.sh"
          }
        ]
      }
    ]
  }
}
```

### The check hook (`one-way-door-check.sh`)

```bash
#!/bin/sh
# One-way door check hook (PreToolUse:Write)
# Flags architectural decisions that are hard to reverse.
# The most expensive mistakes aren't bugs, they're irreversible decisions.

INPUT=$(cat)
[ -z "$INPUT" ] && exit 0

# Extract the file path from tool_input
FILE_PATH=$(echo "$INPUT" | grep -oP '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*"file_path"\s*:\s*"//;s/"//')
[ -z "$FILE_PATH" ] && exit 0

# Session-scoped approval ledger. Once the user approves a one-way-door file
# via the required AskUserQuestion, the PostToolUse:AskUserQuestion hook
# promotes it to approved, and subsequent writes to that same file proceed.
SESSION_ID=$(echo "$INPUT" | grep -oP '"session_id"\s*:\s*"[^"]*"' | head -1 | sed 's/.*"session_id"\s*:\s*"//;s/"//')
[ -z "$SESSION_ID" ] && SESSION_ID="default"

STATE_DIR="$HOME/.claude/hooks/state/one-way-door"
mkdir -p "$STATE_DIR"
APPROVED_FILE="$STATE_DIR/$SESSION_ID.approved"
PENDING_FILE="$STATE_DIR/$SESSION_ID.pending"

# Already approved this session: allow without re-blocking.
if [ -f "$APPROVED_FILE" ] && grep -Fxq "$FILE_PATH" "$APPROVED_FILE"; then
    echo "one-way-door: proceeding with previously-approved $(basename "$FILE_PATH")" >&2
    exit 0
fi

FILENAME=$(basename "$FILE_PATH")
FILENAME_LOWER=$(echo "$FILENAME" | tr "[:upper:]" "[:lower:]")
FILE_PATH_LOWER=$(echo "$FILE_PATH" | tr "[:upper:]" "[:lower:]")
DIR=$(dirname "$FILE_PATH")

# ---------------------------------------------------------------------------
# Early-exit safelist: clearly-additive, reversible file classes that should
# never trip a one-way-door check even if the filename contains a keyword like
# "auth" or "security". Tests and docs are the common false-positives.
# ---------------------------------------------------------------------------

# Test files (pytest, jest, vitest, go test conventions)
if echo "$FILENAME_LOWER" | grep -qE "^test_.*\.py$|_test\.py$|\.test\.(ts|tsx|js|jsx)$|\.spec\.(ts|tsx|js|jsx)$"; then
    exit 0
fi

# Test / fixture / mock directories anywhere in the path
if echo "$FILE_PATH_LOWER" | grep -qE "/tests?/|/__tests__/|/fixtures?/|/mocks?/|/__mocks__/"; then
    exit 0
fi

# Markdown is always reversible (broader than the later docs-only check, which
# required a docs/ parent dir and missed ad-hoc notes).
if echo "$FILENAME_LOWER" | grep -qE "\.md$"; then
    exit 0
fi

ONE_WAY=0
REASON=""

# Documentation and plan files are always reversible - skip all checks
if echo "$FILENAME_LOWER" | grep -qE "\.txt$|\.rst$"; then
    if echo "$DIR" | grep -qE "plans?|docs?|notes?|superpowers"; then
        exit 0
    fi
fi

# Database schemas and migrations
if echo "$FILENAME_LOWER" | grep -qE "schema\.(prisma|graphql|sql)|migration|\.sql$|models?\.(py|ts|js)$|entities?\.(py|ts|js)$"; then
    ONE_WAY=1
    REASON="data model / database schema"
fi

# Infrastructure and deployment configs
if echo "$FILENAME_LOWER" | grep -qE "^(docker-compose|dockerfile|terraform|pulumi|cdk)|\.tf$|cloudformation|k8s|kubernetes|helm"; then
    ONE_WAY=1
    REASON="infrastructure / deployment config"
fi

# Authentication and authorization (code/config files only - not docs)
if echo "$FILENAME_LOWER" | grep -qE "auth\.(ts|js|py)|firestore\.rules|storage\.rules|security\.(ts|js|py|json|rules|yaml|yml)|\.rules$|rbac\.(ts|js|py|json)|permissions\.(ts|js|py|json)"; then
    ONE_WAY=1
    REASON="auth / security rules"
fi

# API contracts and service interfaces
if echo "$FILENAME_LOWER" | grep -qE "openapi|swagger|\.proto$|\.graphql$|api-schema|routes\.(ts|js|py)$"; then
    ONE_WAY=1
    REASON="API contract / service interface"
fi

# Event systems and message queues
if echo "$FILENAME_LOWER" | grep -qE "event(s|bus|emitter|handler)\.(ts|js|py)$|pubsub|queue|kafka|rabbit"; then
    ONE_WAY=1
    REASON="event system / message bus"
fi

# Package manager configs (dependency choices)
if echo "$FILENAME_LOWER" | grep -qE "^(package\.json|cargo\.toml|go\.mod|requirements\.txt|pyproject\.toml|gemfile)$"; then
    ONE_WAY=1
    REASON="dependency / package config"
fi

# Firebase and cloud service configs
if echo "$FILENAME_LOWER" | grep -qE "^firebase\.json$|^\.firebaserc$|firestore\.indexes"; then
    ONE_WAY=1
    REASON="cloud service config (Firebase)"
fi

# CI/CD pipelines
if echo "$DIR" | grep -qE "\.(github|gitlab|circleci)" || echo "$FILENAME_LOWER" | grep -qE "^(jenkinsfile|\.travis\.yml|cloudbuild)"; then
    ONE_WAY=1
    REASON="CI/CD pipeline"
fi

if [ "$ONE_WAY" = "1" ]; then
    # Record this file as pending approval for the session (deduped).
    if [ ! -f "$PENDING_FILE" ] || ! grep -Fxq "$FILE_PATH" "$PENDING_FILE"; then
        printf '%s\n' "$FILE_PATH" >> "$PENDING_FILE"
    fi
    cat >&2 <<HOOK_MSG
ONE_WAY_DOOR: You tried to create $FILENAME ($REASON). This write has been blocked because it is a one-way door -- a decision that becomes hard to reverse once other code, data, or users depend on it.

REQUIRED ACTION: You MUST use the AskUserQuestion tool before retrying this write. Present the user with:
1. What this file does and why it is a one-way door
2. At least 2 alternative approaches (if any exist) with their trade-offs
3. An option to proceed as planned

Frame the question around the specific architectural decision, not just "should I create this file?" The user needs to understand what they are committing to.

After the user answers the AskUserQuestion, retry the same write -- it will proceed automatically, because answering the question promotes this file to approved for the rest of the session. (Other unapproved one-way-door files still block.)
HOOK_MSG
    exit 2
fi

exit 0
```

### The approval hook (`one-way-door-approve.sh`)

```bash
#!/bin/sh
# One-way door approval promoter (PostToolUse:AskUserQuestion)
# When the user answers any AskUserQuestion, promote every one-way-door file
# that the PreToolUse:Write hook recorded as pending into the approved ledger
# for this session. The retried Write then passes instead of re-blocking.
# Never blocks: PostToolUse hooks must not interrupt the flow.

INPUT=$(cat)
[ -z "$INPUT" ] && exit 0

SESSION_ID=$(echo "$INPUT" | grep -oP '"session_id"\s*:\s*"[^"]*"' | head -1 | sed 's/.*"session_id"\s*:\s*"//;s/"//')
[ -z "$SESSION_ID" ] && SESSION_ID="default"

STATE_DIR="$HOME/.claude/hooks/state/one-way-door"
mkdir -p "$STATE_DIR"
APPROVED_FILE="$STATE_DIR/$SESSION_ID.approved"
PENDING_FILE="$STATE_DIR/$SESSION_ID.pending"

# Nothing pending: nothing to promote.
[ -s "$PENDING_FILE" ] || exit 0

# Promote each pending path into approved, deduped.
while IFS= read -r path; do
    [ -z "$path" ] && continue
    if [ ! -f "$APPROVED_FILE" ] || ! grep -Fxq "$path" "$APPROVED_FILE"; then
        printf '%s\n' "$path" >> "$APPROVED_FILE"
    fi
done < "$PENDING_FILE"

# Empty the pending list now that everything is approved.
: > "$PENDING_FILE"

exit 0
```

**How it works:**

1. `one-way-door-check.sh` intercepts every `Write` (new file creation) and reads the `file_path` and `session_id` from the tool input.
2. If that path is already in the session's `.approved` ledger, the write proceeds, the decision was already discussed this session. (The hook logs a one-line `one-way-door: proceeding with previously-approved <file>` note to stderr; it is not silent.)
3. Otherwise the hook checks the filename against the one-way-door patterns. On a match it records the path in the session's `.pending` list, exits with code 2 (block), and tells Claude to use `AskUserQuestion` and then retry.
4. When the user answers any `AskUserQuestion`, `one-way-door-approve.sh` (PostToolUse:AskUserQuestion) promotes every pending path into `.approved` and clears the pending list. It never blocks, PostToolUse hooks must not interrupt the flow.
5. Claude retries the same write. The path is now approved, so it proceeds. Two-way door files pass through silently the whole time (exit 0, no output).

**State:**

The ledger lives in `~/.claude/hooks/state/one-way-door/`, one pair of files per session: `<session_id>.pending` and `<session_id>.approved`. Approval is per file path, per session, a new session starts with an empty ledger, so the same decision is surfaced again rather than silently inherited from a past session. The key is the file path as Claude Code delivers it, which is normally absolute. If one session writes identically-named files through relative paths in different directories, the path key can collide and approve the second without its own discussion; wiring on absolute paths avoids that.

**Exit codes:**
- `0`, Allow (two-way door, or a path already approved this session)
- `2`, Block (one-way door not yet approved, requires discussion)

### Windows (PowerShell)

The shell scripts above assume a POSIX shell. On Windows, Claude Code invokes hooks through PowerShell, and `tool_input.file_path` can arrive with backslashes, which `basename` does not split on, so the shell version's safelist would misfire. Behavior-matched PowerShell ports ship alongside this skill:

- `one-way-door-check.ps1`, the `PreToolUse:Write` check
- `one-way-door-approve.ps1`, the `PostToolUse:AskUserQuestion` promoter

They use the same session ledger (`%USERPROFILE%\.claude\hooks\state\one-way-door\`), the same early-exit safelist, and the same one-way-door categories as the shell version. Filename and directory splitting goes through `[System.IO.Path]`, and the directory patterns are matched after normalizing `\` to `/`, so the check is correct whether a path uses backslashes or forward slashes. They mirror the shell hooks check-for-check, the same patterns in the same order, so the behavioral contract is identical; only the language differs.

Copy both `.ps1` files from this skill's directory into your hooks folder (for example `%USERPROFILE%\.claude\hooks\`), then wire them with the PowerShell launcher. Update the `command` paths to match where you saved them (replace `<you>` with your username):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File C:/Users/<you>/.claude/hooks/one-way-door-check.ps1"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "AskUserQuestion",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File C:/Users/<you>/.claude/hooks/one-way-door-approve.ps1"
          }
        ]
      }
    ]
  }
}
```

## The three questions

Before committing to any one-way door, ask:

1. **What am I committing to?**, What does this decision constrain? What becomes harder to change?
2. **What are the alternatives?**, Is there a simpler approach? A more reversible one?
3. **What's the migration path?**, If this turns out to be wrong, how do we change course?

If you can't answer these questions clearly, you're not ready to walk through the door.
