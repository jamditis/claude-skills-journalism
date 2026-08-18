# security-toolkit

Four defensive security skills for web applications, APIs, and toolchain hardening, pre-deployment audit, authentication patterns, API hardening, and npm/bun supply-chain hardening.

## Skills in this plugin

| Skill | What it covers |
|---|---|
| api-hardening | Rate limiting, input validation, CORS, security headers, request throttling, defense-in-depth for Express / FastAPI / serverless |
| secure-auth | Password hashing (argon2id, bcrypt cost), session management, JWT, OAuth 2.1, passkeys / WebAuthn, common tutorial pitfalls |
| security-checklist | Pre-deployment audit aligned to OWASP Top 10, authentication, input validation, secrets management, database security, compliance basics |
| supply-chain-hardening | npm/bun install-time cooldown (`min-release-age` / `minimumReleaseAge`) plus a sandboxed pre-install scan for the bypass case. Defends against Mini Shai-Hulud-class worms that ship within the cooldown window. Includes `/security-toolkit:hotpatch` slash command, a reference Bash implementation, and a synthetic test fixture mimicking the TanStack 2026-05-11 attack signatures. |

## Slash commands

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
- [`journalism-core`](../journalism-core/README.md), 13 skills for reporting, verification, publishing
- [`research-toolkit`](../research-toolkit/README.md), 5 skills for research, archives, academic workflows
