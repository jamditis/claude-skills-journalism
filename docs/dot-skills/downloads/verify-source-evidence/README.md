# Verify source evidence

A portable Markdown workflow for checking claims, dates, provenance, conflicting evidence, and the difference between a code change and a working service.

## Contents and use

Download and extract the ZIP, then read `SKILL.md` first. The complete procedure, references and manifest are inside the ZIP; this web directory contains only its explanatory documentation and license. Keep the three reference files beside it. Ask your assistant to use this procedure for a specific claim and an authorized set of sources. If your host supports importing skill directories, use its documented import flow; otherwise provide these files as reference material. Import and invocation behavior has not been tested across hosts. This ZIP is not a `.skills` format claim or a marketplace plugin.

## Requirements

The procedure has no executable scripts, dependencies, lifecycle hooks, automatic schedules, credentials, or bundled connector. An assistant needs authorized read access to the evidence relevant to your question. If a needed source is unavailable, it should report the gap instead of treating retrieval failure as an outage.

## Permissions

Reading this package grants no permission to contact people, post, upload, archive private material, change access, or run production tests. Obtain the permissions required by the host and the actual task. Stop on explicit denials; do not switch identities or transports to evade them.

## Provenance and changes

The underlying catalog skill is Joe Amditis's MIT-licensed source-verification workflow, linked in `references/provenance.md`. This portable edition retains the licensed text and reference files. Host-specific UI metadata and the optional icon are intentionally omitted; neither is required by the Markdown procedure. No private original identifiers or source locators are included. `manifest.json` records byte-level integrity for the distributed files and explicitly excludes itself.

## Validation limits

Static checks cover frontmatter, relative reference targets, exact file inventory, ZIP integrity, checksums, and selected private-data patterns. The text was reviewed for private destinations and embedded action requests. These checks do not prove universal safety or correctness. No import into another account, live connector run, external upload, source contact, or production test was performed for this export.

The fixture checklist in `VALIDATION.md` records procedure-level review, not a runtime test suite. Review permissions, provenance, and current tool behavior before use.

## License

MIT. See `LICENSE`; preserve its copyright and license notice when redistributing.
