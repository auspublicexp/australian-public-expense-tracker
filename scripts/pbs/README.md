# PBS Date of Supply prototype

This prototype uses the official PBS and RPBS Date of Supply workbook to chart the Australian Government contribution to prescription costs.

Run the scripts in this order:

```powershell
python fetch_pbs_date_of_supply.py
python normalize_pbs_date_of_supply.py
python validate_pbs_date_of_supply.py
python generate_pbs_charts.py
python build_pbs_search_index.py
```

`generate_pbs_prototype_charts.py` is optional and is retained for testing. You do
not need to run it for the website.

The chart generator deliberately stays one complete source quarter behind. This gives late claims and revisions more time to be incorporated. It also uses only complete financial years in annual comparisons.

The prototype creates six views:

1. government expenditure by financial year;
2. government expenditure by financial quarter;
3. top medicines in the latest complete financial year;
4. top medicines in the latest publishable quarter;
5. largest medicine expenditure increases between the two latest complete financial years; and
6. government and patient contributions by complete financial year.

Government contribution is not the same as total prescription cost. The source can be revised, recent months are less complete, and some Section 100 special arrangements are excluded. See the official [Date of Supply page](https://www.pbs.gov.au/statistics/dos-and-dop/dos-and-dop) and explanatory notes before interpreting results.

`generate_pbs_charts.py` is the full generator. It creates overview charts plus three charts for every complete annual and quarterly period allowed by the validation cutoff. The complete archive—PNG, SVG and supporting CSV files—goes to `output/pbs/`. Website-ready SVG and CSV files are also copied to `website/public_html/charts/pbs/`; use `--no-website-copy` to disable that copy. The script prints both full destination paths and checks that the PNG and SVG chart counts match before it finishes.

Run `build_pbs_search_index.py` after chart generation. It creates a compact annual and quarterly medicine search index and copies it to `website/public_html/charts/pbs/pbs-search-index.json`.
