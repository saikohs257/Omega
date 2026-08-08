from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"report must be a JSON object: {path}")
    return value


def compare(left: dict[str, Any], right: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"experiment: {left.get('corpus_manifest_hash')} -> {right.get('corpus_manifest_hash')}")
    lines.append(f"decision: {left.get('decision')} -> {right.get('decision')}")
    left_candidates = {c["model_id"]: c for c in left.get("candidates", [])}
    right_candidates = {c["model_id"]: c for c in right.get("candidates", [])}
    for model_id in sorted(set(left_candidates) | set(right_candidates)):
        a = left_candidates.get(model_id)
        b = right_candidates.get(model_id)
        if a is None or b is None:
            lines.append(f"{model_id}: added/removed")
            continue
        for metric in ("nll", "brier", "ece"):
            av = float(a["metrics"][metric])
            bv = float(b["metrics"][metric])
            lines.append(f"{metric:6} {model_id}: {bv - av:+.6f} ({av:.6f} -> {bv:.6f})")
    left_spread = left.get("spread_check", {}).get("observed", {})
    right_spread = right.get("spread_check", {}).get("observed", {})
    for metric in ("nll", "brier", "ece"):
        if metric in left_spread and metric in right_spread:
            lines.append(f"spread  {metric}: {float(right_spread[metric]) - float(left_spread[metric]):+.6f}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two TIAMAT calibration reports")
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    args = parser.parse_args()
    print(compare(load(args.left), load(args.right)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
