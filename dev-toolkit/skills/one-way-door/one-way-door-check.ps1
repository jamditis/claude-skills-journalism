# One-way door check hook (PreToolUse:Write) - PowerShell port for legion2025 (Windows).
# Behavior-matched to ~/.claude/hooks/one-way-door-check.sh on officejawn/houseofjawn.
# Flags architectural decisions that are hard to reverse.
# The most expensive mistakes aren't bugs - they're irreversible decisions.
param()

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrEmpty($raw)) { exit 0 }

# Fail open: a malformed payload must never brick the user's ability to write.
try { $data = $raw | ConvertFrom-Json } catch { exit 0 }

$FILE_PATH = $data.tool_input.file_path
if ([string]::IsNullOrEmpty($FILE_PATH)) { exit 0 }

# Canonical ledger key: normalize separators so approval is keyed on one form.
# Without this, a block recorded as C:\a\b.sql and a retry arriving as C:/a/b.sql
# would miss in the ledger and re-block the same file. Comparisons are also
# case-insensitive (PowerShell -contains), matching Windows path semantics.
$FILE_KEY = $FILE_PATH -replace '\\','/'

# Session-scoped approval ledger. Once the user approves a one-way-door file
# via the required AskUserQuestion, the PostToolUse:AskUserQuestion hook
# promotes it to approved, and subsequent writes to that same file proceed.
$SESSION_ID = $data.session_id
if ([string]::IsNullOrEmpty($SESSION_ID)) { $SESSION_ID = "default" }

$STATE_DIR = "$env:USERPROFILE\.claude\hooks\state\one-way-door"
if (-not (Test-Path $STATE_DIR)) { New-Item -ItemType Directory -Force -Path $STATE_DIR | Out-Null }
$APPROVED_FILE = Join-Path $STATE_DIR "$SESSION_ID.approved"
$PENDING_FILE  = Join-Path $STATE_DIR "$SESSION_ID.pending"

# Already approved this session: allow without re-blocking.
if (Test-Path $APPROVED_FILE) {
    $approved = @(Get-Content -LiteralPath $APPROVED_FILE -Encoding UTF8 -ErrorAction SilentlyContinue)
    if ($approved -contains $FILE_KEY) {
        [Console]::Error.WriteLine("one-way-door: proceeding with previously-approved $([System.IO.Path]::GetFileName($FILE_PATH))")
        exit 0
    }
}

$FILENAME = [System.IO.Path]::GetFileName($FILE_PATH)
$FILENAME_LOWER = $FILENAME.ToLower()
$DIR = [System.IO.Path]::GetDirectoryName($FILE_PATH)
if ($null -eq $DIR) { $DIR = "" }

# Normalize separators to forward slashes for path/dir regex checks, so the
# same patterns match whether Claude Code delivers C:\a\b or C:/a/b. .NET's
# GetFileName/GetDirectoryName already split on both separators on Windows.
$FILE_PATH_LOWER_FWD = ($FILE_PATH.ToLower()) -replace '\\','/'
$DIR_LOWER_FWD = ($DIR.ToLower()) -replace '\\','/'

# ---------------------------------------------------------------------------
# Early-exit safelist: clearly-additive, reversible file classes that should
# never trip a one-way-door check even if the filename contains a keyword like
# "auth" or "security". Tests and docs are the common false-positives.
# ---------------------------------------------------------------------------

# Test files (pytest, jest, vitest, go test conventions)
if ($FILENAME_LOWER -match '^test_.*\.py$|_test\.py$|\.test\.(ts|tsx|js|jsx)$|\.spec\.(ts|tsx|js|jsx)$') { exit 0 }

# Test / fixture / mock directories anywhere in the path
if ($FILE_PATH_LOWER_FWD -match '/tests?/|/__tests__/|/fixtures?/|/mocks?/|/__mocks__/') { exit 0 }

# Markdown is always reversible (broader than the later docs-only check, which
# required a docs/ parent dir and missed ad-hoc notes).
if ($FILENAME_LOWER -match '\.md$') { exit 0 }

$ONE_WAY = $false
$REASON = ""

# Documentation and plan files are always reversible - skip all checks
if ($FILENAME_LOWER -match '\.txt$|\.rst$') {
    if ($DIR_LOWER_FWD -match 'plans?|docs?|notes?|superpowers') { exit 0 }
}

# Database schemas and migrations
if ($FILENAME_LOWER -match 'schema\.(prisma|graphql|sql)|migration|\.sql$|models?\.(py|ts|js)$|entities?\.(py|ts|js)$') {
    $ONE_WAY = $true; $REASON = "data model / database schema"
}

# Infrastructure and deployment configs
if ($FILENAME_LOWER -match '^(docker-compose|dockerfile|terraform|pulumi|cdk)|\.tf$|cloudformation|k8s|kubernetes|helm') {
    $ONE_WAY = $true; $REASON = "infrastructure / deployment config"
}

# Authentication and authorization (code/config files only - not docs)
if ($FILENAME_LOWER -match 'auth\.(ts|js|py)|firestore\.rules|storage\.rules|security\.(ts|js|py|json|rules|yaml|yml)|\.rules$|rbac\.(ts|js|py|json)|permissions\.(ts|js|py|json)') {
    $ONE_WAY = $true; $REASON = "auth / security rules"
}

# API contracts and service interfaces
if ($FILENAME_LOWER -match 'openapi|swagger|\.proto$|\.graphql$|api-schema|routes\.(ts|js|py)$') {
    $ONE_WAY = $true; $REASON = "API contract / service interface"
}

# Event systems and message queues
if ($FILENAME_LOWER -match 'event(s|bus|emitter|handler)\.(ts|js|py)$|pubsub|queue|kafka|rabbit') {
    $ONE_WAY = $true; $REASON = "event system / message bus"
}

# Package manager configs (dependency choices)
if ($FILENAME_LOWER -match '^(package\.json|cargo\.toml|go\.mod|requirements\.txt|pyproject\.toml|gemfile)$') {
    $ONE_WAY = $true; $REASON = "dependency / package config"
}

# Firebase and cloud service configs
if ($FILENAME_LOWER -match '^firebase\.json$|^\.firebaserc$|firestore\.indexes') {
    $ONE_WAY = $true; $REASON = "cloud service config (Firebase)"
}

# CI/CD pipelines
if (($DIR_LOWER_FWD -match '\.(github|gitlab|circleci)') -or ($FILENAME_LOWER -match '^(jenkinsfile|\.travis\.yml|cloudbuild)')) {
    $ONE_WAY = $true; $REASON = "CI/CD pipeline"
}

if ($ONE_WAY) {
    # Record this file as pending approval for the session (deduped).
    $pending = if (Test-Path $PENDING_FILE) { @(Get-Content -LiteralPath $PENDING_FILE -Encoding UTF8 -ErrorAction SilentlyContinue) } else { @() }
    if ($pending -notcontains $FILE_KEY) { Add-Content -LiteralPath $PENDING_FILE -Value $FILE_KEY -Encoding UTF8 }

    $msg = @"
ONE_WAY_DOOR: You tried to create $FILENAME ($REASON). This write has been blocked because it is a one-way door -- a decision that becomes hard to reverse once other code, data, or users depend on it.

REQUIRED ACTION: You MUST use the AskUserQuestion tool before retrying this write. Present the user with:
1. What this file does and why it is a one-way door
2. At least 2 alternative approaches (if any exist) with their trade-offs
3. An option to proceed as planned

Frame the question around the specific architectural decision, not just "should I create this file?" The user needs to understand what they are committing to.

After the user answers the AskUserQuestion, retry the same write -- it will proceed automatically, because answering the question promotes this file to approved for the rest of the session. (Other unapproved one-way-door files still block.)
"@
    [Console]::Error.WriteLine($msg)
    exit 2
}

exit 0
