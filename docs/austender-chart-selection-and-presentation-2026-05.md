# AusTender chart selection and presentation — May 2026 decisions

Historical project note from the early AusTender quarterly chart-development conversation (31 May 2026). This records editorial and chart-design choices, **not** a specification of the current scripts. Consult [AusTender methodology](austender-methodology.md) and [the later quarterly publishing workflow](austender-quarterly-publishing-workflow-2026-07.md) for the maintained processing and publication approach.

## Keep the scheduled chart set focused

The early generator exposed 18 possible value- and count-based procurement breakdowns. The maintainer chose to generate a smaller set of **seven charts intended for X/Buffer**, rather than produce many optional charts and decide what to post later. The seven-chart family was:

1. Top suppliers by reported contract value.
2. Largest individual reported contracts.
3. Top Defence suppliers by reported contract value.
4. Reported contract value by procurement method.
5. Reported contract value by overseas supplier country.
6. Top non-Defence agencies by reported contract value.
7. Top suppliers by number of reported contracts.

This is a **historical editorial selection**, not a prohibition on other analyses or a guarantee of current output filenames/order. Keep full underlying data and supporting CSVs even when the social publishing set is small.

## Chart presentation and quality checks

- Prefer readable horizontal bars, concise axes (for example, values in **A$ billions** where appropriate), and a consistent source/period convention.
- Provide a contract-notice count in supporting captions when available and correctly scoped; avoid implying that a notice count is a count of unique suppliers or cash payments.
- Avoid label overlap, clipped long supplier names and crowded numeric annotations. A bug encountered during development produced repeated-looking company/contract annotations; review the **underlying grouped CSV** as well as the PNG before publishing. Do not fix a visual duplication symptom by silently dropping legitimate contract notices.
- Ensure chart title, legend, annotation, unit and caption all describe the same metric. Contract values are **reported commitments**, not expenditure paid in the quarter.
- Preserve the source attribution and exact supporting data used for each chart, and inspect the resulting PNG manually after generator changes.

## Buffer and tracking sheet

The maintainer wanted a predictable sequence of IPEA and AusTender chart posts rather than a large chart-selection exercise each time. IPEA and quarterly AusTender posts were tracked on **separate Google Sheets tabs**. The AusTender tracking columns used at the time were:

`Post ID | Quarterly Source CSV | Quarterly Category | Caption | C Count (280 Max) | Scheduled on Buffer | X URL | Post Date`

The May 2026 session ended with **seven AusTender charts loaded into Buffer**. This is a historical observation, not evidence that those posts remain scheduled or were published. Continue to verify Buffer status and the live X URL separately.

## Later improvements supersede this note

Subsequent repository work added explicit amendment handling, historical quarter-end views, partial-coverage warnings, supplier-name standardisation and website publication guidance. The current code and methodology take precedence. In particular, don't sum original and amended notice values as separate contracts, and don't equate a weekly export archive with complete official historical coverage.
