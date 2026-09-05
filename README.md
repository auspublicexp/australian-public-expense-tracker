# Australian Public Expense Tracker

Australian Public Expense Tracker (APET) presents publicly available Australian government expenditure data in a clear, accessible and reusable format.

APET is an independent, politically neutral project. It does not advocate for or against any political party, parliamentarian or policy. Its purpose is to make official expenditure data easier to explore and understand so readers can draw their own conclusions.

**[View the published charts at auspublicexp.org](https://auspublicexp.org/)**

## Current coverage

The repository documents processing pipelines for parliamentary expenditure, procurement, grant awards, research grants, government finance, public-hospital funding, subsidised medicines, Medicare benefits and Australian foreign-aid disbursements.

Official sources:

- [Independent Parliamentary Expenses Authority](https://www.ipea.gov.au/)
- [IPEA datasets on data.gov.au](https://data.gov.au/data/organization/ipea)
- [AusTender](https://www.tenders.gov.au/)
- [GrantConnect](https://www.grants.gov.au/)
- [Australian Research Council Grants Search](https://dataportal.arc.gov.au/NCGP/Web/Grant/Grants)
- [Australian Bureau of Statistics — Government](https://www.abs.gov.au/statistics/economy/government)
- [National Health Funding Body public-hospital funding data](https://data.gov.au/data/dataset/c4afb0c6-624b-4f4e-865d-14af55c6a311)
- [PBS and RPBS Date of Supply statistics](https://www.pbs.gov.au/statistics/dos-and-dop/dos-and-dop)
- [Medicare statistics collection](https://www.health.gov.au/resources/collections/medicare-statistics-collection)
- [DFAT AusDevPortal data downloads](https://adp.dfat.gov.au/data-downloads)
- [DFAT Australia IATI Activity File](https://data.gov.au/data/dataset/dfat-australia-iati-activity-file)

## Understanding the figures

The sources measure different things and their values should not be treated as interchangeable.

| Dataset | What the value represents |
| --- | --- |
| IPEA | Reported parliamentary expenses for the relevant reporting period. |
| AusTender | Reported contract value, not necessarily cash paid during the period. |
| GrantConnect | Published grant-award value, not necessarily cash paid during the period. |
| ARC Grants | Whole-of-project ARC allocation grouped by scheduled calendar-year commencement, not cash paid in that year. |
| ABS GFS | Aggregate government expenses recorded on an accrual basis, not individual transactions or inflation-adjusted growth. |
| Public hospital funding | Cash payments reported through the National Health Funding Pool and State Managed Funds, not every cost incurred by public hospitals. |
| PBS and RPBS | Australian Government contributions to subsidised prescription costs, not total prescription cost. |
| Medicare MBS | Medicare benefits paid for claims processed, not total Australian health expenditure. |
| DFAT Foreign Aid | IATI type-3 disbursements reported by financial year, excluding commitments and budgets. |


## Data quality and validation

APET keeps downloaded source files and generated outputs outside version control. Before derived search indexes or charts are published, the processing workflows check the fields they depend on, parse dates and monetary values, and apply source-specific duplicate or amendment handling.

Each source pipeline writes a small latest-run validation report to `output/validation` on the maintainer's computer:

- a readable `*_latest.txt` summary
- a structured `*_latest.json` summary

These reports record the run time, coverage, record and period counts, output locations, and the checks completed. They are working records for the maintainer, are replaced by the next successful run, and are not published on the website or committed to this repository.

Important source-specific limitations remain:

- **IPEA:** transactions generally appear in the period when they were paid, which may differ from when travel or other activity occurred; later adjustments or repayments may also be published.
- **AusTender:** values describe reported contract commitments over the contract's life, not cash paid in a quarter. Reporting thresholds apply, and entities can amend, vary or cancel notices.
- **GrantConnect:** APET groups awards by publication date. Published award values are not necessarily payments made in that period, and recipient names may vary between records.
- **ARC Grants:** values are whole-of-project allocations, including post-award variations, grouped by scheduled calendar commencement year. ARC projects can also appear in GrantConnect, so the two sources must not be added together.
- **ABS GFS:** figures are aggregate accrual estimates in current prices and original series. They are not individual transactions or inflation-adjusted growth, and historical estimates may be revised.
- **Public hospital funding:** figures are cash flows through the national funding arrangements, not the full operating cost of hospitals. Category data omits some payment types and can include negative adjustments.
- **PBS and RPBS:** government contribution is not the total cost of prescriptions. Recent claims data can be incomplete or revised, so APET stays one complete source quarter behind.
- **Medicare MBS:** benefits describe processed Medicare claims and exclude services provided to public patients in public hospitals. Patient location is based on address rather than service location.
- **DFAT Foreign Aid:** charts use reported IATI disbursements, retain negative adjustments and do not add commitments or budgets. Country charts exclude regional and unspecified transactions, so their bars do not sum to the total program.

Validation can identify structural problems such as missing required fields, invalid dates or duplicate identifiers. It cannot independently verify whether an official source record is factually correct. The government publisher remains authoritative, and significant findings should be checked against the linked official record.

## Published data pipelines

### IPEA parliamentary expenditure

APET's IPEA pipeline downloads official quarterly expenditure extracts and produces quarterly, Australian financial-year and long-term trend summaries. Quarterly source filenames retain IPEA's calendar-quarter convention, while generated output folders use APET's Australian financial-year quarter labels.

The public chart-appearance search indexes parliamentarians displayed in person-level chart CSV files. It supports party, state or territory, expense category, period, minimum reported amount and chart-type filters, with links to the relevant chart. A chart appearance is not a count of expenses, transactions or payments.

- [Published IPEA chart-appearance search](https://auspublicexp.org/ipea/search.php)
- [Methodology and limitations](docs/ipea-methodology.md)
- [IPEA scripts](scripts/ipea)
- [Shared chart helpers](scripts/chart_helpers.py)

### AusTender

APET's AusTender pipeline combines official contract-notice exports, resolves amendments for historical reporting, and produces quarterly procurement summaries. Its public search supports supplier, agency, contract description, CN ID, period and reported-value filters, with links to APET charts and official AusTender records.

The long-term overview uses the Department of Finance's official annual AusTender statistics rather than treating APET's newer weekly archive as a complete historical collection. It charts maximum reported contract value and contract volume from FY2016-17. These values can cover multi-year contracts and are not annual expenditure paid. A reporting break is marked from FY2024-25 because value-reducing amendments and other reporting changes affect comparison with earlier years.

- [Published AusTender supplier and contract search](https://auspublicexp.org/austender/search.php)
- [Department of Finance annual procurement statistics](https://www.finance.gov.au/government/procurement/statistics-australian-government-procurement-contracts-)
- [Methodology and limitations](docs/austender-methodology.md)
- [AusTender scripts](scripts/austender)
- [Shared chart helpers](scripts/chart_helpers.py)

### GrantConnect

APET's GrantConnect pipeline produces quarterly and annual summaries from publicly available Australian Government grant-award exports. Its public search supports recipient, activity, agency, category, period, location, identifier and reported-value filters, with links to APET charts and official GrantConnect records.

- [Published GrantConnect award search](https://auspublicexp.org/grantconnect/search.php)
- [Methodology and limitations](docs/grantconnect-methodology.md)
- [GrantConnect scripts](scripts/grantconnect)
- [Shared chart helpers](scripts/chart_helpers.py)

### Australian Research Council grants

APET's ARC pipeline downloads the public National Competitive Grants Program Grants Search API, preserves the raw paginated responses, normalises one row per project, validates identifiers and coverage, and produces overview and calendar-year charts.

ARC is organised by scheduled calendar commencement year because the source does not provide comparable financial-year cash-payment dates. Values represent whole-of-project allocations rather than money paid during the displayed year. Discovery supports fundamental research and researchers; Linkage supports collaborative research, partnerships and research infrastructure.

- [Published ARC grants charts](https://auspublicexp.org/arc-grants/)
- [Methodology and limitations](docs/arc-grants-methodology.md)
- [ARC scripts and workflow](scripts/arc_grants)
- [Official ARC Grants Search](https://dataportal.arc.gov.au/NCGP/Web/Grant/Grants)
- [Official ARC grants dataset information](https://www.arc.gov.au/funding-research/funding-outcomes/grants-dataset)

### ABS Government Finance Statistics

APET's ABS Government Finance Statistics (GFS) pipeline produces annual summaries using Australian financial years (July to June). The figures describe All Australia general government expenses on an accrual basis and are presented in current prices, original series. The topic explorer compares expenditure purposes and government levels across available financial years in dollars or as a share of the selected total.

- [Published ABS GFS topic explorer](https://auspublicexp.org/abs-gfs/explorer.php)
- [Methodology and limitations](docs/abs-gfs-methodology.md)
- [ABS GFS scripts and workflow](scripts/abs_gfs)
- [Published ABS GFS charts](https://auspublicexp.org/abs-gfs/)
- [Official ABS government statistics](https://www.abs.gov.au/statistics/economy/government)

### Public hospital funding

APET downloads official National Health Funding Body monthly cash-payment data, preserves and validates the source files, and produces long-term and annual financial-year charts. The public explorer supports jurisdiction, financial period, funding method, service category, value, share and period-to-period change filters. Complete jurisdiction totals remain separate from service-category components because the latter omit some payment types.

- [Published public-hospital funding explorer](https://auspublicexp.org/hospital-funding/explorer.php)
- [Published public-hospital funding charts](https://auspublicexp.org/hospital-funding/)
- [Public-hospital funding scripts and notes](scripts/public_hospital_funding)
- [Official source dataset](https://data.gov.au/data/dataset/c4afb0c6-624b-4f4e-865d-14af55c6a311)

### Pharmaceutical Benefits Scheme and Repatriation Pharmaceutical Benefits Scheme

APET uses the official PBS and RPBS Date of Supply workbook to chart Australian Government contributions to subsidised prescription costs by financial year and quarter. Publication stays one complete source quarter behind to allow additional time for late claims and revisions. The public medicine search supports medicine, period and reported-value exploration with links to relevant charts.

- [Published PBS and RPBS charts and medicine search](https://auspublicexp.org/pbs/)
- [PBS scripts and workflow](scripts/pbs)
- [Official Date of Supply statistics](https://www.pbs.gov.au/statistics/dos-and-dop/dos-and-dop)

### Medicare Benefits Schedule

APET normalises the Department of Health, Disability and Ageing's quarterly Medicare statistics and produces complete financial-year and quarter charts. The public explorer supports service, location, period and metric filters for Medicare benefits paid and services processed.

- [Published Medicare charts and explorer](https://auspublicexp.org/mbs/)
- [Medicare scripts and workflow](scripts/mbs)
- [Official Medicare statistics collection](https://www.health.gov.au/resources/collections/medicare-statistics-collection)

### DFAT Australian foreign aid

APET's DFAT pipeline downloads the official IATI Activity File through data.gov.au, preserves the raw XML and code lists, normalises transaction-level records, validates the result and produces overview and annual Australian financial-year charts. The charts use reported type-3 disbursements rather than commitments, budgets or whole-of-project investment values.

The current IATI file contains recent financial years and dates its transactions at financial-year end. APET therefore publishes annual—not quarterly—charts. Country-only charts exclude regional and unspecified transactions; total and sector charts retain them. The public search groups transactions by activity and financial year and supports activity, country, region, sector, implementing organisation, status and reported-value filters.

- [Methodology and limitations](docs/dfat-foreign-aid-methodology.md)
- [DFAT foreign-aid scripts](scripts/dfat_foreign_aid)
- [Published foreign-aid activity search](https://auspublicexp.org/foreign-aid/search.php)
- [Published foreign-aid charts](https://auspublicexp.org/foreign-aid/)
- [AusDevPortal downloads](https://adp.dfat.gov.au/data-downloads)
- [Official DFAT IATI Activity File](https://data.gov.au/data/dataset/dfat-australia-iati-activity-file)

## Repository structure

```text
scripts/
├── chart_helpers.py
├── abs_gfs/
├── arc_grants/
├── austender/
├── dfat_foreign_aid/
├── grantconnect/
├── ipea/
├── mbs/
├── pbs/
└── public_hospital_funding/
```

Source datasets and generated outputs are kept outside version control. See the methodology document for each pipeline for its expected local structure, processing steps, limitations, and running instructions.

## Transparency and methodology

APET aims to provide an auditable path from each published result back to its official source:

**Official government data → APET processing script → chart or table → published page**

Where practical, each published chart or table will identify:

- the official source dataset
- the relevant reporting period
- the processing script used
- important definitions, exclusions or limitations
- the date the data was retrieved or updated

The official government publisher remains the authoritative source. APET does not alter source records, estimate unreported expenditure or present its calculations as official government statistics.

## Reproducibility

This repository includes documented data-processing scripts, source links, chart-generation code, methodology notes, and software requirements. Large source datasets are not stored here; users should obtain them from the official publisher.

## Project status

APET is an independently maintained hobby project. Updates are published when time and official source data permit; no fixed publication schedule is promised. Repository documentation and methodology may evolve as the project develops.

## Corrections and questions

Questions, corrections and reproducibility issues can be raised through this repository's [Issues](https://github.com/auspublicexp/australian-public-expense-tracker/issues) section. Please include the relevant dataset, reporting period and page or chart when possible.

## Licence

This project's original code is available under the [MIT License](LICENSE). Government source datasets remain subject to the terms specified by their original publishers.
