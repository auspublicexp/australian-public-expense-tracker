# Australian Research Council grants methodology

## Source and scope

APET uses the Australian Research Council's public National Competitive Grants Program Grants Search API:

- Dataset information: https://www.arc.gov.au/funding-research/funding-outcomes/grants-dataset
- Official Grants Search: https://dataportal.arc.gov.au/NCGP/Web/Grant/Grants
- API endpoint: https://dataportal.arc.gov.au/NCGP/API/grants

The pipeline archives the paginated JSON responses before transformation, then creates one normalised row per ARC project.

## Processing

1. `fetch_arc_grants.py` downloads a small test or the complete paginated collection and records filenames, record counts and SHA-256 checksums in a manifest.
2. `normalize_arc_grants.py` maps API attributes into a consistent project-level CSV.
3. `validate_arc_grants.py` compares raw and normalised counts and checks duplicate project codes, duplicate API IDs, missing key fields and negative current-funding values.
4. `generate_arc_grants_charts.py` produces long-term overview charts and calendar-year charts for organisations, schemes, research fields and large projects.

## Time periods and values

ARC records are grouped by scheduled **calendar funding commencement year**. This differs from APET's financial-year presentation for IPEA, AusTender, GrantConnect and ABS GFS because the ARC source does not provide a comparable payment date.

Funding figures are whole-of-project allocations, not cash paid in the commencement year. Announced funding describes the award at announcement; current funding may include later variations.

## Important limitations

- ARC projects can also be published through GrantConnect. Do not add ARC and GrantConnect totals together.
- The administering organisation is not necessarily where every component of the research takes place.
- The earliest 2001 records appear partial.
- The current incomplete calendar year is excluded from charts by default.
- Research-field classifications transition from FoR 2008 to FoR 2020 in recent records, so long-term field comparisons require care.
- Validation can detect structural problems but cannot independently confirm that an official source record is factually correct.

Discovery supports fundamental research and researchers. Linkage supports collaborative research, partnerships and research infrastructure.

The Australian Research Council remains the authoritative source.

