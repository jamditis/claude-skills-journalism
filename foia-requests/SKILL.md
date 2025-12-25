---
name: foia-requests
description: Freedom of Information Act (FOIA) and public records request workflows. Use when drafting records requests, tracking submissions, understanding exemptions, appealing denials, or managing large document productions. Essential for investigative journalists, researchers, and transparency advocates.
---

# FOIA and public records requests

Comprehensive guide for obtaining government records through freedom of information laws.

## Understanding FOIA landscape

### Jurisdiction overview

| Level | Law | Scope |
|-------|-----|-------|
| Federal | Freedom of Information Act (5 U.S.C. § 552) | Federal executive branch agencies |
| State | Varies by state (e.g., OPRA in NJ, FOIL in NY) | State and local agencies |
| Local | Often covered by state law | Municipal, county, school boards |

### Key federal exemptions (FOIA)

```markdown
## The 9 FOIA exemptions

1. **National security** - Classified information
2. **Internal personnel rules** - Agency housekeeping matters
3. **Statutory exemptions** - Other laws prohibit disclosure
4. **Trade secrets** - Confidential business information
5. **Inter/intra-agency memos** - Deliberative process privilege
6. **Personal privacy** - Personnel, medical files
7. **Law enforcement** - Could interfere with proceedings
8. **Financial institutions** - Bank examination reports
9. **Geological data** - Oil and gas well information

Note: Agencies must segregate and release non-exempt portions
```

## Drafting effective requests

### Request template (Federal FOIA)

```markdown
[Your Name]
[Your Address]
[City, State ZIP]
[Email]
[Phone]

[Date]

FOIA Officer
[Agency Name]
[Agency Address]

RE: Freedom of Information Act Request

Dear FOIA Officer:

Pursuant to the Freedom of Information Act, 5 U.S.C. § 552, I request access to and copies of:

[DESCRIBE RECORDS SPECIFICALLY]

**Scope and timeframe:**
- Date range: [START DATE] to [END DATE]
- Offices/divisions: [SPECIFIC OFFICES if known]
- Keywords: [RELEVANT SEARCH TERMS]

**Format requested:**
I request records in electronic format (PDF, native format) delivered via email to [your email] or via an online portal.

**Fee waiver request:**
I request a waiver of all fees associated with this request. Disclosure is in the public interest because:
- [Explain how information contributes to public understanding]
- [Explain why you are positioned to disseminate information]
- [State if affiliated with news organization or research institution]

Alternatively, if fees cannot be waived, I am willing to pay up to $[AMOUNT] for processing. Please contact me before exceeding this amount.

**Expedited processing request (if applicable):**
I request expedited processing because:
- [Urgent need to inform the public about actual or alleged government activity]
- [Imminent threat to life or physical safety]

**Contact information:**
Please contact me at [email] or [phone] if you have questions or need clarification about this request.

I expect a response within 20 business days as required by law.

Sincerely,
[Your Name]
```

### Request drafting best practices

```markdown
## Effective request strategies

### Be specific but not too narrow
BAD: "All documents about climate change"
BAD: "The email from John Smith on March 15, 2024 at 2:47 PM"
GOOD: "Emails between [Office] and [External Party] regarding [Topic] from [Date Range]"

### Use agency terminology
- Research how agency categorizes information
- Use their document type names (memos, briefings, reports)
- Reference specific programs or initiatives by official name
- Include relevant file numbers if known

### Define your terms
- Specify what you mean by "communications" (emails, texts, calls?)
- Define "records" (include drafts? attachments?)
- Clarify "regarding" vs "mentioning" vs "primarily about"

### Request specific record types
- Emails and email attachments
- Calendar entries and meeting invites
- Text messages and messaging apps
- Memoranda and briefing papers
- Contracts and invoices
- Meeting minutes and notes
- Policies and procedures
- Correspondence (letters, faxes)
```

## Tracking and managing requests

### Request tracking system

```python
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Optional

class RequestStatus(Enum):
    DRAFTED = "drafted"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PROCESSING = "processing"
    PARTIAL_RESPONSE = "partial_response"
    COMPLETED = "completed"
    APPEALED = "appealed"
    LITIGATION = "litigation"
    CLOSED = "closed"

@dataclass
class FOIARequest:
    id: str
    agency: str
    date_submitted: date
    description: str
    status: RequestStatus = RequestStatus.DRAFTED

    # Tracking
    tracking_number: Optional[str] = None
    assigned_officer: Optional[str] = None
    estimated_completion: Optional[date] = None

    # Fees
    fee_estimate: Optional[float] = None
    fee_waiver_requested: bool = True
    fee_waiver_granted: Optional[bool] = None

    # Timeline
    acknowledgment_date: Optional[date] = None
    response_dates: list[date] = None

    # Documents
    pages_received: int = 0
    pages_withheld: int = 0
    exemptions_cited: list[str] = None

    # Appeals
    appeal_deadline: Optional[date] = None
    appeal_filed: Optional[date] = None

    @property
    def statutory_deadline(self) -> date:
        """Federal FOIA: 20 business days from submission."""
        # Simplified - should account for business days
        return self.date_submitted + timedelta(days=28)

    @property
    def is_overdue(self) -> bool:
        return date.today() > self.statutory_deadline and self.status in [
            RequestStatus.SUBMITTED,
            RequestStatus.ACKNOWLEDGED,
            RequestStatus.PROCESSING
        ]

# Tracking spreadsheet structure
TRACKING_COLUMNS = [
    'request_id',
    'agency',
    'date_submitted',
    'tracking_number',
    'description',
    'status',
    'statutory_deadline',
    'actual_response_date',
    'pages_received',
    'exemptions_cited',
    'fee_amount',
    'appeal_deadline',
    'notes'
]
```

### Follow-up communication templates

```markdown
## Status inquiry (after 20+ business days)

Subject: Status Inquiry - FOIA Request [Tracking Number]

Dear FOIA Officer:

I am writing to inquire about the status of my Freedom of Information Act request submitted on [DATE], assigned tracking number [NUMBER].

Under FOIA, agencies must respond within 20 business days. As of today, [X] business days have elapsed.

Please provide:
1. Current status of my request
2. Estimated completion date
3. Any fee estimates
4. Name of assigned processor

I can be reached at [contact info].

Sincerely,
[Name]
```

```markdown
## Fee waiver appeal

Subject: Appeal of Fee Waiver Denial - Request [Number]

Dear FOIA Appeals Officer:

I appeal the denial of my fee waiver request dated [DATE] for request [NUMBER].

The denial was improper because:

1. **Public interest**: [Explain how disclosure serves public interest]

2. **Ability to disseminate**: [Describe your platform/audience]
   - Publication: [name, circulation/readership]
   - Previous FOIA-based reporting: [examples]
   - Planned use of records: [specific plans]

3. **Commercial interest**: I have no commercial interest in these records. [Or: My commercial interest is minimal compared to public benefit because...]

4. **Comparison**: Similar requests have received fee waivers. See: [examples if available]

I request the fee waiver be granted or, alternatively, that fees be limited to [amount].

Sincerely,
[Name]
```

## Handling responses

### Response review checklist

```markdown
## Initial response review

### Administrative check
- [ ] Response received by deadline?
- [ ] Tracking number matches
- [ ] Request description accurate
- [ ] All requested record types addressed

### Completeness assessment
- [ ] All date ranges covered?
- [ ] All offices/divisions searched?
- [ ] Search terms used listed?
- [ ] Any referrals to other agencies?

### Exemption analysis
For each exemption claimed:
- [ ] Specific exemption cited (e.g., "Exemption 6")
- [ ] Explanation provided for each withholding
- [ ] Foreseeable harm articulated?
- [ ] Segregable portions released?

### Document review
- [ ] Page count matches stated total
- [ ] Documents legible
- [ ] Redactions clearly marked
- [ ] Index provided (Vaughn index if applicable)

### Fee assessment
- [ ] Charges match estimate?
- [ ] Itemized breakdown provided?
- [ ] Fee category correct (media, educational, commercial, other)?
```

### Redaction analysis

```markdown
## Understanding redactions

### Types of redactions
- (b)(1) - National security [black bar with exemption]
- (b)(5) - Deliberative process [often overused]
- (b)(6) - Personal privacy [names, contact info]
- (b)(7)(A) - Law enforcement investigation
- (b)(7)(C) - Law enforcement privacy

### Challenging over-redaction
Questions to ask:
1. Is entire document withheld or just portions?
2. Are routine details redacted unnecessarily?
3. Is information already public elsewhere?
4. Is the exemption correctly applied?
5. Was foreseeable harm test applied?

### Building your case
- Compare with similar released documents
- Check if information is already public
- Note inconsistent redaction patterns
- Document segregability arguments
```

## Appeals process

### Federal FOIA appeal template

```markdown
[Your Name]
[Address]
[Date]

Chief FOIA Officer / FOIA Appeals Office
[Agency Name]
[Address]

RE: Administrative Appeal of FOIA Request [Tracking Number]

Dear Appeals Officer:

Pursuant to 5 U.S.C. § 552(a)(6), I appeal the [partial denial / full denial / inadequate search / fee waiver denial] of my FOIA request dated [original date], tracking number [number].

**Original request:**
[Brief description of what you requested]

**Agency response:**
On [date], the agency [describe response - denied, partially released, etc.]

**Grounds for appeal:**

[Choose applicable grounds:]

**1. Improper exemption claim**
The agency improperly invoked Exemption [X] because:
- [Specific argument about why exemption doesn't apply]
- [Legal precedent if known]
- [Foreseeable harm not demonstrated]

**2. Inadequate search**
The agency failed to conduct an adequate search because:
- [Specific offices not searched]
- [Relevant record systems overlooked]
- [Search terms too narrow]

**3. Failure to segregate**
The agency failed to release non-exempt portions as required. Specifically:
- [Identify documents where segregation possible]

**4. Fee waiver improperly denied**
[See fee waiver appeal template above]

**Relief requested:**
I request that the agency:
1. Release all improperly withheld records
2. Conduct additional searches of [specific locations]
3. Provide a detailed justification for any continued withholdings
4. Grant my fee waiver request

I expect a response within 20 business days.

Sincerely,
[Name]
```

### Appeal deadlines by jurisdiction

| Jurisdiction | Appeal deadline | Where to file |
|--------------|-----------------|---------------|
| Federal FOIA | 90 days from response | Agency appeals office |
| New Jersey OPRA | 45 days | Government Records Council |
| New York FOIL | 30 days | Agency appeals officer |
| California PRA | No admin appeal | Direct to court |
| [Add your state] | [Deadline] | [Location] |

## Advanced strategies

### Multi-agency requests

```markdown
## Coordinated request strategy

When a topic spans multiple agencies:

1. **Map the agencies involved**
   - Which agencies have jurisdiction?
   - Which offices within agencies?
   - Are there inter-agency communications?

2. **Sequence requests strategically**
   - Start with agency most likely to release
   - Use released documents to refine subsequent requests
   - Reference other agencies' releases in appeals

3. **Cross-reference responses**
   - Compare what different agencies release
   - Note discrepancies in redactions
   - Use one agency's release to challenge another's withholding

4. **Track coordination**
   - Document all request/response dates
   - Note referrals between agencies
   - Build timeline of events from multiple sources
```

### Document production management

```markdown
## Large production workflow

For responses with 100+ pages:

### Organization system
/FOIA_[Agency]_[Topic]/
├── 01_Request_Materials/
│   ├── original_request.pdf
│   ├── acknowledgment.pdf
│   └── correspondence/
├── 02_Responses/
│   ├── response_2024-01-15/
│   ├── response_2024-02-20/
│   └── final_response/
├── 03_Analysis/
│   ├── document_index.xlsx
│   ├── redaction_log.xlsx
│   └── key_documents/
├── 04_Appeals/
│   └── appeal_2024-03-01.pdf
└── 05_Notes/
    └── research_notes.md

### Document indexing
For each document, track:
- Bates number (if assigned)
- Date of document
- Author/recipient
- Document type
- Subject/summary
- Exemptions applied
- Relevance rating (1-5)
- Follow-up needed?
```

## State-specific resources

### Finding your state's law

```markdown
## State public records resources

### Reporters Committee for Freedom of the Press
- Open Government Guide: rcfp.org/open-government-guide
- State-by-state analysis of public records laws
- Sample request letters by state

### National Freedom of Information Coalition
- nfoic.org/state-freedom-of-information-laws
- State FOI organization contacts
- Training and resources

### MuckRock
- muckrock.com
- File requests through platform
- Search previous requests/responses
- Agency response time data
```
