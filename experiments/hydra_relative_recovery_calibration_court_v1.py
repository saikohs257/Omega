"""HYDRA relative-recovery calibration court V1.

Calibrates the pre-registered winning relative-recovery representation
(recovery_minus_burden) using the exact feature-construction path from the
successful relative-recovery court. Calibration is fit only on strictly
walk-forward discovery OOF predictions; 2024 remains a frozen holdout.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

from hydra_relative_recovery_court_v1 import history

INPUT = Path("data/canonical/layer1_structured_hazard_arm_timeseries.csv")
OUT = Path("artifacts/hydra_relative_recovery_calibration_v1.json")
TARGET = "Crash72"


def fit_score(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    col = "rr_recovery_minus_burden"
    tr = train.dropna(subset=[col, TARGET])
    if tr[TARGET].nunique() < 2:
        return np.full(len(test), np.nan)
    scaler = StandardScaler()
    model = LogisticRegression(max_iter=2000, class_weight="balanced")
    Xtr = scaler.fit_transform(tr[[col]].astype(float))
    model.fit(Xtr, tr[TARGET].astype(int))
    Xt = scaler.transform(test[[col]].fillna(tr[[col]].median()).astype(float))
    return model.predict_proba(Xt)[:, 1]


def safe_auc(y, p):
    return float(roc_auc_score(y, p)) if len(np.unique(y)) > 1 else None


def metrics(y, p):
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-8, 1 - 1e-8)
    return {
        "n": int(len(y)),
        "events": int(y.sum()),
        "prevalence": float(y.mean()) if len(y) else None,
        "roc_auc": safe_auc(y, p),
        "pr_auc": float(average_precision_score(y, p)) if y.sum() > 0 else None,
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p, labels=[0, 1])),
        "mean_prediction": float(np.mean(p)),
    }


def calibration_stats(y, p):
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-8, 1 - 1e-8)
    X = np.column_stack([np.ones(len(p)), np.log(p / (1 - p))])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    return {"calibration_intercept": float(beta[0]), "calibration_slope": float(beta[1])}


def prevalence_baseline(y):
    return np.full(len(y), float(np.mean(y)))


def main():
    raw = pd.read_csv(INPUT)
    assert len(raw) == 43848
    df = history(raw)
    df["year"] = pd.to_datetime(df["open_time"], utc=True).dt.year
    starts = int(((df.entry_path == "3_to_4") & (df.episode_age_h == 1)).sum())
    assert starts == 169

    discovery = df[df.year <= 2023].copy()
    holdout = df[df.year == 2024].copy()
    if holdout.empty:
        raise RuntimeError("2024 frozen holdout is missing")

    # Strict temporal OOF predictions: each calibration fold sees only earlier years.
    oof_parts: List[pd.DataFrame] = []
    for year in [2021, 2022, 2023]:
        tr = discovery[discovery.year < year]
        va = discovery[discovery.year == year]
        p = fit_score(tr, va)
        out = va[[TARGET, "year"]].copy()
        out["raw"] = p
        oof_parts.append(out.dropna(subset=["raw"]))
    oof = pd.concat(oof_parts, ignore_index=True)
    if oof[TARGET].nunique() < 2:
        raise RuntimeError("Discovery OOF has insufficient class variation for calibration")

    raw_oof = np.clip(oof["raw"].to_numpy(), 1e-8, 1 - 1e-8)
    X = np.log(raw_oof / (1 - raw_oof)).reshape(-1, 1)
    y = oof[TARGET].astype(int).to_numpy()
    platt = LogisticRegression(max_iter=2000)
    platt.fit(X, y)
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(raw_oof, y)

    raw_2024 = fit_score(discovery, holdout)
    mask = ~np.isnan(raw_2024)
    y24 = holdout.loc[mask, TARGET].astype(int).to_numpy()
    raw24 = np.clip(raw_2024[mask], 1e-8, 1 - 1e-8)
    logit24 = np.log(raw24 / (1 - raw24))
    platt24 = platt.predict_proba(logit24.reshape(-1, 1))[:, 1]
    iso24 = iso.predict(raw24)
    base24 = prevalence_baseline(y24)

    result = {
        "experiment": "hydra_relative_recovery_calibration_court_v1",
        "candidate": "rr_recovery_minus_burden",
        "canonical_input": str(INPUT),
        "selection_rule": "candidate frozen from prior relative-recovery court; calibration methods fit only on strictly temporal 2021-2023 OOF discovery predictions",
        "holdout_year": 2024,
        "models": {
            "raw": {**metrics(y24, raw24), **calibration_stats(y24, raw24)},
            "platt": {**metrics(y24, platt24), **calibration_stats(y24, platt24)},
            "isotonic": {**metrics(y24, iso24), **calibration_stats(y24, iso24)},
            "prevalence_baseline": metrics(y24, base24),
        },
        "discovery_oof": {"rows": int(len(oof)), "events": int(y.sum()), "years": sorted(oof.year.unique().tolist())},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
