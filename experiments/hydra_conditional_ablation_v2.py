"""HYDRA conditional head ablation court V2.1.

Purpose: test whether candidate heads add independent information after
conditioning on previously retained heads. 2024 is a frozen holdout.
All persistence transforms are generated causally from each split's training
history so no test-row history can initialize the counter.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

TARGET = "Crash72"
LEAKAGE = {TARGET, "episode_type", "duration_bucket", "entry_path", "episode_age_h"}
DISCOVERY_YEARS = (2020, 2021, 2022, 2023)
HOLDOUT = 2024

HEAD_FEATURES = {
    "Hazard": ("hazard_score",),
    "Burden": ("LiveDeficit_lag6",),
    "Recovery": ("RecoveryWeakness_v1_lag6",),
    "Trajectory": ("SimpleShock_mean24", "hazard_score_mean24", "hazard_diff1"),
}


def prepare(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d.open_time, utc=True)
    d = d.sort_values("open_time").reset_index(drop=True)
    for c in ("SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_score"):
        s = pd.to_numeric(d[c], errors="coerce")
        d[f"{c}_lag6"] = s.shift(6)
        d[f"{c}_diff1"] = s.diff()
        d[f"{c}_mean24"] = s.shift(1).rolling(24, min_periods=6).mean()
        d[f"{c}_slope24"] = (s.shift(1) - s.shift(24)) / 24.0
    d["burden_minus_shock24"] = d.LiveDeficit - d.SimpleShock.shift(1).rolling(24, min_periods=6).max()
    d["age_log_obs"] = np.log1p(np.maximum(pd.to_numeric(d["episode_age_h"], errors="coerce"), 0.0))
    return d


def with_persistence(train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = train.copy(); test = test.copy()
    ld = pd.to_numeric(train.LiveDeficit, errors="coerce")
    rw = pd.to_numeric(train.RecoveryWeakness_v1, errors="coerce")
    ld_thr = float(ld.quantile(.75)); rw_thr = float(rw.quantile(.75))

    # Build a causal counter for train. For test, initialize from the terminal
    # train state and then advance chronologically through the test rows.
    def advance(values: np.ndarray, threshold: float, initial: int = 0) -> np.ndarray:
        n = 0 if not np.isfinite(initial) else int(initial)
        out = []
        for x in values:
            if np.isfinite(x) and x >= threshold:
                n += 1
            else:
                n = 0
            out.append(float(n))
        return np.asarray(out, dtype=float)

    train["persistence_ld"] = advance(ld.to_numpy(float), ld_thr)
    train["persistence_rw"] = advance(rw.to_numpy(float), rw_thr)
    ld_initial = int(train["persistence_ld"].iloc[-1]) if len(train) else 0
    rw_initial = int(train["persistence_rw"].iloc[-1]) if len(train) else 0
    test["persistence_ld"] = advance(pd.to_numeric(test.LiveDeficit, errors="coerce").to_numpy(float), ld_thr, ld_initial)
    test["persistence_rw"] = advance(pd.to_numeric(test.RecoveryWeakness_v1, errors="coerce").to_numpy(float), rw_thr, rw_initial)
    return train, test


def estimator(cols):
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=2000, C=.5, solver="liblinear"))


def fit(train, test, cols):
    m = estimator(cols)
    m.fit(train[list(cols)].astype(float), train[TARGET].astype(int))
    return m.predict_proba(test[list(cols)].astype(float))[:, 1]


def score(y, p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    r = {"brier": float(brier_score_loss(y, p)), "logloss": float(log_loss(y, p, labels=[0, 1]))}
    if len(np.unique(y)) == 2:
        r["auc"] = float(roc_auc_score(y, p))
        r["pr_auc"] = float(average_precision_score(y, p))
        a, b = calibration_curve(y, p, n_bins=10, strategy="quantile")
        r["ece10_mae"] = float(np.mean(np.abs(a - b)))
    else:
        r.update({"auc": None, "pr_auc": None, "ece10_mae": None})
    return r


def crossfit_heads(train, test, specs):
    # Expanding-origin OOF predictions for the discovered head signals.
    n = len(train); oof = {k: np.full(n, np.nan) for k in specs}; ts = {}
    cuts = np.linspace(0, n, 4, dtype=int)
    for k, hcols in specs.items():
        for i in range(1, 4):
            lo, hi = cuts[i - 1], cuts[i]
            if lo < 100: continue
            oof[k][lo:hi] = fit(train.iloc[:lo], train.iloc[lo:hi], hcols)
        ts[k] = fit(train, test, hcols)
    matrix = np.column_stack(list(oof.values()))
    mask = np.all(np.isfinite(matrix), axis=1)
    return {k: v[mask] for k, v in oof.items()}, ts, mask


def coordinator(oof, test_outputs, y):
    names = list(oof)
    X = np.column_stack([oof[n] for n in names])
    Z = np.column_stack([test_outputs[n] for n in names])
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=.5, solver="liblinear"))
    m.fit(X, y)
    return m.predict_proba(Z)[:, 1]


def audit(d):
    return {
        "rows": len(d),
        "leakage_fields_present": sorted(LEAKAGE & set(d.columns)),
        "h3_starts_posthoc": int(((d.entry_path == "3_to_4") & (d.episode_age_h == 1)).sum()),
    }


def run_config(train, test, specs):
    tr, te = with_persistence(train, test)
    oof, to, mask = crossfit_heads(tr, te, specs)
    y = tr[TARGET].astype(int).to_numpy()[mask]
    p = coordinator(oof, to, y)
    return score(te[TARGET].astype(int).to_numpy(), p), to


def select_best(d, candidates):
    scored = {}
    for c in candidates:
        vals = []
        for year in DISCOVERY_YEARS[1:]:
            tr = d[d.open_time.dt.year < year].copy()
            te = d[d.open_time.dt.year == year].copy()
            if len(tr) < 200 or te[TARGET].nunique() < 2: continue
            vals.append(score(te[TARGET].astype(int), fit(tr, te, (c,))))
        aucs = [x["auc"] for x in vals if x["auc"] is not None]
        scored[c] = {"folds": vals, "mean_auc": float(np.mean(aucs)) if aucs else None, "worst_auc": float(np.min(aucs)) if aucs else None}
    best = max(scored, key=lambda c: (scored[c]["mean_auc"] if scored[c]["mean_auc"] is not None else -1, scored[c]["worst_auc"] if scored[c]["worst_auc"] is not None else -1))
    return scored, best


def main(csv: Path, out: Path | None):
    d = prepare(pd.read_csv(csv)); a = audit(d)
    if len(d) != 43848 or a["h3_starts_posthoc"] != 169: raise ValueError(f"canonical validation failed: {a}")
    train23 = d[d.open_time.dt.year <= 2023].copy()
    hold = d[d.open_time.dt.year == HOLDOUT].copy()

    recovery_candidates = ("LiveDeficit_diff1", "LiveDeficit_slope24", "burden_minus_shock24", "RecoveryWeakness_v1_diff1")
    persistence_candidates = ("persistence_ld", "persistence_rw")
    rec_scores, best_r = select_best(train23, recovery_candidates)
    trp, _ = with_persistence(train23, hold)
    per_scores, best_p = select_best(trp, persistence_candidates)

    base = {
        "Hazard": HEAD_FEATURES["Hazard"],
        "Burden": HEAD_FEATURES["Burden"],
        "Recovery": (best_r,),
        "Persistence": (best_p,),
        "Trajectory": HEAD_FEATURES["Trajectory"],
    }
    orders = [
        ["Hazard", "Burden", "Recovery", "Persistence", "Trajectory"],
        ["Hazard", "Trajectory", "Burden", "Recovery", "Persistence"],
        ["Burden", "Recovery", "Trajectory", "Persistence", "Hazard"],
    ]

    def evaluate_sequence(tr, te, order):
        admitted = {}; steps = []
        for h in order:
            admitted[h] = base[h]
            s, _ = run_config(tr, te, admitted)
            steps.append({"added": h, "configuration": list(admitted), "metrics": s})
        return steps

    folds = []
    for year in (2021, 2022, 2023):
        tr = d[d.open_time.dt.year < year].copy(); te = d[d.open_time.dt.year == year].copy()
        for order in orders:
            folds.append({"year": year, "order": order, "steps": evaluate_sequence(tr, te, order)})
    holdout = [{"order": order, "steps": evaluate_sequence(train23, hold, order)} for order in orders]

    # Null on frozen holdout for the fully admitted configuration.
    trh, teh = with_persistence(train23, hold)
    admitted = {h: base[h] for h in orders[0]}
    oof, to, mask = crossfit_heads(trh, teh, admitted); y = trh[TARGET].astype(int).to_numpy()[mask]
    observed = coordinator(oof, to, y); obs = score(teh[TARGET].astype(int), observed)["auc"]
    rng = np.random.default_rng(17); null = []
    for _ in range(200):
        y_perm = rng.permutation(y)
        null.append(roc_auc_score(teh[TARGET].astype(int), coordinator(oof, to, y_perm)))
    perm = {"observed_auc": obs, "null_mean_auc": float(np.mean(null)), "null_p95_auc": float(np.quantile(null, .95)), "separation": None if obs is None else float(obs - np.quantile(null, .95))}

    payload = {
        "court": "HYDRA_HEAD_CONDITIONAL_ABLATION_V2.1",
        "audit": a,
        "recovery_candidates": rec_scores,
        "selected_recovery_representation": best_r,
        "persistence_candidates": per_scores,
        "selected_persistence_representation": best_p,
        "walk_forward": folds,
        "holdout_2024": holdout,
        "full_model_permutation_holdout": perm,
        "decision_rule": "No head promotion/merge/rejection from marginal metrics alone; require incremental frozen-holdout evidence plus null control and walk-forward recurrence.",
    }
    if out: out.write_text(json.dumps(payload, indent=2, default=str))
    print(json.dumps(payload, indent=2, default=str))

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path); x=ap.parse_args(); main(x.csv,x.out)
