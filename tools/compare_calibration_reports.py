from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from tiamat import load_calibration_bundle


def _bundle_dir(path: str | Path) -> Path:
    bundle_dir = Path(path)
    if bundle_dir.name == "" or bundle_dir.parent.name == "" or bundle_dir.parent.parent.name != "calibration_reports":
        raise ValueError("expected a canonical calibration bundle directory: .../calibration_reports/<corpus_hash>/<run_id>")
    return bundle_dir


def _load(path: str | Path) -> dict[str, Any]:
    bundle_dir = _bundle_dir(path)
    return load_calibration_bundle(bundle_dir.parents[2], bundle_dir.parent.name, bundle_dir.name)


def _metric_delta(base: Mapping[str, Any], head: Mapping[str, Any], keys: tuple[str, ...] = ("nll", "brier", "ece")) -> dict[str, float]:
    delta: dict[str, float] = {}
    for key in keys:
        if key in base and key in head:
            delta[key] = float(head[key]) - float(base[key])
    return delta


def _compare_named_entries(base_entries: list[dict[str, Any]], head_entries: list[dict[str, Any]], name_field: str) -> dict[str, Any]:
    base_by_name = {entry[name_field]: entry for entry in base_entries}
    head_by_name = {entry[name_field]: entry for entry in head_entries}
    shared = sorted(set(base_by_name) & set(head_by_name))
    result: dict[str, Any] = {}
    for name in shared:
        result[name] = {
            "base": base_by_name[name],
            "head": head_by_name[name],
            "delta": _metric_delta(base_by_name[name], head_by_name[name]),
        }
    return result


def _compare_reliability_bins(base_bins: dict[str, Any], head_bins: dict[str, Any]) -> dict[str, Any]:
    base_pred = {entry["predictor"]: entry for entry in base_bins["predictors"]}
    head_pred = {entry["predictor"]: entry for entry in head_bins["predictors"]}
    shared = sorted(set(base_pred) & set(head_pred))
    result: dict[str, Any] = {}
    for predictor in shared:
        base_entry = base_pred[predictor]
        head_entry = head_pred[predictor]
        if bool(base_entry.get("comparable")) != bool(head_entry.get("comparable")):
            result[predictor] = {
                "comparable": False,
                "reason": "comparability changed across runs",
                "base": {"comparable": base_entry.get("comparable"), "reason": base_entry.get("reason")},
                "head": {"comparable": head_entry.get("comparable"), "reason": head_entry.get("reason")},
            }
            continue
        base_bins = base_entry.get("bins")
        head_bins = head_entry.get("bins")
        if base_bins is None or head_bins is None:
            result[predictor] = {
                "comparable": False,
                "reason": base_entry.get("reason") or head_entry.get("reason") or "incomparable predictor",
                "base": {"comparable": base_entry.get("comparable"), "reason": base_entry.get("reason")},
                "head": {"comparable": head_entry.get("comparable"), "reason": head_entry.get("reason")},
            }
            continue
        if len(base_bins) != len(head_bins):
            raise ValueError(f"reliability bin cardinality changed for {predictor}: {len(base_bins)} vs {len(head_bins)}")
        bin_deltas = []
        for base_bin, head_bin in zip(base_bins, head_bins):
            bin_deltas.append(
                {
                    "index": base_bin["index"],
                    "count_delta": int(head_bin["count"]) - int(base_bin["count"]),
                    "mean_confidence_delta": (
                        None
                        if base_bin.get("mean_confidence") is None or head_bin.get("mean_confidence") is None
                        else float(head_bin["mean_confidence"]) - float(base_bin["mean_confidence"])
                    ),
                    "empirical_accuracy_delta": (
                        None
                        if base_bin.get("empirical_accuracy") is None or head_bin.get("empirical_accuracy") is None
                        else float(head_bin["empirical_accuracy"]) - float(base_bin["empirical_accuracy"])
                    ),
                }
            )
        result[predictor] = {"comparable": True, "bin_deltas": bin_deltas}
    return result


def compare_calibration_bundles(base_path: str | Path, head_path: str | Path, *, allow_cross_corpus: bool = False) -> dict[str, Any]:
    base = _load(base_path)
    head = _load(head_path)
    base_manifest = base["manifest"]
    head_manifest = head["manifest"]
    if base_manifest.get("schema_version") != head_manifest.get("schema_version"):
        raise ValueError("calibration bundle schema_version mismatch")
    if not allow_cross_corpus and base_manifest.get("corpus_manifest_hash") != head_manifest.get("corpus_manifest_hash"):
        raise ValueError("calibration bundles originate from different corpus snapshots")
    base_report = base["calibration_report"]
    head_report = head["calibration_report"]
    base_bins = base["reliability_bins"]
    head_bins = head["reliability_bins"]
    if base_bins["_meta"]["n_bins"] != head_bins["_meta"]["n_bins"]:
        raise ValueError("reliability bin count mismatch")
    if base_bins["_meta"].get("bin_edges") != head_bins["_meta"].get("bin_edges"):
        raise ValueError("reliability bin edge mismatch")
    return {
        "base": {
            "corpus_manifest_hash": base_manifest["corpus_manifest_hash"],
            "run_id": base_manifest["run_id"],
            "bundle_hash": base_manifest["bundle_hash"],
            "calibration_hash": base_report["calibration_hash"],
        },
        "head": {
            "corpus_manifest_hash": head_manifest["corpus_manifest_hash"],
            "run_id": head_manifest["run_id"],
            "bundle_hash": head_manifest["bundle_hash"],
            "calibration_hash": head_report["calibration_hash"],
        },
        "control_deltas": _compare_named_entries(base_report["controls"], head_report["controls"], "label"),
        "candidate_deltas": _compare_named_entries(base_report["candidates"], head_report["candidates"], "model_id"),
        "reliability_bin_deltas": _compare_reliability_bins(base_bins, head_bins),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two sealed calibration bundles")
    parser.add_argument("base_bundle", help="Path to the base bundle directory")
    parser.add_argument("head_bundle", help="Path to the head bundle directory")
    parser.add_argument("--allow-cross-corpus", action="store_true", help="Allow comparison across different corpus hashes")
    args = parser.parse_args(argv)
    comparison = compare_calibration_bundles(args.base_bundle, args.head_bundle, allow_cross_corpus=args.allow_cross_corpus)
    print(json.dumps(comparison, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
