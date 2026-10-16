# NDIS payments: methodology and limitations

APET uses the NDIA's [payments datasets](https://dataresearch.ndis.gov.au/datasets/payments-datasets) to present recorded payments for FY2023–24, FY2024–25 and FY2025–26. Each June snapshot covers the preceding 12 months. These are payments, not plan budgets, committed supports or the full administrative cost of the scheme.

## Aggregation

The build selects published aggregate rows with all ages, disabilities, service districts and support items. National totals sum the four published support classes once; detailed rows are never added to those aggregates. State and territory totals use one aggregate per support class and participant residence. They are not spending by state governments, and are not adjusted for population or participant numbers.

Participant counts overlap between support groups and are not summed. Suppressed values are unavailable, never zero. Other territories includes suppression; Missing location has repeated labels and suppression, so those totals are not inferred. Consequently, the eight displayed jurisdictions do not sum to the national total. June 2024 has four suppressed class-0 detail rows without a national aggregate; these are excluded from the national class sum. The June 2026 negative $3,000 Missing support entry is preserved.

## Periods and comparisons

Use June snapshots for complete financial years. Successive quarterly snapshots contain overlapping 12-month periods and must not be added together. Historical values retain their original snapshot vintage. Comparisons are in nominal Australian dollars without inflation adjustment or revision harmonisation.

The explorer produces one annual-total chart, three category breakdowns, three pairwise category-change charts and eight jurisdiction trends. Category changes are calculated from category values, not national-total differences. State charts have individually labelled vertical scales starting at zero; compare their values rather than visual slopes.

## Source checks and discrepancies

The national dataset totals are $41,254,223,000 (2023–24), $45,853,407,000 (2024–25) and $51,451,547,000 (2025–26). Category sums exceed class totals by $1,000, $2,000 and $2,000 respectively; these differences are preserved.

The build compares each total with payment columns in the matching Q4 National Supplement workbook: E.116/E.117 for 2023–24, E.111/E.112 for 2024–25 and E.109/E.110 for 2025–26. Workbook values are read as dollars even where their displayed format is millions. Tables organised by the year support was provided measure something different.

Dataset totals exceed the corresponding report totals by $17,673,921.72, $9,314,661.10 and $5,611,821.40. The reasons are not established; APET discloses these differences without claiming exact reconciliation or adjusting the dataset to force agreement.

Each annual page includes source links, a SHA-256 checksum in its JSON download, CSV downloads and a validation JSON recording structural checks and discrepancies. Original source files and generated outputs are not committed to GitHub.

## Reproduction

See the [NDIS build instructions](../scripts/ndis/README.md) for official file identifiers, filenames, commands and website dependencies. Source files were retrieved and checked on 16 October 2026. New releases require review of dates, dimensions, suppression and report tables before extending the pinned configuration.
