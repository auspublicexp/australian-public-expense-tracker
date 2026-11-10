# GrantConnect chart QA: lessons from early 2026 chart troubleshooting

This note preserves the useful outcomes of the June 2026 APET GrantConnect chart-debugging session. It is historical context, **not** a claim that the old screenshots or source exports have been revalidated. See [GrantConnect methodology](grantconnect-methodology.md) for the current data workflow.

## Visual layout fixes (implemented in current shared helper)

- Use dynamic height for short top-N lists (`max(4.8, min(10, row_count * 0.85 + 2.5))`) and a narrower 14-inch canvas for 1–3 rows, otherwise 16 inches.
- Format monetary bar labels once, at the bar endpoint, using `max_value * 0.006` offset and `max_value * 1.16` x-axis limit. Avoid an additional `ax.text()` loop in the caller; duplicated chart-label code can produce misleading overprinted values.
- Wrap long recipient / grant-activity labels, use restrained bar height and vertical margins, and inspect the chart when there are only 2–5 entries or a large outlier. Prefer concise *display* descriptions when the exported source contains boilerplate, without changing the retained source data.

## The duplicate-label trap

Early charts appeared to show fewer bars than top-N input rows, with multiple value labels printed on one bar. The problem was that `matplotlib.barh` was supplied **non-unique categorical y labels** (same recipient plus activity): Matplotlib assigned the same y-position to distinct records. Adding a rank prefix made the *display positions* distinct and revealed all five rows.

Current annual and quarterly chart 04 implementations prefix the row rank to `Recipient Name — Grant Activity`, preserving distinct display labels. Ranking is a presentation fix, **not deduplication**.

## The duplicate-award trap (critical)

An early workaround used `drop_duplicates(subset=["Recipient Name", "Grant Activity", "Value (AUD)"])` before selecting top five. **Do not reinstate that heuristic.** Separate valid GrantConnect award records can share these fields; dropping one would change the ranking or underestimate totals.

The current pipeline instead removes *exact duplicate rows*, then checks remaining repeated `GA ID` values and stops for review rather than silently deleting or collapsing distinct records. The two-step approach is documented in the main methodology. The specific June screenshots cannot establish whether matching-value records were truly duplicate awards without their original GA IDs and workbook context.

## Suggested QA regression cases

1. Five different GA IDs with two identical recipient/activity/value combinations: all five records must remain eligible for top five and have separate y positions.
2. Identical rows repeated across overlapping exports: exact duplicates should not count twice; a repeated GA ID with nonidentical rows should trigger review.
3. One to three bars: compact, legible canvas, source footer/logo and value labels visible.
4. Ten bars and long text: no category collision or accidental truncation of important grant meaning.
5. Large outlier (the June 2022 screenshot showed a reported award around A$2.35bn): smaller awards should remain interpretable, and exact outside labels should not overlap.
6. Validate generated PNG/SVG and matching CSV against the original retained award records before publishing; a visually plausible chart is not proof of completeness or deduplication correctness.

## Scope and status

- This note describes lessons and QA cases; no chart data was recomputed or government source records independently verified while writing it.
- Current repo code was inspected 10 November 2026: `scripts/chart_helpers.py`, `scripts/grantconnect/generate_grantconnect_annual_charts.py`, and `scripts/grantconnect/generate_grantconnect_quarterly_charts.py` already contain the visual-layout and rank-label corrections.
- No production code change is required solely to preserve this historical discussion. Future QA should investigate the old duplicate-value examples using original `GA ID` values rather than deleting them based on apparent matching labels.
