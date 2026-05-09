---
name: vibe-coding
description: Methodology for effective AI-assisted software development. Use when helping users build software with AI coding assistants, debugging AI-generated code, planning features for AI implementation, managing version control in AI workflows, or when users mention "vibe coding," Claude Code, Cursor, GitHub Copilot, Aider, Continue, Cline, Codex, Windsurf, or similar AI coding tools. Provides strategies for planning, testing, debugging, and iterating on code written with LLM assistance.
---

# Vibe coding methodology

Practical strategies for building software effectively with AI coding assistants.

> **Tool landscape moves fast.** This skill was last swept 2026-05-08. The methodology (planning, version control, testing, bug-fixing) is stable; the specific tool names, instruction-file conventions, and pricing details drift quarterly. Treat the named tools as representative, not exhaustive.

## Planning process

Start by working with the AI to write a detailed implementation plan in a markdown file.

**Scope management**: Review and refine the plan—delete unnecessary items, mark complex features as "won't do," and keep a separate section for ideas to implement later. This prevents scope creep and maintains focus.

**Incremental implementation**: Work section by section rather than building everything at once. Have the AI mark sections complete after successful implementation, and commit each working section to git before moving to the next.

**Track progress visibly**: Use todo lists, markdown checklists, or inline status markers so both you and the AI can see what's done and what remains. This prevents re-implementing completed work and keeps sessions focused.

## Version control strategies

Git is your safety net — don't rely solely on the AI tool's revert functionality.

**Branch per attempt**: Begin each new feature on a fresh feature branch (`git switch -c feature/xyz`) and commit small chunks as the AI makes progress. The branch boundary is your "if this goes off the rails, throw it away" boundary — you discard the branch, not your working tree.

**When the AI goes down a bad path**: Prefer reversible commands. `git restore .` discards uncommitted changes; `git stash` parks them; `git switch -` jumps back to your previous branch. Reach for `git reset --hard HEAD` only when you've confirmed there's nothing in the working tree worth keeping — destructive commands skip the reflog niceties and can swallow uncommitted experiments. (If the agent has been creating new files, a separate `git clean -fd` is also part of "really, throw it all away" — same caveats.)

**Clean re-implementation**: When you finally find a working solution after several attempts, branch from main, implement it fresh, and discard the throwaway branch. Multiple failed AI attempts leave layers of dead code that compound future confusion — a clean re-implementation of a known-good solution is faster and more maintainable than untangling the spaghetti.

## Testing framework

Prioritize end-to-end integration tests over unit tests. Focus on simulating user behavior—testing features by simulating someone clicking through the site or app.

**Regression prevention**: LLMs often make unnecessary changes to unrelated logic. Tests catch these regressions before they compound.

**Tests as guardrails**: Consider starting with test cases to provide clear boundaries for what the AI should and shouldn't change. Ensure tests pass before moving to the next feature.

## Effective bug fixing

**Error messages**: Simply copy-pasting error messages is often enough context for the AI to identify and fix issues.

**Analyze before coding**: Ask the AI to consider multiple possible causes before jumping to implementation. This prevents chasing the wrong problem.

**Reset after failures**: Start with a clean slate after each unsuccessful fix attempt rather than layering fixes on top of broken code.

**Strategic logging**: Add logging statements to better understand what's happening when bugs are opaque.

**Switch models**: Try different AI models when one gets stuck on a problem.

## AI tool landscape (as of 2026-05)

The current tools cluster into four shapes. Pick by where you work, not by hype.

| Shape | Examples | When |
|---|---|---|
| CLI agents | Claude Code, Aider, Codex CLI, Gemini CLI, GitHub Copilot CLI, opencode, Goose | Repo-wide changes, multi-file refactors, automation, headless / cron use |
| Standalone IDEs | Cursor, Windsurf, Zed, Kiro | Day-to-day editing with chat + autocomplete tightly integrated |
| IDE extensions | GitHub Copilot, Continue, Cline, Roo Code, Amazon Q | Stay in your existing editor (VS Code, JetBrains, Neovim) |
| Cloud agents | Devin, OpenHands, Jules, GitHub Copilot Coding Agent | Async / background work via PR, no local terminal needed |

A common stack many developers converge on: **Cursor or Copilot for daily editing + Claude Code (or Codex CLI) for repo-wide / agentic tasks**. They're complementary — fast inline edits in the IDE, longer agentic loops at the terminal.

## AI tool optimization

**Instruction files**: Write project-specific context for your AI assistants. Conventions have splintered, but several tools converge on `AGENTS.md` as a shared format. Current naming as of 2026-05:

| Tool | File(s) | Notes |
|---|---|---|
| Claude Code | `CLAUDE.md` (per-directory, nested) | Loaded automatically; see [docs.anthropic.com/en/docs/claude-code/memory](https://docs.anthropic.com/en/docs/claude-code/memory) |
| Cursor | `.cursor/rules/*.mdc` (modern) — Markdown + YAML frontmatter (`description`, `globs`, `alwaysApply`) | Legacy `.cursorrules` single-file still works but Cursor recommends migrating |
| Windsurf | `.windsurfrules` or `.windsurf/rules/*.md` | Same dual pattern as Cursor |
| GitHub Copilot | `.github/copilot-instructions.md` | Single repo-level file, ~4k char practical cap |
| Cline | `.clinerules` | Single file |
| Aider | `.aider.conf.yml` (config) + chat history files | Git-native; reads `CONVENTIONS.md` if you point it there |
| Continue | `.continue/config.json` | JSON config; per-repo |
| Codex CLI / Gemini CLI / Aider / Continue | `AGENTS.md` (vendor-neutral fallback) | Becoming the cross-tool common denominator |

When working across multiple tools, keep the canonical guidance in `AGENTS.md` and reference it from tool-specific files (`CLAUDE.md`: "Also read AGENTS.md."). That avoids drift between siblings.

**Local documentation**: Download API documentation to your project folder. AI tools work more accurately against local docs than against recalled training data — especially for libraries that release breaking changes faster than training cutoffs (e.g., Sentry SDK, Google GenAI SDK, Selenium).

**Run multiple tools**: There's no penalty for running Cursor for inline edits while a Claude Code or Codex CLI session works in another terminal on a separate task. Different shapes for different work.

**Compare outputs**: For high-stakes decisions, generate solutions from two different model families (e.g., Claude + GPT-5) and pick the better one. They make different mistakes.

## Complex feature development

**Standalone prototypes**: Build complex features in a clean codebase first, then integrate once working. This isolates problems and makes debugging easier.

**Reference implementations**: Point the AI to working examples to follow. Existing code patterns provide concrete guidance.

**Clear boundaries**: Maintain consistent external APIs while allowing internal changes. Service-based architectures with clear boundaries work better than monorepos for AI-assisted development.

## Tech stack considerations

**Established frameworks**: Ruby on Rails and similar mature frameworks work well due to 20+ years of consistent conventions in training data.

**Training data matters**: Newer languages like Rust or Elixir may have less training data, leading to more errors or outdated patterns.

**Modularity**: Small, modular files are easier for both humans and AIs to work with. Avoid files with thousands of lines—they exceed context windows and create confusion.

## Beyond coding

AI assistants help with more than writing code:

- **DevOps**: Configuring servers, DNS, and hosting
- **Design**: Generating favicons and other design elements
- **Documentation**: Drafting docs and marketing materials
- **Education**: Explaining implementations line by line
- **Visual input**: Share screenshots for UI bugs or design inspiration. Most modern assistants (Claude Code via paste, Cursor, Copilot Chat) accept image input directly.
- **Voice input**: Whisper-based transcription tools (Whispr Flow, Superwhisper, MacWhisper, Aqua) reach 130-180 wpm with current OpenAI / Whisper.cpp models. Useful for long-form prompting and rubber-ducking.

## Continuous improvement

**Regular refactoring**: Once tests are in place, refactor frequently. Ask the AI to identify refactoring candidates.

**Stay current**: Try every new model release. Different models excel at different tasks—experiment to find which works best for your use case.
