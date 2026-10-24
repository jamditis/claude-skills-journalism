---
name: surface-completeness
description: Use to check UI coverage, design compliance, and docs during frontend changes.
---

# Surface completeness

Use this workflow during user-facing implementation, after each cosmetic change,
and before declaring the affected work complete. An explicit session closeout can
also cover new services and their user documentation without a UI change. Scope
follows the requested change. It does not authorize unrelated redesign, releases,
provider changes, or new external communication.

## Preserve the accepted result

Record the accepted baseline, intended improvement, affected surfaces, and recent
work that must survive in your task list or plan tool. Distinguish current source,
open pull requests, approved references, and deployed screens. For overlapping
pull requests, compare their incremental intent and shared history before
reconciling files. Do not replace a whole file from one branch when that discards
unrelated work.

A direction such as "use bolder colors" changes presentation within the
established action hierarchy. It does not promote Cancel, make a safe secondary
action look like success, or erase the distinction between ordinary and
destructive actions. Preserve the project's accepted palette and interaction
model. Use authoritative [standards guidance](references/standards.md) when
deciding hierarchy, action emphasis, color meaning, contrast, focus, motion, or
target behavior. Separate normative accessibility requirements from design-system
recommendations.

## Change the shared owner

Find the existing semantic token, shared component, or style rule that owns the
element. Change its parameters once and inspect all affected consumers. Avoid
repeating a common style in individual components or adding a parallel system.
Trace aliases, variants, generated outputs, and local overrides. A local exception
needs a concrete behavior or context difference and documented scope.

When the new design changes the accepted rule, update its owning contract,
tokens, and existing enforcement in the same work. Otherwise, cite the existing
rule that already covers it. Do not update screenshots only to make a failure
disappear. Use checks proportional to the change. Do not create persistent
exact-text or CSS assertions that only mirror the implementation.

## Keep one compliance and completeness reviewer

At the first cosmetic change, use one dedicated subagent or parallel worker if
your client supports one, or reuse the existing reviewer. Give it the scope,
accepted baseline, shared owners, affected consumer inventory, final diff, and
evidence paths. Its task is independent compliance and completeness review, not
redesign or autonomous repository changes. Ask it to check in at the end of each
cosmetic change before that change is accepted. Do not create a new reviewer for
every minor fix.

The reviewer checks:

- The result follows the accepted rules, contracts, and tokens, or the intended
  new rule and its enforcement were updated together.
- Shared changes propagate through their consumers. Local overrides do not
  defeat them, and component exceptions have a scoped reason.
- All intended surfaces, components, variants, roles, and relevant states are
  covered, with unrelated recent improvements preserved.
- Code documentation and user guidance reflect the finished behavior, including
  relevant screenshots and tutorials.

The primary worker verifies findings, repairs actual gaps, and owns the final
judgment. After a repair, request focused verification of that finding instead
of restarting broad review. If delegation is unavailable, record the missing
gate and the checks performed. Do not describe a self-review as independent.

## Prove affected coverage

Maintain a concise matrix in your task list or plan tool: shared owner,
consumers, intended effect, relevant states and viewports, documentation,
evidence, and unresolved gaps. Derive consumers from imports, styles, routes,
registries, and existing surface inventories. Two representative screenshots
alone cannot prove that a shared system change reached every consumer.

Use static consumer and override inspection to prove propagation. Use browser
evidence to check distinct layouts and interactions. Include relevant phone and
desktop layouts, action roles, keyboard focus, disabled, pending and error
states, long content, motion, and role variants when affected. Do not demand
every state for an unrelated copy or layout edit. Browser navigation uses
structured snapshots and element references. Screenshots verify results and
supply documentation.

Inspect intended changes before accepting visual baselines. Confirm screenshot
provenance, deterministic fixtures, responsive layout, and actual user behavior.
A green snapshot alone does not establish usability or complete coverage.

## Maintain documentation with the result

Map the change to code contracts, runbooks, staff guides, public design-system
pages, handbooks, tutorials, screenshots, and generated architecture or status
maps. Trace each displayed map to its source data. Reconcile released entries
and remaining proposals with the same deployment receipt. Update relevant
generated copies through their source owner. "Not affected" needs a brief reason
in the matrix, not an unnecessary rewrite.

Current guides, runbooks, comments, and architecture summaries describe what the
system does and how it works now. Remove obsolete behavior, superseded receipts,
and development stories. Do not keep tombstone sections or historical anchors
only to preserve documentation. Git history and private session evidence retain
the audit trail. Keep current recovery steps and explicit verification limits.
Update inbound links to support the current claim. A working anchor alone is not
proof. Keep earlier test evidence separate from current deployment evidence in
your task list or plan tool, and verify delivery of generated documentation.

Replace images that misrepresent the finished interface. Add screenshots when
they explain a new feature, service, state, or meaningful step. Capture the final
verified view with suitable test data. Retain no secrets or private content.
Check image paths, useful captions or alternative text, links, and rendered
pages. Clearly label preview or undeployed behavior and keep public and staff
boundaries.

## Checkpoints and completion

Update your task list or plan tool after each cosmetic change, compliance
review, repair, documentation update, and release boundary. Store exact source
or pull request identifiers, evidence paths, findings and dispositions, and the
next action so a new session can resume without repeating settled work.

At session closeout, reconcile the intended scope against the coverage matrix
and final diff. Require the reviewer's final check of affected design and
documentation when independent review is available. Report remaining gaps
explicitly. Source, tests, merged code, deployed applications, persisted
content, and public visibility are separate facts. Reuse valid evidence. This
workflow never creates merge or deployment authority.

Related skills: [accessibility-compliance](../accessibility-compliance/SKILL.md)
covers accessibility implementation and testing, and
[web-ui-best-practices](../web-ui-best-practices/SKILL.md) covers interface
design conventions.
