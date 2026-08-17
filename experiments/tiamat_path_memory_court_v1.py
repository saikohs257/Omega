from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

OBS = ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_raw"]
PATHS = {"0_to_4", "2_to_4", "3_to_4"}
DISCOVERY_YEARS = (2021, 2022, 2023)
HOLDOUT_YEAR = 2024
HORIZONS = (6, 24)


def numeric(d: pd.DataFrame, c: str) -> pd.Series:
    return pd.to_numeric(d[c], errors="coerce")


def causal_history(d: pd.DataFrame) -> pd.DataFrame:
    d = d.sort_values("open_time").reset_index(drop=True).copy()
    for c in OBS:
        d[c] = numeric(d, c)

    # All history terms use t-1 and earlier only. No hidden labels are used.
    for lag in (1, 6, 24, 72):
        for c in ("LiveDeficit", "SimpleShock", "RecoveryWeakness_v1", "hazard_raw"):
            d[f"{c}_lag{lag}"] = d[c].shift(lag)

    d["ld_delta_1"] = d["LiveDeficit"].shift(1) - d["LiveDeficit"].shift(2)
    d["ld_delta_6"] = d["LiveDeficit"].shift(1) - d["LiveDeficit"].shift(7)
    d["ld_delta_24"] = d["LiveDeficit"].shift(1) - d["LiveDeficit"].shift(25)

    # Path-free accumulation: burden area and shock excess over fixed observable thresholds.
    ld_prev = d["LiveDeficit"].shift(1)
    ss_prev = d["SimpleShock"].shift(1)
    d["ld_area24"] = ld_prev.rolling(24, min_periods=12).mean()
    d["ld_area72"] = ld_prev.rolling(72, min_periods=36).mean()
    d["shock_excess24"] = (ss_prev - 0.50).clip(lower=0).rolling(24, min_periods=12).sum()
    d["shock_excess72"] = (ss_prev - 0.50).clip(lower=0).rolling(72, min_periods=36).sum()
    d["ld_above85_hours24"] = (ld_prev > 0.85).rolling(24, min_periods=12).sum()
    d["recovery_area24"] = d["RecoveryWeakness_v1"].shift(1).rolling(24, min_periods=12).mean()
    d["hazard_peak24"] = d["hazard_raw"].shift(1).rolling(24, min_periods=12).max()
    d["hazard_peak72"] = d["hazard_raw"].shift(1).rolling(72, min_periods=36).max()
    return d


def future_target(d: pd.DataFrame, horizon_h: int, path: str = "3_to_4") -> pd.Series:
    # Target-only use of entry_path. It is forbidden from features.
    x = d[["open_time", "entry_path"]].copy().sort_values("open_time")
    t = x["open_time"].to_numpy()
    is_start = x["entry_path"].isin(PATHS).to_numpy()
    labels = np.zeros(len(x), dtype=np.int8)
    for i in range(len(x)):
        upper = t[i] + np.timedelta64(horizon_h, "h")
        j = np.searchsorted(t, upper, side="right")
        if j <= i + 1:
            continue
        labels[i] = int(np.any(x["entry_path"].iloc[i + 1:j].eq(path).to_numpy()))
    return pd.Series(labels, index=d.index)


def fit_auc(train: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> tuple[float, float, int]:
    qtr = train.dropna(subset=["target"])
    qte = test.dropna(subset=["target"])
    if qtr.target.nunique() < 2 or qte.target.nunique() < 2:
        return float("nan"), float("nan"), int(qte.target.nunique())
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear", C=0.5),
    )
    model.fit(qtr[features].astype(float), qtr.target.astype(int))
    p = model.predict_proba(qte[features].astype(float))[:, 1]
    return float(roc_auc_score(qte.target, p)), float(average_precision_score(qte.target, p)), int(qte.target.nunique())


def conditional_bins(d: pd.DataFrame) -> pd.Series:
    # Coarse present-state strata. History must explain residual differences within these strata.
    parts = []
    for c in OBS:
        parts.append(pd.qcut(d[c], 10, duplicates="drop", labels=False))
    return pd.concat(parts, axis=1).astype("Int64").astype(str).agg("|".join, axis=1)


def conditioned_history_auc(te: pd.DataFrame, history_col: str) -> float:
    q = te.copy()
    q["stratum"] = conditional_bins(q)
    vals = []
    for _, g in q.groupby("stratum", observed=False):
        if len(g) < 12 or g.target.nunique() < 2:
            continue
        vals.append((len(g), roc_auc_score(g.target, g[history_col])))
    if not vals:
        return float("nan")
    return float(sum(n * a for n, a in vals) / sum(n for n, _ in vals))


def run(d: pd.DataFrame) -> dict:
    d = causal_history(d)
    d["year"] = d.open_time.dt.year
    d["target"] = np.nan
    results = {}

    present = OBS
    history = [
        "LiveDeficit_lag1", "LiveDeficit_lag6", "LiveDeficit_lag24", "LiveDeficit_lag72",
        "ld_delta_1", "ld_delta_6", "ld_delta_24", "ld_area24", "ld_area72",
        "shock_excess24", "shock_excess72", "ld_above85_hours24", "recovery_area24",
        "hazard_peak24", "hazard_peak72",
    ]

    for h in HORIZONS:
        x = d.copy()
        x["target"] = future_target(x, h, "3_to_4")
        folds = {}
        for y in DISCOVERY_YEARS:
            tr = x[x.year < y]
            te = x[x.year == y]
            ba, bp, bc = fit_auc(tr, te, present)
            fa, fp, fc = fit_auc(tr, te, present + history)
            folds[str(y)] = {
                "base_auc": ba, "base_pr_auc": bp, "full_auc": fa, "full_pr_auc": fp,
                "base_test_classes": bc, "full_test_classes": fc,
                "rows": int(len(te)), "positives": int(te.target.sum()),
            }
        tr = x[x.year.isin(DISCOVERY_YEARS)]
        te = x[x.year == HOLDOUT_YEAR]
        ba, bp, bc = fit_auc(tr, te, present)
        fa, fp, fc = fit_auc(tr, te, present + history)
        history_cond = {c: conditioned_history_auc(te, c) for c in history}
        results[str(h)] = {
            "target": f"future_3_to_4_within_{h}h",
            "discovery": folds,
            "holdout": {
                "base_auc": ba, "base_pr_auc": bp,
                "full_auc": fa, "full_pr_auc": fp,
                "rows": int(len(te)), "positives": int(te.target.sum()),
                "base_test_classes": bc, "full_test_classes": fc,
            },
            "conditioned_history_auc_2024": history_cond,
        }
    return results


def main(csv: Path, out: Path) -> None:
    d = pd.read_csv(csv)
    required = OBS + ["open_time", "entry_path"]
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    payload = {
        "experiment": "TIAMAT_PATH_MEMORY_COURT_V1",
        "classification": "experimental/non-authoritative",
        "feature_contract": {
            "present": OBS,
            "history": "causally constructed from t-1 and earlier observable Layer1 fields only",
            "forbidden_predictors": ["entry_path", "episode_type", "duration_bucket", "Crash72"],
        },
        "target_contract": "entry_path is used only after the fact to define future 3_to_4 targets; it never enters the feature matrix",
        "folds": {"discovery": DISCOVERY_YEARS, "holdout": HOLDOUT_YEAR},
        "results": run(d),
    }
    out.write_text(json.dumps(payload, indent=2, allow_nan=True))
    print(out.read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
