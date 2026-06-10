# One-way door approval promoter (PostToolUse:AskUserQuestion) - PowerShell port for legion2025.
# Behavior-matched to ~/.claude/hooks/one-way-door-approve.sh on officejawn/houseofjawn.
# When the user answers any AskUserQuestion, promote every one-way-door file
# that the PreToolUse:Write hook recorded as pending into the approved ledger
# for this session. The retried Write then passes instead of re-blocking.
# Never blocks: PostToolUse hooks must not interrupt the flow.
param()

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrEmpty($raw)) { exit 0 }

try { $data = $raw | ConvertFrom-Json } catch { exit 0 }

$SESSION_ID = $data.session_id
if ([string]::IsNullOrEmpty($SESSION_ID)) { $SESSION_ID = "default" }

$STATE_DIR = "$env:USERPROFILE\.claude\hooks\state\one-way-door"
if (-not (Test-Path $STATE_DIR)) { New-Item -ItemType Directory -Force -Path $STATE_DIR | Out-Null }
$APPROVED_FILE = Join-Path $STATE_DIR "$SESSION_ID.approved"
$PENDING_FILE  = Join-Path $STATE_DIR "$SESSION_ID.pending"

# Nothing pending: nothing to promote.
if (-not (Test-Path $PENDING_FILE)) { exit 0 }
$pending = @(Get-Content -LiteralPath $PENDING_FILE -Encoding UTF8 -ErrorAction SilentlyContinue) | Where-Object { $_ -ne "" }
if (-not $pending) { exit 0 }

# Promote each pending path into approved, deduped.
$approved = if (Test-Path $APPROVED_FILE) { @(Get-Content -LiteralPath $APPROVED_FILE -Encoding UTF8 -ErrorAction SilentlyContinue) } else { @() }
foreach ($path in $pending) {
    if ($approved -notcontains $path) { $approved += $path }
}
Set-Content -LiteralPath $APPROVED_FILE -Value $approved -Encoding UTF8

# Empty the pending list now that everything is approved.
Clear-Content -LiteralPath $PENDING_FILE

exit 0
