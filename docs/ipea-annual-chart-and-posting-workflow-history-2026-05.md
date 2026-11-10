# Historical IPEA annual chart and posting workflow decisions (May 2026)

> **Historical design record, not current operating instructions.** This note preserves the decisions from the May 23, 2026 APET annual-chart development discussion. The maintained pipeline has since changed from calendar-year annual aggregation to Australian financial years. Follow [IPEA methodology](ipea-methodology.md), [party-normalisation caveats](ipea-party-normalisation-and-quarterly-comparisons.md), and [editorial policy](editorial-social-media-policy.md) for present-day behaviour.

## Why annual charts were introduced

The initial IPEA workflow generated up to **23 charts per quarter**: three overview charts, ten individual-spender rankings, and ten quarter-on-quarter increase rankings. At a proposed pace of three social posts per day, publishing the historical quarterly backlog would have taken considerable time. The annual series was conceived as a more compact, public-facing summary, while quarterly charts remained a detailed searchable/archive layer.

An early proof-of-concept loaded four calendar-quarter files such as `2024q01_dataextract.csv` through `2024q04_dataextract.csv` with `pandas.concat`, then aggregated the official `Amount` field. It used the source's `FullNameWithTitle`, `Party`, `StateOrTerritory`, `HighLevelCategory`, and `MajorSubCategory` fields. Mixed-type CSV warnings were addressed with `pd.read_csv(..., low_memory=False)`. The first generic-column draft failed with `KeyError: 'Parliamentarian'`, illustrating why source-schema validation matters.

**Superseded:** The first annual prototype considered *calendar years*, whereas today's maintained annual generator requires four quarters forming a complete *Australian financial year*. For example, FY2024-25 combines 2024 Q3, 2024 Q4, 2025 Q1 and 2025 Q2. Do not replace the current generator with the transcript's early scripts.

## Original 13 annual chart types and ordering

The May 2026 annual social-series/data-validation list was:

| Number | Original chart title |
| --- | --- |
| 01 | Annual Spending by High-Level Category |
| 02 | Annual Spending by Party |
| 03 | Annual Spending by State or Territory |
| 04 | Top Annual Parliamentary Expense Totals |
| 05 | Top Annual Travel Spending |
| 06 | Top Annual Domestic Travel |
| 07 | Top Annual International Travel |
| 08 | Top Annual COMCAR Spending |
| 09 | Top Annual Travel Allowance |
| 10 | Top Annual Printing and Communications |
| 11 | Top Annual Publications |
| 12 | Top Annual Telecommunications |
| 13 | Top Annual Office Consumables and Services |

The initial recommendation was **not** to proliferate narrow category charts merely to increase post counts. Year-on-year increase charts were deferred as a possible later enhancement, rather than added to the 13-chart baseline. Chart titles and categories should always be checked against the current script and IPEA definitions.

## Shared chart formatting decisions

- Put reusable cleaning, colours, source attribution, brand/logo layout and party legends in `scripts/chart_helpers.py` and import them from both generators.
- The old quarterly script initially defined its own `add_footer()`, so edits to the helper logo size had no effect. The subsequent refactor removed that inconsistency. Reuse shared code instead of duplicating footer definitions.
- The logo was enlarged in the original 16:9 chart design after visual review; preserve readable margins and test chart screenshots.
- Display currency labels inside bars where there is sufficient space, otherwise outside with enough padding. This was a visual preference in the early charts, **not** a guarantee of the latest helper implementation.
- Keep party colours and *canonical display* party names consistent across quarterly/annual figures. In particular, historical extract variants of the Liberal Party and Australian Labor Party should not appear as separate bars merely due to case or wording; retain raw labels for traceability.
- Export a supporting CSV alongside each chart for verification. Avoid assuming a chart that renders without error has reconciled correctly.

See the separately maintained [party label and comparison notes](ipea-party-normalisation-and-quarterly-comparisons.md) for limitations of personal overrides and unmatched quarter-on-quarter records.

## Historical publishing-log proposal

The original workbook was to use separate **Quarterly Posts** and **Annual Posts** tabs, each with a chart-type data-validation dropdown. Proposed opaque post identifiers were `IPEAQ0001` for quarterly and `IPEAA0001` for annual, with independent sequential counters that **do not restart each year**. The metadata considered useful were post ID, reporting type, financial/calendar period, chart number/title, source, status, posted date, link and notes. These identifiers were a **proposal** and should not be assumed to have been adopted in the current live posting log.

The then-proposed release order was: post annual summaries for the historical backlog, resume quarterly distribution when caught up, and publish a year-end annual recap. The idea was meant to limit repetitive publishing, not impose a schedule. **Current editorial policy supersedes any automatic posting quota:** the website hosts the full chart archive, while X posts should be selective, sourced, neutral, verified and human-approved.

## Preservation and exclusions

This note records decisions, not runnable old versions of the scripts. Do not commit raw official extracts, generated plot PNGs, local posting workbooks, or old pasted helper/quarterly/annual scripts simply to archive this conversation. The maintained code and methodology remain authoritative.
