---
name: one-way-door-check
event: PreToolUse
tools:
  - Write
description: Blocks creation of files that represent irreversible architectural decisions until the user confirms. Requires the companion PostToolUse:AskUserQuestion hook (one-way-door-approve), which promotes the session's pending files to approved so the retry passes, install both, not just this check.
---

# One-way door check

This hook intercepts `Write` tool calls and checks whether the target file represents a one-way door, an architectural decision that becomes hard to reverse once other code, data, or users depend on it.

It ships as two scripts that share a session-scoped approval ledger:

- **`one-way-door-check.sh`** (`PreToolUse:Write`) blocks the first write to a one-way-door file and records it as pending.
- **`one-way-door-approve.sh`** (`PostToolUse:AskUserQuestion`) promotes the pending files to approved once the user answers any `AskUserQuestion`, normally the one the check told Claude to ask.

Behavior-matched PowerShell ports for Windows (`one-way-door-check.ps1`, `one-way-door-approve.ps1`) ship in the [`one-way-door` skill directory](../dev-toolkit/skills/one-way-door/); see [Windows (PowerShell)](#windows-powershell) below.

The ledger is what makes the hook stateful. A stateless check would re-block the same file on the retry, so the "ask, then retry" instruction would loop forever. With the ledger, answering the question promotes every file currently pending, usually just the one the check told Claude to ask about, and keeps it open for the rest of the session. A one-way-door file you have not tried to write yet is not pending, so it still blocks the first time Claude attempts it.

The promoter keys on the `AskUserQuestion` event, not on which question was answered: it approves the whole pending set at once, so if two one-way-door files are blocked before Claude asks, or it asks an unrelated question while a file is pending, they are all approved together. The block-then-discuss prompt is the guardrail; the ledger only stops an already-discussed file from re-blocking.

## When this hook fires

- **Event:** PreToolUse (the check, before Claude writes a file) and PostToolUse:AskUserQuestion (the approval promoter)
- **Tools:** Write only for the check (not Edit, editing an existing file is a two-way door); AskUserQuestion for the approval promoter

## Detection logic

Before any pattern check, the hook early-exits an explicit safelist of always-reversible file classes (test files, test/fixture/mock directories, Markdown, and docs/plans text files) so they never trip even when the name contains a keyword like `auth`. It then checks the filename against patterns for known one-way door categories:

### Patterns that trigger blocking

| Category | File patterns |
|----------|--------------|
| Data models | `schema.prisma`, `schema.graphql`, `*.sql`, `migration*`, `models.py`, `models.ts`, `entities.py`, `entities.ts` |
| Infrastructure | `docker-compose*`, `Dockerfile`, `*.tf`, `terraform*`, `pulumi*`, `cdk*`, `cloudformation*`, `k8s*`, `helm*` |
| Auth / security | `auth.{ts,js,py}`, `firestore.rules`, `storage.rules`, `*.rules`, `security.{ts,js,py,json,rules,yaml,yml}`, `rbac.{ts,js,py,json}`, `permissions.{ts,js,py,json}` |
| API contracts | `openapi*`, `swagger*`, `*.proto`, `*.graphql`, `api-schema*`, `routes.ts`, `routes.py` |
| Event systems | `events.ts`, `eventbus.py`, `eventemitter.ts`, `pubsub*`, `queue*`, `kafka*`, `rabbit*` |
| Dependencies | `package.json`, `Cargo.toml`, `go.mod`, `requirements.txt`, `pyproject.toml`, `Gemfile` |
| Cloud configs | `firebase.json`, `.firebaserc`, `firestore.indexes*` |
| CI/CD | Files in `.github/`, `.gitlab/`, `.circleci/`, `Jenkinsfile`, `.travis.yml`, `cloudbuild*` |

### Patterns that pass through (two-way doors)

- UI components (`.tsx`, `.vue`, `.svelte` in component directories)
- Utility functions and helpers
- Test files
- Documentation (`.md`, `.txt`)
- Static assets
- Configuration that doesn't lock you into architecture (`.env`, feature flags)

Some of these are enforced by the early-exit safelist rather than left to the absence of a match. The hook hard-codes pass-through for:

- Test files by convention, `test_*.py`, `*_test.py`, `*.test.{ts,tsx,js,jsx}`, `*.spec.{ts,tsx,js,jsx}`
- Anything under a `tests/`, `__tests__/`, `fixtures/`, `mocks/`, or `__mocks__/` directory
- All Markdown (`*.md`)
- `*.txt` / `*.rst` under a `plans/`, `docs/`, `notes/`, or `superpowers` directory

## Hook behavior

### When the check blocks (exit code 2)

The check hook records the file path as pending for the session, then outputs a message to stderr instructing Claude to:

1. Explain what the file does and why it's a one-way door
2. Present at least 2 alternative approaches with trade-offs
3. Offer an option to proceed as planned
4. Use `AskUserQuestion` to get the user's decision

### When the check allows (exit code 0)

The check allows the write in two cases:

- The file is a two-way door (no pattern match), exits silently, no output.
- The file path is already in the session's approved ledger, the decision was discussed earlier this session, so the write proceeds. This case is not silent: the hook logs `one-way-door: proceeding with previously-approved <file>` to stderr first.

### When the approval promoter runs

After the user answers any `AskUserQuestion`, the PostToolUse:AskUserQuestion hook promotes every pending path into the approved ledger and clears the pending list. It never blocks (exit 0 always), PostToolUse hooks must not interrupt the flow. Claude's retried write then proceeds because the path is now approved.

### State

The ledger lives in `~/.claude/hooks/state/one-way-door/`, one pair of files per session: `<session_id>.pending` and `<session_id>.approved`. Approval is per file path, per session, a new session starts with an empty ledger, so the same decision is surfaced again rather than inherited from a past session. The key is the file path as Claude Code delivers it, which is normally absolute. If a single session writes identically-named files through relative paths in different directories, the path key can collide and approve the second without its own discussion; wiring on absolute paths avoids that.

## Hook scripts

### Check hook (`one-way-door-check.sh`)

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

### Approval hook (`one-way-door-approve.sh`)

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

## Configuration

Add both hooks to your Claude Code `settings.json` (user or project level):

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

Save both scripts, make them executable (`chmod +x one-way-door-check.sh one-way-door-approve.sh`), and update the paths in the config. The approval hook is required: without it, the check would re-block an approved file on every retry.

### Windows (PowerShell)

The shell scripts assume a POSIX shell. On Windows, Claude Code invokes hooks through PowerShell, and `tool_input.file_path` can arrive with backslashes, which `basename` does not split on, so the shell version's safelist would misfire. Behavior-matched PowerShell ports ship in the [`one-way-door` skill directory](../dev-toolkit/skills/one-way-door/):

- `one-way-door-check.ps1`, the `PreToolUse:Write` check
- `one-way-door-approve.ps1`, the `PostToolUse:AskUserQuestion` promoter

They use the same session ledger (`%USERPROFILE%\.claude\hooks\state\one-way-door\`), the same early-exit safelist, and the same categories as the shell version. Filename and directory splitting goes through `[System.IO.Path]`, and the directory patterns are matched after normalizing `\` to `/`, so the check is correct for backslash and forward-slash paths alike.

Copy both `.ps1` files from the skill directory into your hooks folder (for example `%USERPROFILE%\.claude\hooks\`), then wire them with the PowerShell launcher. Update the `command` paths to match where you saved them (replace `<you>` with your username):

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

## Examples

### Example 1: Blocked, new database schema

Claude attempts: `Write schema.prisma`

Hook blocks with:
```
ONE_WAY_DOOR: You tried to create schema.prisma (data model / database schema).
```

Claude must ask the user about the data model design before proceeding.

### Example 2: Allowed, new React component

Claude attempts: `Write src/components/UserCard.tsx`

Hook allows (exit 0), UI components are two-way doors.

### Example 3: Blocked, new CI/CD pipeline

Claude attempts: `Write .github/workflows/deploy.yml`

Hook blocks with:
```
ONE_WAY_DOOR: You tried to create deploy.yml (CI/CD pipeline).
```

Claude must discuss the deployment strategy before proceeding.

### Example 4: Approved, retry after the discussion

Continuing from Example 3: Claude uses `AskUserQuestion` to walk through the deployment trade-offs, and the user picks an option. The approval hook promotes `deploy.yml` to approved for the session.

Claude retries: `Write .github/workflows/deploy.yml`

Hook allows (exit 0), the file is already approved this session:
```
one-way-door: proceeding with previously-approved deploy.yml
```

A different one-way-door file (say `schema.prisma`) still blocks until it gets its own discussion.
