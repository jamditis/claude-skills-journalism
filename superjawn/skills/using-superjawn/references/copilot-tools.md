# Copilot CLI capability mapping

Shared skills describe capabilities instead of vendor tool names. Use the platform equivalent:

| Skill references | Copilot CLI equivalent |
|-----------------|----------------------|
| `Read` (file reading) | `view` |
| `Write` (file creation) | `create` |
| `Edit` (file editing) | `edit` |
| `Bash` (run commands) | `bash` |
| `Grep` (search file content) | `grep` |
| `Glob` (search files by name) | `glob` |
| Load a skill | `skill` |
| `WebFetch` | `web_fetch` |
| Dispatch a subagent | `task` (see [Agent types](#agent-types)) |
| Parallel independent work | Multiple `task` calls |
| Worker status or output | `read_agent` / `list_agents` |
| Task tracking | `sql` with the built-in `todos` table |
| `WebSearch` | No equivalent, use `web_fetch` with a search engine URL |
| `EnterPlanMode` / `ExitPlanMode` | No equivalent, stay in the main session |

## Agent types

Copilot CLI's `task` tool accepts an `agent_type` parameter:

| Skill role | Copilot CLI equivalent |
|-------------------|----------------------|
| `general-purpose` | `"general-purpose"` |
| `Explore` | `"explore"` |
| Named plugin agents (e.g. `superpowers:code-reviewer`) | Discovered automatically from installed plugins |

## Async shell sessions

Copilot CLI supports persistent async shell sessions. Treat this as a client-specific capability, not a shared skill requirement:

| Tool | Purpose |
|------|---------|
| `bash` with `async: true` | Start a long-running command in the background |
| `write_bash` | Send input to a running async session |
| `read_bash` | Read output from an async session |
| `stop_bash` | Terminate an async session |
| `list_bash` | List all active shell sessions |

## Additional Copilot CLI tools

| Tool | Purpose |
|------|---------|
| `store_memory` | Persist facts about the codebase for future sessions |
| `report_intent` | Update the UI status line with current intent |
| `sql` | Query the session's SQLite database (todos, metadata) |
| `fetch_copilot_cli_documentation` | Look up Copilot CLI documentation |
| GitHub MCP tools (`github-mcp-server-*`) | Native GitHub API access (issues, PRs, code search) |
