---
name: secure-auth
description: Secure authentication implementation patterns. Use when implementing user login, registration, password reset, session management, JWT authentication, OAuth, MFA, or passkeys. Provides production-ready patterns aligned with NIST SP 800-63B-4, OWASP 2026 cheat sheets, OAuth 2.1, and WebAuthn L3, with breach-driven lessons.
---

# Secure authentication

## Step 0: Research the current security landscape (do this first)

> Security knowledge ages on a 6-12 month half-life. The recipes below were last verified on 2026-05-08; they may be stale by the time you read this. Before applying any pattern in this skill, fan out research scoped to the authentication primitive being implemented (passwords, sessions, JWT, OAuth, MFA, passkeys) so the recipes are interpreted against current authoritative sources, not against this file's snapshot.

### Default-on, with a documented skip

Run the 4-angle research below by default. Skip ONLY when ALL of these hold:

- (a) You ran this same skill on this same primitive within the last 4 hours of the current session,
- (b) That prior research surfaced no urgent advisories for the authentication primitive being implemented (passwords, sessions, JWT, OAuth, MFA, passkeys),
- (c) You log a one-line `Research skipped because <reason>` note in your response.

"I think I know" / "moving fast" / "user wants this done quickly" / "already familiar" are NOT valid skip reasons. The whole point of this preamble is that future-you should not trust this skill body's defaults until current state is checked.

### Fan out 4 subagents in parallel

Each subagent returns at most 300 words of bullets with citations. Dispatch all 4 in a single message so they run concurrently.

**Angle 1 — Authoritative standards.** Have NIST / OWASP / IETF (RFCs and Internet-Drafts) / W3C / CISA published anything new about the authentication primitive being implemented (passwords, sessions, JWT, OAuth, MFA, passkeys) in the last 6-12 months? Look for: spec finalizations, deprecations, replacement specs, RFC publications, draft revisions, NIST SP updates, OWASP project version bumps. Cite by document number plus publication date.

**Angle 2 — Active exploitation.** What's actively being exploited that targets the authentication primitive being implemented (passwords, sessions, JWT, OAuth, MFA, passkeys)? Pull from: CISA Known Exploited Vulnerabilities (KEV) catalog (filter to last 6-12 months), recent CVE / GHSA entries with high CVSS or in-the-wild exploitation, breach postmortems and incident reports (CSRB, vendor RCAs, security-vendor research). Surface CWE patterns dominating recent KEV adds. Cite by CVE number plus advisory URL.

**Angle 3 — Tooling and library state.** Are the libraries this skill recommends still current? What are the latest major versions in the relevant package registry (npm / PyPI / RubyGems / crates.io)? Have any been deprecated, replaced, or merged into another project? Have any flipped a secure default? Look up current versions in: registry.npmjs.org, pypi.org, rubygems.org, crates.io, pkg.go.dev. Cite by package plus version plus release date.

**Angle 4 — Practitioner discourse.** What are practitioners and security teams talking about in the last 6 months? Pull from: OWASP Cheat Sheet Series (last-modified date matters), GitHub Security Lab posts, vendor security blogs (Cloudflare, Fastly, Snyk, Datadog, Wiz, GitGuardian), conference talks (Black Hat, DEF CON, OWASP Global AppSec, USENIX Security), SANS ISC, Krebs, recent OWASP project re-releases. Surface the patterns being adopted and the anti-patterns being called out. Cite by post URL plus author plus date.

### Synthesize before applying recipes

After the 4 returns land, write a 1-paragraph "current state for the authentication primitive being implemented (passwords, sessions, JWT, OAuth, MFA, passkeys), as of <today's date>" that names:

- The current normative ceiling (what specs say SHOULD be the default in 2026).
- 1-2 active threats specific to the authentication primitive being implemented (passwords, sessions, JWT, OAuth, MFA, passkeys) from the last 6-12 months.
- Any tooling drift (deprecated lib, new default in a framework, package merged or replaced).
- Any practitioner consensus shift visible in recent cheat sheet / blog updates.

If the synthesis flags drift in this skill body's recipes (e.g., a spec finalized after 2026-05-08, a library now deprecated, a default flipped), call that out explicitly in your response and override the skill body where they conflict. The synthesis wins. The skill body is scaffolding, not scripture.

### When you cannot run subagents

If subagents are not available in your runtime, the same shape applies in-line: do 4 sequential targeted searches (web search for standards, KEV catalog lookup, package registry version checks, recent cheat-sheet diff). Land the same 1-paragraph synthesis. Cost goes up; the protection does not change.

---

Production-ready authentication patterns. These aren't the simplest implementations — they're the ones that won't get you sued.

## Authentication architecture decision

The 2020-era "session vs JWT" frame is no longer the only axis. In 2026 the question is closer to "passkey plus short-lived bound tokens" vs "session cookie." Pick by deployment shape, not by what a tutorial used.

### Sessions

Use sessions when:
- Server-rendered application
- Need immediate logout / revocation
- Single domain
- Simpler to implement correctly

### JWTs (with refresh tokens)

Use JWTs when:
- Multiple services need to verify auth
- Stateless verification preferred (with revocation strategy)
- Mobile app plus API
- Third-party integrations
- High-value APIs benefit from sender-constrained tokens (DPoP per RFC 9449, mTLS per RFC 8705)

### Passkeys-first

Use passkeys (WebAuthn / FIDO2) as the primary factor when:
- The user agent supports WebAuthn (every current Chromium, Firefox, Safari, and major mobile browser does)
- You can run alongside passwords during transition (offer passkey enrollment after first login, keep password as fallback while user installs)
- Phishing resistance is required (NIST AAL3, government, financial, medical)

The passkey-first stance reflects 2026 consensus: WebAuthn L3 reached W3C Candidate Recommendation Snapshot 2026-01-13 (https://www.w3.org/TR/webauthn-3/) and CTAP 2.3 became a FIDO Alliance Proposed Standard 2026-02-26. See the Passkeys / WebAuthn section below.

**Common mistake:** Using JWTs because a tutorial did, then storing them in localStorage (XSS-vulnerable) and having no revocation strategy. Refresh-token reuse detection and full token validation (issuer, audience, scope, signing-key tenancy) are non-optional in 2026 — see the Storm-0558 lesson.

## Password storage

The single source of truth for password hashing across this skill. The Session and JWT examples below assume these defaults.

### Default: argon2id

OWASP Password Storage Cheat Sheet (last updated 2026-05-07, https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) lists any of 5 equivalent argon2id profiles. Pick whichever fits your server's memory budget; they're calibrated to similar work factors:

- m=47104 KiB (46 MiB), t=1, p=1
- m=19456 KiB (19 MiB), t=2, p=1
- m=12288 KiB (12 MiB), t=3, p=1
- m=9216 KiB (9 MiB), t=4, p=1
- m=7168 KiB (7 MiB), t=5, p=1

```javascript
// Node — argon2 package (current 0.44.0; pre-1.0, pin by minor)
const argon2 = require('argon2');

const hash = await argon2.hash(password, {
  type: argon2.argon2id,
  memoryCost: 19456, // KiB — one of the 5 OWASP-equivalent profiles
  timeCost: 2,
  parallelism: 1
});

// Verify
const valid = await argon2.verify(hash, password);
```

```python
# Python — argon2-cffi
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(
    memory_cost=19456,  # KiB
    time_cost=2,
    parallelism=1,
)

hashed = ph.hash(password)

try:
    ph.verify(hashed, password)
except VerifyMismatchError:
    # invalid password
    pass
```

RFC 9106 (https://datatracker.ietf.org/doc/rfc9106/) defines a more aggressive "FIRST RECOMMENDED" profile (t=1, p=4, m=2 GiB) intended for server environments with that memory available; OWASP's 5 profiles are the practical floor.

### Alternate: bcrypt

Still acceptable. OWASP says cost 10 minimum, "as large as performance allows." The current code uses cost 12, which is fine — just know the floor moved.

```javascript
// Node — bcrypt (current 6.0.0)
const bcrypt = require('bcrypt');

// bcrypt has a 72-byte input limit. Pre-hash with SHA-256
// when accepting longer passphrases, OR reject inputs over 72 bytes.
const crypto = require('crypto');

function safeBcryptInput(password) {
  const bytes = Buffer.byteLength(password, 'utf8');
  if (bytes > 72) {
    // Pre-hash to a fixed 32-byte digest, base64-encoded (44 ASCII bytes)
    return crypto.createHash('sha256').update(password).digest('base64');
  }
  return password;
}

const hashed = await bcrypt.hash(safeBcryptInput(password), 12);
const ok = await bcrypt.compare(safeBcryptInput(password), hashed);
```

### Alternate: scrypt

Acceptable. OWASP minimum is N=2^17, r=8, p=1.

### PBKDF2: only when FIPS-140 required

PBKDF2 is the algorithm to use when FIPS-140 compliance is a hard requirement. Otherwise prefer argon2id. OWASP minimum: 600,000 iterations of PBKDF2-HMAC-SHA256, or 210,000 of PBKDF2-HMAC-SHA512.

### Never

- The OS shell-execution primitive composing a password into a command line — pass via stdin or argv.
- Plain-text storage. No exceptions, no "just for now," no "we'll fix it before launch."
- Logging the plain-text password in any code path, including error handlers.
- A custom hashing scheme. Roll-your-own is the most common breach precondition.

## Password policy (NIST SP 800-63B-4)

NIST SP 800-63B-4 went FINAL 2025-07-31 (https://csrc.nist.gov/pubs/sp/800/63/b/4/final). The old 800-63B was withdrawn 2025-08-01. The values below are normative. Don't deviate.

### Length

- Single-factor passwords: **15-character minimum**.
- Multi-factor passwords (one factor among several): 8-character minimum.
- Maximum: at least **64 characters** (verifier MUST allow up to 64; it MAY allow longer).

### Composition

- **No composition rules.** NIST 800-63B-4 §5.1.1 explicitly: "Verifiers and CSPs SHALL NOT impose other composition rules" (no "must contain uppercase / digit / symbol").
- **Allow Unicode.** Each Unicode code point counts as one character.
- **Allow paste.** Password managers depend on it.

### Rotation

- **No periodic rotation.** Don't force "change every 90 days." Rotate only on evidence of compromise.

### Blocklist (mandatory in 2026)

The verifier MUST check candidate passwords against a list of known-compromised values. Use the HaveIBeenPwned k-anonymity API (https://haveibeenpwned.com/API/v3#PwnedPasswords) — you submit the first 5 chars of a SHA-1 hash, get back the suffixes that match, never send the password itself.

```javascript
// Check candidate password against HIBP
const crypto = require('crypto');

async function isPwned(password) {
  const sha1 = crypto.createHash('sha1').update(password).digest('hex').toUpperCase();
  const prefix = sha1.slice(0, 5);
  const suffix = sha1.slice(5);

  const res = await fetch(`https://api.pwnedpasswords.com/range/${prefix}`, {
    headers: { 'Add-Padding': 'true' }
  });
  if (!res.ok) {
    // Fail closed on availability blip? Up to your threat model.
    // Default: don't block registration if HIBP is down; log and proceed.
    return false;
  }
  const body = await res.text();
  return body.split('\n').some(line => line.startsWith(suffix));
}
```

### Phishing resistance

NIST 800-63B-4 REQUIRES phishing resistance at AAL3. Passwords alone never reach AAL3. AAL2 with phishing resistance is what most consumer apps should target now — that means WebAuthn (passkey) or PIV/CAC, not TOTP and not SMS.

## Session-based authentication

### Complete Express.js implementation

```javascript
const express = require('express');
const session = require('express-session');
const RedisStore = require('connect-redis').default;
const { createClient } = require('redis');
const argon2 = require('argon2');
const crypto = require('crypto');

const app = express();

// Redis client for session storage
const redisClient = createClient({ url: process.env.REDIS_URL });
redisClient.connect();

// Session configuration
app.use(session({
  store: new RedisStore({ client: redisClient }),
  secret: process.env.SESSION_SECRET, // At least 32 random bytes
  name: 'sessionId', // Don't use default 'connect.sid'
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production', // HTTPS only in prod
    httpOnly: true,  // Not accessible via JavaScript
    sameSite: 'lax', // CSRF protection
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Rate limiting for auth endpoints
const loginAttempts = new Map();

function checkRateLimit(ip) {
  const attempts = loginAttempts.get(ip) || { count: 0, resetAt: Date.now() + 900000 };

  if (Date.now() > attempts.resetAt) {
    attempts.count = 0;
    attempts.resetAt = Date.now() + 900000; // 15 minute window
  }

  if (attempts.count >= 5) {
    return false;
  }

  attempts.count++;
  loginAttempts.set(ip, attempts);
  return true;
}

// Argon2id parameters — one of the 5 OWASP-equivalent profiles
const ARGON2_OPTS = {
  type: argon2.argon2id,
  memoryCost: 19456, // KiB
  timeCost: 2,
  parallelism: 1
};

// Precompute a real argon2id hash for the user-not-found timing-attack defense.
// Must be a valid hash string at the same parameters used for storage so that
// argon2.verify does the full work — a malformed string would short-circuit at
// parse time and reintroduce the timing channel.
let DUMMY_VERIFY_HASH = null;
(async () => {
  DUMMY_VERIFY_HASH = await argon2.hash('argon2-timing-defense-init', ARGON2_OPTS);
})();

// Registration
app.post('/auth/register', async (req, res) => {
  const { email, password } = req.body;

  // Validate input
  if (!email || !password) {
    return res.status(400).json({ error: 'Email and password required' });
  }

  // NIST 800-63B-4: 15-char minimum for single-factor passwords
  if (password.length < 15) {
    return res.status(400).json({ error: 'Password must be at least 15 characters' });
  }

  // Reject up-front pwned passwords (HIBP k-anonymity)
  if (await isPwned(password)) {
    return res.status(400).json({ error: 'This password has appeared in a known breach. Choose a different one.' });
  }

  // Check if user exists
  const existingUser = await db.query(
    'SELECT id FROM users WHERE email = $1',
    [email.toLowerCase()]
  );

  if (existingUser.rows.length > 0) {
    // Don't reveal if email exists - use same message/timing
    return res.status(400).json({ error: 'Registration failed' });
  }

  // Hash password
  const hashedPassword = await argon2.hash(password, ARGON2_OPTS);

  // Create user
  const result = await db.query(
    'INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id',
    [email.toLowerCase(), hashedPassword]
  );

  // Create session
  req.session.userId = result.rows[0].id;
  req.session.createdAt = Date.now();

  res.json({ success: true });
});

// Login
app.post('/auth/login', async (req, res) => {
  const { email, password } = req.body;
  const clientIp = req.ip;

  // Rate limiting
  if (!checkRateLimit(clientIp)) {
    return res.status(429).json({ error: 'Too many attempts. Try again later.' });
  }

  // Validate input
  if (!email || !password) {
    return res.status(400).json({ error: 'Email and password required' });
  }

  // Find user
  const result = await db.query(
    'SELECT id, password_hash FROM users WHERE email = $1',
    [email.toLowerCase()]
  );

  if (result.rows.length === 0) {
    // Timing attack prevention: full-cost verify against a real precomputed hash.
    // A malformed hash string would make argon2.verify fail at parse time —
    // that's faster than the valid-user path and leaks "user not found" via
    // timing. DUMMY_VERIFY_HASH is computed once at module init below so
    // this path does the same work as the real verify.
    if (DUMMY_VERIFY_HASH) {
      await argon2.verify(DUMMY_VERIFY_HASH, password).catch(() => false);
    }
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  const user = result.rows[0];

  // Verify password
  const isValid = await argon2.verify(user.password_hash, password).catch(() => false);

  if (!isValid) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Regenerate session to prevent fixation.
  // Also regenerate on privilege CHANGE (e.g. role escalation, MFA upgrade), not just login.
  req.session.regenerate((err) => {
    if (err) {
      return res.status(500).json({ error: 'Session error' });
    }

    req.session.userId = user.id;
    req.session.createdAt = Date.now();

    // Clear rate limit on successful login
    loginAttempts.delete(clientIp);

    res.json({ success: true });
  });
});

// Logout
app.post('/auth/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).json({ error: 'Logout failed' });
    }
    res.clearCookie('sessionId');
    res.json({ success: true });
  });
});

// Auth middleware
function requireAuth(req, res, next) {
  if (!req.session.userId) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  // Optional: Check session age
  const maxAge = 24 * 60 * 60 * 1000; // 24 hours
  if (Date.now() - req.session.createdAt > maxAge) {
    req.session.destroy();
    return res.status(401).json({ error: 'Session expired' });
  }

  next();
}

// Protected route
app.get('/api/profile', requireAuth, async (req, res) => {
  const user = await db.query(
    'SELECT id, email, created_at FROM users WHERE id = $1',
    [req.session.userId]
  );
  res.json(user.rows[0]);
});
```

## JWT authentication

### Full token validation: the Storm-0558 lesson

Microsoft's Storm-0558 incident (CSRB review, https://www.cisa.gov/resources-tools/resources/CSRB-Review-Summer-2023-MEO-Intrusion) traced to OWA accepting a consumer-key-signed token for enterprise mailboxes — the token-validation library skipped the issuer / audience / scope / signing-key-tenancy checks. Validate every claim every time:

- `iss` (issuer) — MUST match your expected issuer string
- `aud` (audience) — MUST include your service identifier
- `exp`, `nbf` (expiration / not-before) — MUST be enforced; reject expired or future-dated tokens
- `scope` — MUST contain the scope required for the endpoint
- Signing key — MUST belong to the issuer's tenancy, not "any key the JWKS endpoint hands out"

### Complete implementation with refresh tokens

```javascript
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

// Token configuration
const ACCESS_TOKEN_SECRET = process.env.ACCESS_TOKEN_SECRET;
const REFRESH_TOKEN_SECRET = process.env.REFRESH_TOKEN_SECRET;
const ACCESS_TOKEN_EXPIRY = '15m';
const REFRESH_TOKEN_EXPIRY = '7d';
const ISSUER = 'https://auth.yourapp.com';
const AUDIENCE = 'https://api.yourapp.com';

// Store refresh tokens (use Redis in production).
// Each entry tracks the family chain so reuse can revoke siblings.
const refreshTokens = new Map();

function generateAccessToken(userId, scopes = []) {
  return jwt.sign(
    { userId, scope: scopes.join(' '), type: 'access' },
    ACCESS_TOKEN_SECRET,
    {
      expiresIn: ACCESS_TOKEN_EXPIRY,
      issuer: ISSUER,
      audience: AUDIENCE
    }
  );
}

function generateRefreshToken(userId, familyId = null) {
  const tokenId = crypto.randomBytes(32).toString('hex');
  const family = familyId || crypto.randomBytes(16).toString('hex');
  const token = jwt.sign(
    { userId, tokenId, familyId: family, type: 'refresh' },
    REFRESH_TOKEN_SECRET,
    {
      expiresIn: REFRESH_TOKEN_EXPIRY,
      issuer: ISSUER,
      audience: AUDIENCE
    }
  );

  refreshTokens.set(tokenId, {
    userId,
    familyId: family,
    createdAt: Date.now(),
    used: false,
    revoked: false
  });

  return { token, familyId: family };
}

// Revoke an entire refresh-token family (used on reuse detection).
function revokeFamily(familyId) {
  for (const [id, entry] of refreshTokens) {
    if (entry.familyId === familyId) {
      entry.revoked = true;
    }
  }
}

// Login - returns both tokens
app.post('/auth/login', async (req, res) => {
  const { email, password } = req.body;

  // ... validation and password check ...

  const accessToken = generateAccessToken(user.id, ['read', 'write']);
  const { token: refreshToken } = generateRefreshToken(user.id);

  // Set refresh token as httpOnly cookie
  res.cookie('refreshToken', refreshToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
  });

  // Return access token in response body
  res.json({ accessToken });
});

// Refresh endpoint with rotation + reuse detection
app.post('/auth/refresh', (req, res) => {
  const refreshToken = req.cookies.refreshToken;

  if (!refreshToken) {
    return res.status(401).json({ error: 'Refresh token required' });
  }

  let decoded;
  try {
    decoded = jwt.verify(refreshToken, REFRESH_TOKEN_SECRET, {
      issuer: ISSUER,
      audience: AUDIENCE
    });
  } catch (err) {
    return res.status(401).json({ error: 'Invalid refresh token' });
  }

  const stored = refreshTokens.get(decoded.tokenId);
  if (!stored || stored.revoked) {
    return res.status(401).json({ error: 'Token revoked' });
  }

  // REUSE DETECTION: if a previously-rotated refresh token is presented,
  // the family is compromised. Revoke every sibling immediately.
  if (stored.used) {
    revokeFamily(decoded.familyId);
    return res.status(401).json({ error: 'Token reuse detected; family revoked' });
  }

  stored.used = true;

  // Rotate: issue a new access + refresh in the same family.
  const newAccess = generateAccessToken(decoded.userId, ['read', 'write']);
  const { token: newRefresh } = generateRefreshToken(decoded.userId, decoded.familyId);

  res.cookie('refreshToken', newRefresh, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    maxAge: 7 * 24 * 60 * 60 * 1000
  });

  res.json({ accessToken: newAccess });
});

// Logout - revoke entire refresh-token family
app.post('/auth/logout', (req, res) => {
  const refreshToken = req.cookies.refreshToken;

  if (refreshToken) {
    try {
      const decoded = jwt.verify(refreshToken, REFRESH_TOKEN_SECRET, {
        issuer: ISSUER,
        audience: AUDIENCE
      });
      revokeFamily(decoded.familyId);
    } catch (err) {
      // Token invalid, no action needed
    }
  }

  res.clearCookie('refreshToken');
  res.json({ success: true });
});

// Auth middleware for protected routes.
//
// Scope of THIS sample: single-issuer private-token deployments using HS256
// (shared secret). It enforces iss / aud / exp / scope / pinned algorithm —
// the claim-level half of the Storm-0558 lesson.
//
// What this sample does NOT cover and you MUST add for multi-issuer / OIDC
// (Azure AD / Auth0 / Cognito / etc.): the signing-key tenancy half. There:
// 1. Use a public-key algorithm (RS256, ES256, EdDSA) — not HS256.
// 2. Resolve the issuer's JWKS at the issuer's well-known URL.
// 3. Pin which JWKS each trusted issuer is allowed to use, and reject any
//    token whose iss does not match the JWKS that signed it. Storm-0558's
//    proximate failure was OWA accepting a consumer-tenant key for an
//    enterprise-tenant token because the verifier did NOT enforce this
//    issuer-to-key-set binding.
// 4. Select the verifying key by the JWT's `kid` — but only from within
//    the pinned key set for that issuer.
function requireAuth(requiredScope) {
  return function (req, res, next) {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Access token required' });
    }

    const token = authHeader.substring(7);

    let decoded;
    try {
      decoded = jwt.verify(token, ACCESS_TOKEN_SECRET, {
        issuer: ISSUER,
        audience: AUDIENCE,
        algorithms: ['HS256'] // pin algorithm; reject 'none' and unexpected algs
      });
    } catch (err) {
      if (err.name === 'TokenExpiredError') {
        return res.status(401).json({ error: 'Token expired', code: 'TOKEN_EXPIRED' });
      }
      return res.status(401).json({ error: 'Invalid token' });
    }

    if (decoded.type !== 'access') {
      return res.status(401).json({ error: 'Invalid token type' });
    }

    if (requiredScope) {
      const scopes = (decoded.scope || '').split(' ');
      if (!scopes.includes(requiredScope)) {
        return res.status(403).json({ error: 'Insufficient scope' });
      }
    }

    req.userId = decoded.userId;
    req.scopes = (decoded.scope || '').split(' ');
    next();
  };
}

// Usage: app.get('/api/admin', requireAuth('admin'), handler)
```

### Bound tokens for high-value APIs

Bearer tokens are stealable. For payments, healthcare, government, or any context where token theft is catastrophic, use sender-constrained tokens:

- **DPoP (RFC 9449, https://datatracker.ietf.org/doc/rfc9449/)** — client signs each request with a private key; the access token is bound to the public-key thumbprint (`cnf.jkt` claim). Token alone is useless without the key.
- **mTLS (RFC 8705, https://datatracker.ietf.org/doc/rfc8705/)** — token bound to the client certificate used in the TLS handshake (`cnf.x5t#S256` claim).

Both make stolen tokens worthless to the attacker.

### Frontend token handling

```javascript
// auth.js - Frontend token management

class AuthManager {
  constructor() {
    this.accessToken = null;
  }

  async login(email, password) {
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Important for cookies
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const { accessToken } = await response.json();
    this.accessToken = accessToken;

    return true;
  }

  async refreshToken() {
    const response = await fetch('/auth/refresh', {
      method: 'POST',
      credentials: 'include'
    });

    if (!response.ok) {
      this.accessToken = null;
      throw new Error('Session expired');
    }

    const { accessToken } = await response.json();
    this.accessToken = accessToken;

    return accessToken;
  }

  async fetchWithAuth(url, options = {}) {
    if (!this.accessToken) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${this.accessToken}`
      }
    });

    // If token expired, try to refresh and retry
    if (response.status === 401) {
      const body = await response.json();

      if (body.code === 'TOKEN_EXPIRED') {
        await this.refreshToken();

        // Retry original request
        return fetch(url, {
          ...options,
          headers: {
            ...options.headers,
            'Authorization': `Bearer ${this.accessToken}`
          }
        });
      }
    }

    return response;
  }

  async logout() {
    await fetch('/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });

    this.accessToken = null;
  }
}

export const auth = new AuthManager();
```

Don't store access tokens in `localStorage` — they're readable by any XSS payload. In-memory (as above) plus an httpOnly refresh cookie is the standard shape. For SPAs that need to survive a page refresh, use the BroadcastChannel API to share the in-memory token across tabs and accept that a hard refresh forces a `/auth/refresh` call.

## Passkeys / WebAuthn

WebAuthn L3 is at W3C Candidate Recommendation Snapshot as of 2026-01-13 (https://www.w3.org/TR/webauthn-3/). Comments accepted through 2026-02-10. CTAP 2.3 became a FIDO Alliance Proposed Standard 2026-02-26.

Recommended libraries:

- **Node:** `@simplewebauthn/server` (current 13.3.0). Companion browser package: `@simplewebauthn/browser`.
- **Python:** `webauthn` on PyPI (current 2.7.1). Note: the GitHub repo is `duo-labs/py_webauthn`, but the install command is `pip install webauthn` — the PyPI package name is `webauthn`, NOT `py_webauthn`.

### Registration ceremony

```javascript
// Node — @simplewebauthn/server
const {
  generateRegistrationOptions,
  verifyRegistrationResponse,
} = require('@simplewebauthn/server');

const RP_ID = 'yourapp.com';                  // your effective domain
const RP_NAME = 'YourApp';
const ORIGIN = 'https://yourapp.com';

// 1. Server: build options for the browser
app.post('/auth/passkey/register/options', requireAuth(), async (req, res) => {
  const user = await db.query('SELECT id, email, name FROM users WHERE id = $1', [req.userId]);
  const existing = await db.query(
    'SELECT credential_id, transports FROM passkeys WHERE user_id = $1',
    [req.userId]
  );

  const options = await generateRegistrationOptions({
    rpName: RP_NAME,
    rpID: RP_ID,
    userID: Buffer.from(String(user.rows[0].id)),
    userName: user.rows[0].email,
    userDisplayName: user.rows[0].name,
    attestationType: 'none',
    excludeCredentials: existing.rows.map(c => ({
      id: c.credential_id,
      transports: c.transports || undefined,
    })),
    authenticatorSelection: {
      residentKey: 'preferred',           // discoverable credentials enable conditional UI
      userVerification: 'preferred',
    },
  });

  // Store challenge for the verify step (Redis with short TTL)
  await redisClient.setEx(
    `webauthn:reg:${req.userId}`,
    300,
    options.challenge
  );

  res.json(options);
});

// 2. Server: verify what the browser returned
app.post('/auth/passkey/register/verify', requireAuth(), async (req, res) => {
  const expectedChallenge = await redisClient.get(`webauthn:reg:${req.userId}`);

  let verification;
  try {
    verification = await verifyRegistrationResponse({
      response: req.body,
      expectedChallenge,
      expectedOrigin: ORIGIN,
      expectedRPID: RP_ID,
      requireUserVerification: false,
    });
  } catch (err) {
    return res.status(400).json({ error: err.message });
  }

  if (!verification.verified || !verification.registrationInfo) {
    return res.status(400).json({ error: 'Registration not verified' });
  }

  const { credential, credentialBackedUp, credentialDeviceType } =
    verification.registrationInfo;

  await db.query(
    `INSERT INTO passkeys
     (user_id, credential_id, public_key, counter, transports, device_type, backed_up)
     VALUES ($1, $2, $3, $4, $5, $6, $7)`,
    [
      req.userId,
      credential.id,
      credential.publicKey,
      credential.counter,
      req.body.response?.transports || null,
      credentialDeviceType,
      credentialBackedUp,
    ]
  );

  await redisClient.del(`webauthn:reg:${req.userId}`);
  res.json({ verified: true });
});
```

```html
<!-- Browser — @simplewebauthn/browser -->
<script type="module">
  import { startRegistration } from 'https://unpkg.com/@simplewebauthn/browser/dist/bundle/index.js';

  async function enrollPasskey() {
    const optsRes = await fetch('/auth/passkey/register/options', { method: 'POST', credentials: 'include' });
    const options = await optsRes.json();

    const attResp = await startRegistration({ optionsJSON: options });

    const verRes = await fetch('/auth/passkey/register/verify', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(attResp),
    });
    return verRes.json();
  }

  document.getElementById('enroll').addEventListener('click', enrollPasskey);
</script>
```

### Authentication ceremony (with conditional UI)

Conditional UI lets the browser surface passkeys directly inside the username autofill dropdown — the user picks a passkey from the same UI they'd use to autofill an email.

```javascript
// Node — server side
const {
  generateAuthenticationOptions,
  verifyAuthenticationResponse,
} = require('@simplewebauthn/server');

app.post('/auth/passkey/login/options', async (req, res) => {
  const options = await generateAuthenticationOptions({
    rpID: RP_ID,
    userVerification: 'preferred',
    // allowCredentials omitted → discoverable credentials → conditional UI works
  });

  // Tie the challenge to a temporary session marker
  const challengeId = crypto.randomBytes(16).toString('hex');
  await redisClient.setEx(`webauthn:auth:${challengeId}`, 300, options.challenge);
  res.json({ options, challengeId });
});

app.post('/auth/passkey/login/verify', async (req, res) => {
  const { challengeId, response } = req.body;
  const expectedChallenge = await redisClient.get(`webauthn:auth:${challengeId}`);

  if (!expectedChallenge) {
    return res.status(400).json({ error: 'Challenge expired' });
  }

  const credentialId = response.id;
  const stored = await db.query(
    `SELECT user_id, public_key, counter, transports FROM passkeys WHERE credential_id = $1`,
    [credentialId]
  );
  if (stored.rows.length === 0) {
    return res.status(401).json({ error: 'Unknown credential' });
  }

  let verification;
  try {
    verification = await verifyAuthenticationResponse({
      response,
      expectedChallenge,
      expectedOrigin: ORIGIN,
      expectedRPID: RP_ID,
      credential: {
        id: credentialId,
        publicKey: stored.rows[0].public_key,
        counter: stored.rows[0].counter,
        transports: stored.rows[0].transports || undefined,
      },
      requireUserVerification: false,
    });
  } catch (err) {
    return res.status(401).json({ error: err.message });
  }

  if (!verification.verified) {
    return res.status(401).json({ error: 'Authentication not verified' });
  }

  // Persist new counter
  await db.query(
    `UPDATE passkeys SET counter = $1, last_used_at = NOW() WHERE credential_id = $2`,
    [verification.authenticationInfo.newCounter, credentialId]
  );

  // Issue session/tokens as usual
  req.session.regenerate(() => {
    req.session.userId = stored.rows[0].user_id;
    res.json({ verified: true });
  });
});
```

```html
<!-- Browser — discoverable credential + conditional UI -->
<input type="email" name="email" autocomplete="username webauthn">
<script type="module">
  import { startAuthentication, browserSupportsWebAuthnAutofill }
    from 'https://unpkg.com/@simplewebauthn/browser/dist/bundle/index.js';

  if (await browserSupportsWebAuthnAutofill()) {
    const optsRes = await fetch('/auth/passkey/login/options', { method: 'POST' });
    const { options, challengeId } = await optsRes.json();

    const authResp = await startAuthentication({
      optionsJSON: options,
      useBrowserAutofill: true, // conditional UI
    });

    await fetch('/auth/passkey/login/verify', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ challengeId, response: authResp }),
    });
    location.href = '/dashboard';
  }
</script>
```

### WebAuthn L3 signal methods

L3 adds `PublicKeyCredential` static methods so the relying party can keep syncable passkeys aligned with server state without forcing a re-enrollment:

- `signalUnknownCredential({ rpId, credentialId })` — call after a verify attempt against a credential the server no longer knows about. The authenticator hides it from the user's account-picker UI.
- `signalAllAcceptedCredentials({ rpId, userId, allAcceptedCredentialIds })` — call after the server's credential list changes (revoke, enroll). The authenticator prunes anything not on the list.
- `signalCurrentUserDetails({ rpId, userId, name, displayName })` — call after profile changes. The authenticator updates labels in the picker UI.

These are advisory and best-effort; treat them as housekeeping, not security boundaries.

### When to use `webauthn` (Python)

```python
# pip install webauthn   # PyPI package name is `webauthn`, NOT py_webauthn
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

RP_ID = "yourapp.com"
RP_NAME = "YourApp"
ORIGIN = "https://yourapp.com"

options = generate_registration_options(
    rp_id=RP_ID,
    rp_name=RP_NAME,
    user_id=str(user_id).encode(),
    user_name=user_email,
    authenticator_selection=AuthenticatorSelectionCriteria(
        resident_key=ResidentKeyRequirement.PREFERRED,
        user_verification=UserVerificationRequirement.PREFERRED,
    ),
)
```

## Password reset flow

### Secure implementation

```javascript
const crypto = require('crypto');

// Request password reset
app.post('/auth/forgot-password', async (req, res) => {
  const { email } = req.body;

  // Always return success to prevent email enumeration
  res.json({ message: 'If an account exists, a reset link has been sent.' });

  // Find user (async, after response)
  const result = await db.query(
    'SELECT id FROM users WHERE email = $1',
    [email.toLowerCase()]
  );

  if (result.rows.length === 0) {
    return; // User doesn't exist, but don't reveal that
  }

  const user = result.rows[0];

  // Generate secure token
  const token = crypto.randomBytes(32).toString('hex');
  const tokenHash = crypto.createHash('sha256').update(token).digest('hex');
  const expiresAt = new Date(Date.now() + 3600000); // 1 hour

  // Store hashed token (not plain token)
  await db.query(
    'INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES ($1, $2, $3)',
    [user.id, tokenHash, expiresAt]
  );

  // Send email with plain token
  const resetUrl = `https://yourapp.com/reset-password?token=${token}`;
  await sendEmail(email, 'Password Reset', `Reset your password: ${resetUrl}`);
});

// Reset password
app.post('/auth/reset-password', async (req, res) => {
  const { token, newPassword } = req.body;

  if (!token || !newPassword) {
    return res.status(400).json({ error: 'Token and new password required' });
  }

  // NIST 800-63B-4: 15-char minimum
  if (newPassword.length < 15) {
    return res.status(400).json({ error: 'Password must be at least 15 characters' });
  }

  if (await isPwned(newPassword)) {
    return res.status(400).json({ error: 'This password has appeared in a known breach. Choose a different one.' });
  }

  // Hash the provided token to compare with stored hash
  const tokenHash = crypto.createHash('sha256').update(token).digest('hex');

  // Find valid reset token
  const result = await db.query(
    `SELECT user_id FROM password_resets
     WHERE token_hash = $1 AND expires_at > NOW() AND used = false`,
    [tokenHash]
  );

  if (result.rows.length === 0) {
    return res.status(400).json({ error: 'Invalid or expired token' });
  }

  const userId = result.rows[0].user_id;

  // Hash new password with argon2id
  const hashedPassword = await argon2.hash(newPassword, ARGON2_OPTS);

  // Update password and invalidate token
  await db.query('UPDATE users SET password_hash = $1 WHERE id = $2', [hashedPassword, userId]);
  await db.query('UPDATE password_resets SET used = true WHERE token_hash = $1', [tokenHash]);

  // Invalidate all existing sessions and refresh-token families for this user
  await db.query('DELETE FROM sessions WHERE user_id = $1', [userId]);
  // (also revoke all refresh-token families for the user in your token store)

  res.json({ success: true });
});
```

## OAuth 2.1 (with Google example)

OAuth 2.1 is currently `draft-ietf-oauth-v2-1-15` dated 2026-03-02 (https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-15). Not yet an RFC, but providers (Google, Microsoft, Okta, Auth0) already implement these constraints today, so design to the 2.1 baseline.

### What 2.1 requires (and removes)

- **PKCE mandatory for ALL clients, including confidential clients.** S256 only — `plain` is deprecated.
- **Exact-string redirect-URI matching.** No prefix or wildcard matching.
- **No implicit grant (`response_type=token`).** Use authorization code with PKCE.
- **No Resource Owner Password Credentials (ROPC).** First-party login flows go through the authorization endpoint.
- **Bearer tokens never in URL query strings.** Always Authorization header.

### Server-side code-with-PKCE flow (Google)

```javascript
const { OAuth2Client } = require('google-auth-library');
const crypto = require('crypto');

const oauth2Client = new OAuth2Client(
  process.env.GOOGLE_CLIENT_ID,
  process.env.GOOGLE_CLIENT_SECRET,
  process.env.GOOGLE_REDIRECT_URI
);

function pkcePair() {
  const verifier = crypto.randomBytes(32).toString('base64url');
  const challenge = crypto.createHash('sha256').update(verifier).digest('base64url');
  return { verifier, challenge };
}

// Step 1: Redirect to Google
app.get('/auth/google', (req, res) => {
  const state = crypto.randomBytes(32).toString('hex');
  const { verifier, challenge } = pkcePair();

  req.session.oauthState = state;
  req.session.oauthVerifier = verifier;

  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: ['email', 'profile'],
    state,
    prompt: 'consent',
    code_challenge: challenge,
    code_challenge_method: 'S256',
  });

  res.redirect(authUrl);
});

// Step 2: Handle callback
app.get('/auth/google/callback', async (req, res) => {
  const { code, state } = req.query;

  // Verify state to prevent CSRF
  if (!state || state !== req.session.oauthState) {
    return res.status(400).send('Invalid state parameter');
  }

  const verifier = req.session.oauthVerifier;
  delete req.session.oauthState;
  delete req.session.oauthVerifier;

  if (!verifier) {
    return res.status(400).send('Missing PKCE verifier');
  }

  try {
    // Exchange code for tokens — include the PKCE verifier
    const { tokens } = await oauth2Client.getToken({
      code,
      codeVerifier: verifier,
    });
    oauth2Client.setCredentials(tokens);

    // Validate the id_token: Google verifies signature; we MUST check audience
    const ticket = await oauth2Client.verifyIdToken({
      idToken: tokens.id_token,
      audience: process.env.GOOGLE_CLIENT_ID,
    });

    const payload = ticket.getPayload();
    if (payload.iss !== 'https://accounts.google.com' && payload.iss !== 'accounts.google.com') {
      return res.status(400).send('Unexpected issuer');
    }

    const { sub: googleId, email, name, picture } = payload;

    // Find or create user
    let user = await db.query('SELECT id FROM users WHERE google_id = $1', [googleId]);

    if (user.rows.length === 0) {
      user = await db.query(
        `INSERT INTO users (google_id, email, name, avatar_url)
         VALUES ($1, $2, $3, $4) RETURNING id`,
        [googleId, email, name, picture]
      );
    }

    // Create session
    req.session.regenerate((err) => {
      if (err) {
        return res.status(500).send('Session error');
      }
      req.session.userId = user.rows[0].id;
      res.redirect('/dashboard');
    });

  } catch (error) {
    console.error('OAuth error:', error);
    res.status(400).send('Authentication failed');
  }
});
```

The same pattern applies to any OAuth 2.1 / OIDC provider — substitute issuer, client, scopes, and the userinfo lookup. Confirm exact-string redirect URIs in the provider console match what your server sends.

## MFA (passkey-first)

CISA "Implementing Phishing-Resistant MFA" (2022-10-31, still current 2026-05; https://www.cisa.gov/sites/default/files/publications/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf) ranks factor strength:

- **Phishing-resistant tier:** FIDO2 / WebAuthn (passkeys), PKI smartcards (PIV/CAC). Required at NIST AAL3.
- **AAL2-acceptable, not phishing-resistant:** App-based push with number matching, TOTP via authenticator app.
- **Restricted, last resort:** SMS / voice OTP. NIST 800-63B-4 §5 explicitly restricts these.

In 2026: **don't add SMS as a new factor.** Migrate users off it where you can.

### Passkey-as-second-factor

If passwords are still your first factor, a registered passkey is the strongest second factor available. The registration and authentication ceremonies in the Passkeys / WebAuthn section above work unchanged — gate `/auth/login` on a successful passkey verify after password verify.

### TOTP (still valid for AAL2)

```javascript
const speakeasy = require('speakeasy');
const QRCode = require('qrcode');

// Enable MFA for user
app.post('/auth/mfa/enable', requireAuth(), async (req, res) => {
  // Generate secret
  const secret = speakeasy.generateSecret({
    name: `YourApp:${req.user.email}`,
    issuer: 'YourApp'
  });

  // Store secret (encrypted) temporarily until verified
  await db.query(
    'UPDATE users SET mfa_secret_temp = $1 WHERE id = $2',
    [encrypt(secret.base32), req.userId]
  );

  // Generate QR code
  const qrCode = await QRCode.toDataURL(secret.otpauth_url);

  res.json({
    secret: secret.base32, // Show this as backup
    qrCode: qrCode
  });
});

// Verify and activate MFA
app.post('/auth/mfa/verify', requireAuth(), async (req, res) => {
  const { code } = req.body;

  const result = await db.query(
    'SELECT mfa_secret_temp FROM users WHERE id = $1',
    [req.userId]
  );

  const secret = decrypt(result.rows[0].mfa_secret_temp);

  const verified = speakeasy.totp.verify({
    secret: secret,
    encoding: 'base32',
    token: code,
    window: 1 // Allow 1 step tolerance
  });

  if (!verified) {
    return res.status(400).json({ error: 'Invalid code' });
  }

  // Move secret from temp to permanent
  await db.query(
    'UPDATE users SET mfa_secret = mfa_secret_temp, mfa_secret_temp = NULL, mfa_enabled = true WHERE id = $1',
    [req.userId]
  );

  res.json({ success: true });
});

// Login with MFA
app.post('/auth/login', async (req, res) => {
  const { email, password, mfaCode } = req.body;

  // ... verify email/password first ...

  if (user.mfa_enabled) {
    if (!mfaCode) {
      return res.status(401).json({
        error: 'MFA code required',
        requiresMfa: true
      });
    }

    const verified = speakeasy.totp.verify({
      secret: decrypt(user.mfa_secret),
      encoding: 'base32',
      token: mfaCode,
      window: 1
    });

    if (!verified) {
      return res.status(401).json({ error: 'Invalid MFA code' });
    }
  }

  // ... create session/token ...
});
```

### SMS: don't add it as a new factor in 2026

If you already have SMS in production, plan its retirement. Snowflake (see breach lessons) and the broader SIM-swap landscape make SMS a liability, not a safeguard. NIST 800-63B-4 §5 restricts it; CISA recommends moving off it.

## Common breach lessons

Vignettes anchoring patterns to actual incidents. Each is a 2-3 sentence summary plus the lesson encoded in the recipes above.

### Change Healthcare ransomware (Feb 2024)

Attackers used compromised credentials on a Citrix remote-access portal that lacked MFA. Disruption ran for weeks; UnitedHealth Group disclosed an approximately $22M ransom and exposure of records for roughly 1 in 3 US patients. Per the UnitedHealth Group RCA at https://www.unitedhealthgroup.com/newsroom/2024/2024-04-22-uhg-update-on-change-healthcare-cyberattack.html.

**Lesson:** MFA on every remote-access portal — VPN, Citrix, RDP gateway, jump host — not just user-facing apps. The "internal" portal is the one attackers target precisely because it's less guarded.

### Snowflake / UNC5537 (Apr-Jun 2024)

Approximately 165 customer tenants were breached because Snowflake's MFA was opt-in per tenant; attackers used infostealer-harvested credentials against accounts with no second factor. Mandiant's writeup is at https://cloud.google.com/blog/topics/threat-intelligence/unc5537-snowflake-data-theft-extortion. Snowflake enforced default-on MFA from October 2024 and has been phasing in mandatory blocking of password-only sign-in across 2025-2026; see Snowflake's MFA enforcement documentation (https://docs.snowflake.com/) for the current rollout schedule.

**Lesson:** MFA must default to ON, not opt-in. If your customers can disable it, attackers will find the ones who did.

### Storm-0558 (CSRB review, 2024-04)

A Microsoft consumer signing key was compromised; attackers forged Azure AD tokens and accessed enterprise OWA mailboxes. The proximate failure was that OWA's token-validation library accepted a consumer-key-signed token for enterprise mailboxes — it skipped scope, issuer, and signing-key tenancy validation. CSRB report: https://www.cisa.gov/resources-tools/resources/CSRB-Review-Summer-2023-MEO-Intrusion. (Microsoft's MSRC postmortem URL is decommissioned.)

**Lesson:** Validate every claim every time — issuer, audience, scope, expiration, pinned algorithm. AND for multi-issuer / OIDC deployments, validate signing-key tenancy: pin which JWKS each trusted issuer is allowed to use, and never select a verifying key from a different issuer's set, even if the `kid` matches. The JWT recipe above bakes in `iss` / `aud` / `scope` / pinned algorithm — that's the claim-level half of the lesson and covers single-issuer private-token deployments. The signing-key tenancy half (JWKS resolution and issuer-to-key-set binding) is not in the sample; see the comment block above the `requireAuth` function for what to add when accepting tokens from multiple tenants.

### Okta HAR breach (Oct 2023)

Customers uploaded HAR (HTTP Archive) debug files to Okta support; the files contained live session tokens. Five customer sessions were hijacked. Per Okta's writeup at https://sec.okta.com/articles/harfiles/.

**Lesson:** Sanitize session tokens and other bearer credentials at log boundaries. HAR uploads, error reports, debug dumps — strip Authorization headers, set-cookie, and known token-shaped values before they leave the user's browser.

### 23andMe credential stuffing (Oct 2023, settled 2024)

Attackers credential-stuffed approximately 14,000 accounts using passwords reused from other breaches, then traversed the DNA Relatives social graph to expose data on roughly 6.9 million users.

**Lesson:** Per-account read quotas on relationship and graph endpoints, not just per-IP rate limits. A single compromised account should not be able to enumerate the social graph faster than a human user reasonably would. Pwned-password screening (HIBP) at registration and password-reset blocks the inbound vector entirely.

## Security considerations checklist

NIST AAL terminology in parentheses where relevant.

### Password storage
- [ ] Default is argon2id with one of OWASP's 5 equivalent profiles (m=47104/t=1, m=19456/t=2, m=12288/t=3, m=9216/t=4, m=7168/t=5; all p=1)
- [ ] If using bcrypt, cost 10 minimum; pre-hash inputs over 72 bytes with SHA-256 (or reject)
- [ ] PBKDF2 only when FIPS-140 compliance is required
- [ ] Never storing plain-text passwords
- [ ] Never logging passwords (including in error handlers)

### Password policy (NIST SP 800-63B-4)
- [ ] 15-character minimum for single-factor; 8-char minimum for multi-factor
- [ ] 64-character minimum maximum (verifier accepts at least 64)
- [ ] No composition rules ("SHALL NOT impose")
- [ ] Unicode and paste allowed
- [ ] No periodic rotation
- [ ] Verifier checks against breach blocklist (HIBP k-anonymity or equivalent)

### Session management
- [ ] Sessions stored server-side (not just in cookies)
- [ ] Session IDs are cryptographically random
- [ ] Sessions regenerated on login AND on privilege change
- [ ] Sessions invalidated on logout AND on password reset
- [ ] Sessions have a maximum lifetime
- [ ] Cookies set `httpOnly`, `secure` in prod, `sameSite=lax` or stricter

### JWT security
- [ ] Short access-token lifetime (15 min or less)
- [ ] Refresh tokens stored as httpOnly cookies
- [ ] Refresh-token rotation with reuse detection (rotated token used twice → revoke entire family)
- [ ] Token revocation mechanism exists
- [ ] Secrets are at least 256 bits
- [ ] Full validation on every request: issuer, audience, expiration, scope, algorithm pinned (no `alg=none`), signing-key tenancy (Storm-0558)
- [ ] Bound tokens (DPoP per RFC 9449 or mTLS per RFC 8705) for high-value APIs

### Passkeys / WebAuthn
- [ ] Registration ceremony validates challenge, origin, and RP ID
- [ ] Authentication ceremony validates challenge, origin, RP ID, and signature counter
- [ ] Discoverable credentials enabled (`residentKey: 'preferred'`) for conditional UI
- [ ] WebAuthn L3 signal methods called when server credential state changes
- [ ] CTAP 2.3 considered when picking authenticator policy

### MFA (CISA tier ranks)
- [ ] Phishing-resistant tier (FIDO2/WebAuthn, PIV/CAC) for AAL3 contexts
- [ ] App-based push with number matching or TOTP for AAL2
- [ ] No new SMS factors in 2026; migrate existing users off SMS
- [ ] MFA defaults to ON, not opt-in (Snowflake lesson)
- [ ] MFA enforced on every remote-access portal (Change Healthcare lesson)

### OAuth 2.1
- [ ] PKCE with S256 on all clients, including confidential
- [ ] Exact-string redirect-URI matching
- [ ] No implicit or ROPC grants
- [ ] State parameter validated on callback
- [ ] `id_token` audience and issuer validated

### Rate limiting
- [ ] Login attempts limited per IP and per account
- [ ] Account lockout after N failures
- [ ] Password reset requests limited
- [ ] MFA verification attempts limited
- [ ] Per-account quotas on relationship / graph endpoints (23andMe lesson)

### CSRF protection
- [ ] SameSite cookie attribute set
- [ ] CSRF tokens for state-changing operations
- [ ] OAuth state parameter verified

### Information disclosure
- [ ] Same error messages for valid / invalid users
- [ ] Timing attacks mitigated (dummy hash compare on missing user)
- [ ] No user enumeration via registration / reset
- [ ] Bearer tokens stripped from log boundaries (Okta HAR lesson)
