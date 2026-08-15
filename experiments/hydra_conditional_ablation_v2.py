"""HYDRA conditional ablation court V2.

This court is deliberately skeptical of native TIAMAT-derived state scores.
Primary target is the independent future outcome Crash72 for every configuration.
2024 is a frozen holdout. Discovery/representation fitting occurs only before it.

The court reports three orderings, representation-conditional Recovery/Persistence,
newest-head permutation controls, calibration, and stability. It does not promote
an architecture; it produces evidence for PROMOTE/MERGE/REWORK/REJECT/HOLD.
"""
from __future__ import annotations

import argparse
import json
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

LEAKAGE_FIELDS = {"Crash72", "episode_type", "duration_bucket", "entry_path", "episode_age_h"}
NATIVE_SUSPECT = {"hazard_score", "hazard_raw"}


@dataclass(frozen=True)
class HeadSpec:
    name: str
    columns: tuple[str, ...]


def past_features(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    d = d.sort_values("open_time").reset_index(drop=True)
    for col in ("SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_score"):
        s = pd.to_numeric(d[col], errors="coerce").astype(float)
        d[f"{col}_lag6"] = s.shift(6)
        d[f"{col}_diff1"] = s.diff(1)
        d[f"{col}_mean6"] = s.shift(1).rolling(6, min_periods=3).mean()
        d[f"{col}_mean24"] = s.shift(1).rolling(24, min_periods=6).mean()
        d[f"{col}_slope24"] = (s.shift(1) - s.shift(24)) / 24.0
    # Shock-adjusted burden: current burden minus only past shock context.
    d["burden_minus_shock24"] = d["LiveDeficit"] - d["SimpleShock"].shift(1).rolling(24, min_periods=6).max()
    # Persistence representation: duration since a training-independent threshold
    # is crossed. Threshold itself is learned from each training fold.
    d["_ld"] = pd.to_numeric(d["LiveDeficit"], errors="coerce")
    d["_rw"] = pd.to_numeric(d["RecoveryWeakness_v1"], errors="coerce")
    return d


def add_persistence(train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = train.copy(); test = test.copy()
    ld_threshold = float(train["_ld"].quantile(0.75))
    rw_threshold = float(train["_rw"].quantile(0.75))

    def tenure(frame: pd.DataFrame) -> pd.Series:
        vals = frame["_ld"].to_numpy(float)
        out = np.zeros(len(vals), dtype=float)
        age = 0
        for i, x in enumerate(vals):
            if np.isfinite(x) and x >= ld_threshold:
                age += 1
            else:
                age = 0
            out[i] = age
        return pd.Series(out, index=frame.index)

    def rw_tenure(frame: pd.DataFrame) -> pd.Series:
        vals = frame["_rw"].to_numpy(float)
        out = np.zeros(len(vals), dtype=float)
        age = 0
        for i, x in enumerate(vals):
            if np.isfinite(x) and x >= rw_threshold:
                age += 1
            else:
                age = 0
            out[i] = age
        return pd.Series(out, index=frame.index)

    train["persistence_ld"] = tenure(train)
    train["persistence_rw"] = rw_tenure(train)
    # Test tenure is intentionally reset at the fold boundary: no hidden state from
    # the future is carried backward. The first test row has zero newly observed age.
    test["persistence_ld"] = tenure(test)
    test["persistence_rw"] = rw_tenure(test)
    return train, test


def recovery_candidates() -> tuple[str, ...]:
    return ("LiveDeficit_diff1", "LiveDeficit_slope24", "burden_minus_shock24", "RecoveryWeakness_v1_diff1")


def persistence_candidates() -> tuple[str, ...]:
    return ("persistence_ld", "persistence_rw")


def model_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> np.ndarray:
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=2000, C=0.5, solver="liblinear"),
    )
    model.fit(train[cols].astype(float), train["Crash72"].astype(int))
    return model.predict_proba(test[cols].astype(float))[:, 1]


def metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float | None]:
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    out: dict[str, float | None] = {
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p, labels=[0, 1])),
    }
    if len(np.unique(y)) == 2:
        out["auc"] = float(roc_auc_score(y, p))
        out["pr_auc"] = float(average_precision_score(y, p))
        frac, mean_pred = calibration_curve(y, p, n_bins=10, strategy="quantile")
        out["ece10_mae"] = float(np.mean(np.abs(frac - mean_pred)))
    else:
        out.update({"auc": None, "pr_auc": None, "ece10_mae": None})
    return out


def fit_head_outputs(train: pd.DataFrame, test: pd.DataFrame, specs: dict[str, HeadSpec]) -> dict[str, np.ndarray]:
    return {name: model_predict(train, test, list(spec.columns)) for name, spec in specs.items()}


def coordinator(head_outputs_train: dict[str, np.ndarray], head_outputs_test: dict[str, np.ndarray], y_train: np.ndarray) -> np.ndarray:
    names = list(head_outputs_train)
    Xtr = np.column_stack([head_outputs_train[n] for n in names])
    Xte = np.column_stack([head_outputs_test[n] for n in names])
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=0.5, solver="liblinear"))
    model.fit(Xtr, y_train)
    return model.predict_proba(Xte)[:, 1]


def audit_columns(d: pd.DataFrame) -> dict[str, object]:
    return {
        "leakage_fields_present": sorted(LEAKAGE_FIELDS & set(d.columns)),
        "native_suspect_fields_present": sorted(NATIVE_SUSPECT & set(d.columns)),
        "rows": int(len(d)),
        "h3_starts_posthoc": int(((d.entry_path == "3_to_4") & (d.episode_age_h == 1)).sum()) if "entry_path" in d else None,
        "note": "H3/episode annotations are audit-only and never predictors.",
    }


def evaluate_configuration(train: pd.DataFrame, test: pd.DataFrame, head_specs: dict[str, HeadSpec]) -> dict[str, object]:
    # Each head is fitted separately. The coordinator sees only frozen head outputs.
    train_h, test_h = add_persistence(train, test)
    train_outputs = fit_head_outputs(train_h, train_h, head_specs)
    test_outputs = fit_head_outputs(train_h, test_h, head_specs)
    # In-sample head outputs are only used to fit the coordinator; the coordinator's
    # final score is reported on the untouched fold. This is intentionally simple and
    # conservative; a future court can replace this with cross-fitted stacking.
    p = coordinator(train_outputs, test_outputs, train_h.Crash72.to_numpy(int))
    return {"metrics": metrics(test_h.Crash72.to_numpy(int), p), "features": {k: list(v.columns) for k, v in head_specs.items()}}


def run_ordering(train: pd.DataFrame, test: pd.DataFrame, ordering: list[str], recovery_col: str, persistence_col: str) -> dict[str, object]:
    base = {
        "Hazard": HeadSpec("Hazard", ("hazard_score",)),
        "Burden": HeadSpec("Burden", ("LiveDeficit_lag6",)),
        "Recovery": HeadSpec("Recovery", (recovery_col,)),
        "Persistence": HeadSpec("Persistence", (persistence_col,)),
        "Trajectory": HeadSpec("Trajectory", ("SimpleShock_mean24", "hazard_score_mean24")),
    }
    result = []
    admitted: dict[str, HeadSpec] = {}
    for head in ordering:
        admitted[head] = base[head]
        r = evaluate_configuration(train, test, admitted)
        result.append({"added": head, "configuration": list(admitted), **r})
    return {"ordering": ordering, "recovery": recovery_col, "persistence": persistence_col, "steps": result}


def main(csv: Path, out: Path | None) -> None:
    raw = pd.read_csv(csv)
    d = past_features(raw)
    audit = audit_columns(d)
    if len(d) != 43848:
        raise ValueError(f"canonical row count mismatch: {len(d)} != 43848")
    if int(audit["h3_starts_posthoc"]) != 169:
        raise ValueError(f"canonical H3 population mismatch: {audit['h3_starts_posthoc']} != 169")
    if not {"Crash72", "hazard_score", "LiveDeficit"}.issubset(d.columns):
        raise ValueError("required causal/audit columns missing")

    # Hazard skepticism pass: same independent future target, but explicitly labeled
    # as an audit. It cannot authorize hazard_score as a causal anchor.
    train23 = d[d.open_time.dt.year <= 2023].copy()
    hold24 = d[d.open_time.dt.year == 2024].copy()
    hazard_audit = {
        "lineage_status": "SUSPECT_NATIVE_TIAMAT_DERIVED",
        "holdout_2024": metrics(hold24.Crash72.to_numpy(int), model_predict(train23, hold24, ["hazard_score"])),
        "warning": "Near-perfect performance is an investigation trigger, not a promotion decision.",
    }

    # Recovery/Persistence representation search is explicitly conditional on the
    # current candidate family. The best candidate is selected only from 2020-2023.
    train = train23.copy()
    recovery_scores = []
    for col in recovery_candidates():
        p = model_predict(train, train, [col])
        recovery_scores.append((metrics(train.Crash72.to_numpy(int), p)["auc"] or -1.0, col))
    best_recovery = max(recovery_scores)[1]
    persistence_train, _ = add_persistence(train, hold24)
    persistence_scores = []
    for col in persistence_candidates():
        p = model_predict(persistence_train, persistence_train, [col])
        persistence_scores.append((metrics(persistence_train.Crash72.to_numpy(int), p)["auc"] or -1.0, col))
    best_persistence = max(persistence_scores)[1]

    orderings = [
        ["Hazard", "Burden", "Recovery", "Persistence", "Trajectory"],
        ["Hazard", "Trajectory", "Burden", "Recovery", "Persistence"],
        ["Burden", "Recovery", "Trajectory", "Persistence", "Hazard"],
    ]
    all_results = []
    # Walk-forward years 2021-2023. 2020 has no pre-2020 training window and is
    # therefore not misrepresented as a conventional forward fold.
    for test_year in (2021, 2022, 2023):
        tr = d[d.open_time.dt.year < test_year].copy()
        te = d[d.open_time.dt.year == test_year].copy()
        for order in orderings:
            all_results.append({"year": test_year, **run_ordering(tr, te, order, best_recovery, best_persistence)})

    # Frozen 2024: no selection occurs after this point.
    holdout_results = [
        run_ordering(train23, hold24, order, best_recovery, best_persistence)
        for order in orderings
    ]

    # Newest-head permutation: shuffle only the newly admitted head representation
    # in the frozen 2024 fold, while retaining prior head outputs.
    permutation = []
    rng = np.random.default_rng(17)
    order = orderings[0]
    base_specs = {
        "Hazard": HeadSpec("Hazard", ("hazard_score",)),
        "Burden": HeadSpec("Burden", ("LiveDeficit_lag6",)),
        "Recovery": HeadSpec("Recovery", (best_recovery,)),
        "Persistence": HeadSpec("Persistence", (best_persistence,)),
        "Trajectory": HeadSpec("Trajectory", ("SimpleShock_mean24", "hazard_score_mean24")),
    }
    trh, teh = add_persistence(train23, hold24)
    prior = {}
    for head in order:
        current = {**prior, head: base_specs[head]}
        tr_out = fit_head_outputs(trh, trh, current)
        te_out = fit_head_outputs(trh, teh, current)
        observed = coordinator(tr_out, te_out, trh.Crash72.to_numpy(int))
        observed_auc = metrics(teh.Crash72.to_numpy(int), observed)["auc"]
        # Permute only newest-head test output; all prior outputs remain fixed.
        null = []
        for _ in range(200):
            perm_out = dict(te_out)
            perm_out[head] = rng.permutation(perm_out[head])
            pp = coordinator(tr_out, perm_out, trh.Crash72.to_numpy(int))
            auc = metrics(teh.Crash72.to_numpy(int), pp)["auc"]
            if auc is not None:
                null.append(auc)
        permutation.append({
            "added": head,
            "observed_auc": observed_auc,
            "null_p95_auc": float(np.quantile(null, 0.95)) if null else None,
            "incremental_permutation_separation": float(observed_auc - np.quantile(null, 0.95)) if null and observed_auc is not None else None,
        })
        prior = current

    payload = {
        "court": "HYDRA_HEAD_CONDITIONAL_ABLATION_V2",
        "audit": audit,
        "target": "Crash72 for every ablation configuration",
        "hazard_audit": hazard_audit,
        "recovery_representation": best_recovery,
        "persistence_representation": best_persistence,
        "recovery_candidates": recovery_scores,
        "persistence_candidates": persistence_scores,
        "walk_forward": all_results,
        "holdout_2024": holdout_results,
        "newest_head_permutation": permutation,
        "decision_rule": "See HYDRA_HEAD_CONDITIONAL_ABLATION_COURT_V2_LOCK_20260815.md; no architecture promotion is automatic.",
    }
    if out:
        out.write_text(json.dumps(payload, indent=2, default=str))
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    main(args.csv, args.out)
