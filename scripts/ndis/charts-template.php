<?php
$pageTitle = 'NDIS Payment Charts | Australian Public Expense Tracker';
$pageDescription = 'Compare NDIS payments across 2023–24, 2024–25 and 2025–26: annual totals, support categories, category changes and state trends.';
$manifest = json_decode(file_get_contents(__DIR__ . '/charts/manifest.json'), true, 512, JSON_THROW_ON_ERROR);
$years = ['2023-24', '2024-25', '2025-26'];
$year = isset($_GET['fy']) && is_string($_GET['fy']) && in_array($_GET['fy'], $years, true) ? $_GET['fy'] : '2025-26';
$comparisons = ['2023-24-2024-25'=>'2023–24 to 2024–25', '2024-25-2025-26'=>'2024–25 to 2025–26', '2023-24-2025-26'=>'2023–24 to 2025–26'];
$comparison = isset($_GET['comparison']) && is_string($_GET['comparison']) && isset($comparisons[$_GET['comparison']]) ? $_GET['comparison'] : '2024-25-2025-26';
function ndisEscape($value) { return htmlspecialchars((string)$value, ENT_QUOTES, 'UTF-8'); }
function ndisChart($key, $wide = false) {
    global $manifest;
    $chart = $manifest[$key];
    echo '<figure class="mb-4"><div class="chart-scroll'.($wide ? ' chart-wide' : '').'"><img class="chart-image" width="'.(int)$chart['width'].'" height="'.(int)$chart['height'].'" src="charts/'.ndisEscape($key).'.svg" alt="'.ndisEscape($chart['title']).'. Exact values are in the table below." loading="lazy"></div>';
    echo '<figcaption class="small mt-2">Download: <a href="charts/'.$key.'.png" download>PNG image</a> · <a href="charts/'.$key.'.svg" download>SVG image</a> · <a href="charts/'.$key.'.csv" download>CSV data</a></figcaption></figure>';
    echo '<details class="mb-4"><summary>View exact values: '.ndisEscape($chart['title']).'</summary><div class="table-responsive mt-3"><table class="table table-sm"><caption>'.ndisEscape($chart['title']).' · AUD, not adjusted for inflation</caption><thead><tr>';
    foreach ($chart['columns'] as $column) echo '<th scope="col">'.ndisEscape(ucwords(str_replace('_',' ',$column))).'</th>';
    echo '</tr></thead><tbody>';
    foreach ($chart['rows'] as $row) {
        echo '<tr>';
        foreach ($row as $i=>$value) {
            $column=$chart['columns'][$i];
            $display=$value===null ? '—' : (str_ends_with($column,'_aud') ? ($value<0?'−':'').'$'.number_format(abs($value),0) : (str_ends_with($column,'_percent') ? number_format($value,2).'%' : $value));
            echo '<td>'.ndisEscape($display).'</td>';
        }
        echo '</tr>';
    }
    echo '</tbody></table></div></details>';
}
include __DIR__ . '/../includes/header.php';
?>
<style>
.ndis-charts{max-width:1100px}.chart-image{display:block;width:100%;height:auto;background:white}.chart-scroll{overflow-x:auto;border:1px solid #ddd;border-radius:6px;background:white}.chart-wide .chart-image{min-width:650px}.chart-annual{max-width:680px;margin:auto}.ndis-charts section{scroll-margin-top:1rem}.ndis-charts summary{cursor:pointer;color:#176378}.state-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.5rem}.state-panel{min-width:0}
@media(max-width:767px){.state-grid{grid-template-columns:1fr}.ndis-charts h1{font-size:2rem}}
</style>
<main class="container ndis-charts py-5">
<a href="/ndis/">← NDIS annual data and sources</a>
<h1 class="mt-3">NDIS payments in charts</h1>
<p class="lead">Where payments go and how they changed across three financial years.</p>
<p><strong>1 July 2023 – 30 June 2026.</strong> Each year uses its June snapshot. Amounts are Australian dollars, not adjusted for inflation.</p>
<nav aria-label="Chart sections" class="d-flex flex-wrap gap-2 my-4"><a class="btn btn-outline-dark" href="#annual">Annual payments</a><a class="btn btn-outline-dark" href="#categories">Support categories</a><a class="btn btn-outline-dark" href="#changes">Category changes</a><a class="btn btn-outline-dark" href="#states">State trends</a></nav>
<section id="annual" class="my-5"><h2>Annual NDIS payments</h2><p>National payment totals, with percentage changes from the preceding financial year. The vertical scale starts at zero.</p><div class="chart-annual"><?php ndisChart('annual'); ?></div></section>
<form method="get" action="charts.php#categories" class="card card-body my-5"><h2 class="h5">Choose the category charts</h2><div class="row g-3 align-items-end"><div class="col-md-4"><label for="fy" class="form-label">Payments by category: financial year</label><select id="fy" name="fy" class="form-select"><?php foreach (array_reverse($years) as $option): ?><option value="<?= ndisEscape($option) ?>" <?= $year===$option?'selected':'' ?>><?= ndisEscape($option) ?></option><?php endforeach; ?></select></div><div class="col-md-5"><label for="comparison" class="form-label">Category changes: comparison</label><select id="comparison" name="comparison" class="form-select"><?php foreach ($comparisons as $key=>$label): ?><option value="<?= ndisEscape($key) ?>" <?= $comparison===$key?'selected':'' ?>><?= ndisEscape($label) ?></option><?php endforeach; ?></select></div><div class="col-md-3"><button class="btn btn-dark" type="submit">Update charts</button></div></div></form>
<section id="categories" class="my-5"><h2>Where payments go · <?= ndisEscape($year) ?></h2><p>Support categories ranked by payments. “CB” means Capacity Building. Chart labels are in millions; the horizontal axis is in billions.</p><p class="small text-secondary">On a small screen, swipe the chart sideways or open the exact-values table.</p><?php ndisChart('categories-'.$year,true); ?></section>
<section id="changes" class="my-5"><h2>Which categories account for the increase?</h2><p><strong><?= ndisEscape($comparisons[$comparison]) ?>.</strong> Each bar is the later year minus the earlier year. Bars to the right show increases; bars to the left show decreases. This describes where changes occurred, without establishing their causes.</p><?php ndisChart('change-'.$comparison,true); ?><p class="small text-secondary">Category sums differ slightly from the national support-class totals in the source. Changes here use category values consistently and may not add exactly to the change in the national total. “Missing” is retained as a source category, including the negative entry in 2025–26.</p></section>
<section id="states" class="my-5"><h2>State and territory trends</h2><p>Payments by participant residence. <strong>Each chart has its own vertical scale, starting at zero.</strong> Compare the labelled amounts when comparing states; line steepness is not comparable across panels. Values are not adjusted for population or participant numbers.</p><div class="state-grid"><?php foreach (['ACT','NSW','NT','QLD','SA','TAS','VIC','WA'] as $code): ?><div class="state-panel"><?php ndisChart('state-'.$code); ?></div><?php endforeach; ?></div><p class="small text-secondary">Other territories and Missing location are excluded from these charts because their totals are unavailable. They remain represented in the national aggregate. No suppressed values have been estimated.</p></section>
<section class="border-top pt-4"><h2>Sources and interpretation</h2><p>Source: <a href="https://dataresearch.ndis.gov.au/datasets/payments-datasets">NDIA payments datasets</a>, June 2024, June 2025 and June 2026 snapshots, retrieved 16 October 2026. These are payments for the preceding 12 months, not quarterly payments, plan budgets or measures of service quality.</p><p>Historical values use their original snapshots. Differences in reporting, revisions and classification may affect comparisons. The payments dataset differs slightly from matching quarterly-report totals; the reason has not been established. See each annual page for the exact comparison and source qualifications:</p><ul><li><a href="fy2023-24.php#sources">2023–24 sources and notes</a></li><li><a href="fy2024-25.php#sources">2024–25 sources and notes</a></li><li><a href="/ndis/#sources">2025–26 sources and notes</a></li></ul><p class="small">Download images and data beside each chart. Please retain the financial year, units and source attribution when sharing.</p></section>
</main>
<?php include __DIR__ . '/../includes/footer.php'; ?>
