"""Write compact validation reports for APET data pipelines."""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = Path(
    os.environ.get(
        "APET_VALIDATION_DIR",
        PROJECT_ROOT / "output" / "validation",
    )
)


def _json_safe(value: Any) -> Any:
    """Convert common pandas/path/date values into JSON-compatible values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return str(value)


def write_validation_report(
    pipeline: str,
    metrics: Mapping[str, Any],
    checks: Iterable[str] = (),
    *,
    status: str = "PASSED",
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Write latest human-readable and machine-readable validation reports."""
    report_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
    report_dir.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r"[^a-z0-9]+", "_", pipeline.lower()).strip("_")
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    safe_metrics = {key: _json_safe(value) for key, value in metrics.items()}
    check_list = [str(check) for check in checks]
    payload = {
        "pipeline": pipeline,
        "status": status,
        "generated_at_utc": generated_at,
        "metrics": safe_metrics,
        "checks": check_list,
    }

    json_path = report_dir / f"{slug}_latest.json"
    text_path = report_dir / f"{slug}_latest.txt"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"APET validation report: {pipeline}",
        f"Status: {status}",
        f"Generated (UTC): {generated_at}",
        "",
        "Summary",
    ]
    for key, value in safe_metrics.items():
        label = key.replace("_", " ").capitalize()
        lines.append(f"- {label}: {value}")
    if check_list:
        lines.extend(["", "Checks"])
        lines.extend(f"- PASS: {check}" for check in check_list)
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Validation report: {text_path}")
    return text_path, json_path
