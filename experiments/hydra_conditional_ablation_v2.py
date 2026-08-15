"""HYDRA conditional ablation court V2.

Crash72 is the single target for the nested ablation. 2024 is frozen.
Native TIAMAT-derived hazard state is audited but not trusted as a causal anchor.
Head outputs are cross-fitted before the coordinator sees them.

This implementation seals representation selection to each outer training fold,
keeps persistence state continuous across train/test boundaries, reports fold
stability, and keeps 2024 completely untouched by discovery.
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

LEAKAGE = {"Crash72", "episode_type", "duration_bucket", "entry_path", "episode_age_h"}
SUSPECT = {"hazard_score", "hazard_raw"}


@dataclass(frozen=True)
class Head:
    cols: tuple[str, ...]


def prepare(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    d = d.sort_values("open_time").reset_index(drop=True)
    for c in ("SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_score"):
        s = pd.to_numeric(d[c], errors="coerce")
        d[f"{c}_lag6"] = s.shift(6)
        d[f"{c}_diff1"] = s.diff()
        d[f"{c}_mean24"] = s.shift(1).rolling(24, min_periods=6).mean()
        d[f"{c}_slope24"] = (s.shift(1) - s.shift(24)) / 24.0
    d["burden_minus_shock24"] = d["LiveDeficit"] - d["SimpleShock"].shift(1).rolling(24, min_periods=6).max()
    d["_ld"] = pd.to_numeric(d["LiveDeficit"], errors="coerce")
    d["_rw"] = pd.to_numeric(d["RecoveryWeakness_v1"], errors="coerce")
    return d


def _age_from_start(values: np.ndarray, threshold: float, initial_age: int = 0) -> np.ndarray:
    age = initial_age
    out = np.zeros(len(values), dtype=float)
    for i, x in enumerate(values):
        if np.isfinite(x) and x >= threshold:
            age += 1
        else:
            age = 0
        out[i] = age
    return out


def add_persistence(train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build persistence using a threshold learned from train and continuous state across the boundary."""
    train = train.copy()
    test = test.copy()
    ld_threshold = float(train["_ld"].quantile(0.75))
    rw_threshold = float(train["_rw"].quantile(0.75))

    train["persistence_ld"] = _age_from_start(train["_ld"].to_numpy(float), ld_threshold)
    train["persistence_rw"] = _age_from_start(train["_rw"].to_numpy(float), rw_threshold)

    if len(test):
        ld_tail = train["_ld"].to_numpy(float)[-1:]
        rw_tail = train["_rw"].to_numpy(float)[-1:]
        ld_initial = 1 if np.isfinite(ld_tail[0]) and ld_tail[0] >= ld_threshold else 0
        rw_initial = 1 if np.isfinite(rw_tail[0]) and rw_tail[0] >= rw_threshold else 0
        combined_ld = np.concatenate([ld_tail, test["_ld"].to_numpy(float)])
        combined_rw = np.concatenate([rw_tail, test["_rw"].to_numpy(float)])
        test_ld = _age_from_start(combined_ld, ld_threshold, max(0, ld_initial - 1))[1:]
        test_rw = _age_from_start(combined_rw, rw_threshold, max(0, rw_initial - 1))[1:]
        test["persistence_ld"] = test_ld
        test["persistence_rw"] = test_rw
    else:
        test["persistence_ld"] = np.array([], dtype=float)
        test["persistence_rw"] = np.array([], dtype=float)
    return train, test


def estimator(cols: tuple[str, ...] | list[str]):
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=2000, C=0.5, solver="liblinear"),
    )


def fit(train: pd.DataFrame, test: pd.DataFrame, cols: tuple[str, ...] | list[str]) -> np.ndarray:
    model = estimator(cols)
    model.fit(train[list(cols)].astype(float), train["Crash72"].astype(int))
    return model.predict_proba(test[list(cols)].astype(float))[:, 1]


def score(y: np.ndarray, p: np.ndarray) -> dict[str, float | None]:
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    result: dict[str, float | None] = {
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p, labels=[0, 1])),
    }
    if len(np.unique(y)) == 2:
        result["auc"] = float(roc_auc_score(y, p))
        result["pr_auc"] = float(average_precision_score(y, p))
        frac, mean_pred = calibration_curve(y, p, n_bins=10, strategy="quantile")
        result["ece10_mae"] = float(np.mean(np.abs(frac - mean_pred)))
    else:
        result.update({"auc": None, "pr_auc": None, "ece10_mae": None})
    return result


def crossfit_heads(train: pd.DataFrame, test: pd.DataFrame, specs: dict[str, Head]):
    """Return OOF train head outputs and frozen test outputs."""
    n = len(train)
    oof = {name: np.full(n, np.nan) for name in specs}
    test_outputs: dict[str, np.ndarray] = {}
    cuts = np.linspace(0, n, 4, dtype=int)
    for name, head in specs.items():
        for i in range(1, 4):
            lo, hi = cuts[i - 1], cuts[i]
            fit_end = lo
            if fit_end < 100:
                continue
            oof[name][lo:hi] = fit(train.iloc[:fit_end], train.iloc[lo:hi], head.cols)
        test_outputs[name] = fit(train, test, head.cols)
    mask = np.all(np.isfinite(np.column_stack(list(oof.values()))), axis=1)
    return {name: values[mask] for name, values in oof.items()}, test_outputs, mask


def coordinator(oof: dict[str, np.ndarray], test_outputs: dict[str, np.ndarray], y: np.ndarray) -> np.ndarray:
    names = list(oof)
    x_train = np.column_stack([oof[name] for name in names])
    x_test = np.column_stack([test_outputs[name] for name in names])
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=0.5, solver="liblinear"))
    model.fit(x_train, y)
    return model.predict_proba(x_test)[:, 1]


def audit(d: pd.DataFrame) -> dict[str, object]:
    return {
        "rows": len(d),
        "leakage_fields_present": sorted(LEAKAGE & set(d.columns)),
        "native_suspect": sorted(SUSPECT & set(d.columns)),
        "h3_starts_posthoc": int(((d.entry_path == "3_to_4") & (d.episode_age_h == 1)).sum()),
    }


def _candidate_score(train: pd.DataFrame, col: str) -> float | None:
    p = fit(train, train, [col])
    return score(train.Crash72.astype(int).to_numpy(), p)["auc"]


def select_representations(train: pd.DataFrame) -> tuple[str, str, dict[str, float | None], dict[str, float | None]]:
    """Select Recovery/Persistence using only the current outer training fold."""
    recovery_candidates = (
        "LiveDeficit_diff1",
        "LiveDeficit_slope24",
        "burden_minus_shock24",
        "RecoveryWeakness_v1_diff1",
    )
    persistence_candidates = ("persistence_ld", "persistence_rw")
    train_p, _ = add_persistence(train, train.iloc[0:0].copy())
    recovery_scores = {col: _candidate_score(train_p, col) for col in recovery_candidates}
    persistence_scores = {col: _candidate_score(train_p, col) for col in persistence_candidates}
    best_recovery = max(recovery_scores, key=lambda c: recovery_scores[c] if recovery_scores[c] is not None else -1.0)
    best_persistence = max(persistence_scores, key=lambda c: persistence_scores[c] if persistence_scores[c] is not None else -1.0)
    return best_recovery, best_persistence, recovery_scores, persistence_scores


def make_heads(best_recovery: str, best_persistence: str) -> dict[str, Head]:
    return {
        "Hazard": Head(("hazard_score",)),
        "Burden": Head(("LiveDeficit_lag6",)),
        "Recovery": Head((best_recovery,)),
        "Persistence": Head((best_persistence,)),
        "Trajectory": Head(("SimpleShock_mean24", "hazard_score_mean24")),
    }


def run_config(train: pd.DataFrame, test: pd.DataFrame, specs: dict[str, Head]):
    train_p, test_p = add_persistence(train, test)
    oof, test_outputs, mask = crossfit_heads(train_p, test_p, specs)
    y_train = train_p.Crash72.astype(int).to_numpy()[mask]
    prediction = coordinator(oof, test_outputs, y_train)
    return score(test_p.Crash72.astype(int).to_numpy(), prediction), test_outputs


def run_order(train: pd.DataFrame, test: pd.DataFrame, order: list[str], heads: dict[str, Head]):
    admitted: dict[str, Head] = {}
    steps = []
    for name in order:
        admitted[name] = heads[name]
        metrics, outputs = run_config(train, test, admitted)
        steps.append({"added": name, "configuration": list(admitted), "metrics": metrics})
    return steps


def aggregate_stability(folds: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[float]] = {}
    for fold in folds:
        order = tuple(fold["order"])
        year = fold["year"]
        del year
        for step in fold["steps"]:
            auc = step["metrics"].get("auc")
            if auc is not None:
                groups[(json.dumps(order), step["added"])] = groups.get((json.dumps(order), step["added"]), []) + [float(auc)]
    out = []
    for (order_json, added), values in groups.items():
        out.append({
            "order": json.loads(order_json),
            "added": added,
            "auc_mean": float(np.mean(values)),
            "auc_min": float(np.min(values)),
            "auc_max": float(np.max(values)),
            "auc_spread": float(np.max(values) - np.min(values)),
        })
    return out


def main(csv: Path, out: Path | None):
    d = prepare(pd.read_csv(csv))
    audit_result = audit(d)
    if len(d) != 43848 or audit_result["h3_starts_posthoc"] != 169:
        raise ValueError(f"canonical validation failed: {audit_result}")
    if "Crash72" not in d:
        raise ValueError("Crash72 target missing")

    train23 = d[d.open_time.dt.year <= 2023].copy()
    holdout = d[d.open_time.dt.year == 2024].copy()

    hazard_audit = {
        "lineage": "SUSPECT_NATIVE_TIAMAT_DERIVED",
        "holdout_2024": score(
            holdout.Crash72.astype(int).to_numpy(),
            fit(train23, holdout, ["hazard_score"]),
        ),
        "promotion": False,
    }

    orderings = [
        ["Hazard", "Burden", "Recovery", "Persistence", "Trajectory"],
        ["Hazard", "Trajectory", "Burden", "Recovery", "Persistence"],
        ["Burden", "Recovery", "Trajectory", "Persistence", "Hazard"],
    ]

    folds = []
    representation_audits = []
    for year in (2021, 2022, 2023):
        train = d[d.open_time.dt.year < year].copy()
        test = d[d.open_time.dt.year == year].copy()
        best_recovery, best_persistence, recovery_scores, persistence_scores = select_representations(train)
        heads = make_heads(best_recovery, best_persistence)
        representation_audits.append({
            "year": year,
            "training_years": sorted(train.open_time.dt.year.unique().tolist()),
            "selected_recovery": best_recovery,
            "selected_persistence": best_persistence,
            "recovery_scores": recovery_scores,
            "persistence_scores": persistence_scores,
        })
        for order in orderings:
            folds.append({"year": year, "order": order, "steps": run_order(train, test, order, heads)})

    best_recovery, best_persistence, recovery_scores, persistence_scores = select_representations(train23)
    holdout_heads = make_heads(best_recovery, best_persistence)
    holdout_results = [{"order": order, "steps": run_order(train23, holdout, order, holdout_heads)} for order in orderings]

    permutation = []
    rng = np.random.default_rng(17)
    admitted: dict[str, Head] = {}
    train_h, hold_h = add_persistence(train23, holdout)
    first_order = orderings[0]
    for head_name in first_order:
        admitted[head_name] = holdout_heads[head_name]
        oof, test_outputs, mask = crossfit_heads(train_h, hold_h, admitted)
        y_train = train_h.Crash72.astype(int).to_numpy()[mask]
        observed_prediction = coordinator(oof, test_outputs, y_train)
        observed_auc = score(hold_h.Crash72.astype(int).to_numpy(), observed_prediction)["auc"]
        null_aucs = []
        for _ in range(200):
            shuffled = dict(test_outputs)
            shuffled[head_name] = rng.permutation(shuffled[head_name])
            null_prediction = coordinator(oof, shuffled, y_train)
            null_aucs.append(score(hold_h.Crash72.astype(int).to_numpy(), null_prediction)["auc"])
        null_aucs = [x for x in null_aucs if x is not None]
        null_p95 = float(np.quantile(null_aucs, 0.95)) if null_aucs else None
        permutation.append({
            "added": head_name,
            "observed_auc": observed_auc,
            "null_p95_auc": null_p95,
            "separation": None if observed_auc is None or null_p95 is None else float(observed_auc - null_p95),
            "n_permutations": len(null_aucs),
        })

    payload = {
        "court": "HYDRA_HEAD_CONDITIONAL_ABLATION_V2",
        "audit": audit_result,
        "target": "Crash72 for every configuration",
        "hazard_audit": hazard_audit,
        "walk_forward_representation_selection": representation_audits,
        "frozen_2024_representation_selection": {
            "training_years": [2020, 2021, 2022, 2023],
            "selected_recovery": best_recovery,
            "selected_persistence": best_persistence,
            "recovery_scores": recovery_scores,
            "persistence_scores": persistence_scores,
        },
        "walk_forward": folds,
        "stability": aggregate_stability(folds),
        "holdout_2024": holdout_results,
        "newest_head_permutation": permutation,
        "decision_rule": "V2 lock: PROMOTE/MERGE/REWORK/REJECT/HOLD only after all preregistered gates.",
        "integrity_note": "Recovery/Persistence selection is sealed to each outer training fold; 2024 is untouched by discovery; persistence state carries across each train/test boundary using train-learned thresholds.",
    }
    if out:
        out.write_text(json.dumps(payload, indent=2, default=str))
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    main(args.csv, args.out)
