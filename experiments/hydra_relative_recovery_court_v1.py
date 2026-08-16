"""HYDRA Relative-Recovery Court V1.

Hypothesis: useful recovery information is relative to the excitation/load that
created the structural deficit, rather than an isolated recovery derivative.
2024 is a frozen holdout; candidate selection uses strictly prior discovery
years only. Every candidate logs AUC, PR AUC, Brier, log loss, prevalence,
counts, and walk-forward metrics. AUC is explicitly undefined when a fold has
one class.
"""
from __future__ import annotations
import argparse, json, platform
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

TARGET = "Crash72"
DISCOVERY = (2020, 2021, 2022, 2023)
HOLDOUT = 2024
EPS = 1e-6


def history(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    d = d.sort_values("open_time").reset_index(drop=True)
    ss = pd.to_numeric(d["SimpleShock"], errors="coerce")
    ld = pd.to_numeric(d["LiveDeficit"], errors="coerce")
    rw = pd.to_numeric(d["RecoveryWeakness_v1"], errors="coerce")
    hs = pd.to_numeric(d["hazard_score"], errors="coerce")

    # All transforms use information available strictly before the prediction row.
    d["shock_l1"] = ss.shift(1)
    d["burden_l1"] = ld.shift(1)
    d["recovery_l1"] = rw.shift(1)
    d["hazard_l1"] = hs.shift(1)
    d["shock_m24"] = ss.shift(1).rolling(24, min_periods=6).mean()
    d["burden_m24"] = ld.shift(1).rolling(24, min_periods=6).mean()
    d["recovery_m24"] = rw.shift(1).rolling(24, min_periods=6).mean()
    d["shock_max24"] = ss.shift(1).rolling(24, min_periods=6).max()
    d["burden_max24"] = ld.shift(1).rolling(24, min_periods=6).max()
    d["recovery_max24"] = rw.shift(1).rolling(24, min_periods=6).max()

    # Compatibility features are derived here; they are NOT added to the canonical spine.
    d["RecoveryWeakness_v1__lag6"] = rw.shift(6)
    d["LiveDeficit__lag6"] = ld.shift(6)

    # Relative-recovery candidate families.
    d["rr_diff_recovery_shock"] = d.recovery_l1 - d.shock_m24
    d["rr_ratio_recovery_shock"] = d.recovery_l1 / (d.shock_m24.abs() + EPS)
    d["rr_diff_burden_shock"] = d.burden_l1 - d.shock_m24
    d["rr_ratio_burden_shock"] = d.burden_l1 / (d.shock_m24.abs() + EPS)
    d["rr_recovery_minus_burden"] = d.recovery_l1 - d.burden_l1
    d["rr_recovery_over_burden"] = d.recovery_l1 / (d.burden_l1.abs() + EPS)
    d["rr_recovery_minus_shockmax"] = d.recovery_l1 - d.shock_max24
    d["rr_burden_minus_shockmax"] = d.burden_l1 - d.shock_max24
    d["rr_recovery_vs_recent"] = d.recovery_l1 - d.recovery_m24
    d["rr_burden_vs_recent"] = d.burden_l1 - d.burden_m24
    d["rr_shock_vs_recent"] = d.shock_l1 - d.shock_m24
    d["rr_load_weighted_recovery"] = d.recovery_l1 / (1.0 + d.burden_m24.abs())
    d["rr_shock_weighted_burden"] = d.burden_l1 / (1.0 + d.shock_m24.abs())
    d["rr_hazard_weighted_recovery"] = d.recovery_l1 / (1.0 + d.hazard_l1.rolling(24, min_periods=6).mean().abs())
    return d


def make_history(d: pd.DataFrame) -> pd.DataFrame:
    return history(d)


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, col: str) -> np.ndarray:
    model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=1600, class_weight="balanced", C=.5, solver="liblinear"))
    model.fit(train[[col]].astype(float), train[TARGET].astype(int))
    return model.predict_proba(test[[col]].astype(float))[:, 1]


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, int); p = np.clip(np.asarray(p, float), 1e-6, 1-1e-6)
    two = np.unique(y).size == 2
    return {
        "n": int(len(y)), "events": int(y.sum()), "prevalence": float(y.mean()),
        "auc": float(roc_auc_score(y,p)) if two else None,
        "pr_auc": float(average_precision_score(y,p)) if two else None,
        "brier": float(brier_score_loss(y,p)),
        "logloss": float(log_loss(y,p,labels=[0,1])),
        "mean_prediction": float(p.mean()),
    }


def candidate_list() -> list[str]:
    return [
        "rr_diff_recovery_shock", "rr_ratio_recovery_shock",
        "rr_diff_burden_shock", "rr_ratio_burden_shock",
        "rr_recovery_minus_burden", "rr_recovery_over_burden",
        "rr_recovery_minus_shockmax", "rr_burden_minus_shockmax",
        "rr_recovery_vs_recent", "rr_burden_vs_recent",
        "rr_shock_vs_recent", "rr_load_weighted_recovery",
        "rr_shock_weighted_burden", "rr_hazard_weighted_recovery",
        "RecoveryWeakness_v1__lag6", "LiveDeficit__lag6",
    ]


def discovery_report(d: pd.DataFrame, col: str) -> dict:
    rows = {}
    for year in DISCOVERY:
        # Strictly walk-forward: only years before the evaluation year train the model.
        tr = d[d.open_time.dt.year < year]
        te = d[d.open_time.dt.year == year]
        if len(tr) < 200 or te.empty:
            continue
        rows[str(year)] = metrics(te[TARGET].to_numpy(), fit_predict(tr, te, col))
    valid_auc = [v["auc"] for v in rows.values() if v["auc"] is not None]
    return {
        "folds": rows,
        "mean_auc": float(np.mean(valid_auc)) if valid_auc else None,
        "worst_auc": float(np.min(valid_auc)) if valid_auc else None,
        "mean_brier": float(np.mean([v["brier"] for v in rows.values()])) if rows else None,
        "mean_logloss": float(np.mean([v["logloss"] for v in rows.values()])) if rows else None,
    }


def main(csv: Path, out: Path) -> None:
    raw = pd.read_csv(csv)
    d = history(raw)
    assert len(raw) == 43848
    starts = int(((d.entry_path == "3_to_4") & (d.episode_age_h == 1)).sum())
    assert starts == 169

    candidates = candidate_list()
    discovery = {c: discovery_report(d, c) for c in candidates}
    ranked = sorted(
        candidates,
        key=lambda c: (
            discovery[c]["mean_auc"] if discovery[c]["mean_auc"] is not None else -1,
            -(discovery[c]["mean_brier"] if discovery[c]["mean_brier"] is not None else 999),
        ),
        reverse=True,
    )
    best = ranked[0]
    tr = d[d.open_time.dt.year.isin(DISCOVERY)]
    te = d[d.open_time.dt.year == HOLDOUT]
    holdout = {c: metrics(te[TARGET].to_numpy(), fit_predict(tr, te, c)) for c in candidates}
    payload = {
        "experiment": "hydra_relative_recovery_court_v1",
        "hypothesis": "recovery relative to excitation/load is more informative than isolated recovery derivatives",
        "canonical_rows": len(raw), "canonical_h3_starts": starts,
        "discovery_years": list(DISCOVERY), "holdout_year": HOLDOUT,
        "selection_rule": "highest mean strictly-walk-forward discovery AUC, tie-break lower mean discovery Brier; 2024 untouched",
        "selected_candidate": best,
        "discovery": discovery,
        "holdout_2024": holdout,
        "python": platform.python_version(),
    }
    out.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv", type=Path); ap.add_argument("--out", type=Path, required=True); a = ap.parse_args(); main(a.csv, a.out)
