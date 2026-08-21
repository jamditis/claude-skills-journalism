## Data acquisition

### Public data sources

**Federal data sources**

*General:*
- **Data.gov**, Federal open data portal. Many datasets were removed between Feb 2025 and 2026; consult the [Harvard LIL Data.gov archive](https://lil.law.harvard.edu/blog/2025/02/06/announcing-data-gov-archive/) and the [Data Rescue Project](https://www.datarescueproject.org/) for preserved copies before assuming anything is still accessible.
- **Census Bureau** (census.gov), Demographics, economic data. Many research pages were removed during the 2025 transition; the [End of Term Web Archive](https://eotarchive.org) holds snapshots.
- **BLS** (bls.gov), Employment, inflation, wages. Following the 2025 funding lapse, the October 2025 Employment Situation release was canceled and the CPS October 2025 reference period is permanently uncollected. Check [revised release dates](https://www.bls.gov/bls/2025-lapse-revised-release-dates.htm) before relying on series continuity.
- **BEA** (bea.gov), GDP, economic accounts.
- **FRED / Federal Reserve** (fred.stlouisfed.org), Financial and macroeconomic data; expanded API access through 2026.
- **SEC EDGAR**, Corporate filings.

*Specific domains:*
- **EPA** (epa.gov/data), Environmental data. At least 80 climate webpages were removed in Dec 2025, the endangerment finding was repealed Feb 12, 2026, and the Climate Change Indicators site was largely gutted. The [Environmental Data & Governance Initiative](https://envirodatagov.org) maintains mirrors.
- **FDA / openFDA** (open.fda.gov), Drug approvals, recalls, adverse events.
- **CDC WONDER**, Health statistics. Many datasets were removed from data.cdc.gov after Jan 2025, partially restored under Doctors for America v. Trump (TRO Feb 11, 2025) but with altered terminology in some returns. The volunteer-run [RestoredCDC.org](https://restoredcdc.org/wonder.cdc.gov/) mirrors removed content.
- **NHTSA FARS / vPIC APIs**, Vehicle safety data.
- **DOT**, Transportation statistics.
- **FEC**, Campaign finance; 2025-2026 cycle data live.
- **USASpending.gov**, Federal contracts and grants; API v2 operational.

*Court records:*
- **CourtListener / RECAP** (courtlistener.com), Free PACER alternative covering federal court filings; RECAP Search Alerts launched June 2025 ("Google Alerts for federal courts").
- **PACER**, Federal court filings; $0.10 per page, $30 per quarter waiver threshold.

*State and local:*
- State open data portals (search: "[state] open data")
- Tyler Data & Insights (formerly Socrata, rebranded May 2025) hosts many city and state portals
- OpenStreetMap, municipal GIS portals
- State comptroller and auditor reports

*International:*
- **Eurostat**, **OECD**, **World Bank Open Data**, **UN Data**, major comparative datasets, mostly stable through 2026.

*Specialized:*
- **NICAR Data Library** (IRE), curated datasets, IRE members only.
- **IPUMS** (University of Minnesota), free with account; canonical for harmonized microdata.
- **ICPSR** (University of Michigan), social-science data archive.
- **ProPublica Data Store**, frozen; datasets only run through 2023.

*Federal-data preservation (use when source data has been removed):*
- [Data Rescue Project](https://www.datarescueproject.org), citizen + library mirrors of removed federal data; more than 1,230 datasets across 85 offices as of Aug 2025.
- [End of Term Web Archive](https://eotarchive.org), 500TB / 100M-page snapshot of federal sites at the 2024-2025 transition.
- Internet Archive Wayback Machine, useful for individual page-level recovery.

### Data request strategies

**Public records requests for datasets**

For request mechanics (templates, fee-waiver language, NJ OPRA, appeals, FOIA Improvement Act statutory citations), see the **foia-requests** skill. Data-specific guidance:

- Request databases, not just documents
- Ask for the data dictionary or schema
- Request in native format (CSV, SQL dump), not PDFs or scanned printouts
- Specify field-level needs and any computed columns you want included
- For active datasets, ask the cadence (daily, monthly, quarterly) and request standing access if your reporting will continue

**Building your own dataset**

- Scraping public information (respect robots.txt, ToS, and rate limits)
- Crowdsourcing from readers
- Systematic document review
- Surveys with documented methodology

**Commercial data sources for newsrooms**

- LexisNexis, Refinitiv, Bloomberg
- Industry-specific databases (often via library proxy through your institution)
