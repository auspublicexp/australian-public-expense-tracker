<?php
$pageTitle = 'NDIS Payments | Australian Public Expense Tracker';
$pageDescription = 'Explore NDIS payments for the year ending 30 June 2026 by participant state and support category, using official NDIA data.';
include __DIR__ . '/../includes/header.php';
?>
<style>
.ndis-hero{background:#eef5f7;border-left:5px solid #176378}.ndis-bar{height:7px;background:#176378;margin-top:.55rem;border-radius:4px;min-width:2px}.ndis-section{scroll-margin-top:1rem}.ndis-content{max-width:1100px}.ndis-content th:first-child{width:70%}.ndis-content caption{font-size:.9rem}.ndis-total{font-variant-numeric:tabular-nums}
@media(max-width:575px){.ndis-content th:first-child{width:55%}.ndis-content table{font-size:.85rem}.ndis-content .display-4{font-size:2.4rem}}
</style>
<main class="container ndis-content py-5">
<p class="text-secondary mb-2">DISABILITY SUPPORT · FY2025–26</p>
<h1>NDIS payments</h1>
<p class="lead">Payments recorded in the National Disability Insurance Scheme, by participant residence and type of support.</p>
<p class="my-4"><a class="btn btn-dark" href="/ndis/charts.php">Compare years in charts</a></p>
<section class="ndis-hero rounded p-4 my-4" aria-label="National payments summary">
<p class="fw-semibold mb-2">12 months: 1 July 2025 – 30 June 2026</p>
<p class="display-4 fw-bold ndis-total mb-1">$@@TOTAL@@ billion</p>
<p class="mb-0">National total from the June 2026 payments dataset<br><small>$@@EXACT@@ AUD · Includes the source’s “Missing” support-class entry</small></p>
</section>
<p>This is a full year of payments, not a single quarter. It measures payments recorded in this dataset, rather than plan budgets or the entire cost of administering the scheme.</p>
<nav class="d-flex flex-wrap gap-2 my-4" aria-label="NDIS page sections">
<a class="btn btn-outline-dark" href="#states">States and territories</a><a class="btn btn-outline-dark" href="#supports">Support categories</a><a class="btn btn-outline-dark" href="#sources">Sources and notes</a><a class="btn btn-dark" href="payments-summary.csv" download>Download summary CSV</a>
</nav>
<section id="states" class="ndis-section my-5"><h2>Payments by state and territory</h2>
<p>Based on where participants reside. These are total payments, without adjusting for population or participant numbers.</p>
@@STATES@@
<p class="small text-secondary">Other territories includes suppressed source values. The source repeats “Missing” location labels and contains suppression; APET does not combine those rows. These unavailable groups are included within the national support-class totals, so the visible state amounts do not sum to the national figure.</p>
</section>
<section id="supports" class="ndis-section my-5"><h2>Payments by support type</h2><p>National payments for the same 12-month period. “CB” in the source category names means Capacity Building.</p>
<h3 class="h5 mt-4">Support classes</h3>@@CLASSES@@
<h3 class="h5 mt-4">Support categories</h3>@@CATEGORIES@@
<p class="small text-secondary">“Missing” is the source’s label for unclassified support. Its negative $3,000 entry is retained as published; the data rules do not explain it. Small differences between category and class sums are retained rather than adjusted.</p>
</section>
<section id="sources" class="ndis-section border-top pt-4 my-5"><h2>Sources and interpretation</h2>
<p>Source: National Disability Insurance Agency (NDIA), <a href="https://dataresearch.ndis.gov.au/datasets/payments-datasets">Payments datasets</a>. Snapshot: 30 June 2026. Retrieved: 16 October 2026.</p>
<ul>
<li><a href="https://dataresearch.ndis.gov.au/media/4577/download?attachment">Original June 2026 payments CSV</a> and <a href="https://dataresearch.ndis.gov.au/media/4474/download?attachment">current official data rules (Word)</a>. Historical pages retain the values in their respective June snapshots, rather than revising older years using later reports.</li>
<li>Payments cover the preceding 12 months. Successive quarterly snapshots overlap and must not be added together.</li>
<li>APET uses aggregate rows with all ages, disabilities, service districts and support items. National and state totals sum the four published support classes once. Detailed rows are not added to aggregate rows.</li>
<li>Suppressed payments are unavailable, never zero. Participant counts are not added across support groups because the same person can appear in several groups.</li>
<li>Values are shown in Australian dollars, as published. Category and class totals may differ slightly; the <a href="validation.json">validation summary</a> records the difference. A <a href="payments.json">JSON download</a> includes the source checksum.</li>
</ul>
<div class="bg-light border rounded p-3"><h3 class="h5">Comparison with the quarterly report</h3>
<p class="mb-0">The national payments dataset totals $@@TOTAL@@ billion. Payment totals in Tables E.109 and E.110 of the <a href="https://dataresearch.ndis.gov.au/media/4560/download?attachment">2025–26 Q4 National Supplement (Excel)</a> sum to $@@REPORT@@ billion for the same year. The dataset is $@@DIFF@@ million higher (@@PERCENT@@%). The reason is not established by the published material checked. APET preserves the dataset total and does not claim an exact reconciliation. Table E.111 uses the year support was provided and is a different measure.</p></div>
</section>
</main>
<?php include __DIR__ . '/../includes/footer.php'; ?>
