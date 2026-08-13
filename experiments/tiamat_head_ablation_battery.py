from __future__ import annotations

"""TIAMAT head-local ablation / contamination battery.

Research-only. The common target is survival of the next 15 contiguous hourly
observations inside the active historical run. This is intentionally distinct
from the historical head-local targets recorded elsewhere.

Set TIAMAT_LAYER1_CSV to the canonical 2020-2024 Layer-1 CSV. The default path
is suitable for the local archaeological workspace.
"""

# CI touch: keep the scientific environment and head-court workflow aligned.

import json
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path(os.environ.get("TIAMAT_LAYER1_CSV", "data/layer1_structured_hazard_arm_timeseries.csv"))
OUT = Path(os.environ.get("TIAMAT_HEAD_BATTERY_OUT", "tiamat_head_ablation_battery_results.json"))

HEADS = {"H0": "0_to_4", "H2": "2_to_4", "H3": "3_to_4", "H4": "4_to_4"}
FEATURES = ["LiveDeficit", "hazard_raw", "SimpleShock", "RecoveryWeakness_v1", "episode_age_h"]
CORE = ["LiveDeficit", "hazard_raw", "SimpleShock", "RecoveryWeakness_v1"]
YEARS = [2020, 2021, 2022, 2023, 2024]


def metric(fn: callable, y: pd.Series, score: np.ndarray) -> float:
    values = np.asarray(y, dtype=float)
    if np.unique(values).size < 2:
        return float("nan")
    return float(fn(values, score))


def build_target(df: pd.DataFrame, hours: int = 15) -> pd.Series:
    active = df["entry_path"].ne("none").to_numpy()
    times = df["open_time"].to_numpy()
    target = np.full(len(df), np.nan)
    for i in range(len(df) - hours):
        if not active[i]:
            continue
        expected = times[i] + np.arange(1, hours + 1).astype("timedelta64[h]")
        if not np.array_equal(times[i + 1 : i + hours + 1], expected):
            continue
        target[i] = float(np.all(active[i + 1 : i + hours + 1]))
    return pd.Series(target, index=df.index, name="survive15")


def make_model(features: Iterable[str]) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("lr", LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs")),
        ]
    )


def fit_score(train: pd.DataFrame, test: pd.DataFrame, features: list[str]):
    model = make_model(features)
    model.fit(train[features], train["survive15"])
    return model.predict_proba(test[features])[:, 1], model


def assign_seats(df: pd.DataFrame) -> pd.DataFrame:
    active = df["entry_path"].ne("none")
    previous_active = active.shift(1, fill_value=False)
    episode_start = active & ~previous_active
    df = df.copy()
    df["seat"] = None
    for head, path in HEADS.items():
        if head != "H4":
            df.loc[episode_start & df["entry_path"].eq(path), "seat"] = head
    df.loc[active & ~episode_start, "seat"] = "H4"
    return df


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(f"historical Layer-1 CSV not found: {DATA}")

    df = pd.read_csv(DATA, parse_dates=["open_time"]).sort_values("open_time").reset_index(drop=True)
    df["year"] = df["open_time"].dt.year
    df["survive15"] = build_target(df)
    df = assign_seats(df)
    base = df[df["seat"].notna() & df["survive15"].notna()].copy()

    result = {
        "dataset": str(DATA),
        "rows": int(len(df)),
        "active_rows": int(df["entry_path"].ne("none").sum()),
        "eligible_rows": int(len(base)),
        "target": "survive the next 15 contiguous hourly observations while remaining active",
        "heads": {},
        "cross_head": {},
        "leave_year_out": {},
        "universal_vs_native": {},
        "classification": {
            "status": "research_only",
            "native_local_targets": "not reproduced by this battery; see TIAMAT_HEAD_MECHANISM_COURT_V1",
            "causality": "permutation and ablation are sensitivity evidence, not causal proof",
            "authority": "no runtime promotion",
        },
    }

    rng = np.random.default_rng(20260813)

    for head, path in HEADS.items():
        g = base[base["seat"].eq(head)].copy()
        entry = {"path": path, "n": int(len(g)), "positive_rate": float(g["survive15"].mean()), "ablations": {}, "permutation": {}}
        if len(g) >= 8 and g["survive15"].nunique() == 2:
            score, model = fit_score(g, g, FEATURES)
            entry["full_in_sample"] = {"auc": metric(roc_auc_score, g["survive15"], score), "ap": metric(average_precision_score, g["survive15"], score)}
            variants = {
                "core": CORE,
                "no_LiveDeficit": [f for f in FEATURES if f != "LiveDeficit"],
                "no_hazard_raw": [f for f in FEATURES if f != "hazard_raw"],
                "no_SimpleShock": [f for f in FEATURES if f != "SimpleShock"],
                "no_RecoveryWeakness": [f for f in FEATURES if f != "RecoveryWeakness_v1"],
                "no_episode_age": [f for f in FEATURES if f != "episode_age_h"],
            }
            for name, feats in variants.items():
                s, _ = fit_score(g, g, feats)
                entry["ablations"][name] = {"auc": metric(roc_auc_score, g["survive15"], s), "ap": metric(average_precision_score, g["survive15"], s), "features": feats}
            full_auc = metric(roc_auc_score, g["survive15"], score)
            for feature in FEATURES:
                shuffled = g[FEATURES].copy()
                shuffled[feature] = rng.permutation(shuffled[feature].to_numpy())
                s = model.predict_proba(shuffled)[:, 1]
                shuffled_auc = metric(roc_auc_score, g["survive15"], s)
                entry["permutation"][feature] = {"auc": shuffled_auc, "delta_auc": full_auc - shuffled_auc}
        result["heads"][head] = entry

    for train_head in HEADS:
        train = base[base["seat"].eq(train_head)]
        result["cross_head"][train_head] = {}
        if len(train) < 8 or train["survive15"].nunique() != 2:
            continue
        model = make_model(FEATURES)
        model.fit(train[FEATURES], train["survive15"])
        for test_head in HEADS:
            test = base[base["seat"].eq(test_head)]
            if len(test) < 8 or test["survive15"].nunique() != 2:
                result["cross_head"][train_head][test_head] = {"auc": float("nan"), "ap": float("nan"), "n": int(len(test))}
                continue
            s = model.predict_proba(test[FEATURES])[:, 1]
            result["cross_head"][train_head][test_head] = {"auc": metric(roc_auc_score, test["survive15"], s), "ap": metric(average_precision_score, test["survive15"], s), "n": int(len(test))}

    for head in HEADS:
        g = base[base["seat"].eq(head)]
        result["leave_year_out"][head] = {}
        for year in YEARS:
            train = g[g["year"] != year]
            test = g[g["year"] == year]
            if len(train) < 12 or len(test) < 4 or train["survive15"].nunique() != 2 or test["survive15"].nunique() != 2:
                result["leave_year_out"][head][str(year)] = {"auc": float("nan"), "ap": float("nan"), "n_train": int(len(train)), "n_test": int(len(test))}
                continue
            s, _ = fit_score(train, test, FEATURES)
            result["leave_year_out"][head][str(year)] = {"auc": metric(roc_auc_score, test["survive15"], s), "ap": metric(average_precision_score, test["survive15"], s), "n_train": int(len(train)), "n_test": int(len(test))}

    universal, _ = fit_score(base, base, FEATURES)
    native = np.full(len(base), np.nan)
    for head in HEADS:
        mask = base["seat"].eq(head)
        g = base.loc[mask]
        if len(g) >= 8 and g["survive15"].nunique() == 2:
            s, _ = fit_score(g, g, FEATURES)
            native[mask.to_numpy()] = s
    keep = np.isfinite(native)
    result["universal_vs_native"] = {
        "universal_auc": metric(roc_auc_score, base.loc[keep, "survive15"], universal[keep]),
        "native_combined_auc": metric(roc_auc_score, base.loc[keep, "survive15"], native[keep]),
        "delta_auc": metric(roc_auc_score, base.loc[keep, "survive15"], native[keep]) - metric(roc_auc_score, base.loc[keep, "survive15"], universal[keep]),
        "n": int(keep.sum()),
    }

    OUT.write_text(json.dumps(result, indent=2, default=float))
    print(json.dumps(result, indent=2, default=float))


if __name__ == "__main__":
    main()
