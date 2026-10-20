<?php
/** Image exports for the exact chart displayed; absent files get no link. */
function renderChartDownloads(string $svgUrl, ?string $csvUrl = null): void
{
    $root = realpath(dirname(__DIR__));
    $urlPath = parse_url($svgUrl, PHP_URL_PATH);
    if (!is_string($urlPath) || !str_starts_with($urlPath, '/charts/') || !str_ends_with($urlPath, '.svg')) {
        return;
    }
    $stem = substr($urlPath, 0, -4);
    $links = [];
    foreach (['PNG' => $stem . '.png', 'SVG' => $stem . '.svg', 'CSV' => $csvUrl ?? $stem . '_data.csv'] as $label => $url) {
        $disk = realpath($root . $url);
        if ($disk === false || !str_starts_with($disk, $root . DIRECTORY_SEPARATOR) || !is_file($disk) || !is_readable($disk)) {
            continue;
        }
        $href = htmlspecialchars(implode('/', array_map('rawurlencode', explode('/', $url))), ENT_QUOTES, 'UTF-8');
        $filename = htmlspecialchars(str_replace('/', '_', substr($url, strlen('/charts/'))), ENT_QUOTES, 'UTF-8');
        $links[] = '<a class="btn btn-sm btn-outline-secondary" href="' . $href . '" download="' . $filename . '">Download ' . $label . '</a>';
    }
    if ($links) {
        echo '<div class="card-body border-top py-3 d-flex flex-wrap gap-2" role="group" aria-label="Chart downloads">' . implode('', $links) . '</div>';
    }
}
