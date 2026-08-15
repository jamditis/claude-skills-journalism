# Worked example: environmental enforcement data

A composite example, built from patterns common to environmental records
requests in Brazil. Dates and protocol numbers are illustrative. It shows the
decision points, not a specific case.

---

## The reporting question

Which companies were fined for illegal deforestation in a given state, how
much was actually collected, and how many fines were annulled on appeal.

That is three questions and at least two bodies. Filed as one request, it
draws a "generic" denial within days.

## What was filed

**Three separate requests, same day:**

| # | Body | Object |
| --- | --- | --- |
| 1 | IBAMA | Autos de infração issued 01/01/2020–31/12/2024 in the state, CSV, with the fields already present in the agency's open-data release, plus the data dictionary |
| 2 | IBAMA | Status of collection (arrecadação) for those autos, by auto number |
| 3 | PGFN | Inscriptions in dívida ativa originating from IBAMA environmental fines, same period |

Filing separately meant one denial could not sink the others, and all three
20-day clocks ran in parallel.

## What came back

**Request 1 — partial.** A CSV arrived, but without the data dictionary and
with the CPF/CNPJ column removed entirely.

**Request 2 — denied.** Ground: art. 13, III of Decree 7.724/2012, additional
work of analysis and consolidation.

**Request 3 — granted**, in a format nobody wanted: a 400-page PDF.

## What was done about each

**Request 1 → first-instance appeal.** Two arguments. First, CNPJ is not
personal data — it identifies a legal entity, and IBAMA itself publishes
sanctioned companies' CNPJs elsewhere. Second, on the individual CPFs, art. 7
§2º requires partial access, so masking the CPF column and delivering the rest
was the correct outcome, not deleting it. The data dictionary was requested
again in the same appeal.

*Result: CNPJ restored, CPF masked, dictionary delivered. This is the ordinary
outcome — the personal-data objection is the most over-applied ground in
Brazilian practice, and it rarely survives an appeal that cites art. 7 §2º.*

**Request 2 → appeal, not refiling.** The "additional work" ground is the one
worth fighting: the appeal argued the agency was being asked to export an
existing field from an existing system, not to compute anything, and invoked
art. 13, parágrafo único, which requires the agency, caso tenha conhecimento,
to indicate where the source information is. The appeal asked the agency to
state whether it had that knowledge and to identify the source if it did.

*A refiling here would have conceded the point and started over.*

**Request 3 → appeal on the format, within the 10-day window.** The agency
had a CSV export in its own open-data release (see request 1), so the PDF was
not full compliance — LAI art. 11 §5 entitles the requester to digitally
stored information in that digital format. The appeal cited art. 11 §5
alongside art. 8 §3º, II and III, and asked for the same content in CSV. A
fresh request would have worked too, but it forfeits the shorter 10-day
appeal clock for a new 20-day cycle with no guarantee of a better outcome.

## Timeline

| Day | Event |
| --- | --- |
| 0 | Three requests filed |
| 18 | Requests 1 and 3 answered |
| 20 | Request 2 denied |
| 22 | Appeals filed on 1, 2, and 3 |
| 31 | Request 1 appeal granted in part |
| 45 | Request 2 appeal granted after the agency was asked to locate the raw data; request 3 appeal granted, CSV received |

Seven weeks from filing to usable data, with no denial reaching CGU. Planning
the reporting on a two-month horizon rather than a two-week one was what made
that acceptable.

## What this example is meant to teach

1. Split the question before filing. Three narrow requests beat one broad one.
2. Diagnose before responding. Appeal, refile, and file-new are three
   different tools, and using the wrong one costs weeks.
3. The personal-data objection is usually over-applied. Cite art. 7 §2º.
4. An unusable digital format is not full compliance when the agency already
   holds the data digitally. Appeal it under art. 11 §5 rather than treating
   it as granted.
5. Ask for the data dictionary in the original request, not after.
