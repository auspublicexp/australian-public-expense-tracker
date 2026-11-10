# AusTender weekly contract-notice validation — 12–18 July 2026

This note preserves an early APET validation exercise and its reporting decisions. It describes a **historical local weekly-chart script**, not necessarily a currently maintained repository command. The present repository documents its active quarterly processing in [AusTender methodology](austender-methodology.md).

## Why the distinction matters

An AusTender weekly contract-notice export can contain both **new/original contract notices** and **amendment notices** to contracts originally published much earlier. The contract's `Publish Date` records its original publication; an amendment's `Amendment Publish Date` records when the change was published. An amendment's `Value` is the reported **updated total contract value**, not necessarily the increase or decrease caused by the amendment.

Consequently, summing every exported `Value` and calling it "new contracts" or "spending during the week" overstates what those metrics mean. These values may also cover contracts lasting years and must not be confused with payments made in the reporting week.

## Local validation result

The local Excel source was named `12-Jul-26 to 18-Jul-26.xlsx`. The amended weekly Python chart script separated rows according to `Parent CN ID` (populated = amendment; blank = original notice), excluded amendment notices from its **new contract** charts, and saved them separately as `weekly_amendment_notices.csv`.

| Measure | 12–18 July 2026 |
| --- | ---: |
| Rows in weekly export | 1,740 |
| New/original contract notices | 1,139 |
| Amendment notices | 601 |
| Sum of values attached to all export rows | $19,862,064,253 |
| Sum of values attached to new/original notices | $980,652,452 |
| Sum of values attached to amendment notices | $18,881,411,801 |
| Defence new/original notice value | $301,358,321 |
| Non-Defence new/original notice value | $679,294,131 |

The Defence and non-Defence values reconcile to the new/original notice total. All 18 local weekly charts were generated during the test. The 601 exported amendment rows were further classified in the chat as: 316 variations to contract value, 222 option/extension/renewal notices, 59 administrative corrections, and 4 supplier novations. **These are historical validation observations, not an independently re-run test of the current repository.**

The $18.881 billion figure is **not** "$18.881 billion in additional spending", "new contract value", or the sum of changes caused by the amendments. It is the total of the full values recorded on those amendment notices.

## Reproducing the historical weekly test

The earlier local script was named `generate_austender_charts.py` (not currently present in this repository's `scripts/austender` directory at the time of this note). Its settings used a single weekly source workbook:

```python
TARGET_FILE_PATTERN = "12-Jul-26 to 18-Jul-26.xlsx"
PERIOD_START = "2026-07-12"
PERIOD_END = "2026-07-18"
```

The workbook was kept under `data/austender/`; generated weekly outputs, including `weekly_amendment_notices.csv`, were kept under `output/austender/`. Source workbooks and generated CSVs are local data, not committed here.

If this separate weekly workflow is reinstated, validate the file's headers and date coverage, count new and amended notices separately, reconcile Defence/non-Defence new-notice totals, examine samples of amendments and confirm their publication dates before publishing. Use labels such as **reported new contract value** rather than **weekly spending**.

## Historical quarter vs current contract state

The [active combine script](../scripts/austender/combine_austender_files.py) retains original and amended rows in `output/austender/austender_master.csv` as an audit trail; it also produces `output/austender/austender_current_contracts.csv` containing the latest known version per `Root CN ID`. The current-state file should **not** be used directly to reconstruct historical quarter-end values, because later amendments can change them.

The [active quarterly charts](../scripts/austender/generate_austender_quarterly_charts.py) should select the latest version **published on or before the relevant quarter end** for each underlying contract, while grouping contracts by the original notice's publication quarter. This avoids adding an original value and its amended value together, and avoids using amendments published after the cutoff.

## Possible future amendment analysis

To describe **changes** rather than the full values attached to notices:

1. Link versions using `Root CN ID`, derived from `Parent CN ID` where present or `CN ID` otherwise.
2. Order contract versions by effective record publication date (`Amendment Publish Date` for amendments, otherwise `Publish Date`), with a deterministic tie-breaker.
3. Compare each amendment's reported value with the **immediately previous** published version, not necessarily the original notice.
4. Calculate change as `new reported value - previous reported value`. Keep increases, decreases and administrative corrections identifiable; do not assume every value adjustment represents new procurement or a cash payment.
5. Assign amendment activity to the week of the **amendment publication**, while retaining original publication dates for original-notice reporting.

This is a proposed analytical extension, not an implemented or verified feature of the current repository.

## Related example and caution

During a separate FY2025–26 Q4 investigation, a Department of Home Affairs aerial-surveillance notice for Metrea Australia was observed at approximately $4.319 billion, with a stated contract term extending to 2039. The local raw quarter aggregation also included an original and amendment for a Toll Remote Logistics notice at roughly $151 million each, illustrating why summing contract versions is misleading. These were exploratory findings from the then-local data and should be re-checked against current official AusTender notices before publication or reuse.
