---
name: api-hardening
description: API security hardening patterns. Use when implementing rate limiting, input validation, CORS configuration, API key management, request throttling, or protecting endpoints from abuse. Covers defense-in-depth strategies for REST APIs with practical implementations for Express, FastAPI, and serverless, oriented around the OWASP API Security Top 10:2023.
---

# API hardening

Defense-in-depth patterns for protecting APIs from abuse, injection attacks, and data leakage. Recipes are oriented around the OWASP API Security Top 10:2023 and were last verified on 2026-05-08.

## Step 0: Research the current security landscape (do this first)

> Security knowledge ages on a 6-12 month half-life. The recipes below were last verified on 2026-05-08; they may be stale by the time you read this. Before applying any pattern in this skill, fan out research scoped to the API surface or web defense being added so the recipes are interpreted against current authoritative sources, not against this file's snapshot.

### Default-on, with a documented skip

Run the 4-angle research below by default. Skip ONLY when ALL of these hold:

- (a) You ran this same skill on this same primitive within the last 4 hours of the current session,
- (b) That prior research surfaced no urgent advisories for the API surface or web defense being added,
- (c) You log a one-line `Research skipped because <reason>` note in your response.

"I think I know" / "moving fast" / "user wants this done quickly" / "already familiar" are NOT valid skip reasons. The whole point of this preamble is that future-you should not trust this skill body's defaults until current state is checked.

### Fan out 4 subagents in parallel

Each subagent returns ≤300 words of bullets with citations. Dispatch all 4 in a single message so they run concurrently.

**Angle 1 — Authoritative standards.** Have NIST / OWASP / IETF (RFCs and Internet-Drafts) / W3C / CISA published anything new about the API surface or web defense being added in the last 6-12 months? Look for: spec finalizations, deprecations, replacement specs, RFC publications, draft revisions, NIST SP updates, OWASP project version bumps. Cite by document number + publication date.

**Angle 2 — Active exploitation.** What's actively being exploited that targets the API surface or web defense being added? Pull from: CISA Known Exploited Vulnerabilities (KEV) catalog (filter to last 6-12 months), recent CVE / GHSA entries with high CVSS or in-the-wild exploitation, breach postmortems and incident reports (CSRB, vendor RCAs, security-vendor research). Surface CWE patterns dominating recent KEV adds. Cite by CVE number + advisory URL.

**Angle 3 — Tooling and library state.** Are the libraries this skill recommends still current? What are the latest major versions in the relevant package registry (npm / PyPI / RubyGems / crates.io)? Have any been deprecated, replaced, or merged into another project? Have any flipped a secure default? Look up current versions in: registry.npmjs.org, pypi.org, rubygems.org, crates.io, pkg.go.dev. Cite by package + version + release date.

**Angle 4 — Practitioner discourse.** What are practitioners and security teams talking about in the last 6 months? Pull from: OWASP Cheat Sheet Series (last-modified date matters), GitHub Security Lab posts, vendor security blogs (Cloudflare, Fastly, Snyk, Datadog, Wiz, GitGuardian), conference talks (Black Hat, DEF CON, OWASP Global AppSec, USENIX Security), SANS ISC, Krebs, recent OWASP project re-releases. Surface the patterns being adopted and the anti-patterns being called out. Cite by post URL + author + date.

### Synthesize before applying recipes

After the 4 returns land, write a 1-paragraph "current state for the API surface or web defense being added, as of <today's date>" that names:

- The current normative ceiling (what specs say SHOULD be the default in 2026).
- 1-2 active threats specific to the API surface or web defense being added from the last 6-12 months.
- Any tooling drift (deprecated lib, new default in a framework, package merged or replaced).
- Any practitioner consensus shift visible in recent cheat sheet / blog updates.

If the synthesis flags drift in this skill body's recipes (e.g., a spec finalized after 2026-05-08, a library now deprecated, a default flipped), call that out explicitly in your response and override the skill body where they conflict. The synthesis wins. The skill body is scaffolding, not scripture.

### When you cannot run subagents

If subagents are not available in your runtime, the same shape applies in-line: do 4 sequential targeted searches (web search for standards, KEV catalog lookup, package registry version checks, recent cheat-sheet diff). Land the same 1-paragraph synthesis. Cost goes up; the protection does not change.

## OWASP API Security Top 10:2023 mapping

The active edition for API-specific threat modeling is the OWASP API Security Top 10:2023 (https://owasp.org/API-Security/editions/2023/en/0x00-header/). The general OWASP Top 10:2025 (released late 2025, succeeding the 2021 edition) covers web applications more broadly; for an API surface, the 2023 API-specific list is the right framing.

The 2023 categories, and which sections of this skill speak to each:

- **API1:2023 Broken object level authorization** — enforce per-object access checks; covered alongside API key management and per-user rate limiting.
- **API2:2023 Broken authentication** — see the `secure-auth` skill for the auth primitive itself; this skill covers rate limits, request size, and timeout protections that flank auth endpoints.
- **API3:2023 Broken object property level authorization** — input validation (Zod / Pydantic) and explicit allowlist of writable fields.
- **API4:2023 Unrestricted resource consumption** — rate limiting, request size limits, timeout protection, file upload limits.
- **API5:2023 Broken function level authorization** — out of scope here; route-level auth lives in your framework.
- **API6:2023 Unrestricted access to sensitive business flows** — graph-traversal quotas, per-account read budgets, behavioral signals for credential stuffing.
- **API7:2023 Server side request forgery** — outbound URL allowlists; covered briefly under timeout protection and external API calls.
- **API8:2023 Security misconfiguration** — security headers, TLS posture, CORS configuration.
- **API9:2023 Improper inventory management** — out of scope here; an API gateway / catalog problem.
- **API10:2023 Unsafe consumption of APIs** — input validation on data fetched from upstream, plus deserialization safety.

For the broader web context, OWASP Top 10:2025 reorders the 2021 list. Notable shifts: A03:2025 "Software Supply Chain Failures" absorbs the old 2021 A06 "Vulnerable and Outdated Components" — that 2021 category is dissolved into the supply-chain category. A09:2025 is "Security Logging and Alerting Failures" (previously "Logging and Monitoring"). The 2025 ordering: A01 Broken Access Control / A02 Security Misconfiguration / A03 Software Supply Chain Failures / A04 Cryptographic Failures / A05 Injection / A06 Insecure Design / A07 Authentication Failures / A08 Software or Data Integrity Failures / A09 Security Logging and Alerting Failures / A10 Mishandling of Exceptional Conditions.

## Threat exemplars

Real 2023-2024 incidents that anchor the patterns in this skill. Cite these when explaining "why" to stakeholders.

- **Polyfill.io supply-chain attack (2024-06-25).** Funnull acquired the polyfill.io domain in February 2024 and injected malware into roughly 110,000 sites that loaded the script (per https://sansec.io/research/polyfill-supply-chain-attack). Lesson: every third-party `<script>` and `<link rel="stylesheet">` needs a Subresource Integrity hash and a strict CSP; "trusted CDN" is not a guarantee.
- **23andMe credential stuffing (disclosed 2023-10).** Attackers reused leaked credentials against 23andMe accounts, then pivoted via the DNA Relatives feature to enumerate roughly 6.9 million users from a smaller initial-account compromise (per https://blog.23andme.com/articles/addressing-data-security-concerns). Lesson: per-IP rate limits don't catch distributed credential stuffing, and per-account read quotas on graph or relationship endpoints are needed to cap the blast radius.
- **MOVEit Transfer CVE-2023-34362 (disclosed 2023-05-31).** A pre-authentication SQL injection in Progress MOVEit Transfer (per https://nvd.nist.gov/vuln/detail/CVE-2023-34362) was used by Cl0p to exfiltrate data from thousands of organizations, and the chain landed in the CISA KEV catalog. Lesson: parameterized queries are not optional, even on file-transfer paths that don't look like "user-facing APIs."
- **Ivanti Connect Secure zero-day chain (disclosed 2024-01).** CVE-2023-46805 (auth bypass) and CVE-2024-21887 (command injection) chained for unauthenticated remote code execution (per https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-060b). Lesson: command injection (CWE-78) plus auth bypass is the modern unauthenticated-RCE recipe; both halves need defenses.

## Rate limiting

Maps to API4:2023 (unrestricted resource consumption) and API6:2023 (sensitive business flows).

### Why it matters

Without rate limiting:
- Brute force attacks succeed
- APIs get DDoS'd by accident or intent
- One bad actor affects all users
- You get a surprise bill from your cloud provider

Distributed credential stuffing defeats per-IP limits — attackers rotate through residential proxy networks and one IP rarely hits the threshold. Pair per-IP limits with per-account quotas, behavioral signals (impossible-travel, device fingerprint anomalies), and a WAF in front for botnet patterns.

### Express.js with express-rate-limit

Library versions current as of 2026-05-08: `express-rate-limit` and `rate-limit-redis` — verify in registry.npmjs.org before pinning.

```javascript
const rateLimit = require('express-rate-limit');
const RedisStore = require('rate-limit-redis').default;
const { createClient } = require('redis');

const redisClient = createClient({ url: process.env.REDIS_URL });
redisClient.connect();

// General API rate limit
const apiLimiter = rateLimit({
  store: new RedisStore({ sendCommand: (...args) => redisClient.sendCommand(args) }),
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please try again later' },
  skip: (req) => {
    // Skip rate limiting for health checks
    return req.path === '/health';
  }
});

// Strict limit for auth endpoints
const authLimiter = rateLimit({
  store: new RedisStore({ sendCommand: (...args) => redisClient.sendCommand(args) }),
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts
  message: { error: 'Too many login attempts, please try again in 15 minutes' },
  keyGenerator: (req) => {
    // Rate limit by IP + email to prevent distributed attacks
    return `${req.ip}-${req.body?.email || 'unknown'}`;
  }
});

// Very strict limit for password reset
const passwordResetLimiter = rateLimit({
  store: new RedisStore({ sendCommand: (...args) => redisClient.sendCommand(args) }),
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 3, // 3 requests per hour
  message: { error: 'Too many password reset requests' }
});

// Apply limiters
app.use('/api/', apiLimiter);
app.use('/auth/login', authLimiter);
app.use('/auth/forgot-password', passwordResetLimiter);
```

### Sliding window implementation (custom)

```javascript
// Redis-based sliding window rate limiter
class SlidingWindowRateLimiter {
  constructor(redisClient, options = {}) {
    this.redis = redisClient;
    this.windowMs = options.windowMs || 60000; // 1 minute default
    this.maxRequests = options.maxRequests || 100;
    this.keyPrefix = options.keyPrefix || 'ratelimit';
  }

  async isAllowed(identifier) {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    const key = `${this.keyPrefix}:${identifier}`;

    // Remove old entries and count recent ones
    const multi = this.redis.multi();
    multi.zRemRangeByScore(key, 0, windowStart);
    multi.zCard(key);
    multi.zAdd(key, { score: now, value: `${now}-${Math.random()}` });
    multi.expire(key, Math.ceil(this.windowMs / 1000));

    const results = await multi.exec();
    const requestCount = results[1];

    return {
      allowed: requestCount < this.maxRequests,
      remaining: Math.max(0, this.maxRequests - requestCount - 1),
      resetAt: now + this.windowMs
    };
  }
}

// Express middleware
function createRateLimitMiddleware(limiter) {
  return async (req, res, next) => {
    const identifier = req.ip;
    const result = await limiter.isAllowed(identifier);

    res.setHeader('X-RateLimit-Limit', limiter.maxRequests);
    res.setHeader('X-RateLimit-Remaining', result.remaining);
    res.setHeader('X-RateLimit-Reset', result.resetAt);

    if (!result.allowed) {
      return res.status(429).json({ error: 'Rate limit exceeded' });
    }

    next();
  };
}
```

### Per-user rate limiting with API keys

```javascript
// Different limits based on tier
const tierLimits = {
  free: { windowMs: 60000, max: 10 },
  pro: { windowMs: 60000, max: 100 },
  enterprise: { windowMs: 60000, max: 1000 }
};

async function apiKeyRateLimiter(req, res, next) {
  const apiKey = req.headers['x-api-key'];

  if (!apiKey) {
    return res.status(401).json({ error: 'API key required' });
  }

  // Look up API key
  const keyData = await db.query(
    'SELECT user_id, tier, revoked FROM api_keys WHERE key_hash = $1',
    [hashApiKey(apiKey)]
  );

  if (keyData.rows.length === 0 || keyData.rows[0].revoked) {
    return res.status(401).json({ error: 'Invalid API key' });
  }

  const { user_id, tier } = keyData.rows[0];
  const limits = tierLimits[tier] || tierLimits.free;

  // Rate limit by user, not by key (prevents key rotation abuse)
  const limiter = new SlidingWindowRateLimiter(redisClient, {
    ...limits,
    keyPrefix: 'apikey'
  });

  const result = await limiter.isAllowed(user_id);

  res.setHeader('X-RateLimit-Limit', limits.max);
  res.setHeader('X-RateLimit-Remaining', result.remaining);
  res.setHeader('X-RateLimit-Reset', result.resetAt);

  if (!result.allowed) {
    return res.status(429).json({ error: 'Rate limit exceeded' });
  }

  req.userId = user_id;
  next();
}
```

### Per-account graph-traversal quota (23andMe lesson)

Endpoints that expand a relationship or graph one hop at a time (DNA relatives, contact networks, follower fan-out, organization-membership lookups) are the textbook case for per-account quotas in addition to per-IP. A single compromised account inside a per-IP budget can still walk the graph and exfiltrate data on every other connected account, which is what amplified the 23andMe credential-stuffing breach.

```javascript
// Per-account daily budget for graph-expansion endpoints
const graphLimiter = new SlidingWindowRateLimiter(redisClient, {
  windowMs: 24 * 60 * 60 * 1000, // 24 hours
  maxRequests: 500, // tune to product norms
  keyPrefix: 'graph'
});

async function graphTraversalQuota(req, res, next) {
  const result = await graphLimiter.isAllowed(req.userId);
  if (!result.allowed) {
    return res.status(429).json({ error: 'Daily graph quota exceeded' });
  }
  next();
}

app.get('/api/relatives', requireAuth, graphTraversalQuota, listRelatives);
app.get('/api/contacts/expand', requireAuth, graphTraversalQuota, expandContacts);
```

## Input validation

Maps to API3:2023 (broken object property level authorization) and API10:2023 (unsafe consumption of APIs).

### Validation with Zod (TypeScript/JavaScript)

`zod` is on the 4.x line as of 2026-05-08 (4.4.3 current; verify before pinning). Patterns below work on v4; if you're still on 3.x, `safeParse` and the schema builders below are unchanged.

Untrusted input also has a deserialization dimension — see the dedicated section below. CWE-502 (deserialization of untrusted data) dominated the CISA KEV catalog in 2024-2025, so JSON-only at trust boundaries plus schema validation is the baseline.

```javascript
const { z } = require('zod');

// Define schemas
const createUserSchema = z.object({
  email: z.string().email().max(255),
  password: z.string().min(12).max(128),
  name: z.string().min(1).max(100).optional()
});

const updateProfileSchema = z.object({
  name: z.string().min(1).max(100).optional(),
  bio: z.string().max(500).optional(),
  website: z.string().url().optional().or(z.literal(''))
});

const paginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20)
});

// Middleware factory
function validate(schema) {
  return (req, res, next) => {
    const result = schema.safeParse(req.body);

    if (!result.success) {
      return res.status(400).json({
        error: 'Validation failed',
        details: result.error.issues.map(issue => ({
          field: issue.path.join('.'),
          message: issue.message
        }))
      });
    }

    req.validated = result.data;
    next();
  };
}

// Usage
app.post('/users', validate(createUserSchema), async (req, res) => {
  const { email, password, name } = req.validated;
  // Data is validated and typed
});
```

### Sanitization

Trusted Types is a related browser-side defense — it forces dangerous DOM sinks to consume policy-vetted objects instead of strings, which kills entire classes of DOM-based XSS. As of 2026-05-08 Trusted Types is cross-browser (Chromium since 2020, Firefox 148, Safari 26.0; caniuse global usage ~89%), so `require-trusted-types-for 'script'` is now a realistic CSP directive rather than a Chrome-only nice-to-have. See the security headers section.

```javascript
const createDOMPurify = require('dompurify');
const { JSDOM } = require('jsdom');
const validator = require('validator');

const window = new JSDOM('').window;
const DOMPurify = createDOMPurify(window);

// HTML sanitization (when you MUST allow some HTML)
function sanitizeHtml(dirty) {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
    ALLOWED_ATTR: ['href'],
    ALLOW_DATA_ATTR: false
  });
}

// String sanitization
function sanitizeString(str) {
  if (typeof str !== 'string') return '';

  return str
    .trim()
    .slice(0, 10000) // Max length
    .replace(/[\x00-\x1F\x7F]/g, ''); // Remove control characters
}

// SQL-safe identifier (for dynamic column names)
function sanitizeIdentifier(str) {
  // Only allow alphanumeric and underscores
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(str)) {
    throw new Error('Invalid identifier');
  }
  return str;
}

// Filename sanitization
function sanitizeFilename(filename) {
  return filename
    .replace(/[^a-zA-Z0-9._-]/g, '_')
    .replace(/\.{2,}/g, '.')
    .slice(0, 255);
}
```

### Preventing SQL injection

Maps to OWASP Top 10:2025 A05 (injection). MOVEit CVE-2023-34362 is the canonical 2023 example: a pre-auth SQLi in a file-transfer product, weaponized by Cl0p across thousands of organizations (per https://nvd.nist.gov/vuln/detail/CVE-2023-34362). Don't assume "internal" or "non-user-facing" endpoints are safe to skip parameterization on.

```javascript
// BAD: String interpolation
const query = `SELECT * FROM users WHERE id = ${userId}`;

// BAD: String concatenation
const query = 'SELECT * FROM users WHERE id = ' + userId;

// BAD: Template literals with user input
const query = `SELECT * FROM users WHERE name = '${name}'`;

// GOOD: Parameterized queries (PostgreSQL)
const result = await db.query(
  'SELECT * FROM users WHERE id = $1',
  [userId]
);

// GOOD: Parameterized queries (MySQL)
const result = await db.query(
  'SELECT * FROM users WHERE id = ?',
  [userId]
);

// GOOD: Query builders (Knex)
const users = await knex('users')
  .where('id', userId)
  .first();

// GOOD: ORMs (Prisma)
const user = await prisma.user.findUnique({
  where: { id: userId }
});

// When you need dynamic column names (rare)
const allowedColumns = ['name', 'email', 'created_at'];
const sortColumn = allowedColumns.includes(req.query.sort)
  ? req.query.sort
  : 'created_at';

const query = `SELECT * FROM users ORDER BY ${sortColumn}`; // Safe because allowlisted
```

## Command injection (CWE-78)

CWE-78 (OS command injection) dominated the CISA KEV catalog over 2024-2025 — 14 entries in 2024 and 18 in 2025, more than classic SQL injection. The Ivanti Connect Secure chain (CVE-2024-21887) is the marquee example. The rule is simple: never compose a shell command from untrusted input. Use the language's argv-list spawn primitives with the shell disabled, and allowlist any path or filename that flows into a process.

### Node.js

Avoid the shell-execution primitives in the Node child-process module when any argument can be influenced by user input — they pass the full string through `/bin/sh -c` and any metacharacter (`;`, `&`, `|`, backtick, `$()`) becomes injection. Prefer the argv-list spawn family with the shell disabled, which is the default.

```javascript
const { exec, execFile, spawn } = require('child_process');

// DO NOT USE: shell metacharacters in `filename` execute as commands
exec(`convert ${filename} out.png`, (err, stdout) => { /* ... */ });

// DO NOT USE: same problem with execSync
require('child_process').execSync(`convert ${filename} out.png`);

// GOOD: argv-list with the shell disabled (the default for execFile/spawn)
execFile('convert', [filename, 'out.png'], (err, stdout) => { /* ... */ });

// GOOD: spawn with explicit shell:false plus an allowlist on the filename
const safeFilename = /^[A-Za-z0-9_.-]+\.(png|jpg|jpeg)$/.test(filename)
  ? filename
  : null;
if (!safeFilename) throw new Error('Invalid filename');

const child = spawn('convert', [safeFilename, 'out.png'], { shell: false });
```

### Python

Avoid the OS shell-execution primitives — the `os.system` call, `subprocess.run` with `shell=True`, `subprocess.Popen` with `shell=True`, and `os.popen` — when any argument can be influenced by user input. Use `subprocess.run` with an argv list and `shell=False` (the default), and allowlist any filename or path that crosses the trust boundary.

```python
import subprocess
import re
from pathlib import Path

# DO NOT USE: os.system passes the full string through the shell
import os
os.system(f"convert {filename} out.png")

# DO NOT USE: shell=True is the same vulnerability
subprocess.run(f"convert {filename} out.png", shell=True, check=True)

# DO NOT USE: os.popen also goes through the shell
os.popen(f"convert {filename} out.png").read()

# GOOD: argv list, shell disabled (the default), with input allowlisting
if not re.fullmatch(r"[A-Za-z0-9_.-]+\.(png|jpg|jpeg)", filename):
    raise ValueError("Invalid filename")

subprocess.run(
    ["convert", filename, "out.png"],
    check=True,
    shell=False,  # explicit; this is also the default
    timeout=30,
)

# GOOD: when the input is a path, resolve and confirm it's inside an allowed root
allowed_root = Path("/var/app/uploads").resolve()
candidate = (allowed_root / filename).resolve()
if not candidate.is_relative_to(allowed_root):
    raise ValueError("Path traversal attempt")
```

## Deserialization (CWE-502)

CWE-502 (deserialization of untrusted data) was the second-most-common KEV CWE in 2024-2025 — 11 entries in 2024 and 14 in 2025. The native binary serializers and unrestricted YAML loaders treat the input as a program: arbitrary code runs at parse time, before any of your validation logic. The rule is: JSON-only at trust boundaries, and validate the parsed JSON with a schema (Zod / Pydantic) before using it.

### Python

Avoid the native binary deserialization primitive (the `pickle` loaders) and the unsafe YAML loader (the bare `yaml.load` call without `Loader=SafeLoader`) on any input that crosses a trust boundary — both will execute arbitrary objects on parse. The same warning applies to the `marshal` loader.

```python
import json
import pickle
import yaml
from pydantic import BaseModel

# DO NOT USE: pickle.loads on untrusted input executes arbitrary code
obj = pickle.loads(request.body)

# DO NOT USE: yaml.load with no SafeLoader is a code-execution sink
config = yaml.load(request.body)  # equivalent to yaml.Loader

# DO NOT USE: marshal.loads has the same untrusted-input hazard as pickle
import marshal
obj = marshal.loads(request.body)

# GOOD: JSON parsing returns plain data (dict / list / str / number / bool / None)
class CreateUserRequest(BaseModel):
    email: str
    password: str

data = json.loads(request.body)  # safe parse
user = CreateUserRequest.model_validate(data)  # schema-validated

# GOOD: when YAML is genuinely required, use SafeLoader (or yaml.safe_load)
config = yaml.safe_load(request.body)
```

### Node.js / Java / .NET

In Node, the equivalent risk lives in any library that accepts a "this is a serialized object" payload (the `node-serialize` package, older `funcster`-style packages, eval-based JSON5 forks). Stick to `JSON.parse` and validate with Zod.

In Java, avoid the binary deserialization primitive (`ObjectInputStream.readObject`) on untrusted input — Jackson, GSON, or another JSON library is the safe choice. In .NET, avoid the legacy binary formatter (`BinaryFormatter`, `NetDataContractSerializer`, `LosFormatter`, `SoapFormatter`) — Microsoft has flagged it for removal precisely because of CWE-502 (per https://learn.microsoft.com/en-us/dotnet/standard/serialization/binaryformatter-security-guide). Use `System.Text.Json` for cross-trust-boundary input.

```javascript
// DO NOT USE: a third-party deserializer on untrusted input
const obj = require('node-serialize').unserialize(request.body);

// GOOD: JSON.parse + Zod schema validation
const data = JSON.parse(request.body);
const parsed = createUserSchema.safeParse(data);
if (!parsed.success) {
  return res.status(400).json({ error: 'Validation failed' });
}
```

## CORS configuration

Maps to API8:2023 (security misconfiguration).

### Express.js

```javascript
const cors = require('cors');

// Development: Allow localhost
const developmentOrigins = [
  'http://localhost:3000',
  'http://localhost:5173',
  'http://127.0.0.1:3000'
];

// Production: Specific domains only
const productionOrigins = [
  'https://yourapp.com',
  'https://www.yourapp.com',
  'https://app.yourapp.com'
];

const allowedOrigins = process.env.NODE_ENV === 'production'
  ? productionOrigins
  : [...productionOrigins, ...developmentOrigins];

const corsOptions = {
  origin: (origin, callback) => {
    // Allow requests with no origin (mobile apps, curl, etc.)
    if (!origin) {
      return callback(null, true);
    }

    if (allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key'],
  exposedHeaders: ['X-RateLimit-Limit', 'X-RateLimit-Remaining'],
  credentials: true, // Allow cookies
  maxAge: 86400 // Cache preflight for 24 hours
};

app.use(cors(corsOptions));

// Handle CORS errors
app.use((err, req, res, next) => {
  if (err.message === 'Not allowed by CORS') {
    return res.status(403).json({ error: 'CORS not allowed' });
  }
  next(err);
});
```

### Common CORS mistakes

```javascript
// BAD: Allow all origins
app.use(cors()); // Defaults to '*'

// BAD: Allow all origins with credentials
app.use(cors({ origin: '*', credentials: true })); // Browsers will reject this

// BAD: Reflecting Origin header (allows any origin)
app.use(cors({
  origin: (origin, cb) => cb(null, origin) // Never do this
}));

// BAD: Regex that's too permissive
const origin = /yourapp\.com/; // Matches evilyourapp.com too!

// GOOD: Exact match or strict regex
const origin = /^https:\/\/(www\.)?yourapp\.com$/;
```

### Private Network Access (draft)

Private Network Access (PNA) is a WICG draft (https://wicg.github.io/private-network-access/) that adds CORS-style preflight when a public origin tries to reach a private-network resource (LAN IPs, localhost, intranet hostnames). As of 2026-05-08 only Chromium enforces it, and even there enforcement has been gradually rolled back to warnings while the spec evolves. Treat it as a draft: don't rely on PNA as a primary defense, but do plan for the day it lights up everywhere — keep your private-network APIs behind real authentication, not just network position.

## API key management

Maps to API1:2023 (broken object level authorization) when keys scope per-user data, and API2:2023 (broken authentication) for credential lifecycle.

### Secure key generation and storage

```javascript
const crypto = require('crypto');

// Generate API key
function generateApiKey() {
  // Format: prefix_randomBytes
  // Prefix helps identify key type and makes it recognizable
  const prefix = 'sk_live';
  const randomPart = crypto.randomBytes(24).toString('base64url');
  return `${prefix}_${randomPart}`;
}

// Hash for storage (never store plain keys)
function hashApiKey(key) {
  return crypto.createHash('sha256').update(key).digest('hex');
}

// Create new API key
app.post('/api-keys', requireAuth, async (req, res) => {
  const { name } = req.body;

  // Generate key
  const plainKey = generateApiKey();
  const keyHash = hashApiKey(plainKey);

  // Store only the hash
  await db.query(
    `INSERT INTO api_keys (user_id, key_hash, name, created_at)
     VALUES ($1, $2, $3, NOW())`,
    [req.userId, keyHash, name]
  );

  // Return plain key ONCE - user must save it
  res.json({
    key: plainKey,
    message: 'Save this key now. It will not be shown again.'
  });
});

// Verify API key
async function verifyApiKey(key) {
  const keyHash = hashApiKey(key);

  const result = await db.query(
    `SELECT id, user_id, revoked, last_used_at
     FROM api_keys WHERE key_hash = $1`,
    [keyHash]
  );

  if (result.rows.length === 0) {
    return null;
  }

  const keyData = result.rows[0];

  if (keyData.revoked) {
    return null;
  }

  // Update last used timestamp
  await db.query(
    'UPDATE api_keys SET last_used_at = NOW() WHERE id = $1',
    [keyData.id]
  );

  return keyData;
}

// Revoke API key
app.delete('/api-keys/:id', requireAuth, async (req, res) => {
  // Users can only revoke their own keys
  await db.query(
    'UPDATE api_keys SET revoked = true, revoked_at = NOW() WHERE id = $1 AND user_id = $2',
    [req.params.id, req.userId]
  );

  res.json({ success: true });
});
```

### Rotate on a schedule, not just on compromise

Even without a compromise signal, rotate API keys on a schedule (90 days is a common baseline; tighten for high-privilege keys). Long-lived keys collect risk: leaked log lines, stale CI secrets, departed employees, forgotten test scripts. The rotation flow should support overlap — a "next" key live alongside the "current" one for the rotation window — so callers can swap without an outage.

```javascript
// Add columns: rotated_from, rotation_due_at
// On rotation:
// 1. Generate new key
// 2. Insert with rotated_from = old key id, expires_at = old key expiry + window
// 3. Notify the key owner with the new value (out-of-band)
// 4. Mark old key revoked = true at the end of the overlap window

// Background job: flag keys past their rotation_due_at
const stale = await db.query(
  `SELECT id, user_id, name FROM api_keys
   WHERE revoked = false
     AND rotation_due_at < NOW()`
);
// Email each owner; auto-revoke after a grace period.
```

### API key middleware

```javascript
async function apiKeyAuth(req, res, next) {
  // Accept the key from headers ONLY — never query strings.
  // Query strings are routinely logged by web servers, reverse proxies, CDN
  // edge nodes, and analytics tooling, so a key in `?api_key=...` becomes a
  // credential leak by way of access logs. OWASP API Top 10 (API2:2023) and
  // RFC 6750 §2.3 both call this out.
  const apiKey = req.headers['x-api-key']
    || req.headers['authorization']?.replace('Bearer ', '');

  if (!apiKey) {
    return res.status(401).json({
      error: 'API key required',
      hint: 'Pass API key in X-API-Key header'
    });
  }

  const keyData = await verifyApiKey(apiKey);

  if (!keyData) {
    // Don't reveal if key exists but is revoked
    return res.status(401).json({ error: 'Invalid API key' });
  }

  req.apiKeyId = keyData.id;
  req.userId = keyData.user_id;

  next();
}
```

## Request size limits

Maps to API4:2023 (unrestricted resource consumption).

```javascript
const express = require('express');

// Global body size limit
app.use(express.json({ limit: '100kb' }));
app.use(express.urlencoded({ limit: '100kb', extended: true }));

// Per-route limits
app.post('/api/upload', express.json({ limit: '10mb' }), (req, res) => {
  // Handle large upload
});

// File upload limits
const multer = require('multer');
const upload = multer({
  limits: {
    fileSize: 5 * 1024 * 1024, // 5MB
    files: 5 // Max 5 files
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type'));
    }
  }
});

app.post('/upload', upload.single('file'), (req, res) => {
  // Handle upload
});
```

## Response security

Maps to API8:2023 (security misconfiguration).

### Don't leak information

```javascript
// BAD: Leaking stack traces
app.use((err, req, res, next) => {
  res.status(500).json({
    error: err.message,
    stack: err.stack // Never in production!
  });
});

// GOOD: Generic error in production
app.use((err, req, res, next) => {
  console.error(err); // Log full error server-side

  if (process.env.NODE_ENV === 'production') {
    res.status(500).json({ error: 'Internal server error' });
  } else {
    res.status(500).json({ error: err.message, stack: err.stack });
  }
});

// BAD: Revealing database structure
res.status(400).json({
  error: 'duplicate key value violates unique constraint "users_email_key"'
});

// GOOD: User-friendly error
res.status(400).json({
  error: 'An account with this email already exists'
});
```

## Preventing XSS

Maps to OWASP Top 10:2025 A05 (injection). The 2026 shape of XSS defense is, in priority order:

1. **CSP3 with nonce + `'strict-dynamic'`** — modern strict CSP. Allowlists (`script-src https://cdn.foo.com …`) are no longer recommended; per Weichselbaum et al. they're routinely bypassable. Nonce-or-hash plus `'strict-dynamic'` is the W3C-blessed strict CSP.
2. **Trusted Types (`require-trusted-types-for 'script'`)** — kills DOM-based XSS by forcing dangerous sinks (`innerHTML`, `eval`, `setTimeout(string)`) to consume policy-vetted objects. Cross-browser as of 2026 (Chromium since 2020, Firefox 148, Safari 26.0; ~89% global usage per https://caniuse.com/trusted-types).
3. **Framework auto-escaping** — React, Vue, Angular, Svelte, modern template engines all escape interpolated strings by default. Don't reach for the bypass APIs (`dangerouslySetInnerHTML`, `v-html`, `[innerHTML]`, `{@html}`) without DOMPurify.
4. **Manual escaping at the last server-side boundary** — when you genuinely need to inject a value into a non-templated HTML response, use a vetted escaper.

```javascript
// BAD: Directly inserting user content
res.send(`<h1>Hello ${userName}</h1>`);

// GOOD: Use a template engine with auto-escaping
// EJS (auto-escapes by default with <%= %>)
res.render('greeting', { name: userName });

// GOOD: Escape manually when needed
const escapeHtml = require('escape-html');
res.send(`<h1>Hello ${escapeHtml(userName)}</h1>`);

// GOOD: Set Content-Type for JSON responses
res.json({ name: userName }); // Express sets correct headers

// In React/Vue/Angular/Svelte: framework handles escaping by default.
// Don't use dangerouslySetInnerHTML / v-html / [innerHTML] / {@html} on user input.
```

For the `'unsafe-inline'` and inline-script story, see the security headers section — strict CSP3 makes the inline question moot when nonces are wired through the template.

## Security headers

Maps to API8:2023 (security misconfiguration). `helmet` is on the 8.x line as of 2026-05-08 (8.1.0 current; verify before pinning). The 2026 strict-CSP baseline replaces the older "set every X- header" advice.

```javascript
const helmet = require('helmet');
const crypto = require('crypto');

// Per-request CSP nonce middleware (wire this into your template engine)
app.use((req, res, next) => {
  res.locals.cspNonce = crypto.randomBytes(16).toString('base64');
  next();
});

// Strict CSP3: nonce + 'strict-dynamic' + downgrade fallbacks
app.use(helmet.contentSecurityPolicy({
  useDefaults: false,
  directives: {
    defaultSrc: ["'self'"],
    // Strict CSP per https://www.w3.org/TR/CSP3/ and MDN strict-CSP guide.
    // 'strict-dynamic' lets nonced scripts load further scripts;
    // https: + 'unsafe-inline' are downgrade fallbacks for old browsers
    // that ignore 'strict-dynamic' (modern browsers ignore the fallbacks).
    scriptSrc: [
      (req, res) => `'nonce-${res.locals.cspNonce}'`,
      "'strict-dynamic'",
      'https:',
      "'unsafe-inline'"
    ],
    styleSrc: ["'self'", (req, res) => `'nonce-${res.locals.cspNonce}'`],
    imgSrc: ["'self'", 'data:', 'https:'],
    connectSrc: ["'self'", 'https://api.yourapp.com'],
    fontSrc: ["'self'", 'https://fonts.gstatic.com'],
    objectSrc: ["'none'"],
    baseUri: ["'self'"],
    frameAncestors: ["'none'"], // replaces X-Frame-Options
    formAction: ["'self'"],
    upgradeInsecureRequests: [],
    // Trusted Types: kills DOM-based XSS at the sink.
    // Cross-browser as of 2026 per https://caniuse.com/trusted-types
    requireTrustedTypesFor: ["'script'"],
    // Reporting via the Reporting API (W3C WD)
    reportTo: ['default']
  }
}));

// HSTS: 2 years + includeSubDomains + preload (per https://hstspreload.org)
// Operationally irreversible once preload-listed — verify subdomains first.
app.use(helmet.hsts({
  maxAge: 63072000,
  includeSubDomains: true,
  preload: true
}));

// Cross-origin isolation (COOP / COEP / CORP)
// Required for crossOriginIsolated === true (SharedArrayBuffer, high-resolution timers).
// Per WHATWG HTML Origin chapter: https://html.spec.whatwg.org/multipage/origin.html
app.use((req, res, next) => {
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
  res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp'); // or 'credentialless'
  res.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
  next();
});

// Permissions-Policy: structured-fields syntax, opt-out of dangerous features.
// Per https://www.w3.org/TR/permissions-policy/ (W3C WD 2025-10-06; per-directive
// caniuse lookup required — this is "Limited Availability", not Baseline).
app.use((req, res, next) => {
  res.setHeader(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()'
  );
  next();
});

// Reporting API: Reporting-Endpoints + report-to wiring.
// Per https://www.w3.org/TR/reporting-1/
app.use((req, res, next) => {
  res.setHeader(
    'Reporting-Endpoints',
    'default="https://reports.yourapp.com/csp"'
  );
  next();
});

// Keep nosniff
app.use(helmet.noSniff());

// Note: X-XSS-Protection is deprecated and ignored by modern browsers — do not set it.
// X-Frame-Options is replaced by CSP's frame-ancestors directive (set above).
```

When you render HTML, the template needs to read `res.locals.cspNonce` and emit it on every inline `<script>` and `<style>` tag (`<script nonce="<%= cspNonce %>">…`). That's how the strict-dynamic policy decides which scripts to trust.

## Subresource Integrity

Maps to OWASP Top 10:2025 A03 (software supply chain failures). The Polyfill.io 2024 incident is the canonical reason: Funnull bought the polyfill.io domain in February 2024 and injected malware into ~110k sites that loaded the script (per https://sansec.io/research/polyfill-supply-chain-attack). A CSP `'strict-dynamic'` policy would have blocked the unauthorized script-loaded-by-script chain; an SRI hash would have failed the load even if the policy permitted it.

Every third-party `<script src>` and `<link rel="stylesheet">` SHOULD carry an `integrity` attribute. SRI is a W3C Recommendation (https://www.w3.org/TR/SRI/).

```html
<script
  src="https://cdn.example.com/lib.min.js"
  integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
  crossorigin="anonymous"></script>

<link
  rel="stylesheet"
  href="https://cdn.example.com/lib.min.css"
  integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh"
  crossorigin="anonymous">
```

Generate an SRI hash from a fetched asset:

```bash
curl -fsSL https://cdn.example.com/lib.min.js \
  | openssl dgst -sha384 -binary \
  | openssl base64 -A
```

cdnjs and jsdelivr include `integrity` attributes in their copy-paste snippets; unpkg has an "SRI-on" mode. Use them. Pin to a specific version, never `@latest`.

## TLS posture

Maps to OWASP Top 10:2025 A04 (cryptographic failures) and API8:2023 (security misconfiguration).

- **Default to TLS 1.3** — RFC 8446 (https://datatracker.ietf.org/doc/rfc8446/), published August 2018.
- **Minimum TLS 1.2** — older versions are deprecated.
- **Disable TLS 1.0 and TLS 1.1** — RFC 8996 / BCP 195 (https://datatracker.ietf.org/doc/rfc8996/), March 2021, formally deprecates both.
- **SSL Labs caps non-TLS-1.3 servers at A-** since v2009r (16 May 2025). If you want an A or A+ grade, TLS 1.3 has to be available.
- **Direction of travel: post-quantum hybrid key exchange.** Cloudflare reported that more than half of its HTTPS traffic in late 2025 negotiated post-quantum hybrid key exchange (X25519+Kyber / X25519MLKEM768). This is moving fast; check your CDN / load balancer for current support.

If you operate behind a managed edge (Cloudflare, Fastly, AWS CloudFront, Azure Front Door), the right knob is usually a single "minimum TLS version" setting — set it to 1.2 at minimum, prefer 1.3, and let the edge handle the cipher suite negotiation. If you terminate TLS yourself, consult the Mozilla SSL Configuration Generator (https://ssl-config.mozilla.org/) for current "intermediate" or "modern" profiles.

## Timeout protection

Maps to API4:2023 (unrestricted resource consumption) and API7:2023 (server side request forgery — pair timeouts with outbound URL allowlists).

```javascript
// Request timeout middleware
function timeout(ms) {
  return (req, res, next) => {
    res.setTimeout(ms, () => {
      res.status(408).json({ error: 'Request timeout' });
    });
    next();
  };
}

app.use(timeout(30000)); // 30 second default

// External API call timeout
async function fetchWithTimeout(url, options = {}, timeoutMs = 5000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

// Database query timeout
const result = await db.query({
  text: 'SELECT * FROM large_table WHERE condition = $1',
  values: [value],
  timeout: 5000 // 5 second query timeout
});
```

## FastAPI (Python) equivalents

Library versions current as of 2026-05-08 (verify on PyPI before pinning):

- `fastapi` is on the 0.x line (0.136.1 current; pre-1.0, so pin by minor — breaking changes can land between minors).
- `slowapi` is on the 0.1.x line (pre-1.0; pin by minor).
- `pydantic` is on the 2.x line (2.13.4 current).

```python
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, EmailStr, Field
import hashlib
import secrets

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    # Handle login
    pass

# Input validation with Pydantic 2.x
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    name: str = Field(max_length=100, default=None)

@app.post("/users")
async def create_user(user: CreateUserRequest):
    # Data is already validated
    pass

# API key generation
def generate_api_key() -> str:
    return f"sk_live_{secrets.token_urlsafe(24)}"

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
```

## Security checklist for APIs

Organized by OWASP API Security Top 10:2023 category. Skip categories that don't apply (API5 / API9 are out of scope here).

### API1:2023 Broken object level authorization
- [ ] Per-object access checks on every fetch / update / delete
- [ ] API keys scoped to a user, not shared across tenants
- [ ] Object IDs aren't predictable or enumerable when that matters

### API2:2023 Broken authentication
- [ ] Auth endpoints have stricter rate limits than general API endpoints
- [ ] Password reset endpoints have very strict per-account limits
- [ ] All auth flows over HTTPS only
- [ ] See the `secure-auth` skill for the auth primitive itself

### API3:2023 Broken object property level authorization
- [ ] Input validated against a schema (Zod / Pydantic)
- [ ] Writable fields are explicitly allowlisted, not "everything in the body"
- [ ] Mass-assignment paths (`Object.assign`, `model.update(req.body)`) avoided

### API4:2023 Unrestricted resource consumption
- [ ] Rate limiting on all endpoints
- [ ] Request body size limits configured
- [ ] File upload size and count limits configured
- [ ] Timeouts on all DB queries and external calls
- [ ] Pagination caps on list endpoints

### API6:2023 Unrestricted access to sensitive business flows
- [ ] Per-account quotas on graph / relationship / fan-out endpoints (23andMe lesson)
- [ ] Behavioral signals (impossible-travel, device fingerprint) for credential-stuffing-prone endpoints
- [ ] WAF or bot management in front for distributed abuse patterns

### API7:2023 Server side request forgery
- [ ] Outbound HTTP calls go to allowlisted hosts only
- [ ] Timeouts on every outbound call
- [ ] Cloud metadata endpoints blocked at the network layer

### API8:2023 Security misconfiguration
- [ ] Strict CSP3: nonce + `'strict-dynamic'` + Trusted Types
- [ ] HSTS with `max-age=63072000; includeSubDomains; preload`
- [ ] COOP / COEP / CORP set
- [ ] Permissions-Policy restricting dangerous features
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-XSS-Protection` NOT set (deprecated)
- [ ] `X-Frame-Options` replaced by CSP `frame-ancestors`
- [ ] CORS configured to specific origins, never `*` with credentials
- [ ] TLS 1.3 default, TLS 1.2 minimum, TLS 1.0/1.1 disabled
- [ ] SRI hashes on every third-party `<script>` and `<link rel="stylesheet">`
- [ ] Error messages don't leak system info or DB structure

### API10:2023 Unsafe consumption of APIs
- [ ] Upstream responses validated with the same rigor as user input
- [ ] No native binary deserializers or unrestricted YAML loaders on cross-trust-boundary input
- [ ] No shell-execution primitives composed from upstream-controlled values

### Cross-cutting
- [ ] API keys hashed before storage; rotation on a schedule, not just on compromise
- [ ] API versioning for breaking changes
