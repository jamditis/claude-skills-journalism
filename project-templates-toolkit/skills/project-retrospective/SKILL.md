---
name: project-retrospective
description: Generate LESSONS.md retrospective files that capture institutional knowledge, especially failures. Use when closing out journalism projects, investigations, events, or publications. Includes templates for research projects, event post-mortems, editorial tools, and publications.
---

# Project retrospective writer

Create LESSONS.md files that capture institutional knowledge, especially failures. Think like a journalist writing about your own project — be specific, be honest, name the actual mistakes.

## Frame the retrospective: blame-aware, not pure-blameless

The 2024–2026 consensus in incident-analysis writing (PagerDuty, J. Paul Reed, Lorin Hochstein) is that pure blamelessness is neurobiologically unrealistic — humans default to blame. Healthier framing: acknowledge the blame bias exists and counter it deliberately. Source: https://postmortems.pagerduty.com/culture/blameless/

Cognitive biases to counter explicitly:
- **Fundamental attribution error** — blaming individuals for failures the system permitted
- **Confirmation bias** — looking for evidence that confirms a pre-formed narrative
- **Hindsight bias** — judging past decisions by knowledge that wasn't available at the time
- **Negativity bias** — over-weighting what went wrong vs. what worked

The voice rule isn't "no blame" — it's "name the system that permitted the human action, not just the action."

## Drop the single-root-cause framing

Allspaw's canonical critique (still the dominant view in 2024–2026) calls Five Whys / single-root-cause analysis "seductively satisfying and compellingly simple — but false." It locks analysts into a linear causal chain that terminates in individual blame. Source: https://www.kitchensoap.com/2014/11/14/the-infinite-hows-or-the-dangers-of-the-five-whys/

Use "how" narratives instead, gathering on four prompts:
- **Cues** — what signals were available, who saw them when?
- **Interpretation** — how did people make sense of those signals?
- **Goals** — what were people trying to accomplish?
- **Taking action** — what did they do, and what did they expect to happen?

The retrospective's job is to surface contributing factors, not declare a root cause.

## When to run a retrospective

Pre-define triggers before incidents happen, not after. Google SRE specifies criteria: user-visible downtime past a threshold, any data loss, on-call rollbacks, monitoring failures requiring manual discovery, stakeholder request. Source: https://sre.google/sre-book/postmortem-culture/

Translated to journalism:

| Trigger | Examples |
|---|---|
| Live-event failure | Live-blog downtime during election night, breaking-news embed breakage, paywall regression mid-investigation |
| Editorial process failure | Missed correction window, source-management breach, fact-check process bypass |
| Tool failure affecting subscribers | CMS migration regression, paywall logic affecting >X% of readers |
| Stakeholder request | Editor / publisher / source explicitly asking "what happened?" |

Pre-defined triggers prevent retrospective theater on routine work and ensure they happen on real failures.

## Timing: aim for under one week

Google's good-vs-bad postmortem comparison cites a "four months later" example as a quality failure because contributors' memories had decayed. Source: https://sre.google/workbook/postmortem-culture/

Recommended cadence:

| Project type | Target window |
|---|---|
| Live-event retro (election night, breaking news) | Same-day debrief, written within 48h |
| Tool / CMS incident | Within one week |
| Investigation or publication launch | Within one month of project close |
| Annual review of ongoing initiative | Once per year, scoped to discrete decision points |

The empirical floor is "fresh in contributors' minds." Past one week and the narrative gets reconstructed rather than remembered.

## For event-type retros, use AAR structure

The US Army's After Action Review (FM 7-0 Appendix K) was designed for facilitated post-event debriefs and fits live-news realities better than a project-close template. Source: https://www.first.army.mil/Portals/102/FM%207-0%20Appendix%20K.pdf

Four prompts:
1. **What was supposed to happen?**
2. **What did happen?**
3. **What was right or wrong about the difference?**
4. **How do we perform to standard next time?**

Run AAR immediately after the event with all participants — election night newsroom team, live-blog runners, breaking-news desk. Use `event.md` template for this; project-close templates are wrong for live-event retros.

## The critical section: "The real problem"

This is the most valuable part of any retrospective. It answers:

> "What did we THINK we were building vs. what was ACTUALLY needed?"

**Strong example:**
> We built an admin dashboard for editors when they actually needed a Slack bot. They live in Slack — forcing them to open a web app was friction they'd never accept. The dashboard has 2 monthly active users; the Slack bot prototype we built in a day has 47.

**Weak example:**
> We learned the importance of user research.

## Template structure

```markdown
# LESSONS.md

## Project
- **Name:** [Project name]
- **Dates:** [Start - End]
- **Status:** [Completed / Abandoned / Ongoing]
- **Author:** [Your name]
- **Retrospective written:** [Date — should be within timing window above]

## Summary
[One paragraph: what it did, what impact it had, why it matters]

## What worked

### Technical wins
- [Specific decision and WHY it worked]
- [Tool/pattern that saved time]

### Process wins
- [Methodology that helped]
- [Communication pattern that worked]

## What didn't work

For each item below, separate the system layer from the people layer.
"What did the system permit or require?" comes before "What did the
people inside that system do?"

### Critical failures
- **System:** [What the architecture / process / tooling permitted]
- **People:** [What humans did inside that constraint]
- **Cost:** [Quantified impact: hours, subscribers affected, money]

### Technical debt
- [Shortcut that hurt later — and why it was the rational choice at the time]
- [Complexity that wasn't needed]

### External factors
- [Things outside your control that impacted the project]

## The real problem

What we thought: [Initial assumption]
What was actually needed: [Reality]
The gap cost us: [Time / effort / money wasted]

## Action items

Each item must have an owner, a deadline, a tracker URL, and a priority.
"Postmortems without subsequent action are indistinguishable from no postmortem."
— Google SRE

| # | Action | Owner | Deadline | Tracker | Priority |
|---|--------|-------|----------|---------|----------|
| 1 | [Specific change] | [Name] | [Date] | [Issue URL] | P0 / P1 / P2 |
| 2 | [Specific change] | [Name] | [Date] | [Issue URL] | P0 / P1 / P2 |

Failure modes to avoid:
- Ambiguous wording ("make automation better")
- Equal priority across all items (defeats the purpose of priority)
- No tracker bug or issue URL (action items vanish)
- Fixes targeting human behavior instead of system redesign ("be more careful")

Add a 30/60/90-day check-in note: who reviews progress on these, and when.

## Reusable artifacts

| Component | Why it's valuable |
|-----------|-------------------|
| [Name] | [Specific reuse potential] |
| [Name] | [Why someone else should use this] |

## Questions for next time
- [Unanswered questions worth investigating]
- [Things you'd research before starting]
```

## Voice guidelines

- Honest, specific, slightly self-deprecating
- Like explaining to a friend why the project took twice as long
- Name what the system permitted, then what the people did inside it
- Specific mistakes, not vague "challenges"
- Active voice; avoid "mistakes were made" passives that hide who decided what

## Sourcing-decision retrospectives (journalism-native)

The canonical SRE / AAR / Allspaw frameworks don't cover the editorial-judgment retrospective an investigation needs. The `research-project.md` template adds a "Source decisions revisited" section:

- Which sources we trusted, and why?
- Which we declined, and why?
- What was the redaction logic? Did it hold up?
- What would we reconsider if we ran the investigation again?
- What patterns should we carry forward to the next investigation?

Newsroom engineering blogs (NYT Open, ProPublica News Apps, WaPo Engineering) publish project descriptions but rarely retrospective methodologies, so this is treated as a journalism-native extension to the system rather than borrowed from precedent.

## What to include vs exclude

| Include | Exclude |
|---------|---------|
| Specific failures with quantified context | Vague "learnings" |
| Actual time / cost of mistakes | Blame for individuals |
| What the system permitted (then what humans did) | "Mistakes were made" passives |
| Tools that helped or hurt, by name | Generic best practices |
| Decisions you'd reverse — and why now, not then | Obvious statements |
| Surprising discoveries | Information already in other docs |

## The specificity test

For each item in "What didn't work," ask:
- Can I name the specific decision?
- Can I quantify the impact?
- Did I separate what the system permitted from what the people did?
- Would this help someone avoid the same mistake?

If no to any → be more specific.

## Red flags in your writing

If you find yourself writing these, stop and be more specific:
- "Communication is key"
- "We learned the importance of..."
- "Going forward, we should..."
- "Challenges included..."
- "There were some issues with..."
- "Mistakes were made" (who made them? in what system?)

These are placeholders for real insights. Replace them.

## Examples of good vs bad entries

**Bad — too vague:**
> - Communication could have been better
> - We underestimated the complexity
> - Testing was insufficient

**Good — specific and actionable:**
> - The schema validation step was disabled in CI for the data-import script (system) and the freelance reporter who imported new entries didn't know it had been disabled (people). Cost: 3 hours debugging a typo that caused silent failures across 12 published stories.
> - We built a custom date picker when the browser native input would have worked. Tracker: ENG-1247. Owner: K. Park. 2 days wasted.

## Journalism-specific templates

Templates are in the `templates/` directory:

| Template | Use for |
|----------|---------|
| `research-project.md` | Investigations, data journalism projects (includes sourcing-decision retro) |
| `event.md` | Conferences, workshops, campaigns (uses AAR structure) |
| `publication.md` | Newsletters, podcasts, ongoing content |
| `editorial-tool.md` | Newsroom software, AI tools |

### Template selection

```
What kind of project?
├── Investigation/analysis → research-project.md
├── Conference/workshop/election night → event.md (use AAR)
├── Newsletter/podcast → publication.md
└── Newsroom tool → editorial-tool.md
```

## Last currency sweep

2026-05-09. Sources verified: kitchensoap.com (Allspaw "Infinite Hows"), postmortems.pagerduty.com, sre.google/sre-book and /workbook, first.army.mil FM 7-0 Appendix K, adaptivecapacitylabs.com.

---

*The best retrospectives are written by people who got burned and want to save others from the same fate.*
