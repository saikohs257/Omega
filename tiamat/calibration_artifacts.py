from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any, Mapping

from .calibration import CalibrationReport

CALIBRATION_ARTIFACT_SCHEMA_VERSION = 2
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def artifact_directory(root: str | Path, manifest_hash: str, run_id: str) -> Path:
    """Return the immutable-by-convention storage location for one calibration run."""
    if not _SHA256_RE.fullmatch(manifest_hash):
        raise ValueError("manifest_hash must be a lowercase 64-character SHA-256 hex digest")
    if not run_id or Path(run_id).name != run_id:
        raise ValueError("run_id must be a non-empty path-safe identifier")
    return Path(root) / "calibration_reports" / manifest_hash / run_id


def _first_comparable_bins(report: CalibrationReport) -> list[dict[str, Any]] | None:
    for entry in report.reliability_bins:
        bins = entry.get("bins")
        if bins is not None:
            return [dict(bucket) for bucket in bins]
    return None


def _reliability_payload(report: CalibrationReport) -> dict[str, Any]:
    first_bins = _first_comparable_bins(report)
    n_bins = len(first_bins) if first_bins is not None else 0
    bin_edges: list[float] = []
    if first_bins:
        bin_edges = [float(bucket["edge_lo"]) for bucket in first_bins]
        bin_edges.append(float(first_bins[-1]["edge_hi"]))
    predictors: list[dict[str, Any]] = []
    for entry in report.reliability_bins:
        bins = entry.get("bins")
        if bins is not None:
            bins = [dict(bucket) for bucket in bins]
            if n_bins and len(bins) != n_bins:
                raise AssertionError("reliability writer must emit every configured bin")
        predictors.append(
            {
                "predictor": entry.get("predictor"),
                "comparable": bool(entry.get("comparable", bins is not None)),
                "reason": entry.get("reason"),
                "bins": bins,
            }
        )
    if first_bins is not None and len(first_bins) != n_bins:
        raise AssertionError("reliability writer must emit every configured bin")
    return {
        "schema_version": CALIBRATION_ARTIFACT_SCHEMA_VERSION,
        "_meta": {
            "schema_version": CALIBRATION_ARTIFACT_SCHEMA_VERSION,
            "n_bins": n_bins,
            "aggregation": "true_state_probability",
            "bin_edges": bin_edges,
        },
        "predictors": predictors,
    }


def _metric_distributions_payload(report: CalibrationReport) -> dict[str, Any]:
    return {
        "schema_version": CALIBRATION_ARTIFACT_SCHEMA_VERSION,
        "report_version": report.report_version,
        "controls": [control.to_dict() for control in report.controls],
        "candidates": [candidate.to_dict() for candidate in report.candidates],
    }


def _calibration_report_payload(report: CalibrationReport) -> dict[str, Any]:
    return report.to_dict()


def _bundle_hash(artifact_hashes: Mapping[str, str]) -> str:
    ordered = [(key, artifact_hashes[key]) for key in sorted(artifact_hashes)]
    return _sha256_bytes(_canonical_json(ordered))


def load_calibration_bundle(root: str | Path, manifest_hash: str, run_id: str) -> dict[str, Any]:
    """Load and validate a sealed calibration bundle."""
    bundle_dir = artifact_directory(root, manifest_hash, run_id)
    manifest_path = bundle_dir / "bundle.manifest"
    if not manifest_path.exists():
        raise ValueError("calibration bundle is incomplete: missing bundle.manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != CALIBRATION_ARTIFACT_SCHEMA_VERSION:
        raise ValueError("unsupported calibration bundle schema")
    if manifest.get("corpus_manifest_hash") != bundle_dir.parent.name:
        raise ValueError("bundle corpus hash does not match parent directory")
    artifacts: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    for name, metadata in manifest["artifacts"].items():
        path = bundle_dir / f"{name}.json"
        if not path.exists():
            raise ValueError(f"calibration bundle incomplete: missing {name}.json")
        data = path.read_bytes()
        digest = _sha256_bytes(data)
        if digest != metadata["hash"]:
            raise ValueError(f"calibration artifact hash mismatch: {name}")
        hashes[name] = digest
        artifacts[name] = json.loads(data.decode("utf-8"))
    if _bundle_hash(hashes) != manifest["bundle_hash"]:
        raise ValueError("calibration bundle hash mismatch")
    return {"manifest": manifest, **artifacts}


def write_calibration_artifacts(
    report: CalibrationReport,
    *,
    root: str | Path,
    run_id: str,
    metric_distributions: dict[str, Any] | None = None,
) -> Path:
    """Persist a calibration bundle as small, diffable JSON artifacts.

    The report is the source of truth. `metric_distributions` is retained for
    compatibility but the sealed bundle is always derived from the report.
    """
    del metric_distributions
    directory = artifact_directory(root, report.corpus_manifest_hash, run_id)
    directory.parent.mkdir(parents=True, exist_ok=True)
    if directory.exists():
        raise FileExistsError(f"refusing to overwrite calibration artifact bundle: {directory}")

    temp_dir = Path(
        tempfile.mkdtemp(prefix=f".tmp-{run_id}-{uuid.uuid4().hex}-", dir=str(directory.parent))
    )
    artifacts = {
        "calibration_report": _calibration_report_payload(report),
        "reliability_bins": _reliability_payload(report),
        "metric_distributions": _metric_distributions_payload(report),
    }
    encoded = {name: _canonical_json(payload) for name, payload in artifacts.items()}
    artifact_hashes = {name: _sha256_bytes(data) for name, data in encoded.items()}
    bundle_hash = _bundle_hash(artifact_hashes)
    manifest = {
        "schema_version": CALIBRATION_ARTIFACT_SCHEMA_VERSION,
        "bundle_hash": bundle_hash,
        "corpus_manifest_hash": report.corpus_manifest_hash,
        "run_id": run_id,
        "artifacts": {
            name: {"hash": artifact_hashes[name], "size_bytes": len(encoded[name])}
            for name in sorted(encoded)
        },
        "written_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        for name, data in encoded.items():
            (temp_dir / f"{name}.json").write_bytes(data)
        (temp_dir / "bundle.manifest").write_bytes(_canonical_json(manifest))
        if directory.exists():
            raise FileExistsError(f"refusing to overwrite calibration artifact bundle: {directory}")
        os.replace(temp_dir, directory)
    except Exception:
        if temp_dir.exists():
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()
        raise

    return directory
