# security-toolkit

Four defensive security skills for web applications, APIs, and toolchain hardening, pre-deployment audit, authentication patterns, API hardening, and npm/bun supply-chain hardening.

## Skills in this plugin

| Skill | What it covers |
|---|---|
| api-hardening | Rate limiting, input validation, CORS, security headers, request throttling, defense-in-depth for Express / FastAPI / serverless |
| secure-auth | Password hashing (argon2id, bcrypt cost), session management, JWT, OAuth 2.1, passkeys / WebAuthn, common tutorial pitfalls |
| security-checklist | Pre-deployment audit aligned to OWASP Top 10, authentication, input validation, secrets management, database security, compliance basics |
| supply-chain-hardening | npm/bun install-time cooldown (`min-release-age` / `minimumReleaseAge`) plus a sandboxed pre-install scan for the bypass case. Defends against Mini Shai-Hulud-class worms that ship within the cooldown window. Includes `/security-toolkit:hotpatch` slash command, a reference Bash implementation, and a synthetic test fixture mimicking the TanStack 2026-05-11 attack signatures. |

## Codex compatibility

The four shared skills remain candidates, not a tested package-wide Codex
workflow. The [project-copy preflight](../plans/2026-09-04-security-toolkit-codex-preflight.md)
records activation observations, blocked filesystem reads, and a missing-resource
boundary: copying only `skills/supply-chain-hardening/` does not include the
package-level scan script or synthetic fixture. Do not run its quick-start as
though those resources were installed with the skill.

`/security-toolkit:hotpatch` and its sandbox, cooldown-bypass, and install
lifecycle are **Claude-only**. No Codex command adapter is provided or approved.

## Slash commands (Claude Code only)

| Command | What it does |
|---|---|
| `/security-toolkit:hotpatch <pkg>[@<version>]` | Sandboxed pre-install scan + cooldown bypass for an urgent npm/bun install, see `supply-chain-hardening` skill for threat model |

## Reference script + test fixture

- `scripts/hotpatch.example.sh`, Linux/`bwrap` reference implementation of the scan. Copy and adapt for your machine.
- `test-fixtures/fake-mini-shai.tgz`, synthetic malicious tarball. Run `bash scripts/hotpatch.example.sh --self-test` to verify the heuristics fire (expected: `2 red, 1 yellow, SELF-TEST PASSED`).

## Installation

```
/plugin marketplace add jamditis/claude-skills-journalism
/plugin install security-toolkit@claude-skills-journalism
```

## See also

- [`dev-toolkit`](../dev-toolkit/README.md), 11 development skills (accessibility, Electron, scraping, frontend patterns, CLAUDE.md maintenance)
- [`journalism-core`](../journalism-core/README.md), 15 skills for reporting, verification, publishing
- [`research-toolkit`](../research-toolkit/README.md), 6 skills for research, archives, academic workflows
