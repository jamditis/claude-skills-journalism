# Dependency provenance

This file records manual checks for public CDN assets that are not installed
through the package lock.

## Lucide 1.31.0

- Source: `https://unpkg.com/lucide@1.31.0/dist/umd/lucide.min.js`
- Verified: 2026-08-15
- Integrity: `sha384-/ApD3KXMqTmTxEJjuldaZDgdJj7/Hox2LRuKqV3rC7Bu/wE4obLaJRjF1rLHNP57`
- Command:

  ```bash
  curl -fsSL https://unpkg.com/lucide@1.31.0/dist/umd/lucide.min.js \
    | openssl dgst -sha384 -binary \
    | openssl base64 -A
  ```

The command output must match the base64 value after `sha384-` above.
