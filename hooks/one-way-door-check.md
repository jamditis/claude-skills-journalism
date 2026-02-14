---
name: one-way-door-check
event: PreToolUse
tools:
  - Write
description: Blocks creation of files that represent irreversible architectural decisions until the user confirms
---

# One-way door check

This hook intercepts `Write` tool calls and checks whether the target file represents a one-way door — an architectural decision that becomes hard to reverse once other code, data, or users depend on it.

## When this hook fires

- **Event:** PreToolUse (before Claude writes a file)
- **Tools:** Write only (not Edit — editing an existing file is a two-way door)

## Detection logic

The hook extracts the file path from the tool input and checks the filename against patterns for known one-way door categories:

### Patterns that trigger blocking

| Category | File patterns |
|----------|--------------|
| Data models | `schema.prisma`, `schema.graphql`, `*.sql`, `migration*`, `models.py`, `models.ts`, `entities.py`, `entities.ts` |
| Infrastructure | `docker-compose*`, `Dockerfile`, `*.tf`, `terraform*`, `pulumi*`, `cdk*`, `cloudformation*`, `k8s*`, `helm*` |
| Auth / security | `auth.ts`, `auth.py`, `firestore.rules`, `storage.rules`, `*.rules`, `rbac*`, `permissions*` |
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

## Hook behavior

### When it blocks (exit code 2)

The hook outputs a message to stderr instructing Claude to:

1. Explain what the file does and why it's a one-way door
2. Present at least 2 alternative approaches with trade-offs
3. Offer an option to proceed as planned
4. Use `AskUserQuestion` to get the user's decision

### When it allows (exit code 0)

The hook exits silently when the file is a two-way door.

## Hook script

```bash
#!/bin/sh
# One-way door check hook (PreToolUse:Write)
# Flags architectural decisions that are hard to reverse.

INPUT=$(cat)
[ -z "$INPUT" ] && exit 0

FILE_PATH=$(echo "$INPUT" | grep -oP '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*"file_path"\s*:\s*"//;s/"//')
[ -z "$FILE_PATH" ] && exit 0

FILENAME=$(basename "$FILE_PATH")
FILENAME_LOWER=$(echo "$FILENAME" | tr "[:upper:]" "[:lower:]")
DIR=$(dirname "$FILE_PATH")

ONE_WAY=0
REASON=""

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

# Authentication and authorization
if echo "$FILENAME_LOWER" | grep -qE "auth\.(ts|js|py)|firestore\.rules|storage\.rules|security|\.rules$|rbac|permissions"; then
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

# Package manager configs
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
    cat >&2 <<HOOK_MSG
ONE_WAY_DOOR: You tried to create $FILENAME ($REASON). This write has been blocked because it is a one-way door -- a decision that becomes hard to reverse once other code, data, or users depend on it.

REQUIRED ACTION: You MUST use the AskUserQuestion tool before retrying this write. Present the user with:
1. What this file does and why it is a one-way door
2. At least 2 alternative approaches (if any exist) with their trade-offs
3. An option to proceed as planned

Frame the question around the specific architectural decision, not just "should I create this file?" The user needs to understand what they are committing to.

After the user responds, proceed according to their choice.
HOOK_MSG
    exit 2
fi

exit 0
```

## Configuration

Add to your Claude Code `settings.json` (user or project level):

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
    ]
  }
}
```

Save the script, make it executable (`chmod +x one-way-door-check.sh`), and update the path in the config.

## Examples

### Example 1: Blocked — new database schema

Claude attempts: `Write schema.prisma`

Hook blocks with:
```
ONE_WAY_DOOR: You tried to create schema.prisma (data model / database schema).
```

Claude must ask the user about the data model design before proceeding.

### Example 2: Allowed — new React component

Claude attempts: `Write src/components/UserCard.tsx`

Hook allows (exit 0) — UI components are two-way doors.

### Example 3: Blocked — new CI/CD pipeline

Claude attempts: `Write .github/workflows/deploy.yml`

Hook blocks with:
```
ONE_WAY_DOOR: You tried to create deploy.yml (CI/CD pipeline).
```

Claude must discuss the deployment strategy before proceeding.
