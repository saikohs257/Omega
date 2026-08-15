"""Build the leakage-clean Layer-1 causal spine from the recovered 15-column panel.

The recovered panel is useful evidence, but it mixes runtime-observable state with
hindsight labels and episode annotations. This script creates the feature spine
used by causal discovery. It deliberately keeps future outcomes/labels separate.

SAFE RUNTIME FEATURES
- open_time
- close
- SimpleShock
- LiveDeficit
- RecoveryWeakness_v1
- recovery_gate
- regime_30d
- hazard_raw
- hazard_score
- hazard_bucket

EXCLUDED FROM FEATURE SPACE
- Crash72: future outcome/target
- entry_path: episode-path label/annotation
- episode_age_h: episode-state annotation that can encode post-entry history
- duration_bucket: final duration label
- episode_type: final episode label

The exclusions are intentional. They are not deleted from the source evidence;
they are kept in a separate label/annotation sidecar when needed for evaluation.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import hashlib
import json
import pandas as pd

SAFE_COLUMNS = [
    "open_time", "close", "SimpleShock", "LiveDeficit",
    "RecoveryWeakness_v1", "recovery_gate", "regime_30d",
    "hazard_raw", "hazard_score", "hazard_bucket",
]
LABEL_COLUMNS = ["open_time", "Crash72"]
ANNOTATION_COLUMNS = [
    "open_time", "entry_path", "episode_age_h",
    "duration_bucket", "episode_type",
]
EXPECTED_ROWS = 43848
EXPECTED_H3_STARTS = 169


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonicalize(src: Path, out_dir: Path) -> dict:
    df = pd.read_csv(src)
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, got {len(df)}")
    required = set(SAFE_COLUMNS + LABEL_COLUMNS[1:] + ANNOTATION_COLUMNS[1:])
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    df["open_time"] = pd.to_datetime(df["open_time"], errors="raise")
    df = df.sort_values("open_time", kind="stable").reset_index(drop=True)

    h3_starts = ((df["entry_path"] == "3_to_4") & (df["episode_age_h"] == 1)).sum()
    if int(h3_starts) != EXPECTED_H3_STARTS:
        raise ValueError(f"expected {EXPECTED_H3_STARTS} H3 starts, got {h3_starts}")

    out_dir.mkdir(parents=True, exist_ok=True)
    causal = df[SAFE_COLUMNS].copy()
    labels = df[LABEL_COLUMNS].copy()
    annotations = df[ANNOTATION_COLUMNS].copy()

    for frame in (causal, labels, annotations):
        frame["open_time"] = frame["open_time"].dt.strftime("%Y-%m-%d %H:%M:%S")

    causal_path = out_dir / "layer1_structured_hazard_arm_causal_spine_2020_2024.csv"
    labels_path = out_dir / "layer1_structured_hazard_arm_labels_2020_2024.csv"
    annotations_path = out_dir / "layer1_structured_hazard_arm_annotations_2020_2024.csv"
    causal.to_csv(causal_path, index=False)
    labels.to_csv(labels_path, index=False)
    annotations.to_csv(annotations_path, index=False)

    return {
        "source": str(src),
        "source_sha256": sha256_bytes(src.read_bytes()),
        "rows": int(len(df)),
        "h3_start_count": int(h3_starts),
        "causal_columns": SAFE_COLUMNS,
        "future_target_columns": ["Crash72"],
        "hindsight_annotation_columns": ANNOTATION_COLUMNS[1:],
        "outputs": {
            "causal_spine": str(causal_path),
            "labels": str(labels_path),
            "annotations": str(annotations_path),
        },
        "output_sha256": {
            "causal_spine": sha256_bytes(causal_path.read_bytes()),
            "labels": sha256_bytes(labels_path.read_bytes()),
            "annotations": sha256_bytes(annotations_path.read_bytes()),
        },
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("data/canonical"))
    ap.add_argument("--manifest", type=Path, default=Path("data/canonical/manifest.json"))
    args = ap.parse_args()
    manifest = canonicalize(args.source, args.out_dir)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
