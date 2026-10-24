# Gemini CLI capability mapping

Shared skills describe capabilities instead of vendor tool names. Use the platform equivalent:

| Skill references | Gemini CLI equivalent |
|-----------------|----------------------|
| `Read` (file reading) | `read_file` |
| `Write` (file creation) | `write_file` |
| `Edit` (file editing) | `replace` |
| `Bash` (run commands) | `run_shell_command` |
| `Grep` (search file content) | `grep_search` |
| `Glob` (search files by name) | `glob` |
| Task tracking | `write_todos` |
| Load a skill | `activate_skill` |
| `WebSearch` | `google_web_search` |
| `WebFetch` | `web_fetch` |
| Dispatch a subagent | No equivalent; do the steps in sequence |

## No subagent support

When no worker capability is available, skills that delegate work (`subagent-driven-development`, `dispatching-parallel-agents`) fall back to single-session execution through `executing-plans`.

## Additional Gemini CLI tools

These capabilities are client-specific and are not shared skill requirements:

| Tool | Purpose |
|------|---------|
| `list_directory` | List files and subdirectories |
| `save_memory` | Persist facts to `GEMINI.md` across sessions |
| `ask_user` | Request structured input from the user |
| `tracker_create_task` | Rich task management (create, update, list, visualize) |
| `enter_plan_mode` / `exit_plan_mode` | Switch to read-only research mode before making changes |
