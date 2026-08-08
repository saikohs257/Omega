from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .calibration import CalibrationReport


def artifact_directory(root: str | Path, manifest_hash: str, run_id: str) -> Path:
    """Return the immutable-by-convention storage location for one calibration run."""
    if len(manifest_hash) != 64 or not manifest_hash.isalnum():
        raise ValueError("manifest_hash must be a 64-character identity")
    if not run_id or "/" in run_id or "\\" in run_id:
        raise ValueError("run_id must be a non-empty path-safe identifier")
    return Path(root) / "calibration_reports" / manifest_hash / run_id


def write_calibration_artifacts(
    report: CalibrationReport,
    *,
    root: str | Path,
    run_id: str,
    metric_distributions: dict[str, Any] | None = None,
) -> Path:
    """Persist a report as small, diffable JSON artifacts.

    The manifest hash is part of the path; the report hash is part of the
    payload. Existing files are never overwritten by this helper.
    """
    directory = artifact_directory(root, report.corpus_manifest_hash, run_id)
    directory.mkdir(parents=True, exist_ok=True)
    files = {
        "calibration_report.json": report.to_dict(),
        "reliability_bins.json": {
            "n_bins": len(report.reliability_bins),
            "confidence_measure": "metric_contract",
            "bins": list(report.reliability_bins),
        },
        "metric_distributions.json": metric_distributions or {
            "controls": [c.to_dict() for c in report.controls],
            "candidates": [c.to_dict() for c in report.candidates],
        },
    }
    for filename, payload in files.items():
        path = directory / filename
        encoded = json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n"
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if existing != encoded:
                raise FileExistsError(f"refusing to overwrite calibration artifact: {path}")
            continue
        path.write_text(encoded, encoding="utf-8")
    return directory
