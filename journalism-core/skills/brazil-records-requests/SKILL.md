---
name: brazil-records-requests
description: Public records requests under Brazil's Access to Information Law (Lei 12.527/2011, "LAI"). Use when filing, tracking, or appealing a request to any Brazilian government body — federal, state, municipal, judicial or legislative — including Fala.BR filings, the four-level appeal chain (first instance, agency head, CGU, CMRI), and rewriting requests denied as generic or as requiring additional analysis work. Triggers on "LAI", "Lei de Acesso à Informação", "pedido de acesso à informação", "e-SIC", "Fala.BR", "recurso à CGU", "CMRI", or any request for Brazilian government records. Companion to foia-requests, which covers the US.
---

# Brazilian public records requests (LAI)

Brazil's Access to Information Law — Lei 12.527/2011, universally called the
LAI — is one of the stronger transparency statutes in Latin America and one of
the most under-used by reporters. Most denials are not legal defeats. They are
drafting failures that a differently worded request would have avoided.

This skill covers the full cycle: choosing the body, drafting, filing,
tracking, and the four-level appeal chain.

## When to use

- Drafting a request to any Brazilian government body
- Deciding which body and which portal actually holds the records
- Diagnosing a denial and deciding whether to appeal or refile
- Writing an appeal at any of the four levels
- Planning the timeline of an investigation that depends on records
- Training reporters on LAI practice

## Do not use for

- US records requests — use `foia-requests`
- Court case data, which in Brazil is mostly public through other channels
  (DataJud, e-SAJ, PJe) and rarely needs a records request
- Data already published under transparência ativa (see "Check first" below)

## Check first: is a request even necessary?

Art. 8 of the LAI obliges agencies to publish core categories of information
on their own initiative. Filing for something already public wastes 20 days
and signals inexperience to the agency.

Check, in order:

1. **Portal da Transparência** (portaltransparencia.gov.br) — federal spending,
   payroll, sanctions, benefits
2. **Dados abertos** (dados.gov.br) and the agency's own open-data page
3. **PNCP** (pncp.gov.br) — federal, state and municipal procurement since 2021
4. **Painel Lei de Acesso à Informação** (CGU) — request statistics by agency
5. **Busca de Pedidos e Respostas** (CGU) — published federal responses can
   show how an agency describes its own data. Sensitive, personal, classified,
   or otherwise restricted information may be redacted or excluded. A missing
   result does not prove that no earlier request exists.
6. **Achados e Pedidos** (achadosepedidos.org.br), Abraji and Transparência
   Brasil's archive of requests and responses across jurisdictions

Step 5 is the single highest-value habit in Brazilian records work. Reading
prior responses from the same agency teaches you its internal vocabulary,
which is what determines whether your request is understood or bounced.

## Step 1: Identify the body and the portal

There is no single filing system. The portal follows the body.

| Body | Where to file |
| --- | --- |
| Federal executive (ministries, agencies, autarquias, federal state-owned firms) | **Fala.BR** (falabr.cgu.gov.br), gov.br login required |
| States and the Federal District | Each state runs its own e-SIC; some have joined Fala.BR |
| Municipalities | Municipal e-SIC; smaller cities often accept email or in-person only |
| Judiciary | Each court's own SIC, under CNJ rules |
| Ministério Público | Each MP's own SIC, under CNMP rules |
| Legislature | Câmara, Senado, and each state assembly and city council run separate systems |

Practical consequences:

- **Filing with the wrong body costs the full 20 days.** The agency will
  answer that it does not hold the information, and under art. 11, §1º, III it
  should indicate who does — but frequently does not.
- **When you are unsure which of two bodies holds the record, file with
  both.** There is no penalty and no cost.
- **Sub-national practice is uneven.** Many municipal systems are broken,
  unstaffed, or require in-person filing. Budget extra time and keep evidence
  of failed filing attempts; that evidence supports later escalation.
- **CGU and CMRI appeals only reach the federal executive.** For state and
  municipal denials, the last administrative step is usually the local
  controladoria or ouvidoria, and after that the courts.

## Step 2: Draft the request

### What the law lets you refuse to explain

Art. 10 §3º forbids agencies from requiring the reasons for a request.

Do not explain that you are a journalist, do not name the story, do not
describe what you plan to do with the data. It is legally unnecessary and
it invites the request to be routed to the press office instead of the
records unit. Filing as a private citizen is normal practice.

### What the request must contain

- Requester identification (name and a valid ID document — CPF is common but
  not mandated by art. 12; a user already identified on Fala.BR does not need
  to re-disclose it) — anonymous filing is not available
- A specific description of the information sought
- The delivery format you want

For a federal-executive request filed outside Fala.BR, add a physical or
electronic address for communications. Decree 7.724/2012, art. 12, IV requires
it. Other bodies can have different local rules.

### What makes a request survive

Be specific about the record, not about the subject. Agencies hold documents
and databases, not topics.

| Weak | Strong |
| --- | --- |
| "All information about environmental fines" | "The complete IBAMA sanctions database (autos de infração) issued between 01/01/2020 and 31/12/2024, in CSV, containing the fields already published in the agency's open-data release" |
| "Contracts with company X" | "The full text of contracts and their amendments signed between the ministry and CNPJ 00.000.000/0001-00 since January 2023, with contract numbers and SEI process numbers" |
| "Documents about the decision" | "Process number 00000.000000/2024-00 in full, including technical opinions (notas técnicas) and dispatches" |

Techniques that work:

- **Ask for the database, not a report.** Requesting an existing table in CSV
  or XLSX avoids the "additional analysis work" objection, because the agency
  only has to export what it already has.
- **Cite the SEI or process number** whenever you have one. It removes all
  ambiguity about scope.
- **Bound the request by date and by field.** Unbounded requests draw the
  "disproportionate" objection.
- **Ask for the data dictionary too.** A dump without field definitions often
  cannot be used.
- **Split a broad question into several narrow requests.** Each is judged
  separately, so one refusal does not sink the rest, and each starts its own
  20-day clock in parallel.
- **Ask for the existing digital format.** If the information is stored
  digitally, agree to receive it in that format under LAI art. 11 §5º. For a
  dataset, request its existing CSV, XLSX, or other digital export. Do not
  demand conversion of a document that exists only as a PDF.

Use `templates/pedido-inicial.md` for the general form and
`templates/pedido-base-de-dados.md` when the target is a database.

## Step 3: Deadlines

Under art. 11:

- **Immediate**, when the information is readily available
- Otherwise **20 days** to grant access, state the reasons for refusal, or
  say the body does not hold the information and indicate who does
- **Extendable once, by 10 days**, with express written justification
  communicated to the requester (art. 11 §2º)

So the realistic worst case for a first answer is 30 days. Silence does not
route through the same channel as a reasoned denial — see "Step 5: The
appeal chain" for the federal-executive procedure (reclamação, not a direct
appeal).

Service is free; agencies may charge only for reproduction costs, and
low-income requesters are exempt on declaration (art. 12).

Plan investigations backwards from this: a request filed in March with a full
appeal chain may not resolve until August.

## Step 4: Diagnose the denial

Almost all denials fall into a few categories. The right response differs
for each — appealing a denial that should have been refiled wastes months.

Decree 7.724/2012 applies only to the federal executive. The first three
grounds below use that Decree. For state, municipal, judicial, legislative,
and Ministério Público bodies, check the local rule before characterizing a
denial or citing the Decree.

| Denial | Basis | Response |
| --- | --- | --- |
| Generic request | Federal executive: Decree 7.724/2012, art. 13, I | **Refile**, narrowed. Faster than appealing. |
| Disproportionate or unreasonable | Federal executive: Decree 7.724, art. 13, II | **Refile** in slices, or appeal if the volume claim is implausible |
| Requires additional analysis, interpretation or consolidation of data | Federal executive: Decree 7.724, art. 13, III | **Appeal.** If it knows where the source information is, the agency must identify that location (art. 13, parágrafo único). Ask it to state whether it has that knowledge and to identify the source if it does. |
| Personal data | LAI art. 31 | **Appeal**, requesting the record with personal fields redacted. Partial access is the rule, full withholding the exception. |
| Classified | LAI arts. 23–24 | **Appeal**, demanding the classification instrument (termo de classificação), its date, level and authority. The maximum restriction periods are 5 years for reservada, 15 for secreta, and 25 for ultrassecreta. Check whether an earlier event ends the restriction. |
| Body does not hold it | LAI art. 11, §1º, III | Ask which body does — the agency is required to say — then refile there |
| Silence (federal executive) | Decree 7.724/2012, arts. 22–23 | **Reclamação** to the monitoring authority, not a direct appeal — see Step 5. |
| Silence (other spheres) | Local LAI regulation | Usually an immediate appeal under LAI art. 15; confirm the state, municipal, judicial or legislative body's own rule — Decree 7.724/2012 binds the federal executive only. |

Two provisions worth knowing by heart:

- **Art. 21**: information necessary to the judicial or administrative defense
  of fundamental rights cannot be withheld, and information about conduct
  implicating human rights violations by state agents cannot be restricted.
  This defeats many classification claims in cases involving police,
  military or prison records.
- **Art. 14**: you are entitled to the full text of the denial decision.
  Request it. Agencies often refuse informally, by email, without a formal
  decision that can be appealed — demanding the decision forces the issue.

## Step 5: The appeal chain

**A reasoned denial** goes up four administrative levels. Each has its own
window, and missing one closes the chain.

```
Reasoned denial
   │  10 days to file
   ▼
1. Immediate superior authority          → decides in 5 days   (LAI art. 15)
   │  10 days
   ▼
2. Agency head (autoridade máxima)       → decides in 5 days
   │  10 days
   ▼
3. CGU — federal executive only          → decides in 5 days   (LAI art. 16)
   │  10 days
   ▼
4. CMRI — final administrative recourse  (LAI art. 16 §3º)
```

**Silence from a federal executive body** does not enter that chain directly.
It goes through a separate reclamação step first:

```
Silence past the deadline (30 days after filing, at the earliest)
   │  10 days to file
   ▼
1. Reclamação to the monitoring authority → decides in 5 days  (Decree 7.724/2012, art. 22)
   │  if unsuccessful, 10 days
   ▼
2. Recurso to CGU                         → decides in 5 days  (Decree 7.724/2012, art. 23)
   │  10 days
   ▼
3. CMRI — final administrative recourse   (LAI art. 16 §3º)
```

For state, municipal, judicial and legislative bodies, Decree 7.724/2012 does
not apply — check whether the local LAI regulation has an equivalent
reclamação step, or whether silence is appealed directly under LAI art. 15.

Notes from practice:

- The 5-day decision windows are routinely missed. Escalate on expiry rather
  than waiting.
- **CGU is where journalists win.** Its published decisions are a body of
  precedent you can cite. Search prior CGU rulings on the same denial ground
  and quote them in your appeal.
- **CMRI is slow.** It meets periodically and a decision can take many
  months. It is worth using for precedent-setting refusals, less so when the
  story has a deadline.
- Each appeal should add an argument, not repeat the last one. Restating the
  original request is the most common reason appeals fail.
- Consult the outlet's lawyers promptly if a judicial remedy may be needed. A
  mandado de segurança has a 120-day period from notice of the challenged act
  (Lei 12.016/2009, art. 23). Track that deadline in parallel with the
  administrative process. The outlet's lawyers decide whether the remedy fits.

Templates: `recurso-1a-instancia.md`, `recurso-2a-instancia.md`,
`recurso-cgu.md`, `recurso-cmri.md`.

## Step 6: Track everything

Keep a log per request. Protocol numbers are the only reliable identifier,
and Fala.BR does not notify reliably.

```markdown
## Request log

**Protocol:** [Fala.BR / e-SIC number]
**Body:** [agency]
**Filed:** [date]
**Statutory deadline:** [filed + 20 days]
**Extended to:** [+10 days, if invoked — note the justification given]
**Status:** [pending / granted / partial / denied / appealed]
**Denial ground cited:** [article and text]
**Appeal level:** [1 / 2 / CGU / CMRI]
**Next deadline:** [date, and whose]
**Files received:** [paths]
```

Publishing the request and the response afterwards — through Achados e
Pedidos or the outlet's own site — is standard practice in Brazilian
investigative work and helps the next reporter. Before publishing, redact
CPFs, home addresses, and any other personal field the agency did not
already withhold under LAI art. 31 — a public record is not automatically a
public-interest publication, and this is especially true for victim,
witness, and juvenile identifiers. LGPD does not apply to processing carried
out exclusively for journalistic purposes (LGPD art. 4, II, a). That exclusion
does not remove editorial, ethical, or other applicable legal duties to
safeguard personal data.

## Working with what comes back

- Responses often arrive as PDFs of screenshots of tables. Where the agency
  stores the information digitally, agree to receive that existing format under
  art. 11 §5º. If the agency will not budge, extract and document the process.
- Check the response against the request field by field. Partial delivery
  presented as full delivery is common, and the 10-day appeal clock starts
  from receipt.
- Preserve the original file exactly as received, before any cleaning. It is
  the evidence that the agency provided it.

## Statutory currency

The core citations here are Lei 12.527/2011 and Decree 7.724/2012 (federal
executive regulation). Both have been amended, and state and municipal
regulations vary. Verify article numbers against the current consolidated
text on planalto.gov.br before relying on them in an appeal, and check
current CGU guidance for procedural changes to Fala.BR.

Related Brazilian statutes that intersect: Lei 13.709/2018 (LGPD),
Lei 13.460/2017 (users of public services), Lei 14.129/2021 (digital
government).

## Contributor credit

Reinaldo Chaves ([@reichaves](https://github.com/reichaves)) contributed this
skill in [PR #267](https://github.com/jamditis/claude-skills-journalism/pull/267).
