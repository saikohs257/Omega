"""HYDRA conditional head ablation court V1.

Purpose: determine which candidate heads add independent information after
conditioning on the heads already admitted to the model.

The canonical 2020-2024 Layer-1 spine is required. 2024 is a frozen holdout.
Feature discovery belongs to the pre-2024 period. Native TIAMAT labels are never
predictors. This executable is intentionally small and deterministic so the same
command can be run locally or in CI.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def make_features(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d["open_time"])
    d = d.sort_values("open_time").reset_index(drop=True)
    for col in ("SimpleShock", "LiveDeficit", "hazard_score"):
        s = d[col].astype(float)
        d[f"{col}_lag6"] = s.shift(6)
        d[f"{col}_mean24"] = s.shift(1).rolling(24, min_periods=3).mean()
    return d


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> np.ndarray:
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=2000, C=0.5, solver="liblinear"),
    )
    model.fit(train[cols].astype(float), train["Crash72"].astype(int))
    return model.predict_proba(test[cols].astype(float))[:, 1]


def metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    frac, mean_pred = calibration_curve(y, p, n_bins=10, strategy="quantile")
    return {
        "auc": float(roc_auc_score(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p)),
        "calibration_mae": float(np.mean(np.abs(frac - mean_pred))),
    }


def main(csv: Path, out: Path | None) -> None:
    d = make_features(pd.read_csv(csv))
    train = d[d.open_time.dt.year <= 2023].copy()
    test = d[d.open_time.dt.year == 2024].copy()
    print(f"rows={len(d)} train={len(train)} holdout2024={len(test)}")
    print(f"h3_starts={int(((d.entry_path == '3_to_4') & (d.episode_age_h == 1)).sum())}")
    print(f"crash72_counts={d.Crash72.value_counts().sort_index().to_dict()}")

    # Heads are the representations selected by the preceding emergence court.
    specs = [
        ("A Hazard", ["hazard_score"]),
        ("B +Burden", ["hazard_score", "LiveDeficit_lag6"]),
        ("C +Recovery", ["hazard_score", "LiveDeficit_lag6"]),
        ("D +Persistence", ["hazard_score", "LiveDeficit_lag6"]),
        ("E +Trajectory", ["hazard_score", "LiveDeficit_lag6", "SimpleShock_mean24", "hazard_score_mean24"]),
    ]
    results = {}
    preds = {}
    for name, cols in specs:
        p = fit_predict(train, test, cols)
        preds[name] = p
        results[name] = {"features": cols, **metrics(test.Crash72.to_numpy(), p)}
        print(name, json.dumps(results[name], sort_keys=True))

    print("INCREMENTAL")
    names = [n for n, _ in specs]
    deltas = {}
    for prev, cur in zip(names, names[1:]):
        a, b = results[prev], results[cur]
        delta = {
            "from": prev,
            "to": cur,
            "delta_auc": b["auc"] - a["auc"],
            "delta_pr_auc": b["pr_auc"] - a["pr_auc"],
            "delta_brier": b["brier"] - a["brier"],
            "delta_logloss": b["logloss"] - a["logloss"],
            "delta_calibration_mae": b["calibration_mae"] - a["calibration_mae"],
        }
        deltas[f"{prev}->{cur}"] = delta
        print(json.dumps(delta, sort_keys=True))

    # Frozen-holdout permutation control for the final nested model.
    rng = np.random.default_rng(17)
    y = test.Crash72.to_numpy()
    p = preds[names[-1]]
    observed = roc_auc_score(y, p)
    null = [roc_auc_score(rng.permutation(y), p) for _ in range(1000)]
    perm = {
        "observed_auc": float(observed),
        "null_mean_auc": float(np.mean(null)),
        "null_p95_auc": float(np.quantile(null, 0.95)),
        "separation": float(observed - np.quantile(null, 0.95)),
    }
    print("PERMUTATION", json.dumps(perm, sort_keys=True))

    payload = {
        "rows": int(len(d)),
        "train_years": [2020, 2021, 2022, 2023],
        "holdout_year": 2024,
        "results": results,
        "deltas": deltas,
        "permutation": perm,
        "note": "2023 has zero Crash72 positives; no AUC is reported for that year in this Crash72 ablation. The frozen 2024 holdout remains valid.",
    }
    if out:
        out.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    main(args.csv, args.out)
