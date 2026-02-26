---
description: Check for updates and install the latest version
allowed-tools: Bash, Read
---

Check if the PDF Playground plugin is up to date and update if needed.

## Steps

1. Read the current installed version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`
2. Tell the user the current version
3. Run the update:
   ```bash
   claude plugin update pdf-playground@claude-skills-journalism
   ```
4. Read the version again to confirm it changed
5. Tell the user:
   > Updated successfully. Please restart Claude Code for the changes to take effect.

   If the version didn't change:
   > You're already on the latest version.
