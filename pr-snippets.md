# PR snippets, files to edit besides the skill folder

Not part of the skill. Copy these into the repo files, adjusting wording to
match whatever is actually there when you branch.

## 1. `journalism-core/README.md`, skill table row

```markdown
| [brazil-records-requests](skills/brazil-records-requests/) | Public records requests under Brazil's Access to Information Law (Lei 12.527/2011), portal selection across federal, state, municipal, judicial and legislative bodies; deadlines; the four-level appeal chain (first instance, agency head, CGU, CMRI); templates in Portuguese with English glosses |
```

## 2. root `README.md`

Same row in the core-skills table, plus the count. "Fourteen" appears in at
least three places, the plugin description, the plugin table, and the
journalism-core section heading. Grep before committing:

```bash
grep -rn -i "fourteen\|14 skills" README.md journalism-core/ .claude-plugin/ docs/
```

Suggested revision to the plugin blurb: add `Brazilian LAI requests` to the
list after `FOIA + NJ OPRA requests`.

## 3. `CHANGELOG.md`

```markdown
### Added
- `brazil-records-requests` (#266): public records requests under Brazil's
  Access to Information Law (Lei 12.527/2011). Covers portal selection across
  federal, state, municipal, judicial and legislative bodies; the 20+10 day
  response deadlines; the four-level appeal chain (immediate superior, agency
  head, CGU, CMRI); denial diagnosis, including the art. 13 grounds of Decree
  7.724/2012; and six request and appeal templates in Portuguese with English
  glosses. First non-US jurisdiction in `journalism-core`. Triggers on both
  Portuguese and English prompts and does not collide with `foia-requests`.
```

Follow the existing changelog's version-heading convention, this is a
`journalism-core` minor bump, not a patch.

## 4. Plugin manifest

Check `.claude-plugin/marketplace.json` and any `plugin.json` under
`journalism-core/` for a skill list, a count, or a description string that
names the skills. Update whichever exist.

```bash
grep -rn "foia-requests" --include="*.json" .
```

That grep finds every manifest that enumerates skills, wherever
`foia-requests` is listed, `brazil-records-requests` belongs too.

## 5. Docs landing page

The changelog mentions `docs/<skill>/index.html` landing pages per skill. If
that pattern still holds, either add one following the existing template or
say in the PR that you left it for the maintainer's generator, ask, don't
guess.

## Before opening the PR

- [ ] Statutory citations verified against the current text on planalto.gov.br
- [ ] Installed to `~/.claude/skills/` and triggered on the three test prompts
- [ ] Confirmed no trigger collision with `foia-requests` on US prompts
- [ ] No AI attribution anywhere in commit messages or file contents
- [ ] Sentence case in all headings
- [ ] Branch is off current `master`
