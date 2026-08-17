from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import tiamat_path_memory_court_v3_strict as base


def robust_all_candidate_distances(te, med, iqr):
    q, z, pos, neg, _ = base.prepare(te, med, iqr)
    times = q["open_time"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy(dtype="datetime64[ns]")
    candidates = []
    for i in pos:
        if not len(neg):
            continue
        delta = z[neg] - z[i]
        dist = np.sqrt(np.sum(delta * delta, axis=1)) / np.sqrt(len(base.OBS))
        gap_h = np.abs((times[neg] - times[i]) / np.timedelta64(1, "h"))
        valid = gap_h >= base.MIN_SEPARATION_H
        for j_local in np.flatnonzero(valid):
            candidates.append((int(i), int(neg[j_local]), float(dist[j_local])))
    candidates.sort(key=lambda x: x[2])
    return candidates, len(pos), len(neg)


def run(csv: Path) -> dict:
    base.all_candidate_distances = robust_all_candidate_distances
    payload = base.run(csv)
    payload["experiment"] = "TIAMAT_PATH_MEMORY_COURT_V4_STRICT_TIMEFIX"
    payload["matching"]["timestamp_method"] = "timezone-normalized datetime64[ns] timedelta hours; no integer-unit assumption"
    return payload


def main(csv: Path, out: Path) -> None:
    import json
    payload = run(csv)
    out.write_text(json.dumps(payload, indent=2, allow_nan=True))
    print(out.read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
