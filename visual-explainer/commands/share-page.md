---
description: Deploy a generated visual-explainer HTML page and return a live Vercel URL
---
# Share Visual Explainer Page

Share a visual explainer HTML file instantly via Vercel. Returns a live URL with no authentication required when a Pi-compatible `vercel-deploy` skill is installed.

## Usage

```
/share-page <file-path>
```

**Arguments:**
- `file-path` - Path to the HTML file to share (required)

**Examples:**
```
/share-page ~/.agent/diagrams/my-diagram.html
/share-page /tmp/visual-explainer-output.html
```

## How It Works

1. Finds the `visual-explainer` skill directory for the current harness
2. Copies your HTML file to a temp directory as `index.html`
3. Deploys via the Pi-compatible `vercel-deploy` skill
4. Returns a live URL immediately

## Requirements

- **vercel-deploy skill** - Required for deployment. In Pi, install with: `pi install npm:vercel-deploy`

No Vercel account, Cloudflare account, or API keys needed. The deployment is "claimable" — you can transfer it to your Vercel account later if you want.

## Script Location

Resolve the script from the installed skill directory, then run it with the HTML file path:

```bash
bash ~/.pi/agent/skills/visual-explainer/scripts/share.sh <file>
```

If the skill is installed somewhere else, use that install path instead. Common locations include `~/.codex/skills/visual-explainer/scripts/share.sh`, `~/.config/opencode/skill/visual-explainer/scripts/share.sh`, or `./plugins/visual-explainer/scripts/share.sh` from a repository checkout.

The script currently looks for the Pi-compatible `vercel-deploy` script in the standard Pi skill locations. Other harnesses can generate and open HTML normally, but sharing requires that dependency to be available in a compatible location.

## Output

```
Sharing my-diagram.html...

✓ Shared successfully!

Live URL:  https://skill-deploy-abc123.vercel.app
Claim URL: https://vercel.com/claim-deployment?code=...
```

The script also outputs JSON for programmatic use:
```json
{"previewUrl":"https://...","claimUrl":"https://...","deploymentId":"...","projectId":"..."}
```

## Notes

- Deployments are **public** — anyone with the URL can view
- Preview deployments have a configurable retention period (default: 30 days)
- Each share creates a new deployment with a unique URL
