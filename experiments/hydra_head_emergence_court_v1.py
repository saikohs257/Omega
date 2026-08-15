"""HYDRA Head Emergence Court V1 — job-specific, leakage-safe.

This court discovers a representation for each head independently rather than
assuming the current five-head architecture is correct.

Primary objectives:
  hazard      -> ranking/separation
  burden      -> probability quality
  recovery    -> separation + temporal stability
  trajectory  -> transition separation
  persistence -> incremental information beyond hazard

Secondary metrics are always reported: ROC AUC, PR AUC, Brier, log loss,
calibration MAE, and balanced accuracy.

Selection is confined to 2020-2023 discovery years. 2024 is frozen and
reported only after selection. Candidate feature transforms are causal lags,
rolling summaries, deltas, and episode-tempo counters. Final labels and
future fields are forbidden as predictors.

The design is inspired by floating feature-selection methods and stability-
focused nested-validation practice: feature selection belongs inside the
training/discovery process, not on the final holdout. Brier is treated as a
probabilistic score rather than a pure calibration metric; the court reports
calibration error separately. See the companion design note for references.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

TARGET = "Crash72"
FORBIDDEN = {
    TARGET, "episode_type", "duration_bucket", "entry_path", "regime_30d",
    "hazard_bucket", "recovery_gate", "open_time", "close",
}
DISCOVERY_YEARS = (2020, 2021, 2022, 2023)
HOLDOUT_YEAR = 2024
SEARCH_SAMPLE_PER_YEAR = 1800


@dataclass(frozen=True)
class Metrics:
    auc: float
    pr_auc: float
    brier: float
    logloss: float
    calibration_mae: float
    bacc: float


def metric(y: np.ndarray, p: np.ndarray) -> Metrics:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    auc = roc_auc_score(y, p) if np.unique(y).size == 2 else 0.5
    pr = average_precision_score(y, p) if np.unique(y).size == 2 else float(np.mean(y))
    bs = brier_score_loss(y, p)
    ll = log_loss(y, p, labels=[0, 1])
    frac, mean_pred = calibration_curve(y, p, n_bins=10, strategy="quantile")
    cal = float(np.mean(np.abs(frac - mean_pred))) if len(frac) else 1.0
    bacc = balanced_accuracy_score(y, p >= 0.5)
    return Metrics(float(auc), float(pr), float(bs), float(ll), float(cal), float(bacc))


def objective(m: Metrics, head: str, stability_auc: float, complexity: int, baseline_auc: float = 0.5) -> float:
    if head == "hazard":
        raw = 0.50*m.auc + 0.25*m.pr_auc + 0.15*stability_auc + 0.10*(1-m.brier)
    elif head == "burden":
        raw = 0.35*(1-m.brier) + 0.25*(1-m.calibration_mae) + 0.20*(1-min(m.logloss/2,1)) + 0.20*m.auc
    elif head == "recovery":
        raw = 0.35*m.auc + 0.25*m.pr_auc + 0.25*stability_auc + 0.15*(1-m.brier)
    elif head == "trajectory":
        raw = 0.45*m.auc + 0.25*m.pr_auc + 0.20*stability_auc + 0.10*(1-m.brier)
    elif head == "persistence":
        incremental = max(0.0, m.auc - baseline_auc)
        raw = 0.40*incremental + 0.25*stability_auc + 0.20*m.pr_auc + 0.15*(1-m.brier)
    else:
        raise ValueError(head)
    return float(raw - 0.012*max(0, complexity-1))


def make_history(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d["open_time"])
    d = d.sort_values("open_time").reset_index(drop=True)
    base = ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_raw", "hazard_score"]
    additions: dict[str, pd.Series] = {}
    for c in base:
        s = d[c].astype(float)
        for lag in (1, 3, 6, 12, 24, 48, 72):
            additions[f"{c}__lag{lag}"] = s.shift(lag)
        for w in (6, 24, 48, 72):
            prior = s.shift(1)
            additions[f"{c}__mean{w}"] = prior.rolling(w, min_periods=3).mean()
            additions[f"{c}__std{w}"] = prior.rolling(w, min_periods=3).std()
            additions[f"{c}__delta{w}"] = s - s.shift(w)
    additions["hazard__accel"] = d["hazard_score"].diff() - d["hazard_score"].diff().shift(1)
    additions["burden__accel"] = d["LiveDeficit"].diff() - d["LiveDeficit"].diff().shift(1)
    additions["recovery__delta24"] = d["RecoveryWeakness_v1"] - d["RecoveryWeakness_v1"].shift(24)
    additions["age__log"] = np.log1p(np.maximum(d["episode_age_h"].astype(float), 0.0))
    additions["age__saturation"] = np.minimum(d["episode_age_h"].astype(float) / 24.0, 1.0)
    starts = ((d["entry_path"] == "3_to_4") & (d["episode_age_h"] == 1)).astype(int)
    for w in (24, 48, 72):
        additions[f"episode_starts{w}"] = starts.shift(1).rolling(w, min_periods=1).sum()
    return pd.concat([d, pd.DataFrame(additions)], axis=1)


def pool_for_head(d: pd.DataFrame, head: str) -> list[str]:
    numeric = [c for c in d.columns if c not in FORBIDDEN and pd.api.types.is_numeric_dtype(d[c])]
    groups = {
        "hazard": [c for c in numeric if "hazard" in c.lower() or "shock" in c.lower()],
        "burden": [c for c in numeric if "livedeficit" in c.lower()],
        "recovery": [c for c in numeric if "recovery" in c.lower() or "livedeficit" in c.lower() or "shock" in c.lower()],
        "trajectory": [c for c in numeric if ("delta" in c.lower() or "accel" in c.lower() or "lag" in c.lower() or "mean" in c.lower()) and ("hazard" in c.lower() or "shock" in c.lower())],
        "persistence": [c for c in numeric if any(k in c.lower() for k in ("age", "episode_starts", "lag", "mean", "std"))],
    }
    return list(dict.fromkeys(groups[head]))


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> np.ndarray:
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=1400, class_weight="balanced", C=0.5, solver="liblinear"),
    )
    model.fit(train[cols].astype(float), train[TARGET].astype(int))
    return model.predict_proba(test[cols].astype(float))[:, 1]


def discovery_subset(d: pd.DataFrame, seed: int = 41) -> pd.DataFrame:
    parts = []
    for year in DISCOVERY_YEARS:
        part = d[d.open_time.dt.year == year]
        if len(part) > SEARCH_SAMPLE_PER_YEAR:
            part = part.sample(SEARCH_SAMPLE_PER_YEAR, random_state=seed + year)
        parts.append(part)
    return pd.concat(parts, ignore_index=True).sort_values("open_time")


def lo_year_scores(d: pd.DataFrame, cols: list[str], sample: bool = True) -> dict[int, Metrics]:
    out: dict[int, Metrics] = {}
    if sample:
        d = discovery_subset(d)
    for year in DISCOVERY_YEARS:
        tr = d[d.open_time.dt.year.isin([y for y in DISCOVERY_YEARS if y != year])]
        te = d[d.open_time.dt.year == year]
        if tr[TARGET].nunique() < 2 or te[TARGET].nunique() < 2:
            continue
        out[year] = metric(te[TARGET].to_numpy(), fit_predict(tr, te, cols))
    return out


def discovery_score(d: pd.DataFrame, cols: list[str], head: str) -> float:
    yearly = lo_year_scores(d, cols, sample=True)
    if not yearly:
        return -np.inf
    mean_auc = float(np.mean([m.auc for m in yearly.values()]))
    sample = discovery_subset(d)
    ys: list[np.ndarray] = []
    ps: list[np.ndarray] = []
    for year in DISCOVERY_YEARS:
        tr = sample[sample.open_time.dt.year.isin([y for y in DISCOVERY_YEARS if y != year])]
        te = sample[sample.open_time.dt.year == year]
        if te.empty or te[TARGET].nunique() < 2:
            continue
        ys.append(te[TARGET].to_numpy())
        ps.append(fit_predict(tr, te, cols))
    primary = metric(np.concatenate(ys), np.concatenate(ps))
    baseline_auc = 0.5
    if head == "persistence":
        baseline = lo_year_scores(d, ["hazard_score"], sample=True)
        baseline_auc = float(np.mean([m.auc for m in baseline.values()]))
    return objective(primary, head, mean_auc, len(cols), baseline_auc)


def select_head(d: pd.DataFrame, head: str, shortlist_n: int = 8) -> tuple[list[str], list[tuple[list[str], float]]]:
    pool = pool_for_head(d, head)
    ranked = sorted(((discovery_score(d, [c], head), c) for c in pool), reverse=True)
    shortlist = [c for _, c in ranked[:shortlist_n]]
    chosen: list[str] = []
    remaining = set(shortlist)
    history: list[tuple[list[str], float]] = []
    current = -np.inf

    while remaining and len(chosen) < 4:
        trials = [(discovery_score(d, chosen + [c], head), c) for c in sorted(remaining)]
        best, feat = max(trials)
        if chosen and best < current + 0.003:
            break
        chosen.append(feat)
        remaining.remove(feat)
        current = best
        history.append((chosen.copy(), current))

        while len(chosen) > 1:
            drops = []
            for c in chosen:
                cand = [x for x in chosen if x != c]
                drops.append((discovery_score(d, cand, head), c, cand))
            best_drop, dropped, cand = max(drops)
            if best_drop >= current + 0.003:
                chosen = cand
                remaining.add(dropped)
                current = best_drop
                history.append((chosen.copy(), current))
            else:
                break
    return chosen, history


def evaluate_holdout(d: pd.DataFrame, cols: list[str]) -> Metrics:
    tr = d[d.open_time.dt.year.isin(DISCOVERY_YEARS)]
    te = d[d.open_time.dt.year == HOLDOUT_YEAR]
    return metric(te[TARGET].to_numpy(), fit_predict(tr, te, cols))


def permutation_holdout(d: pd.DataFrame, cols: list[str], n: int = 100, seed: int = 123) -> dict[str, float]:
    tr = d[d.open_time.dt.year.isin(DISCOVERY_YEARS)]
    te = d[d.open_time.dt.year == HOLDOUT_YEAR].copy()
    p = fit_predict(tr, te, cols)
    y = te[TARGET].to_numpy()
    observed = roc_auc_score(y, p)
    rng = np.random.default_rng(seed)
    null = [roc_auc_score(rng.permutation(y), p) for _ in range(n)]
    return {
        "observed_auc": float(observed),
        "null_mean_auc": float(np.mean(null)),
        "null_p95_auc": float(np.quantile(null, 0.95)),
        "separation": float(observed - np.quantile(null, 0.95)),
    }


def main(csv: Path, out: Path | None) -> None:
    raw = pd.read_csv(csv)
    d = make_history(raw)
    print(f"rows={len(raw)}")
    print(f"years={d.open_time.dt.year.value_counts().sort_index().to_dict()}")
    print("Discovery=2020-2023; Holdout=2024; selection never touches 2024.")
    print("Forbidden predictors: episode_type, duration_bucket, entry_path, recovery_gate, regime labels, Crash72.")

    results = []
    for head in ("hazard", "burden", "recovery", "trajectory", "persistence"):
        chosen, history = select_head(d, head)
        hold = evaluate_holdout(d, chosen)
        perm = permutation_holdout(d, chosen)
        walk = lo_year_scores(d, chosen, sample=False)
        result = {
            "head": head,
            "chosen": chosen,
            "holdout_2024": asdict(hold),
            "walk_forward": {str(k): asdict(v) for k, v in walk.items()},
            "mean_discovery_auc": float(np.mean([m.auc for m in walk.values()])),
            "worst_discovery_auc": float(np.min([m.auc for m in walk.values()])),
            "permutation_holdout": perm,
            "selection_path": [{"features": f, "score": s} for f, s in history],
        }
        results.append(result)
        print(f"\n[{head.upper()}] chosen={chosen}")
        print("2024", asdict(hold))
        print("discovery AUC mean/worst", result["mean_discovery_auc"], result["worst_discovery_auc"])
        print("permutation", perm)

    if out:
        out.write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    main(args.csv, args.out)
