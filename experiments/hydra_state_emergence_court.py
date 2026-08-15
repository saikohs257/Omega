"""HYDRA State Emergence Court V1.

Purpose: discover a small, stable set of causal state variables by adding and
removing candidate history features, rather than assuming Hydra's architecture.

The court uses:
- causal lag/rolling transforms only;
- H3 starts selected by live entry_path/episode_age, never as a predictor;
- 2020-2023 for discovery;
- untouched 2024 for the primary holdout;
- forward floating addition and backward floating removal;
- permutation controls;
- walk-forward stability checks.

Inspired by floating feature-search methods (Pudil et al., 1994) and stability-
selection ideas: selection is useful only when a compact set survives held-out
and permutation tests. This is an experiment, not canonical TIAMAT logic.
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

BASE = [
    "SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "episode_age_h",
    "hazard_raw", "hazard_score", "h3_prev24", "h3_prev48", "h3_gap",
]


def add_causal_history(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d["open_time"])
    d = d.sort_values("open_time").reset_index(drop=True)
    for col in ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_score", "hazard_raw"]:
        s = d[col].astype(float)
        for lag in (1, 3, 6, 12, 24, 48):
            d[f"{col}_l{lag}"] = s.shift(lag)
        prior = s.shift(1)
        for w in (6, 24, 48):
            d[f"{col}_m{w}"] = prior.rolling(w, min_periods=1).mean()
            d[f"{col}_d{w}"] = s - s.shift(w)
    starts = ((d["entry_path"] == "3_to_4") & (d["episode_age_h"] == 1)).astype(int)
    d["h3_prev24"] = starts.shift(1).rolling(24, min_periods=1).sum()
    d["h3_prev48"] = starts.shift(1).rolling(48, min_periods=1).sum()
    last = -1
    gap = []
    for i, flag in enumerate(starts):
        gap.append(np.nan if last < 0 else i - last)
        if i > 0 and starts.iloc[i - 1]:
            last = i - 1
    d["h3_gap"] = gap
    return d


def h3_table(d: pd.DataFrame) -> pd.DataFrame:
    h = d[(d["entry_path"] == "3_to_4") & (d["episode_age_h"] == 1)].copy()
    h["year"] = h["open_time"].dt.year
    h["y"] = h["Crash72"].astype(int)
    return h


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> np.ndarray:
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=1200, class_weight="balanced", C=0.5, solver="liblinear"),
    )
    model.fit(train[cols].astype(float), train["y"])
    return model.predict_proba(test[cols].astype(float))[:, 1]


def cv_score(h: pd.DataFrame, cols: list[str]) -> tuple[float, float]:
    data = h[h["year"] < 2024].reset_index(drop=True)
    skf = StratifiedKFold(4, shuffle=True, random_state=17)
    pred = np.zeros(len(data))
    for tr, te in skf.split(data, data["y"]):
        pred[te] = fit_predict(data.iloc[tr], data.iloc[te], cols)
    return roc_auc_score(data["y"], pred), balanced_accuracy_score(data["y"], pred >= 0.5)


def holdout(h: pd.DataFrame, cols: list[str]) -> tuple[float, float]:
    train = h[h["year"] < 2024]
    test = h[h["year"] == 2024]
    pred = fit_predict(train, test, cols)
    return roc_auc_score(test["y"], pred), balanced_accuracy_score(test["y"], pred >= 0.5)


def forward_floating(h: pd.DataFrame, pool: list[str]) -> list[tuple[list[str], float, float]]:
    chosen: list[str] = []
    remaining = set(pool)
    current = 0.0
    history = []
    for _ in range(6):
        trials = []
        for feat in sorted(remaining):
            a, b = cv_score(h, chosen + [feat])
            trials.append((b, a, feat))
        trials.sort(reverse=True)
        b, a, feat = trials[0]
        if chosen and b <= current + 0.003:
            break
        chosen.append(feat)
        remaining.remove(feat)
        current = b
        # Floating backtracking.
        while len(chosen) > 1:
            candidates = []
            for drop in chosen:
                cand = [x for x in chosen if x != drop]
                aa, bb = cv_score(h, cand)
                candidates.append((bb, aa, drop, cand))
            candidates.sort(reverse=True)
            bb, aa, drop, cand = candidates[0]
            if bb <= current + 0.003:
                break
            chosen = cand
            remaining.add(drop)
            current = bb
        history.append((chosen.copy(), a, current))
    return history


def backward_floating(h: pd.DataFrame, pool: list[str]) -> list[tuple[list[str], float, float, str]]:
    chosen = pool.copy()
    auc, bacc = cv_score(h, chosen)
    history = []
    while len(chosen) > 1:
        trials = []
        for drop in chosen:
            cand = [x for x in chosen if x != drop]
            aa, bb = cv_score(h, cand)
            trials.append((bb, aa, drop, cand))
        trials.sort(reverse=True)
        bb, aa, drop, cand = trials[0]
        if bb < bacc - 0.003:
            break
        chosen, auc, bacc = cand, aa, bb
        history.append((chosen.copy(), auc, bacc, drop))
    return history


def permutation_control(h: pd.DataFrame, cols: list[str], n: int = 100, seed: int = 9) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    observed = cv_score(h, cols)[1]
    null = []
    original = h["y"].to_numpy().copy()
    for _ in range(n):
        h["y"] = rng.permutation(original)
        null.append(cv_score(h, cols)[1])
    h["y"] = original
    return observed, float(np.mean(null)), float(np.quantile(null, 0.95))


def main(csv_path: Path) -> None:
    full = pd.read_csv(csv_path)
    d = add_causal_history(full)
    h = h3_table(d)
    pool = [c for c in BASE if c in h.columns]
    pool += [c for c in h.columns if "_l" in c or "_m" in c or "_d" in c]
    pool = list(dict.fromkeys(pool))

    print(f"rows={len(full)} h3_starts={len(h)} positives={int(h.y.sum())}")
    print(f"years={h.year.value_counts().sort_index().to_dict()}")
    print(f"candidate_count={len(pool)}")

    # Stable pre-screen on discovery period.
    uni = []
    for col in pool:
        a, b = cv_score(h, [col])
        uni.append((a, b, col))
    uni.sort(reverse=True)
    top = [x[2] for x in uni[:12]]
    print("TOP_UNIVARIATE")
    for a, b, c in uni[:12]:
        print(c, round(a, 4), round(b, 4))

    fwd = forward_floating(h, top)
    print("FORWARD_FLOATING")
    for cols, a, b in fwd:
        print(cols, round(a, 4), round(b, 4))
    forward_best = fwd[-1][0] if fwd else [top[0]]

    bwd = backward_floating(h, top)
    print("BACKWARD_FLOATING")
    for cols, a, b, drop in bwd:
        print("removed", drop, cols, round(a, 4), round(b, 4))
    backward_best = bwd[-1][0] if bwd else top

    for label, cols in [("forward", forward_best), ("backward", backward_best), ("top12", top)]:
        a, b = holdout(h, cols)
        print(f"HOLDOUT2024 {label} cols={cols} auc={a:.4f} bacc={b:.4f}")

    print("PERMUTATION", permutation_control(h, forward_best))

    print("WALK_FORWARD")
    for year in (2021, 2022, 2023, 2024):
        tr = h[h.year < year]
        te = h[h.year == year]
        if te.y.nunique() < 2:
            print(year, "single_class_test", te.y.value_counts().to_dict())
            continue
        p = fit_predict(tr, te, forward_best)
        print(year, round(roc_auc_score(te.y, p), 4), round(balanced_accuracy_score(te.y, p >= 0.5), 4))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    main(ap.parse_args().csv)
