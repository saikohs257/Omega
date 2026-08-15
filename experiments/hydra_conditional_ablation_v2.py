"""HYDRA conditional head ablation court V2.

Purpose: test whether candidate heads add independent information after
conditioning on previously retained heads. 2024 is a frozen holdout.
Selection is walk-forward only; no in-sample candidate selection is allowed.
"""
from __future__ import annotations
import argparse, json
from dataclasses import dataclass
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
SUSPECT = {"hazard_score", "hazard_raw"}
DISCOVERY_YEARS = (2020, 2021, 2022, 2023)
HOLDOUT = 2024

@dataclass(frozen=True)
class Head:
    cols: tuple[str, ...]


def prepare(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d.open_time, utc=True)
    d = d.sort_values("open_time").reset_index(drop=True)
    for c in ("SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_score"):
        s = pd.to_numeric(d[c], errors="coerce")
        d[f"{c}_lag6"] = s.shift(6)
        d[f"{c}_diff1"] = s.diff()
        d[f"{c}_mean24"] = s.shift(1).rolling(24, min_periods=6).mean()
        d[f"{c}_slope24"] = (s.shift(1) - s.shift(24)) / 24
    d["burden_minus_shock24"] = d.LiveDeficit - d.SimpleShock.shift(1).rolling(24, min_periods=6).max()
    d["_ld"] = pd.to_numeric(d.LiveDeficit, errors="coerce")
    d["_rw"] = pd.to_numeric(d.RecoveryWeakness_v1, errors="coerce")
    return d


def add_persistence(train, test):
    train = train.copy(); test = test.copy()
    ld = float(train._ld.quantile(.75)); rw = float(train._rw.quantile(.75))
    def age(s, threshold):
        a = 0; out = []
        for x in s:
            if np.isfinite(x) and x >= threshold: a += 1
            else: a = 0
            out.append(a)
        return np.asarray(out, float)
    train["persistence_ld"] = age(train._ld.to_numpy(float), ld)
    train["persistence_rw"] = age(train._rw.to_numpy(float), rw)
    test["persistence_ld"] = age(test._ld.to_numpy(float), ld)
    test["persistence_rw"] = age(test._rw.to_numpy(float), rw)
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
    n = len(train); oof = {k: np.full(n, np.nan) for k in specs}; ts = {}
    cuts = np.linspace(0, n, 4, dtype=int)
    for k, h in specs.items():
        for i in range(1, 4):
            lo, hi = cuts[i - 1], cuts[i]
            if lo < 100: continue
            oof[k][lo:hi] = fit(train.iloc[:lo], train.iloc[lo:hi], h.cols)
        ts[k] = fit(train, test, h.cols)
    mask = np.all(np.isfinite(np.column_stack(list(oof.values()))), axis=1)
    return {k: v[mask] for k, v in oof.items()}, ts, mask


def coordinator(oof, test_outputs, y):
    names = list(oof)
    X = np.column_stack([oof[n] for n in names])
    Z = np.column_stack([test_outputs[n] for n in names])
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=.5, solver="liblinear"))
    m.fit(X, y)
    return m.predict_proba(Z)[:, 1]


def audit(d):
    return {"rows": len(d), "leakage_fields_present": sorted(LEAKAGE & set(d.columns)), "native_suspect": sorted(SUSPECT & set(d.columns)), "h3_starts_posthoc": int(((d.entry_path == "3_to_4") & (d.episode_age_h == 1)).sum())}


def run_config(train, test, specs):
    tr, te = add_persistence(train, test)
    oof, to, mask = crossfit_heads(tr, te, specs)
    y = tr[TARGET].astype(int).to_numpy()[mask]
    p = coordinator(oof, to, y)
    return score(te[TARGET].astype(int).to_numpy(), p), to


def walkforward_single(d, cols):
    vals = []
    for year in (2021, 2022, 2023):
        tr = d[d.open_time.dt.year < year].copy()
        te = d[d.open_time.dt.year == year].copy()
        if len(tr) < 200 or te[TARGET].nunique() < 2: continue
        vals.append(score(te[TARGET].astype(int), fit(tr, te, cols)))
    return vals


def select_best(d, candidates):
    scored = {}
    for c in candidates:
        vals = walkforward_single(d, (c,))
        aucs = [x["auc"] for x in vals if x["auc"] is not None]
        scored[c] = {"folds": vals, "mean_auc": float(np.mean(aucs)) if aucs else None, "worst_auc": float(np.min(aucs)) if aucs else None}
    best = max(scored, key=lambda c: (scored[c]["mean_auc"] if scored[c]["mean_auc"] is not None else -1, scored[c]["worst_auc"] if scored[c]["worst_auc"] is not None else -1))
    return scored, best


def main(csv: Path, out: Path | None):
    d = prepare(pd.read_csv(csv)); a = audit(d)
    if len(d) != 43848 or a["h3_starts_posthoc"] != 169: raise ValueError(f"canonical validation failed: {a}")
    if TARGET not in d: raise ValueError("Crash72 target missing")
    train23 = d[d.open_time.dt.year <= 2023].copy()
    hold = d[d.open_time.dt.year == HOLDOUT].copy()

    hazard = {"lineage": "SUSPECT_NATIVE_TIAMAT_DERIVED", "holdout_2024": score(hold[TARGET].astype(int), fit(train23, hold, ["hazard_score"])), "promotion": False}
    recovery_candidates = ("LiveDeficit_diff1", "LiveDeficit_slope24", "burden_minus_shock24", "RecoveryWeakness_v1_diff1")
    persistence_candidates = ("persistence_ld", "persistence_rw")
    rec_scores, best_r = select_best(train23, recovery_candidates)
    trp, _ = add_persistence(train23, hold)
    per_scores, best_p = select_best(trp, persistence_candidates)

    base = {
        "Hazard": Head(("hazard_score",)),
        "Burden": Head(("LiveDeficit_lag6",)),
        "Recovery": Head((best_r,)),
        "Persistence": Head((best_p,)),
        "Trajectory": Head(("SimpleShock_mean24", "hazard_score_mean24")),
    }
    orders = [
        ["Hazard", "Burden", "Recovery", "Persistence", "Trajectory"],
        ["Hazard", "Trajectory", "Burden", "Recovery", "Persistence"],
        ["Burden", "Recovery", "Trajectory", "Persistence", "Hazard"],
    ]

    def evaluate_year(tr, te, order):
        admitted = {}; steps = []
        for h in order:
            admitted[h] = base[h]
            s, _ = run_config(tr, te, admitted)
            steps.append({"added": h, "configuration": list(admitted), "metrics": s})
        return steps

    folds = []
    for year in (2021, 2022, 2023):
        tr = d[d.open_time.dt.year < year].copy(); te = d[d.open_time.dt.year == year].copy()
        for order in orders: folds.append({"year": year, "order": order, "steps": evaluate_year(tr, te, order)})
    holdout = [{"order": order, "steps": evaluate_year(train23, hold, order)} for order in orders]

    rng = np.random.default_rng(17); perm = []; admitted = {}
    trh, teh = add_persistence(train23, hold)
    for h in orders[0]:
        admitted[h] = base[h]
        oof, to, mask = crossfit_heads(trh, teh, admitted); y = trh[TARGET].astype(int).to_numpy()[mask]
        observed = coordinator(oof, to, y); obs = score(teh[TARGET].astype(int), observed)["auc"]
        null = []
        for _ in range(200):
            z = dict(to); z[h] = rng.permutation(z[h]); null.append(score(teh[TARGET].astype(int), coordinator(oof, z, y))["auc"])
        p95 = float(np.quantile(null, .95))
        perm.append({"added": h, "observed_auc": obs, "null_p95_auc": p95, "separation": None if obs is None else float(obs - p95)})

    payload = {"court": "HYDRA_HEAD_CONDITIONAL_ABLATION_V2", "audit": a, "target": TARGET, "hazard_audit": hazard, "recovery_candidates": rec_scores, "selected_recovery_representation": best_r, "persistence_candidates": per_scores, "selected_persistence_representation": best_p, "walk_forward": folds, "holdout_2024": holdout, "newest_head_permutation": perm, "decision_rule": "V2 lock: PROMOTE/MERGE/REWORK/REJECT/HOLD only after all preregistered gates."}
    if out: out.write_text(json.dumps(payload, indent=2, default=str))
    print(json.dumps(payload, indent=2, default=str))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv", type=Path); ap.add_argument("--out", type=Path); x = ap.parse_args(); main(x.csv, x.out)
