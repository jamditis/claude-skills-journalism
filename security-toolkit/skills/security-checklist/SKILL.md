---
name: security-checklist
description: Pre-deployment security audit for web applications, organized by OWASP Top 10:2025 categories. Use when reviewing code before shipping, auditing an existing application, or when users mention "security review," "ready to deploy," "going to production," or express concern about vulnerabilities. Covers access control, supply chain, cryptography, injection, auth, integrity, logging, and exception handling.
---

# Security checklist

Pre-deployment security audit organized around the OWASP Top 10:2025 categories (released late 2025, succeeding the 2021 edition). This is the baseline that prevents obvious disasters — not a substitute for a real penetration test or threat model. For verification depth beyond this checklist, see OWASP ASVS 5.0 (https://owasp.org/www-project-application-security-verification-standard/). For API-specific scope, see OWASP API Security Top 10:2023 (https://owasp.org/API-Security/editions/2023/en/0x00-header/).

## Step 0: Research the current security landscape (do this first)

> Security knowledge ages on a 6-12 month half-life. The recipes below were last verified on 2026-05-08; they may be stale by the time you read this. Before applying any pattern in this skill, fan out research scoped to the OWASP Top 10:2025 categories being audited so the recipes are interpreted against current authoritative sources, not against this file's snapshot.

### Default-on, with a documented skip

Run the 4-angle research below by default. Skip ONLY when ALL of these hold:

- (a) You ran this same skill on this same primitive within the last 4 hours of the current session,
- (b) That prior research surfaced no urgent advisories for the OWASP Top 10:2025 categories being audited,
- (c) You log a one-line `Research skipped because <reason>` note in your response.

"I think I know" / "moving fast" / "user wants this done quickly" / "already familiar" are NOT valid skip reasons. The whole point of this preamble is that future-you should not trust this skill body's defaults until current state is checked.

### Fan out 4 subagents in parallel

Each subagent returns ≤300 words of bullets with citations. Dispatch all 4 in a single message so they run concurrently.

**Angle 1 — Authoritative standards.** Have NIST / OWASP / IETF (RFCs and Internet-Drafts) / W3C / CISA published anything new about the OWASP Top 10:2025 categories being audited in the last 6-12 months? Look for: spec finalizations, deprecations, replacement specs, RFC publications, draft revisions, NIST SP updates, OWASP project version bumps. Cite by document number + publication date.

**Angle 2 — Active exploitation.** What's actively being exploited that targets the OWASP Top 10:2025 categories being audited? Pull from: CISA Known Exploited Vulnerabilities (KEV) catalog (filter to last 6-12 months), recent CVE / GHSA entries with high CVSS or in-the-wild exploitation, breach postmortems and incident reports (CSRB, vendor RCAs, security-vendor research). Surface CWE patterns dominating recent KEV adds. Cite by CVE number + advisory URL.

**Angle 3 — Tooling and library state.** Are the libraries this skill recommends still current? What are the latest major versions in the relevant package registry (npm / PyPI / RubyGems / crates.io)? Have any been deprecated, replaced, or merged into another project? Have any flipped a secure default? Look up current versions in: registry.npmjs.org, pypi.org, rubygems.org, crates.io, pkg.go.dev. Cite by package + version + release date.

**Angle 4 — Practitioner discourse.** What are practitioners and security teams talking about in the last 6 months? Pull from: OWASP Cheat Sheet Series (last-modified date matters), GitHub Security Lab posts, vendor security blogs (Cloudflare, Fastly, Snyk, Datadog, Wiz, GitGuardian), conference talks (Black Hat, DEF CON, OWASP Global AppSec, USENIX Security), SANS ISC, Krebs, recent OWASP project re-releases. Surface the patterns being adopted and the anti-patterns being called out. Cite by post URL + author + date.

### Synthesize before applying recipes

After the 4 returns land, write a 1-paragraph "current state for the OWASP Top 10:2025 categories being audited, as of <today's date>" that names:

- The current normative ceiling (what specs say SHOULD be the default in 2026).
- 1-2 active threats specific to the OWASP Top 10:2025 categories being audited from the last 6-12 months.
- Any tooling drift (deprecated lib, new default in a framework, package merged or replaced).
- Any practitioner consensus shift visible in recent cheat sheet / blog updates.

If the synthesis flags drift in this skill body's recipes (e.g., a spec finalized after 2026-05-08, a library now deprecated, a default flipped), call that out explicitly in your response and override the skill body where they conflict. The synthesis wins. The skill body is scaffolding, not scripture.

### When you cannot run subagents

If subagents are not available in your runtime, the same shape applies in-line: do 4 sequential targeted searches (web search for standards, KEV catalog lookup, package registry version checks, recent cheat-sheet diff). Land the same 1-paragraph synthesis. Cost goes up; the protection does not change.

## How to use this checklist

Walk all 10 categories before any production deployment. For each category: read the framing paragraph, run through the must-do items, and check the code-pattern references where they apply. After the walk, file findings as one issue per category with gaps. The flat 25-item Yes/No gate at the end is the pre-deploy summary, not the audit itself.

If you can't check an item, don't ship — fix it first.

## A01:2025 — Broken Access Control

Authorization failures are the most-exploited class on the web. The 2025 edition folds SSRF (Server-Side Request Forgery) into A01 because the underlying failure is the same: the server acts on a request it should have rejected. Active exemplars in 2024-2025 include broken object-level authorization in API endpoints (still the dominant API risk per OWASP API Top 10:2023 API1) and SSRF used as a pivot to cloud metadata endpoints.

- [ ] Authorization checked at every endpoint, not just at the gateway or middleware layer.
- [ ] Default-deny at the controller level (explicit allow per route, not implicit allow).
- [ ] Object-level authorization on every resource fetch (IDOR — don't expose IDs without checking the principal owns them).
- [ ] Function-level authorization on admin and privileged endpoints (check role, not just route).
- [ ] SSRF defenses: outbound allowlist for any URL fetched server-side; no `localhost`, `127.0.0.0/8`, link-local (`169.254.0.0/16`), or cloud metadata IP (`169.254.169.254`) fetches; DNS rebinding protection on resolvers.
- [ ] Database row-level security enabled where the platform supports it (see code-pattern below).
- [ ] Application uses a dedicated database user with minimum required permissions, not root/admin.

### Code pattern: PostgreSQL / Supabase row-level security

```sql
-- Enable RLS on table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Users can only read their own documents
CREATE POLICY "Users can read own documents" ON documents
  FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert documents as themselves
CREATE POLICY "Users can insert own documents" ON documents
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own documents
CREATE POLICY "Users can update own documents" ON documents
  FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own documents
CREATE POLICY "Users can delete own documents" ON documents
  FOR DELETE USING (auth.uid() = user_id);
```

## A02:2025 — Security Misconfiguration

Misconfiguration moved up the rankings (was A05 in 2021) because default-insecure framework settings keep shipping to production. The 2024 Snowflake / UNC5537 campaign is the canonical lesson: MFA was opt-in per tenant by default, and the campaign harvested credentials at scale before Snowflake flipped the default in 2024.

- [ ] Hardened images / minimal containers (distroless or slim base; no shells unless required).
- [ ] Default credentials removed; default ports closed at the firewall.
- [ ] CORS configured for specific origins (`Access-Control-Allow-Origin: *` flagged in production).
- [ ] Production-mode flag set on web frameworks: Flask `debug=False`, Django `DEBUG=False`, Express `NODE_ENV=production`, Rails `RAILS_ENV=production`.
- [ ] Stack traces never returned to clients.
- [ ] Cloud bucket / blob public-read disabled by default; access via signed URLs or authenticated requests.
- [ ] Admin interfaces not publicly accessible (VPN, allowlist, or auth proxy).
- [ ] Unnecessary services and ports closed; firewall set to deny by default.
- [ ] No secrets in source code or git history; secrets read from environment variables or a secrets manager.
- [ ] Different secrets for development / staging / production.
- [ ] API keys scoped to minimum required permissions; rotatable without code deployment.

### Code pattern: environment variables setup

```bash
# .env (development only, never commit)
# Replace each <placeholder> with a real value generated locally.
# Generate JWT_SECRET with `openssl rand -hex 32` (256 bits).
DATABASE_URL=<your-database-connection-string>
JWT_SECRET=<32-byte-hex-secret>
API_KEY=<api-key-from-your-provider>
```

```gitignore
# .gitignore (mandatory)
.env
.env.local
.env.*.local
*.pem
*.key
credentials.json
secrets/
```

```javascript
// Reading environment variables (Node.js with dotenv)
require('dotenv').config();
const dbUrl = process.env.DATABASE_URL;

// Fail fast if missing
if (!process.env.JWT_SECRET) {
  throw new Error('JWT_SECRET environment variable is required');
}
```

### Code pattern: CORS (Express.js)

```javascript
const cors = require('cors');

// SAFE: specific origins
app.use(cors({
  origin: ['https://myapp.com', 'https://www.myapp.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));
```

The unsafe pattern — `cors()` with no options, which sends `Access-Control-Allow-Origin: *` — is fine for dev but never for production with credentialed requests.

## A03:2025 — Software Supply Chain Failures

New category in 2025 that absorbs the old 2021 A06 "Vulnerable and Outdated Components." Broader than just patching: covers SBOM, build-system integrity, package provenance, and dependency-source trust. The xz-utils CVE-2024-3094 backdoor (March 2024) is the canonical "social-engineering of an open-source maintainer" lesson; Polyfill.io (June 2024) is the canonical "trusted CDN turned hostile" lesson.

- [ ] SBOM generated at build time (CycloneDX 1.7 = ECMA-424 2nd Edition, ratified Dec 2025; or SPDX 2.3+).
- [ ] Dependency scanning runs in CI (Trivy, Grype, Snyk, or GHSA scanner) and fails the build on critical findings.
- [ ] Versions pinned (lockfiles committed; no floating tags like `latest` in container images or `^x.y.z` for security-critical libs).
- [ ] Provenance signing in place: npm provenance (GA Sep 2023), PyPI Trusted Publishing, Sigstore cosign for containers.
- [ ] SLSA v1.2 source/build track adoption tracked (released 2025-11-24, https://slsa.dev/).
- [ ] Patches applied on a schedule. Renovate or Dependabot enabled with auto-merge for patch versions.
- [ ] End-of-life runtimes flagged and replaced (Node 18 EOL April 2025; Python 3.8 EOL Oct 2024).
- [ ] Subresource Integrity on every external `<script>` and `<link rel="stylesheet">` (Polyfill.io lesson — see A08 for the SRI checklist item).

**Compliance pointer:** OMB M-26-05 (issued 2026-01-23) rescinded the federal-wide SBOM self-attestation mandate from M-22-18 + M-23-16. The EU Cyber Resilience Act (Reg 2024/2847) reporting obligations apply from 2026-09-11 and full obligations from 2027-12-11 — don't treat the US rescission as global rescission.

## A04:2025 — Cryptographic Failures

Use vetted high-level libraries. Don't roll crypto. Don't compose AES-CBC + HMAC by hand — use libsodium, AWS Encryption SDK, or Tink. The 2026 normative ceiling is TLS 1.3 by default, TLS 1.2 minimum, TLS 1.0/1.1 disabled (RFC 8996 / BCP 195).

- [ ] HTTPS only; HTTP redirects to HTTPS.
- [ ] TLS 1.3 by default; TLS 1.2 minimum; TLS 1.0/1.1 disabled.
- [ ] HSTS preload header set: `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (2 years).
- [ ] Secure cookie flags set (`Secure`, `HttpOnly`, `SameSite=Lax` or `Strict`).
- [ ] Database connections use SSL/TLS.
- [ ] Backups encrypted at rest and tested for restoration.
- [ ] Password storage uses argon2id with OWASP cheat-sheet parameters (m=47104/t=1, m=19456/t=2, m=12288/t=3, m=9216/t=4, or m=7168/t=5; all p=1). The full policy lives in the `secure-auth` skill in this bundle — link from here.
- [ ] No MD5 / SHA-1 / unsalted hashes anywhere in the auth or integrity path.
- [ ] No hand-rolled crypto — use libsodium, AWS Encryption SDK, Google Tink, or equivalent.

### Code pattern: security headers (Express.js with Helmet)

```javascript
const helmet = require('helmet');

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      frameAncestors: ["'none'"]
    },
  },
  hsts: {
    maxAge: 63072000,
    includeSubDomains: true,
    preload: true
  }
}));
```

```javascript
// Manual headers — modern set
res.setHeader('X-Content-Type-Options', 'nosniff');
res.setHeader('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload');
res.setHeader('Content-Security-Policy', "default-src 'self'; frame-ancestors 'none'");
// Note: X-Frame-Options is replaced by CSP frame-ancestors. The legacy XSS-protection header is deprecated — modern browsers ignore it.
```

## A05:2025 — Injection

CWE-78 OS command injection dominates CISA KEV in 2024-2025 (14 entries in 2024, 18 in 2025) — eclipsing classic SQL injection by volume. CWE-22 path traversal also climbed (9 in 2024, 13 in 2025). MOVEit CVE-2023-34362 remains the canonical SQLi exemplar.

- [ ] All user input validated server-side. Client validation is UX, not security.
- [ ] SQL queries use parameterized statements (CWE-89). Never string concatenation.
- [ ] OS commands invoked with argv-list form, shell disabled. Allowlist-validate any path or filename used in shell-out (CWE-78).
- [ ] LDAP / NoSQL / template injection — same parameterization principle.
- [ ] HTML output escaped (XSS): framework auto-escape + CSP3 nonce + Trusted Types where supported.
- [ ] Header injection: validate any user-supplied value used in response headers (no CR/LF).
- [ ] File uploads validate type, size, and store outside webroot.
- [ ] URLs and redirects validated against an allowlist.
- [ ] JSON/XML parsers have entity expansion limits.

### Code pattern: parameterized SQL (Node.js)

The unsafe pattern — interpolating user input into a SQL template string and calling `db.query` on the result — is CWE-89. Always parameterize.

```javascript
// SAFE: parameterized query, user input bound as $1
db.query('SELECT * FROM users WHERE id = $1', [req.params.id]);
```

### Code pattern: parameterized SQL (Python)

```python
# SAFE: parameterized query, user input bound as %s placeholder
cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])
```

The unsafe pattern — building the SQL string with an f-string that interpolates user input — is CWE-89.

### Code pattern: command injection (Node.js)

The Node child_process module exposes a shell-execution primitive (the one that runs a command string through `/bin/sh`) and an argv-list primitive (the spawn family with `shell: false`). For any input that touches user data, use the argv-list primitive.

```javascript
const { spawn } = require('child_process');

// SAFE: argv-list invocation, shell disabled
// userInput is treated as a single argument, never re-parsed by a shell
spawn('convert', [userInput, 'output.png'], { shell: false });
```

The unsafe pattern — passing a template string with interpolated user input to the shell-execution primitive — is CWE-78. Don't do it. If you absolutely need shell features, allowlist-validate every component of the command first.

### Code pattern: command injection (Python)

Python exposes shell-execution primitives (the OS shell-out function and `subprocess.run(..., shell=True)`) and an argv-list primitive (`subprocess.run([...], shell=False)`). For any input that touches user data, use the argv-list primitive.

```python
import subprocess

# SAFE: argv-list invocation, shell disabled
# user_input is treated as a single argument, never re-parsed by a shell
subprocess.run(["convert", user_input, "output.png"], shell=False, check=True)
```

The unsafe patterns — passing an f-string with interpolated user input to the OS shell-out function or to a subprocess call with `shell=True` — are CWE-78. Don't do them. Allowlist-validate any path or filename component before it reaches a shell-out boundary.

### Code pattern: XSS (React/Frontend)

React auto-escapes JSX child content. The framework also exposes `dangerouslySetInnerHTML`, a prop whose name explicitly warns you what happens if you pass user data through it. Default to rendering as a child; reach for the dangerous prop only with a vetted sanitizer in front.

```javascript
// DO NOT USE: dangerouslySetInnerHTML on user content with no sanitizer
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// SAFE: React escapes content automatically when rendered as a child
<div>{userContent}</div>

// SAFE: when raw HTML is genuinely required, sanitize through DOMPurify first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userContent) }} />
```

For server-rendered HTML, use a template engine with auto-escaping (EJS `<%= %>`, Nunjucks `{{ }}` with autoescape on, etc.) rather than building strings by hand.

```javascript
// DO NOT USE: template-string interpolation of user input into HTML
res.send(`<h1>Hello ${req.query.name}</h1>`);

// SAFE: template engine with auto-escaping
res.render('greeting', { name: req.query.name });
```

## A06:2025 — Insecure Design

Threat-modeling and secure defaults belong in the design phase, not retrofitted post-incident. Snowflake's MFA-opt-in default (until 2024) is the canonical "secure default" lesson — features that ship insecure by default and require opt-in to be safe are misuse-prone.

- [ ] Threat-model new features before code (STRIDE for security, LINDDUN for privacy).
- [ ] Misuse cases written alongside use cases.
- [ ] Least-privilege at the design layer (services, roles, scopes).
- [ ] Rate limits designed in, not retrofitted: API endpoints rate-limited per user/IP, login endpoints stricter, request size limits configured, timeouts on all external calls.
- [ ] CDN or DDoS protection in front of the application.
- [ ] Secure defaults — the safe option is the path of least resistance; opt-in is for the unsafe option, not the safe one.

## A07:2025 — Authentication Failures

Renamed from "Identification and Authentication Failures" in 2021. Defaults live in the `secure-auth` skill in this bundle — checklist items here reference, don't duplicate. NIST SP 800-63B-4 went final 2025-07-31 (https://csrc.nist.gov/pubs/sp/800/63/b/4/final).

- [ ] 15-character single-factor password minimum (NIST SP 800-63B-4). No composition rules. No periodic rotation.
- [ ] Breach blocklist check on registration / change (Have I Been Pwned API or equivalent).
- [ ] Passwords hashed with argon2id (or bcrypt cost ≥10 / scrypt as acceptable alternates). Never MD5, SHA-1, or plain text.
- [ ] MFA available for all accounts; phishing-resistant MFA (WebAuthn / passkey) REQUIRED at AAL3.
- [ ] Session tokens cryptographically random (`crypto.randomBytes` or equivalent).
- [ ] Sessions expire (24 hours for normal apps, shorter for sensitive data).
- [ ] Logout invalidates the session server-side.
- [ ] Password reset tokens are single-use and expire within 1 hour.
- [ ] Failed login attempts rate-limited (e.g., 5 attempts then cooldown).
- [ ] Session regeneration on privilege change (login, role escalation).
- [ ] Refresh-token rotation with reuse detection.
- [ ] No credentials in code, logs, or error messages.

**Anchor lessons:** Change Healthcare Feb 2024 (no MFA on the Citrix remote-access portal — https://www.unitedhealthgroup.com/newsroom/2024/2024-04-22-uhg-update-on-change-healthcare-cyberattack.html), Snowflake / UNC5537 2024 (default-on MFA was opt-in per tenant), Storm-0558 2023 (full token validation; CSRB review at https://www.cisa.gov/resources-tools/resources/CSRB-Review-Summer-2023-MEO-Intrusion), 23andMe 2023 (graph-traversal blast radius across linked accounts).

## A08:2025 — Software or Data Integrity Failures

Note: "Software or Data" — the OR is load-bearing. Covers CI/CD pipeline integrity, signed update channels, and deserialization safety. CWE-502 (deserialization) dominates KEV in 2024-2025 (11 in 2024, 14 in 2025).

- [ ] CI/CD pipeline integrity: signed builds, branch protections, required reviews, no plaintext secrets in pipeline config.
- [ ] Update channels validated: signature checks on auto-updaters; Sigstore cosign for container images.
- [ ] Deserialization gates: never deserialize untrusted input with native binary deserializers or YAML's unrestricted-load primitives. JSON-only across trust boundaries.
- [ ] Subresource Integrity on every external `<script>` and `<link rel="stylesheet">` (Polyfill.io lesson — https://sansec.io/research/polyfill-supply-chain-attack).
- [ ] No third-party scripts referenced from CDNs without SRI hashes pinned.

### Code pattern: deserialization (Python)

Python's native binary-deserialization primitive executes arbitrary code on untrusted input — `loads` runs object constructors, including any `__reduce__` payload an attacker has crafted. JSON does not. Across any trust boundary, use JSON. Same hazard for YAML: the bare loader runs Python code; use `safe_load`.

```python
import json
import yaml

# DO NOT USE: pickle.loads runs arbitrary code on untrusted input —
# any object's __reduce__ method executes at parse time. CWE-502 sink.
#   import pickle
#   obj = pickle.loads(request.body)

# DO NOT USE: yaml.load with no Loader argument is equivalent to yaml.Loader and runs code:
#   config = yaml.load(request.body)

# SAFE: JSON parsing returns plain data (dict / list / str / number / bool / None)
data = json.loads(request.body)

# SAFE: when YAML is genuinely required, use safe_load
config = yaml.safe_load(request.body)
```

CWE-502 (deserialization of untrusted data) dominated the CISA KEV catalog in 2024-2025 (11 in 2024, 14 in 2025). The same warning applies in Java (`ObjectInputStream.readObject`), .NET (`BinaryFormatter`, `NetDataContractSerializer`, `LosFormatter`, `SoapFormatter`), and any Node package that "unserializes" arbitrary objects. JSON is the only safe choice for cross-trust-boundary input.

### Code pattern: SRI

```html
<!-- SAFE: SRI hash pinned -->
<script src="https://cdn.example.com/lib.js"
        integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
        crossorigin="anonymous"></script>
```

The unsafe pattern — referencing an external script with no `integrity` attribute — means any change at the CDN runs in your origin's context. Polyfill.io 2024 was exactly this.

## A09:2025 — Security Logging and Alerting Failures

Note: "Alerting", not "Monitoring" — the 2025 edition reframes around active response, not just collection. The Okta HAR incident (2023) is the anchor lesson: customer-uploaded debug artifacts contained live session tokens because sanitization at log boundaries was inadequate.

- [ ] Log auth events (login, logout, failed attempts), authz failures, admin actions, payment events.
- [ ] Logs do NOT include passwords, tokens, JWTs, API keys, PII, session IDs, credit cards, or full request bodies with user data.
- [ ] Centralized logging with retention policy (90 days minimum for security logs, longer for compliance).
- [ ] Logs stored securely (encrypted at rest, access-controlled).
- [ ] Alerts configured for impossible-travel, mass-failed-auth, privilege-escalation patterns.
- [ ] Error messages don't leak system information to clients (see A10).

**Anchor lesson:** Okta HAR file incident — https://sec.okta.com/articles/harfiles/

### Code pattern: what NOT to log

```javascript
// SAFE: structured logging with field allowlist
console.log('Login attempt:', { email, success: false, reason: 'invalid_password' });
console.log('Request:', { endpoint: req.path, method: req.method, userId: req.user?.id });
```

The unsafe pattern — logging the full request body or a credentials object — leaks every secret a user supplies. Never log password fields, token fields, full request bodies, or session identifiers.

## A10:2025 — Mishandling of Exceptional Conditions

New category in 2025. CWE catalog assigned CWE-1445 to this category, covering CWE-209/234/274/476/636 among 24 CWEs. The CrowdStrike Channel File 291 incident (July 2024) is the anchor lesson: production deployment of an unvalidated config file caused 8.5M Windows hosts to BSOD.

- [ ] Fail-closed by default for security-relevant code paths (don't catch-all-and-continue on auth/authz/integrity failures).
- [ ] Error responses don't leak structure, stack traces, or internal IDs.
- [ ] Config validated before deploying to production. Staged rollouts, canary percentages, validation gates between staging and prod.
- [ ] Catch `Exception` blocks don't swallow security-relevant failures silently.
- [ ] Test exceptional paths (timeout, OOM, partial-write, network partition) — most security regressions hide here.
- [ ] Timeouts set on all external calls, with explicit handling for the timeout case.

**Anchor lesson:** CrowdStrike Falcon Channel File 291 RCA — https://www.crowdstrike.com/en-us/blog/falcon-content-update-preliminary-post-incident-report/

## Pre-deployment summary — 25-item Yes/No gate

Run this at the end of the audit. If any answer is N, don't ship.

1. TLS 1.3 enforced (TLS 1.2 minimum, 1.0/1.1 disabled)? Y/N
2. HSTS preload header set with `max-age=63072000; includeSubDomains; preload`? Y/N
3. argon2id used for password hashing (or bcrypt cost ≥10 / scrypt)? Y/N
4. 15-character password minimum, no composition rules, no rotation? Y/N
5. Phishing-resistant MFA available for all accounts? Y/N
6. Session tokens cryptographically random and invalidated on logout? Y/N
7. SQL queries parameterized everywhere? Y/N
8. OS commands use argv-list form, shell disabled? Y/N
9. HTML output auto-escaped + CSP with `frame-ancestors`? Y/N
10. CORS scoped to specific origins (no `*` in prod)? Y/N
11. Default-deny authorization at controller level? Y/N
12. Object-level authorization on every resource fetch (no IDOR)? Y/N
13. SSRF outbound allowlist + metadata-IP blocklist? Y/N
14. Database row-level security enabled where supported? Y/N
15. No secrets in code or git history; all read from env / secrets manager? Y/N
16. Production-mode flag set (`debug=False`, `NODE_ENV=production`, etc.)? Y/N
17. Stack traces never returned to clients? Y/N
18. SBOM generated at build time and scanned in CI? Y/N
19. All third-party scripts have SRI hashes pinned? Y/N
20. Dependencies pinned via lockfile; no floating container tags? Y/N
21. End-of-life runtimes flagged and replaced? Y/N
22. Auth events, authz failures, admin actions logged (without secrets)? Y/N
23. Alerts configured for mass-failed-auth and privilege-escalation? Y/N
24. Security-relevant code paths fail closed? Y/N
25. Config validated and rolled out via staged deployment? Y/N

## Incident response quick-fixes

### "I stored passwords in plain text"

1. Add password hashing immediately (argon2id; see `secure-auth` skill).
2. Force password reset for all users.
3. Invalidate all existing sessions.
4. Check breach indicators (was the database ever exposed or backed up insecurely?).

### "My API key is in the git history"

1. Rotate the key immediately (generate new one).
2. Revoke the old key.
3. Use `git filter-repo` (preferred over `git filter-branch`) or BFG Repo-Cleaner to remove from history.
4. Force push and coordinate with the team.

### "I don't know what data I'm logging"

1. Search codebase for `console.log`, `logger.`, `print(`.
2. Review what's being logged.
3. Implement structured logging with a field allowlist.
4. Set up log rotation and retention.

### "My database is publicly accessible"

1. Change database credentials immediately.
2. Configure firewall rules (allow only application-server IPs).
3. Enable SSL/TLS for connections.
4. Review access logs for unauthorized queries.

## Compliance quick reference

You likely need to care about:

- **GDPR** (EU users): data deletion rights, consent, breach notification.
- **CCPA** (California users): similar to GDPR.
- **PCI DSS** (credit cards): don't store card numbers; use a payment processor.
- **HIPAA** (health data): encryption, access controls, audit logs.
- **SOC 2** (enterprise sales): security controls documentation.
- **SEC Form 8-K Item 1.05** (US-listed companies): material cybersecurity incidents disclosed within 4 business days (effective 2023-12-18).
- **EU Cyber Resilience Act** (Reg 2024/2847): products with digital elements; reporting obligations from 2026-09-11, full obligations from 2027-12-11.
- **OMB M-26-05** (US federal suppliers): rescinded the federal-wide SBOM self-attestation mandate (issued 2026-01-23). Agency-specific requirements may still apply.

Minimum for any user data:

1. Privacy policy explaining data collection.
2. Way for users to request data deletion.
3. Encryption in transit (HTTPS) and at rest.
4. Access logs and audit trail.
5. Incident response plan (even if basic).

## Resources

### Standards and frameworks
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP API Security Top 10:2023: https://owasp.org/API-Security/editions/2023/en/0x00-header/
- OWASP ASVS 5.0: https://owasp.org/www-project-application-security-verification-standard/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- NIST SP 800-63B-4 (final): https://csrc.nist.gov/pubs/sp/800/63/b/4/final
- TLS 1.3 RFC 8446: https://datatracker.ietf.org/doc/rfc8446/
- RFC 8996 (TLS 1.0/1.1 deprecation): https://datatracker.ietf.org/doc/rfc8996/

### Vulnerability data
- CISA Known Exploited Vulnerabilities catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- MITRE Top 25 2024: https://cwe.mitre.org/top25/archive/2024/2024_cwe_top25.html
- CWE-78 (OS Command Injection): https://cwe.mitre.org/data/definitions/78.html
- CWE-502 (Deserialization of Untrusted Data): https://cwe.mitre.org/data/definitions/502.html
- Have I Been Pwned: https://haveibeenpwned.com/

### Supply chain
- Sigstore: https://www.sigstore.dev/
- SLSA v1.2: https://slsa.dev/
- CycloneDX 1.7 / ECMA-424: https://ecma-international.org/publications-and-standards/standards/ecma-424/
- npm provenance: https://docs.npmjs.com/generating-provenance-statements
- PyPI Trusted Publishing: https://docs.pypi.org/trusted-publishers/
- xz-utils CVE-2024-3094: https://nvd.nist.gov/vuln/detail/CVE-2024-3094
- Polyfill.io writeup (Sansec): https://sansec.io/research/polyfill-supply-chain-attack

### Incident references
- Change Healthcare cyberattack update: https://www.unitedhealthgroup.com/newsroom/2024/2024-04-22-uhg-update-on-change-healthcare-cyberattack.html
- Storm-0558 CSRB review: https://www.cisa.gov/resources-tools/resources/CSRB-Review-Summer-2023-MEO-Intrusion
- CrowdStrike Channel File 291 RCA: https://www.crowdstrike.com/en-us/blog/falcon-content-update-preliminary-post-incident-report/
- Okta HAR file articles: https://sec.okta.com/articles/harfiles/

### Compliance
- EU Cyber Resilience Act (Reg 2024/2847): https://eur-lex.europa.eu/eli/reg/2024/2847/oj
- OMB M-26-05 (rescission): https://www.whitehouse.gov/omb/memoranda/

### Testing tools
- Mozilla Observatory (test your headers): https://observatory.mozilla.org/
- SSL Labs (test your TLS): https://www.ssllabs.com/ssltest/
