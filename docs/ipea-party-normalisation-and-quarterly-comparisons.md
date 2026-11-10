# IPEA chart party labels and quarter-to-quarter comparisons

This note preserves design decisions from the APET quarterly/annual chart review (May–November 2026). It documents existing behaviour; it does not establish independently verified historical party affiliation.

## Party display labels

- The shared helper `scripts/chart_helpers.py` provides `clean_name()`, `clean_party_name()`, `get_display_party(name, party)`, and `get_party_color()`.
- `get_display_party()` first normalises the person's name, checks `KNOWN_PARTY_OVERRIDES`, and otherwise uses the cleaned party label from the IPEA extract.
- The known override maps **Pauline Hanson** to **One Nation Australia** for chart display. This is an APET presentation rule, not a correction to the official IPEA source file.
- Both `scripts/ipea/generate_quarterly_charts.py` and `scripts/ipea/generate_annual_charts.py` apply `get_display_party()` during data loading, before party-based aggregations and chart colours are assigned.
- `clean_name()` removes selected titles and suffixes for display and override matching. Add overrides cautiously: a person's party can change over time, and a global name-based override can misrepresent historical quarters. Any future overrides should be checked against period-specific official evidence and ideally be date-aware.

## Quarterly comparison caveats

- Quarterly charts include largest positive increases in reported amounts relative to the preceding available extract.
- The comparison groups by both `FullNameWithTitle` and the **display** party label, then joins the current and previous aggregates. If a name or party label changes between periods, matching may fail.
- Missing previous-period matches are treated as zero in the current implementation. An apparent increase can therefore represent a new parliamentarian, changed label, or missing comparison record, not necessarily a like-for-like spending increase.
- Review the source period, category coverage, adjustments, and membership changes before presenting an increase as a meaningful trend. Avoid implying wrongdoing from rankings or increases alone.
- Preserve original source values separately from APET-normalised display labels when building future analyses.

## Maintenance checklist

1. Keep the quarterly and annual scripts aligned with shared helper behaviour.
2. When adding an override, test its effect on several historical quarters as well as the current quarter.
3. Check that totals and chart-supporting CSV exports reconcile to source data.
4. For quarter-on-quarter rankings, flag unmatched identities rather than silently interpreting them as genuine zero baselines in future revisions.
5. Retain the official IPEA dataset as the authoritative record and document any APET-specific transformations.

See [IPEA methodology](ipea-methodology.md) for the broader pipeline and source limitations.
