"""HYDRA Calibration Court V1.

Purpose: determine whether Hydra's strong discrimination can be converted into
trustworthy probabilities without touching feature selection or the frozen
2024 holdout. Base models are identical to the incrementality court. Calibration
parameters are learned only from temporally out-of-fold discovery predictions
(2021-2023); 2024 is never used to fit or select a calibrator.

Reports AUC, PR AUC, Brier, log loss, calibration slope/intercept, calibration
MAE, prevalence, counts, prediction distribution, Brier skill vs prevalence
baseline, and walk-forward raw-vs-calibrated metrics.
"""
from __future__ import annotations
import argparse, json, platform
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

TARGET = "Crash72"
YEARS = (2020, 2021, 2022, 2023)
HOLDOUT = 2024
CALIBRATION_YEARS = (2021, 2022, 2023)
HEAD_FEATURES = {
    "Hazard": ["hazard_score"],
    "Burden": ["LiveDeficit__lag6"],
    "Recovery": ["RecoveryWeakness_v1__lag6"],
    "Persistence": ["age__log", "episode_starts24", "episode_starts48"],
    "Trajectory": ["SimpleShock__mean24", "hazard_score__mean6", "hazard__accel"],
}
CONFIGS = {
    "Hazard": ["Hazard"],
    "Hazard+Burden": ["Hazard", "Burden"],
    "Hazard+Burden+Recovery": ["Hazard", "Burden", "Recovery"],
    "Full Hydra": ["Hazard", "Burden", "Recovery", "Persistence", "Trajectory"],
}


def make_history(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d["open_time"])
    d = d.sort_values("open_time").reset_index(drop=True)
    for c in ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_score"]:
        s = d[c].astype(float)
        for lag in (1, 3, 6, 12, 24, 48, 72):
            d[f"{c}__lag{lag}"] = s.shift(lag)
        for w in (6, 24, 48):
            d[f"{c}__mean{w}"] = s.shift(1).rolling(w, min_periods=3).mean()
            d[f"{c}__std{w}"] = s.shift(1).rolling(w, min_periods=3).std()
            d[f"{c}__delta{w}"] = s - s.shift(w)
    d["hazard__accel"] = d["hazard_score"].diff() - d["hazard_score"].diff().shift(1)
    d["age__log"] = np.log1p(np.maximum(d["episode_age_h"].astype(float), 0.0))
    starts = ((d["entry_path"] == "3_to_4") & (d["episode_age_h"] == 1)).astype(int)
    for w in (24, 48, 72):
        d[f"episode_starts{w}"] = starts.shift(1).rolling(w, min_periods=1).sum()
    return d


def cols_for(heads: list[str]) -> list[str]:
    return list(dict.fromkeys(c for h in heads for c in HEAD_FEATURES[h]))


def predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> np.ndarray:
    if not cols:
        return np.full(len(test), train[TARGET].mean(), dtype=float)
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=1500, class_weight="balanced", C=.5, solver="liblinear"),
    )
    model.fit(train[cols].astype(float), train[TARGET].astype(int))
    return model.predict_proba(test[cols].astype(float))[:, 1]


def metric(y: np.ndarray, p: np.ndarray, baseline_brier: float | None = None) -> dict:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    has_both = np.unique(y).size == 2
    frac, mean_pred = calibration_curve(y, p, n_bins=10, strategy="quantile") if has_both else (np.array([]), np.array([]))
    calibration_mae = float(np.mean(np.abs(frac - mean_pred))) if len(frac) else None
    if has_both:
        x = np.log(p / (1.0 - p)).reshape(-1, 1)
        cal_model = LogisticRegression(max_iter=2000, C=1e6, solver="lbfgs")
        cal_model.fit(x, y)
        cal_intercept = float(cal_model.intercept_[0])
        cal_slope = float(cal_model.coef_[0, 0])
        auc = float(roc_auc_score(y, p))
        pr_auc = float(average_precision_score(y, p))
    else:
        cal_intercept = None
        cal_slope = None
        auc = None
        pr_auc = None
    brier = float(brier_score_loss(y, p))
    result = {
        "n": int(len(y)),
        "events": int(y.sum()),
        "prevalence": float(y.mean()),
        "auc": auc,
        "pr_auc": pr_auc,
        "brier": brier,
        "logloss": float(log_loss(y, p, labels=[0, 1])),
        "calibration_mae": calibration_mae,
        "calibration_intercept": cal_intercept,
        "calibration_slope": cal_slope,
        "mean_prediction": float(p.mean()),
        "prediction_std": float(p.std()),
    }
    if baseline_brier is not None and baseline_brier > 0:
        result["brier_skill_vs_prevalence"] = float(1.0 - brier / baseline_brier)
    else:
        result["brier_skill_vs_prevalence"] = None
    return result


def fit_calibrator(kind: str, p: np.ndarray, y: np.ndarray):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    if kind == "platt":
        model = LogisticRegression(max_iter=2000, C=1e6, solver="lbfgs")
        model.fit(np.log(p / (1 - p)).reshape(-1, 1), y)
        return model
    if kind == "isotonic":
        return IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(p, y)
    raise ValueError(kind)


def apply_calibrator(kind: str, model, p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    if kind == "platt":
        return model.predict_proba(np.log(p / (1 - p)).reshape(-1, 1))[:, 1]
    return np.asarray(model.predict(p), dtype=float)


def temporal_oof(d: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, np.ndarray, list[int]]:
    ps, ys, years = [], [], []
    for year in CALIBRATION_YEARS:
        train = d[d.open_time.dt.year < year]
        test = d[d.open_time.dt.year == year]
        if len(train) == 0 or test.empty or train[TARGET].nunique() < 2:
            continue
        ps.append(predict(train, test, cols))
        ys.append(test[TARGET].astype(int).to_numpy())
        years.extend([year] * len(test))
    return np.concatenate(ps), np.concatenate(ys), years


def evaluate_config(d: pd.DataFrame, name: str, heads: list[str]) -> dict:
    cols = cols_for(heads)
    train = d[d.open_time.dt.year.isin(YEARS)]
    hold = d[d.open_time.dt.year == HOLDOUT]
    p_raw = predict(train, hold, cols)
    y_hold = hold[TARGET].astype(int).to_numpy()
    prevalence = float(y_hold.mean())
    baseline = np.full(len(y_hold), prevalence, dtype=float)
    baseline_brier = float(brier_score_loss(y_hold, baseline))

    p_oof, y_oof, oof_years = temporal_oof(d, cols)
    cal_results = {}
    for kind in ("platt", "isotonic"):
        calibrator = fit_calibrator(kind, p_oof, y_oof)
        p_cal = apply_calibrator(kind, calibrator, p_raw)
        cal_results[kind] = {
            "holdout_2024": metric(y_hold, p_cal, baseline_brier),
            "discovery_oof": metric(y_oof, apply_calibrator(kind, calibrator, p_oof), float(y_oof.mean() * (1 - y_oof.mean()))),
        }

    walk = {}
    for year in YEARS:
        train_w = d[d.open_time.dt.year < year]
        test_w = d[d.open_time.dt.year == year]
        if len(train_w) == 0 or test_w.empty or train_w[TARGET].nunique() < 2:
            walk[str(year)] = {"status": "not_evaluable"}
            continue
        if year == 2020:
            walk[str(year)] = {"status": "no_prior_training_year"}
            continue
        p_w = predict(train_w, test_w, cols)
        # Calibrate only from earlier temporal OOF predictions within the training era.
        prior_years = tuple(y for y in CALIBRATION_YEARS if y < year)
        if prior_years:
            ps, ys = [], []
            for cal_year in prior_years:
                tr = d[d.open_time.dt.year < cal_year]
                te = d[d.open_time.dt.year == cal_year]
                if len(tr) and te[TARGET].nunique() >= 2 and tr[TARGET].nunique() >= 2:
                    ps.append(predict(tr, te, cols)); ys.append(te[TARGET].astype(int).to_numpy())
            if ps:
                po = np.concatenate(ps); yo = np.concatenate(ys)
                fold = {}
                for kind in ("platt", "isotonic"):
                    cal = fit_calibrator(kind, po, yo)
                    fold[kind] = metric(test_w[TARGET].astype(int).to_numpy(), apply_calibrator(kind, cal, p_w), float(test_w[TARGET].mean() * (1-test_w[TARGET].mean())))
                walk[str(year)] = {"raw": metric(test_w[TARGET].astype(int).to_numpy(), p_w, float(test_w[TARGET].mean() * (1-test_w[TARGET].mean()))), "calibrated": fold}
            else:
                walk[str(year)] = {"raw": metric(test_w[TARGET].astype(int).to_numpy(), p_w, float(test_w[TARGET].mean() * (1-test_w[TARGET].mean()))), "calibrated": {"status": "insufficient_prior_oof"}}
        else:
            walk[str(year)] = {"raw": metric(test_w[TARGET].astype(int).to_numpy(), p_w, float(test_w[TARGET].mean() * (1-test_w[TARGET].mean()))), "calibrated": {"status": "insufficient_prior_oof"}}

    return {
        "config": name,
        "heads": heads,
        "features": cols,
        "calibration_training": {"method": "temporal_OOF", "years": sorted(set(oof_years)), "rows": int(len(y_oof)), "events": int(y_oof.sum()), "event_rate": float(y_oof.mean())},
        "holdout_prevalence_baseline": metric(y_hold, baseline),
        "raw_holdout_2024": metric(y_hold, p_raw, baseline_brier),
        "calibrated": cal_results,
        "walk_forward": walk,
        "provenance": {"python": platform.python_version(), "calibrators": ["platt", "isotonic"], "holdout_year": HOLDOUT},
    }


def main(csv: Path, out: Path) -> None:
    raw = pd.read_csv(csv)
    d = make_history(raw)
    assert len(raw) == 43848
    starts = ((d.entry_path == "3_to_4") & (d.episode_age_h == 1)).sum()
    assert int(starts) == 169
    payload = {
        "experiment": "HYDRA_CALIBRATION_COURT_V1",
        "canonical_rows": len(raw),
        "canonical_h3_starts": int(starts),
        "discovery_years": list(YEARS),
        "calibration_oof_years": list(CALIBRATION_YEARS),
        "holdout_year": HOLDOUT,
        "selection_rule": "No calibrator is selected on 2024; Platt and isotonic are both reported.",
        "results": [evaluate_config(d, name, heads) for name, heads in CONFIGS.items()],
    }
    out.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
