"""Measure persistence of low-RR/high-Hazard state before 2024 Crash72 Orphans."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from hydra_relative_recovery_court_v1 import history


def main(csv: Path, out: Path):
    d = history(pd.read_csv(csv))
    d["date"] = pd.to_datetime(d["open_time"], utc=True)
    d = d.sort_values("date").reset_index(drop=True)
    y = pd.to_numeric(d["Crash72"], errors="coerce").fillna(0).astype(int)
    path = d["entry_path"].astype("string").fillna("<missing>").str.strip()
    path = path.replace({"": "<missing>", "nan": "<missing>", "None": "<missing>", "none": "<missing>"})
    base = path.eq("3_to_4") & pd.to_numeric(d["episode_age_h"], errors="coerce").eq(1)
    ex = y.eq(1) & ~base
    trans = ex & path.ne("<missing>")
    orphan = ex & path.eq("<missing>")
    core = y.eq(1) & base
    assert (int(core.sum()), int(trans.sum()), int(orphan.sum()), int(y.sum())) == (12, 350, 606, 968)

    train = d[d.date.dt.year < 2024]
    test = d[d.date.dt.year == 2024].copy()
    rr_cut = float(pd.to_numeric(train["rr_recovery_minus_burden"], errors="coerce").quantile(.20))
    hz_cut = float(pd.to_numeric(train["hazard_score"], errors="coerce").quantile(.80))
    rr = pd.to_numeric(test["rr_recovery_minus_burden"], errors="coerce")
    hz = pd.to_numeric(test["hazard_score"], errors="coerce")
    state = (rr < rr_cut) & (hz > hz_cut)
    orphan_test = orphan.loc[test.index].to_numpy(bool)

    vals = state.to_numpy(bool)
    # Consecutive state-run length ending at each row, computed once.
    run_len = np.zeros(len(vals), dtype=int)
    for i, active in enumerate(vals):
        run_len[i] = run_len[i - 1] + 1 if active and i else (1 if active else 0)

    orphan_durations = run_len[orphan_test]
    runs = []
    i = 0
    while i < len(vals):
        if not vals[i]:
            i += 1
            continue
        j = i
        while j < len(vals) and vals[j]:
            j += 1
        runs.append(j - i)
        i = j

    thresholds = [1, 2, 4, 6, 12, 24, 48, 72]
    capture = []
    for th in thresholds:
        captured = (orphan_durations >= th)
        capture.append({
            "min_persistence_h": th,
            "orphan_captured": int(captured.sum()),
            "orphan_total": int(len(orphan_durations)),
            "capture_rate": float(captured.mean()) if len(captured) else None,
        })

    result = {
        "experiment": "hydra_crash72_orphan_persistence_court_v2",
        "holdout_year": 2024,
        "train_years": "2020-2023",
        "cuts": {"rr_p20_train": rr_cut, "hazard_p80_train": hz_cut},
        "class_counts": {"core": 12, "transition": 350, "orphan": 606, "crash72": 968},
        "orphan_persistence": {
            "n": int(len(orphan_durations)),
            "durations_h": orphan_durations.tolist(),
            "median_h": float(np.median(orphan_durations)) if len(orphan_durations) else None,
            "mean_h": float(np.mean(orphan_durations)) if len(orphan_durations) else None,
            "max_h": int(orphan_durations.max()) if len(orphan_durations) else 0,
        },
        "state_run_lengths_summary": {
            "n_runs": len(runs),
            "median_h": float(np.median(runs)) if runs else None,
            "p90_h": float(np.quantile(runs, .90)) if runs else None,
            "max_h": int(max(runs)) if runs else 0,
        },
        "capture_by_threshold": capture,
    }
    out.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
