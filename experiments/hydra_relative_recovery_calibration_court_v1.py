"""HYDRA relative-recovery calibration court V1.

Pre-registered comparison of raw vs discovery-trained Platt/isotonic calibration
for the winning relative-recovery representation (recovery_minus_burden), with
frozen 2024 evaluation and full AUC/Brier/LogLoss/calibration logging.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

INPUT = Path("data/canonical/layer1_structured_hazard_arm_timeseries.csv")
OUT = Path("artifacts/hydra_relative_recovery_calibration_v1.json")
TARGET = "h3_start"
YEARS = [2020, 2021, 2022, 2023, 2024]


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    # Derive the same recovery/burden primitives used by the relative-recovery court.
    x["RecoveryWeakness_v1"] = x["LiveDeficit"].rolling(24, min_periods=6).mean()
    x["burden"] = x["LiveDeficit"].rolling(24, min_periods=6).mean()
    x["recovery_minus_burden"] = x["LiveDeficit"] - x["burden"]
    x = x.replace([np.inf, -np.inf], np.nan)
    return x


def fit_score(train: pd.DataFrame, test: pd.DataFrame) -> Tuple[np.ndarray, float]:
    cols = ["recovery_minus_burden"]
    tr = train.dropna(subset=cols + [TARGET])
    te = test.dropna(subset=cols + [TARGET])
    if tr[TARGET].nunique() < 2 or te.empty:
        return np.full(len(test), np.nan), np.nan
    model = LogisticRegression(max_iter=2000, class_weight="balanced")
    scaler = StandardScaler()
    Xtr = scaler.fit_transform(tr[cols])
    model.fit(Xtr, tr[TARGET].astype(int))
    Xt = scaler.transform(test[cols].fillna(tr[cols].median()))
    return model.predict_proba(Xt)[:, 1], np.nan


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
    X = np.column_stack([np.ones(len(p)), np.log(p / (1-p))])
    try:
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        intercept, slope = map(float, beta)
    except Exception:
        intercept, slope = None, None
    return {"calibration_intercept": intercept, "calibration_slope": slope}


def prevalence_baseline(y):
    q = float(np.mean(y))
    return np.full(len(y), q)


def main():
    df = pd.read_csv(INPUT)
    df["year"] = pd.to_datetime(df["timestamp"]).dt.year
    df = make_features(df)

    discovery = df[df.year <= 2023].copy()
    holdout = df[df.year == 2024].copy()
    if holdout.empty:
        raise RuntimeError("2024 frozen holdout is missing")

    # Generate strictly temporal discovery OOF scores, used ONLY to fit calibrators.
    oof_parts: List[pd.DataFrame] = []
    for year in [2021, 2022, 2023]:
        tr = discovery[discovery.year < year]
        va = discovery[discovery.year == year]
        p, _ = fit_score(tr, va)
        out = va[[TARGET, "year"]].copy()
        out["raw"] = p
        oof_parts.append(out.dropna(subset=["raw"]))
    oof = pd.concat(oof_parts, ignore_index=True)
    if oof[TARGET].nunique() < 2:
        raise RuntimeError("Discovery OOF has insufficient class variation for calibration")

    X = np.log(np.clip(oof["raw"].to_numpy(), 1e-8, 1-1e-8) / np.clip(1-oof["raw"].to_numpy(), 1e-8, 1))
    y = oof[TARGET].astype(int).to_numpy()
    platt = LogisticRegression(max_iter=2000)
    platt.fit(X.reshape(-1, 1), y)
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(oof["raw"].to_numpy(), y)

    raw_2024, _ = fit_score(discovery, holdout)
    mask = ~np.isnan(raw_2024)
    y24 = holdout.loc[mask, TARGET].astype(int).to_numpy()
    raw24 = raw_2024[mask]
    logit24 = np.log(np.clip(raw24, 1e-8, 1-1e-8) / np.clip(1-raw24, 1e-8, 1))
    platt24 = platt.predict_proba(logit24.reshape(-1, 1))[:, 1]
    iso24 = iso.predict(raw24)

    base24 = prevalence_baseline(y24)
    result = {
        "experiment": "hydra_relative_recovery_calibration_court_v1",
        "candidate": "recovery_minus_burden",
        "canonical_input": str(INPUT),
        "selection_rule": "candidate frozen from prior relative-recovery court; calibration methods are fit only on strictly temporal 2021-2023 OOF discovery predictions",
        "holdout_year": 2024,
        "models": {
            "raw": {**metrics(y24, raw24), **calibration_stats(y24, raw24)},
            "platt": {**metrics(y24, platt24), **calibration_stats(y24, platt24)},
            "isotonic": {**metrics(y24, iso24), **calibration_stats(y24, iso24)},
            "prevalence_baseline": metrics(y24, base24),
        },
        "discovery_oof": {
            "rows": int(len(oof)),
            "events": int(y.sum()),
            "years": sorted(oof.year.unique().tolist()),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
