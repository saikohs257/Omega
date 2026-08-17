from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from tiamat_path_memory_court_v1 import OBS, HORIZONS, DISCOVERY_YEARS, HOLDOUT_YEAR, causal_history, future_target, fit_auc, conditioned_history_auc

HISTORY = [
    "LiveDeficit_lag1", "LiveDeficit_lag6", "LiveDeficit_lag24", "LiveDeficit_lag72",
    "ld_delta_1", "ld_delta_6", "ld_delta_24", "ld_area24", "ld_area72",
    "shock_excess24", "shock_excess72", "ld_above85_hours24", "recovery_area24",
    "hazard_peak24", "hazard_peak72",
]


def train_model(train: pd.DataFrame, features: list[str]):
    q = train.dropna(subset=["target"])
    model = make_pipeline(
        SimpleImputer(strategy="median"), StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear", C=0.5),
    )
    model.fit(q[features].astype(float), q.target.astype(int))
    return model


def permuted_holdout_auc(model, te: pd.DataFrame, features: list[str], candidate: str, n: int = 200, seed: int = 17) -> dict:
    q = te.dropna(subset=["target"]).copy()
    if q.target.nunique() < 2:
        return {"observed": float("nan"), "null_mean": float("nan"), "null_p95": float("nan"), "n": 0}
    base_pred = model.predict_proba(q[features].astype(float))[:, 1]
    observed = float(roc_auc_score(q.target, base_pred))
    rng = np.random.default_rng(seed)
    strata = q[OBS].copy()
    for c in OBS:
        strata[c] = pd.qcut(strata[c], 10, duplicates="drop", labels=False)
    strata_key = strata.astype(str).agg("|".join, axis=1)
    null = []
    for _ in range(n):
        qp = q.copy()
        vals = qp[candidate].to_numpy(copy=True)
        for _, idx in qp.groupby(strata_key, sort=False).groups.items():
            idx = np.asarray(list(idx), dtype=int)
            rng.shuffle(vals[idx])
        qp[candidate] = vals
        pred = model.predict_proba(qp[features].astype(float))[:, 1]
        null.append(roc_auc_score(qp.target, pred))
    return {"observed": observed, "null_mean": float(np.mean(null)), "null_p95": float(np.quantile(null, 0.95)), "n": n}


def main(csv: Path, out: Path) -> None:
    d = pd.read_csv(csv)
    required = OBS + ["open_time", "entry_path"]
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    d = causal_history(d)
    d["year"] = d.open_time.dt.year
    x = d.copy()
    x["target"] = future_target(x, 6, "3_to_4")
    tr = x[x.year.isin(DISCOVERY_YEARS)].copy()
    te = x[x.year == HOLDOUT_YEAR].copy()

    base_auc, base_pr, _ = fit_auc(tr, te, OBS)
    rows = []
    for c in HISTORY:
        cols = OBS + [c]
        auc, pr, _ = fit_auc(tr, te, cols)
        delta = auc - base_auc
        cond = conditioned_history_auc(te, c)
        model = train_model(tr, cols)
        null = permuted_holdout_auc(model, te, cols, c, n=200)
        rows.append({
            "history": c,
            "holdout_auc": auc,
            "holdout_pr_auc": pr,
            "delta_auc_vs_present": delta,
            "conditioned_auc": cond,
            "permutation": null,
        })
    rows.sort(key=lambda r: (-r["delta_auc_vs_present"] if np.isfinite(r["delta_auc_vs_present"]) else 999.0))
    payload = {
        "experiment": "TIAMAT_PATH_MEMORY_COURT_V2",
        "target": "future_3_to_4_within_6h",
        "present": OBS,
        "history_candidates": HISTORY,
        "forbidden_predictors": ["entry_path", "episode_type", "duration_bucket", "Crash72"],
        "holdout_year": HOLDOUT_YEAR,
        "base_holdout_auc": base_auc,
        "base_holdout_pr_auc": base_pr,
        "candidate_rows": rows,
        "interpretation_rule": "A candidate is interesting only if incremental holdout separation survives the matched-state view and exceeds its within-stratum permutation null; this remains exploratory, not canonical.",
    }
    out.write_text(json.dumps(payload, indent=2, allow_nan=True))
    print(out.read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
