# Evidence-led investigations and public-claim verification — future roadmap

**Status:** Planning ideas retained from the August 2026 APET strategy discussion; not a claim that these features have been implemented. Reassess against current website features and available source coverage before development.

## Editorial objective

Extend APET's existing official-data charts and search tools into a selective, source-led *follow the public money* research workflow. Do not brand unusual spending as waste or wrongdoing without substantiated official findings. Apply the same verification standards to all parties, governments, parliamentarians and agencies. Correct figures and definitions, not people.

See [editorial and social-media policy](editorial-social-media-policy.md) for the current publication rules. This roadmap supplements, rather than replaces, the existing policy.

## Proposed research workflow

1. Collect and preserve official releases, source URLs, release dates and reporting periods.
2. Use Python/pandas to normalise historical records, identifiers, amendments and definitions.
3. Calculate transparent, reproducible candidate signals (e.g. large changes, repeated awards, concentration).
4. Optionally use local AI to triage descriptions, suggest questions and help locate documentary context. Treat AI output only as leads, never as verified figures or allegations.
5. Check findings against original notices, datasets, program descriptions and, where relevant, ANAO reports or agency annual reports.
6. Distinguish facts, computed comparisons, uncertainty and unresolved questions.
7. Publish an evidence page or chart only if the result offers meaningful public context; human-review all X replies and posts before publication.

**Measurements must never be silently combined:** AusTender contract value (including variations), GrantConnect award value, IPEA reported expense, budget allocation, maximum contract ceiling, payment/disbursement and ABS accrual expense can describe different concepts and periods. Do not double-count grants appearing in overlapping datasets. Contract totals are not cash outlays.

## Candidate investigations, not allegations

- **Procurement:** original versus amended contract values; high-value contracts (consider a clearly labelled illustrative threshold of $20 million); duration versus value; limited tenders; recurring suppliers; supplier concentration by agency/category; description quality; multi-year consultancy trends. Account for notice amendments, incomplete exports, shifting classifications and changing reporting rules.
- **Grants:** recurring recipients and program concentration; trends across years; cross-agency patterns. Grant announcements and award values are not proof of money paid.
- **Parliamentary expenses:** verify claims against specific IPEA person, calendar quarter, expense category, adjustments and associated notes. Distinguish permissible entitlements from expenses actually reported. Watch classification changes over time.
- **Cross-dataset:** verified ABN/organisation links between procurement suppliers and grant recipients; contextual links to department annual reports, portfolio budget statements and ANAO audits.

A high value, unusual pattern, repeated recipient, limited tender or shared identifier **does not establish impropriety**. Do not publish unverified AI-generated claims about personal or corporate connections.

## Sources and order of enrichment

Existing core: [IPEA](https://www.ipea.gov.au/), [AusTender](https://www.tenders.gov.au/), [GrantConnect](https://www.grants.gov.au/) and existing APET datasets including [ABS government finance statistics](https://www.abs.gov.au/statistics/economy/government). These already have documented pipelines; use their current methodology and website features instead of rebuilding them.

Optional next layers, to validate availability/licensing and identifiers before ingesting:
1. [Australian Business Register](https://abr.business.gov.au/) / ABN data for reliable organisation matching; distinguish exact ABN matches from provisional name matches.
2. [Australian National Audit Office](https://www.anao.gov.au/) findings for attributed, independent audit context.
3. Official agency annual reports, portfolio budget statements, procurement registers and parliamentary committee records for explanations of purpose, budgets and audited outcomes.
4. FOI disclosure logs **only as justified by specific research questions**, rather than indiscriminate collection.

Do not collect everything simply because it is available. Evaluate maintenance burden, data quality, source terms and public benefit before expanding.

## Entity/profile ideas

Potential public supplier, agency and recipient pages could show identifiers (when verified), number of notices/awards, reported values, agencies, years, largest items, amendments, methodology notes and links back to official source records. Profiles are exploratory views, not judgements of performance or value for money.

## Public X claim checks — proposed operating checklist

- Capture the exact claim, author/post URL and date; identify the figure, period, subject and claimed measurement.
- Decide whether an APET dataset and original official records can actually test it. If not, skip or explicitly state the limitation.
- Recalculate using the appropriate reporting period and preserve source links and query/filter criteria.
- Check explanations such as adjustments, family/nominee travel categories, contract ceilings, procurement-notice amendments, or recipient-name duplicates, as applicable.
- Classify internally as **supported, contradicted, incomplete/context-needed, or not verifiable**. Never infer dishonesty or motives.
- Prepare a short neutral response stating the supported number or limitation, period, and official source; link to the relevant APET evidence page if available.
- **Human review and approval remain mandatory.** No automated posting or reply. Do not join abusive or low-quality engagement just to increase reach.

Example reply **template only; fill verified fields before use**:

> The [official source] data for [period] reports [amount] under [precise category]. That is [different from / consistent with] the figure in this post because [documented distinction]. Source: [official record].

## Implementation priorities

First: retain the reliability, validation and publication workflows already documented. Next: prototype one transparent, repeatable procurement or IPEA research question and measure whether it produces useful findings. Then consider structured anomaly flags, verified identifiers, profile pages or assisted claim-checking, avoiding duplicates of currently deployed search functionality.

**Do not treat examples or illustrative thresholds from the 2026 discussion as verified findings.** No investigation or fact-check in that conversation established a publishable allegation or corrected specific parliamentary expense total.
