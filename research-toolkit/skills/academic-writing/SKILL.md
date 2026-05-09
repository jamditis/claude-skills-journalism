---
name: academic-writing
description: Academic writing, research methodology, and scholarly communication workflows. Use when writing papers, literature reviews, grant proposals, conducting research, managing citations, preparing for peer review, choosing OA routes under Plan S / 2026 OSTP Nelson Memo, posting preprints, working with persistent identifiers (ORCID, DOI, ROR), assigning CRediT contributor roles, preregistering analyses on OSF / AsPredicted, or disclosing LLM use to journals and funders. Essential for researchers, graduate students, and academics across disciplines.
---

# Academic writing and research methodology

Systematic approaches for scholarly writing, research design, and academic communication.

## Research design fundamentals

### Research question development

```markdown
## Crafting a research question

### The FINER criteria
- **F**easible: Can you actually do this research?
- **I**nteresting: Does it matter to the field?
- **N**ovel: Does it add new knowledge?
- **E**thical: Can it be done ethically?
- **R**elevant: Does it address a real problem?

### Question types
| Type | Purpose | Example |
|------|---------|---------|
| Descriptive | Document phenomena | "What are the characteristics of X?" |
| Comparative | Compare groups/conditions | "How does X differ between groups?" |
| Correlational | Examine relationships | "Is there a relationship between X and Y?" |
| Causal | Establish causation | "Does X cause Y?" |
| Exploratory | Generate hypotheses | "What factors might explain X?" |

### Refining your question
Start broad → Narrow progressively

Draft 1: "How does social media affect politics?"
Draft 2: "How does Twitter use affect political polarization?"
Draft 3: "How does exposure to partisan Twitter accounts affect
         political attitude polarization among US adults?"
Draft 4: "Does increased exposure to ideologically homogeneous Twitter
         feeds increase affective polarization among politically
         engaged US adults aged 18-35?"
```

### Literature review strategy

```markdown
## Systematic literature search

### Database selection by field
- **Multidisciplinary**: Web of Science, Scopus, Google Scholar
- **Social Sciences**: JSTOR, ProQuest, SSRN
- **Communication**: Communication Abstracts, ComAbstracts
- **Health**: PubMed, MEDLINE, CINAHL
- **Education**: ERIC
- **Business**: Business Source Complete

### Search strategy template
1. **Identify key concepts** from research question
2. **Generate synonyms** for each concept
3. **Combine with Boolean operators**

Example for: "social media political polarization"

Concept 1: social media
- OR: Twitter, Facebook, Instagram, "social networking sites",
      "online platforms", "digital media"

Concept 2: political
- OR: partisan, ideological, electoral, civic

Concept 3: polarization
- OR: division, extremism, "attitude change", radicalization

Combined search:
(Twitter OR Facebook OR "social media" OR "social networking")
AND (political OR partisan OR ideological)
AND (polarization OR division OR extremism)

### Inclusion/exclusion criteria
Document your criteria:
- Publication date range: [X to present]
- Languages: [English only / multiple]
- Publication types: [Peer-reviewed only / include preprints]
- Geographic scope: [Global / specific countries]
- Methodologies: [All / specific approaches]

### Managing your search
- Save searches to re-run later
- Export results to reference manager
- Track number of results at each stage
- Document date of each search
```

### Citation management

```python
# Zotero/reference manager integration patterns

# For automated citation workflows
CITATION_STYLES = {
    'apa7': 'American Psychological Association 7th edition',
    'mla9': 'Modern Language Association 9th edition',
    'chicago': 'Chicago Manual of Style 17th edition',
    'harvard': 'Harvard Reference format',
    'ieee': 'IEEE',
    'vancouver': 'Vancouver (medicine)',
}

# BibTeX entry template
BIBTEX_ARTICLE = """
@article{{{citekey},
    author = {{{author}}},
    title = {{{title}}},
    journal = {{{journal}}},
    year = {{{year}}},
    volume = {{{volume}}},
    number = {{{number}}},
    pages = {{{pages}}},
    doi = {{{doi}}}
}}
"""

# Common citation patterns by context
CITATION_CONTEXTS = {
    'introducing_concept': "According to Author (Year), ...",
    'supporting_claim': "Research has shown that X (Author, Year; Author, Year).",
    'contrasting': "While Author (Year) argues X, Author (Year) contends Y.",
    'methodology_reference': "Following the method developed by Author (Year), ...",
    'direct_quote': 'Author (Year) states that "exact quote" (p. X).',
}
```

## Paper structure and writing

### IMRaD structure (scientific papers)

```markdown
## Standard research paper sections

### Abstract (150-300 words typically)
- Background (1-2 sentences)
- Purpose/objective (1 sentence)
- Methods (2-3 sentences)
- Results (2-3 sentences)
- Conclusions (1-2 sentences)

### Introduction
**Funnel structure:**
1. Broad context - Why does this topic matter?
2. Narrow focus - What's the specific problem?
3. Gap identification - What don't we know?
4. Research question/hypothesis - What will you investigate?
5. Contribution preview - Why does this study matter?

### Literature Review
**Organize thematically, not chronologically:**
1. Theme 1: Key findings, debates, gaps
2. Theme 2: Key findings, debates, gaps
3. Theme 3: Key findings, debates, gaps
4. Synthesis: How themes connect to your study

### Methods
**The reproducibility test:** Could another researcher replicate your study from this section alone?

Include:
- Participants/sample (who, how selected, N)
- Materials/measures (what instruments, their validity)
- Procedure (step-by-step what happened)
- Analysis approach (statistical tests, qualitative methods)
- Ethical considerations (IRB, consent)

### Results
**Report, don't interpret:**
- Present findings systematically
- Use tables/figures for complex data
- Report effect sizes, not just p-values
- Address each research question/hypothesis

### Discussion
**Reverse funnel structure:**
1. Summary of key findings
2. Interpretation in context of literature
3. Theoretical implications
4. Practical implications
5. Limitations
6. Future research directions
7. Conclusion
```

### Academic writing style

```markdown
## Writing conventions

### Voice and tense
| Section | Tense | Example |
|---------|-------|---------|
| Abstract | Past (methods/results), Present (conclusions) | "We found... This suggests..." |
| Introduction | Present (established knowledge) | "Research shows..." |
| Methods | Past | "Participants completed..." |
| Results | Past | "Analysis revealed..." |
| Discussion | Present + Past | "These findings indicate... We found..." |

### Hedging language
Appropriate hedging (avoiding overclaiming):
- "This suggests that..." (not "This proves that...")
- "may be related to" (not "causes")
- "Results indicate..." (not "Results demonstrate conclusively...")
- "One possible explanation..." (not "The explanation...")

### Transition words by function
**Addition:** furthermore, moreover, additionally, in addition
**Contrast:** however, nevertheless, conversely, in contrast
**Cause/effect:** therefore, consequently, as a result, thus
**Example:** for instance, specifically, to illustrate
**Sequence:** first, subsequently, finally, meanwhile
**Summary:** in summary, overall, in conclusion

### Paragraphs
Each paragraph should:
1. Begin with a topic sentence
2. Contain one main idea
3. Include supporting evidence
4. Connect to adjacent paragraphs
5. Average 100-200 words (varies by field)
```

### Common writing problems

```markdown
## Issues to avoid

### Wordiness
❌ "It is important to note that the results demonstrate..."
✅ "Results demonstrate..."

❌ "In order to investigate..."
✅ "To investigate..."

❌ "A total of 50 participants..."
✅ "Fifty participants..."

### Weak verbs
❌ "The study was conducted by the researchers"
✅ "The researchers conducted the study"

❌ "There was a significant difference found"
✅ "We found a significant difference"

### Vague language
❌ "Several studies have shown..."
✅ "Three studies (Author, Year; Author, Year; Author, Year) showed..."

❌ "The results were significant"
✅ "The results were statistically significant (p < .05, d = 0.45)"

### Unnecessary jargon
- Define technical terms on first use
- Use simpler words when equally precise
- Consider your audience's expertise level

### Citation problems
❌ Citing secondary sources without noting
✅ "(Author, Year, as cited in Author, Year)"

❌ String citations without synthesis
✅ Group citations that make the same point; distinguish those that differ
```

## Peer review and revision

### Responding to reviewers

```markdown
## Response letter template

Dear Editor and Reviewers,

Thank you for the thoughtful feedback on our manuscript titled "[Title]"
(Manuscript ID: [Number]). We have carefully considered all comments and
revised the manuscript accordingly. Below, we provide point-by-point
responses to each comment.

---

## Reviewer 1

### Comment 1.1
[Quote or paraphrase the reviewer's comment]

**Response:**
[Your response explaining what you did]

**Changes made:**
[Quote the specific changes with page/line numbers]
"New text here..." (p. X, lines XX-XX)

### Comment 1.2
[Continue for each comment]

---

## Reviewer 2
[Same format]

---

We believe these revisions have substantially strengthened the manuscript
and hope you will find it suitable for publication in [Journal Name].

Sincerely,
[Authors]
```

### Handling criticism

```markdown
## Types of reviewer feedback

### Must address
- Methodological concerns
- Missing literature
- Unclear writing
- Logical gaps in argument
- Statistical errors

### Negotiate carefully
- Requests for additional analyses
- Suggestions to restructure
- Disagreements on interpretation

### Pushback appropriately
- Requests outside scope
- Misunderstandings of your argument
- Contradictory advice from reviewers

### Response strategies
**Agreement:** "We thank the reviewer for this suggestion. We have [action]."
**Partial agreement:** "We appreciate this point. While [acknowledge validity], we [explain your approach]. However, we have [partial accommodation]."
**Respectful disagreement:** "We thank the reviewer for raising this issue. We have considered this carefully; however, [explanation]. We hope the reviewer will find this reasoning persuasive."
```

## Grant proposals

### Proposal structure (NSF/NIH style)

```markdown
## Standard grant components

### Specific aims (1 page)
**Opening paragraph:** What's the problem? Why does it matter?
**Gap statement:** What's missing from current understanding?
**Long-term goal:** Your research program vision
**Objective:** What this specific project will accomplish
**Central hypothesis:** Your testable prediction
**Aims:** 2-4 specific, achievable objectives
**Impact statement:** Why funding this matters

### Significance (2-3 pages)
- Importance of the problem
- Gaps in current knowledge
- How your work advances the field
- Potential impact if successful

### Innovation (1 page)
- What's new about your approach?
- Conceptual innovation
- Methodological innovation
- Technical innovation

### Approach (6-12 pages)
For each aim:
- Rationale
- Preliminary data (if any)
- Research design
- Methods
- Expected outcomes
- Potential problems and alternatives
- Timeline

### Broader impacts
- Training opportunities
- Dissemination plans
- Benefits to society
- Diversity and inclusion
```

### Budget justification

```markdown
## Budget categories

### Personnel
- PI salary and effort (% time)
- Co-investigators
- Postdocs (salary + benefits)
- Graduate students (stipend + tuition + benefits)
- Undergraduate researchers
- Technical staff

### Equipment
- Items over $5,000 (check sponsor threshold)
- Justify necessity for project

### Supplies
- Lab consumables
- Software licenses
- Participant payments

### Travel
- Conference presentations
- Data collection sites
- Collaborator visits

### Other direct costs
- Publication costs
- Participant incentives
- Transcription services
- Equipment maintenance

### Indirect costs (F&A — facilities and administrative)
- Each institution negotiates an F&A rate with its cognizant federal agency.
- The rate applies to **modified total direct costs (MTDC)**, not raw total
  direct costs — exclude equipment >$5K, tuition, participant support,
  subaward portions over $25K, and a few other categories per the
  institution's negotiated agreement.
- R1 universities commonly negotiate 55-70% of MTDC; smaller institutions
  often run lower. Always confirm the current rate with your sponsored
  programs office before budgeting.
```

## Publishing strategy

### Journal selection

```markdown
## Evaluating journals

### Quality indicators
- Impact factor (use cautiously)
- Acceptance rate
- Review time
- Time to publication
- Reputation in your field
- Indexing (Web of Science, Scopus)

### Fit indicators
- Scope alignment
- Audience match
- Article type (empirical, theoretical, review)
- Open access route (see below)

### Open access routes
- **Gold OA** — published OA in a fully OA journal; usually requires an
  Article Processing Charge (APC), often $1,000-$3,000+.
- **Green OA** — closed-access journal but author self-archives an
  accepted manuscript in a repository (institutional, arXiv, etc.) under
  the publisher's allowed embargo.
- **Diamond / Platinum OA** — fully OA journal with no APC; supported
  by a sponsor (society, university, consortium). Increasingly common
  in social sciences and humanities.
- **Hybrid** — a closed-access journal that lets individual articles
  go OA for an APC. Note: hybrid is *excluded* from Plan S compliance
  and from many funder OA mandates — verify before paying an APC.
- **Bronze** — free to read but no formal OA license; the publisher
  can revoke access. Treat as not-actually-OA for compliance purposes.

### Funder mandates (US + Europe, as of 2026)
- **OSTP Nelson Memo (US)** — federally-funded research must be made
  immediately publicly accessible upon publication, with no embargo.
  Implementation deadline was **end of 2025**, so as of 2026 this is
  in effect for all major US federal funders (NIH, NSF, DOE, NASA, etc.).
- **Plan S (cOAlition S)** — European funders (Wellcome, UKRI, ANR,
  many others) require immediate Gold or Diamond OA, or Green OA
  with no embargo and a CC-BY license. Hybrid is not compliant.
- Verify the funder's most recent policy before submission — accepted
  routes shift, and some funders cap APCs.

### Red flags (predatory journals)
- Aggressive email solicitation
- Rapid "peer review" (days)
- Unclear editorial board
- Not indexed in major databases
- "Pay to publish" with no clear OA model
- Poor website quality

### Resources for vetting journals + ethics
- **Think. Check. Submit.** (thinkchecksubmit.org) — checklist for legitimacy.
- **DOAJ** (Directory of Open Access Journals) — vetted OA-journal index.
- **Journal Citation Reports** — paid Web of Science product for impact factor.
- **Cabells Predatory Reports** — subscription-based replacement for the
  original Beall's List, which was taken down in 2017 (only stale mirrors
  remain — don't rely on them as a current source of truth).
- **Retraction Watch Database** — searchable record of retractions and
  publisher misconduct; useful for vetting authors and journals.
- **COPE** (Committee on Publication Ethics, publicationethics.org) —
  authoritative guidelines for editors and authors on ethics and integrity.
- **ICMJE** (International Committee of Medical Journal Editors,
  icmje.org/recommendations) — defines authorship criteria, conflict-of-
  interest disclosure, and reporting standards used across many fields.
```

### Cover letter template

```markdown
Dear Dr. [Editor's name],

We are pleased to submit our manuscript titled "[Full title]" for
consideration as a [article type] in [Journal Name].

**Summary (2-3 sentences):**
[What you did and what you found]

**Significance (2-3 sentences):**
[Why this matters for the journal's readership]

**Fit statement:**
[Why this journal specifically]

**Declarations:**
- This manuscript is original and not under consideration elsewhere
- All authors have approved the submission
- [Conflict of interest statement]
- [Funding acknowledgment]

**Suggested reviewers (if requested):**
1. [Name, affiliation, email] - Expert in [relevant area]
2. [Name, affiliation, email] - Expert in [relevant area]
3. [Name, affiliation, email] - Expert in [relevant area]

**Reviewers to exclude (if any):**
[Name] - [Brief, professional reason]

We look forward to your response.

Sincerely,
[Corresponding author name]
[Title, affiliation]
[Contact information]
```

## Preprints and persistent identifiers

### Preprint servers (post a working version, get cited earlier)

Preprints are author-submitted manuscripts posted before formal peer
review. Most journals now permit (or actively encourage) preprinting;
verify the target journal's policy before posting if you're unsure.

| Server | Field | Notes |
|--------|-------|-------|
| **arXiv** (arxiv.org) | Physics, math, CS, quantitative bio, econ, stats | Oldest, largest; moderation by section. |
| **SSRN** (ssrn.com) | Social sciences, law, econ, finance | Owned by Elsevier since 2016 — some authors prefer SocArXiv as an alternative. |
| **bioRxiv** (biorxiv.org) | Biology | Cold Spring Harbor Laboratory; widely cited. |
| **medRxiv** (medrxiv.org) | Health sciences, medicine | Light moderation for safety claims; do not preprint clinical-trial results without preregistration. |
| **EarthArXiv** | Earth, planetary, environmental sciences | Community-run via the OSF infrastructure. |
| **PsyArXiv** | Psychology + behavioral sciences | OSF-hosted. |
| **SocArXiv** | Sociology + social sciences | OSF-hosted; Elsevier-independent alternative to SSRN. |
| **EngrXiv** | Engineering | OSF-hosted. |

**Why preprint:** Faster timestamp on priority claims, citable months
before journal acceptance, and broader feedback before final review.
(The 2026 OSTP Nelson Memo governs immediate public access to the
*peer-reviewed* version of federally-funded US research at publication
— it is not a preprint mandate. Preprinting is a separate, voluntary
choice that complements but doesn't satisfy Nelson Memo compliance.)

### Persistent identifiers — get an ORCID and use DOIs

- **ORCID iD** (orcid.org) — Free 16-digit identifier that
  unambiguously links you across publishers, funders, and institutions.
  Required by most major journals and funders. Connect it to your
  CV, manuscripts, datasets, software, and grant applications.
- **DOI** (doi.org) — Persistent identifier for scholarly objects.
  Assigned automatically by journals at acceptance; you can also mint
  DOIs for your own datasets, code, posters, and preprints via Zenodo
  (zenodo.org) or your institutional repository — useful for citing
  non-journal outputs.
- **ROR** (ror.org) — Persistent identifier for research organizations,
  used by funders and publishers to disambiguate institutional names.

## Research ethics

### Ethical considerations checklist

```markdown
## Before starting research

### Human subjects
- [ ] IRB/ethics board approval obtained
- [ ] Informed consent procedures established
- [ ] Vulnerable populations identified and protected
- [ ] Privacy and confidentiality measures in place
- [ ] Data security plan established
- [ ] Risk/benefit ratio acceptable

### Data management
- [ ] Data management plan created
- [ ] Secure storage arranged
- [ ] Sharing/archiving plans documented
- [ ] Retention period determined
- [ ] Destruction procedures established

### Authorship
- [ ] Contribution criteria discussed (use ICMJE definition: substantial
      contribution + drafting/revising + final approval + accountability)
- [ ] Author order agreed upon
- [ ] All contributors will meet authorship criteria
- [ ] Acknowledgments planned for non-author contributors
- [ ] **CRediT taxonomy** (credit.niso.org) roles assigned for each
      author — most major journals now require or recommend CRediT,
      which has 14 standardized contributor roles (Conceptualization,
      Methodology, Software, Validation, Formal analysis, Investigation,
      Resources, Data curation, Writing — original draft, Writing —
      review & editing, Visualization, Supervision, Project administration,
      Funding acquisition).

### Conflicts of interest
- [ ] Financial conflicts identified
- [ ] Non-financial conflicts identified
- [ ] Disclosure plan established

### Reproducibility
- [ ] Analysis plan pre-registered on **OSF** (osf.io) or **AsPredicted**
      (aspredicted.org) before data collection — distinguishes
      confirmatory from exploratory analyses and protects against
      HARKing. Check whether the target journal accepts **Registered
      Reports** (peer review of the design *before* data collection,
      with in-principle acceptance regardless of results) — this format
      now exists at 350+ journals across psychology, biomedical, and
      social sciences as of 2026.
- [ ] Code will be shared (consider a GitHub release + Zenodo DOI for
      versioned, citable code archives)
- [ ] Data will be shared (FAIR principles; institutional repository,
      Dryad, Figshare, or domain-specific repository as appropriate)
- [ ] Materials will be shared
```

### Avoiding research misconduct

```markdown
## Types of misconduct

### Fabrication
- Making up data or results
- Never acceptable under any circumstances

### Falsification
- Manipulating data, equipment, or processes
- Selectively omitting data to change conclusions
- Image manipulation beyond acceptable adjustment

### Plagiarism
- Using others' words without attribution
- Self-plagiarism (reusing own published work without acknowledgment)
- Paraphrasing too closely

### Other questionable practices
- P-hacking (running multiple analyses until significant)
- HARKing (hypothesizing after results known)
- Salami slicing (fragmenting one study into many papers)
- Gift/ghost authorship
- Selective reporting of results
```

## AI / LLM use in academic writing

LLM-assisted writing is the defining 2024-2026 ethics issue across
academic publishing. Every major journal, funder, and ethics body has
issued policy in this window — and policies are still tightening.
Treat anything below as the floor, not the ceiling: read your target
journal's current submission guidelines AND your funder's most recent
policy before submitting.

### What's universally prohibited (as of 2026)

- **LLM authorship.** ICMJE, COPE, Nature, Science, NEJM, Cell, JAMA,
  Lancet, and the major university presses all explicitly prohibit
  listing an LLM (ChatGPT, Claude, Gemini, etc.) as a co-author. LLMs
  cannot meet the accountability and approval criteria authorship
  requires. Use the acknowledgments section or a methods/disclosure
  statement instead — never the author byline.
- **Generating fabricated citations.** LLMs are well-documented to
  produce plausible-looking but fabricated DOIs, page numbers, and
  even author/title combinations that don't exist. Every citation in
  a manuscript must be verified against the source — the LLM-induced
  fake-citation rate has been a top retraction trigger since 2023.
- **Generating data, results, or images.** Synthesizing experimental
  data, fabricating figures, or using generative AI to "fill in"
  results that weren't actually obtained is research misconduct under
  COPE's definition.
- **Undisclosed substantial use.** Most journals require disclosure
  of any LLM use beyond trivial spell-check/grammar assistance. Failing
  to disclose meaningful use can be grounds for retraction.

### What's typically permitted (with disclosure)

- Idea brainstorming and outlining
- Language polishing and grammar correction
- Translation of your own writing
- Code generation for analyses (with explicit testing)
- Summarization of your own notes or transcripts
- Generating boilerplate sections (cover letters, IRB language)
  that you then fact-check and own

### Disclosure language (template)

Most journals want a methods/acknowledgments statement that names the
tool, version (if available), and what it was used for. Example:

> During the preparation of this work the author(s) used [tool name,
> e.g., ChatGPT-5, Claude Opus 4.7, Gemini 3 Pro] in order to
> [specific use, e.g., language polishing of the introduction; drafting
> code for the cluster analysis in section 3.2]. After using this tool,
> the author(s) reviewed and edited the content as needed and take(s)
> full responsibility for the content of the publication.

Adjust to match the target journal's exact required wording — Elsevier,
Springer Nature, Wiley, Taylor & Francis, IEEE, and ACM each publish
their own preferred language.

### Disclosure checklist before submission

- [ ] Read the target journal's AI/LLM policy in the current submission
      guidelines (policies updated multiple times per year).
- [ ] Read your funder's policy — some (Wellcome, NSF) have stricter
      rules than the journal.
- [ ] Add a disclosure statement using the journal's preferred language.
- [ ] Verify every citation manually — do not trust LLM output for any
      DOI, author list, page range, or quoted passage.
- [ ] Verify every numerical claim, date, and named fact.
- [ ] Re-read the full manuscript to ensure your voice and argument
      structure dominate, not the LLM's.
- [ ] If the LLM was used for code or analysis, re-run with seeds and
      verify all reported numbers reproduce.

### Detection tools (limited reliability)

GPTZero, Turnitin AI Detection, Originality.ai, and similar tools have
documented high false-positive rates against non-native-English writers
and against legitimately human-written technical text — and high false-
negative rates against current models with light editing. **Pangram
Labs** (pangram.com) has published more rigorous benchmarks and tends
to outperform the older detectors at roughly equivalent settings, but
is still not a definitive arbiter and shares the same fundamental
limits when authors edit LLM output substantially. Detection output
should never be the sole basis for a misconduct finding; journals that
rely on it as a gatekeeping signal are increasingly walking that back.
Treat detector results as a flag for follow-up discussion with the
author, not as evidence on their own.

## Productivity and workflow

### Writing routine

```markdown
## Sustainable academic writing

### Daily writing practice
- Write at same time daily (habit formation)
- Start with minimum viable goal (e.g., 30 minutes)
- Track progress (word counts, time)
- Protect writing time from meetings/email

### Managing large projects
1. Break into smallest possible tasks
2. Set deadlines for each component
3. Schedule regular writing blocks
4. Build in buffer time
5. Get feedback early and often

### Overcoming blocks
- Start with easiest section
- Write a "shitty first draft" (Anne Lamott)
- Use placeholders for citations/data
- Talk through ideas with colleague
- Change environment
- Return to outline/structure
```

### Tools for academics

| Purpose | Tools |
|---------|-------|
| Reference management | Zotero (recommended; open source, syncs across devices), Paperpile (web-first, Google Docs integration), EndNote, Citavi. **Note on Mendeley:** Elsevier announced an end to Mendeley Desktop downloads in September 2022, then later restored availability. Mendeley Desktop remains legacy software with no further feature development; the Mendeley Reference Manager (web/cloud) is the actively maintained product. New users are better served by Zotero or Paperpile. |
| Writing | Scrivener, Overleaf (LaTeX collaboration), Word, Typst (newer LaTeX alternative) |
| Collaboration | Google Docs, Overleaf, Hedgedoc |
| Version control | Git / GitHub / GitLab (true version control). **Word's Track Changes is collaborative editing, not version control** — it lacks branching, merging, history rewrite, and atomic commits. |
| Task management | Todoist, Notion, Trello |
| Focus | Forest, Freedom, Cold Turkey |
| Analysis | R, Python, SPSS, Stata, NVivo, Julia |
| Visualization | R/ggplot2, Python/matplotlib + plotly, Observable, Tableau |
| LLM-assisted writing | See "AI / LLM use in academic writing" section above for disclosure requirements before using any of these. |
