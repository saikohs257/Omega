"""HYDRA Crash72 Guard-Surface Court V1.

Goal: discriminate a scalar/additive explanation from an interacting guard surface
using only causal-at-row features derived from the canonical spine.

The canonical CSV is never modified. Relative recovery is reconstructed at runtime
from RecoveryWeakness_v1 and LiveDeficit using the same prior-row construction used
by the frozen relative-recovery court.

Discovery/training: 2020-2023.
Holdout: 2024.

Models:
  additive  = Hazard + Burden + RelativeRecovery
  pairwise  = additive + all 2-way interactions
  surface   = additive + all 2-way + 3-way interaction

A second court fits the surface separately within each entry path. This asks whether
one shared guard surface explains 3->4, 2->4 and 0->4, or whether the controller is
path-conditioned (hysteretic).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from hydra_relative_recovery_court_v1 import history

DISCOVERY_YEARS = (2020, 2021, 2022, 2023)
HOLDOUT_YEAR = 2024
PATHS = ("3_to_4", "2_to_4", "0_to_4")
BASE = ["hazard", "burden", "rr"]


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    two = np.unique(y).size == 2
    return {
        "n": int(y.size),
        "events": int(y.sum()),
        "prevalence": float(y.mean()) if y.size else None,
        "auc": float(roc_auc_score(y, p)) if two else None,
        "pr_auc": float(average_precision_score(y, p)) if two else None,
        "brier": float(brier_score_loss(y, p)) if y.size else None,
        "logloss": float(log_loss(y, p, labels=[0, 1])) if y.size else None,
        "mean_prediction": float(p.mean()) if p.size else None,
    }


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    d = history(raw).copy()
    # All three axes are known strictly before the prediction row.
    d["hazard"] = pd.to_numeric(d["hazard_l1"], errors="coerce")
    d["burden"] = pd.to_numeric(d["burden_l1"], errors="coerce")
    d["rr"] = pd.to_numeric(d["recovery_l1"], errors="coerce") - d["burden_l1"]
    # Extreme burden relative to recent excitation is an optional structural axis.
    d["burden_minus_shock"] = d["burden_l1"] - d["shock_m24"]
    return d


def design(d: pd.DataFrame, kind: str) -> pd.DataFrame:
    x = pd.DataFrame({"hazard": d["hazard"], "burden": d["burden"], "rr": d["rr"]})
    if kind in {"pairwise", "surface"}:
        x["hazard_x_burden"] = x.hazard * x.burden
        x["hazard_x_rr"] = x.hazard * x.rr
        x["burden_x_rr"] = x.burden * x.rr
    if kind == "surface":
        x["hazard_x_burden_x_rr"] = x.hazard * x.burden * x.rr
    return x


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, kind: str) -> np.ndarray:
    xtr = design(train, kind).astype(float)
    xte = design(test, kind).astype(float)
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced", C=0.5, solver="liblinear"),
    )
    model.fit(xtr, train["target"].astype(int))
    return model.predict_proba(xte)[:, 1]


def path_counts(d: pd.DataFrame) -> dict:
    return {p: int((d["entry_path"] == p).sum()) for p in PATHS}


def threshold_surface(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    """Shared 2x2x2 guard surface using train medians only."""
    cuts = {}
    for c in ("hazard", "burden", "rr"):
        cuts[c] = float(pd.to_numeric(train[c], errors="coerce").median())
    def label(frame: pd.DataFrame) -> pd.Series:
        return (
            (frame.hazard >= cuts["hazard"]).astype(int).astype(str)
            + "_" + (frame.burden >= cuts["burden"]).astype(int).astype(str)
            + "_" + (frame.rr >= cuts["rr"]).astype(int).astype(str)
        )
    q = label(test)
    rows = []
    for cell in sorted(q.dropna().unique()):
        m = q == cell
        rows.append({
            "cell": cell,
            "n": int(m.sum()),
            "crash72_events": int(test.loc[m, "target"].sum()),
            "crash72_rate": float(test.loc[m, "target"].mean()) if m.any() else None,
            "3_to_4_events": int(((test.entry_path == "3_to_4") & m & test.target.eq(1)).sum()),
            "2_to_4_events": int(((test.entry_path == "2_to_4") & m & test.target.eq(1)).sum()),
            "0_to_4_events": int(((test.entry_path == "0_to_4") & m & test.target.eq(1)).sum()),
        })
    return {"median_cuts_train": cuts, "cells": rows}


def main(csv: Path, out: Path) -> None:
    raw = pd.read_csv(csv)
    assert len(raw) == 43848, f"canonical row count changed: {len(raw)}"
    d = build_features(raw)
    d["target"] = pd.to_numeric(d["Crash72"], errors="coerce").fillna(0).astype(int)
    d["entry_path"] = d["entry_path"].astype(str)

    train = d[d.open_time.dt.year.isin(DISCOVERY_YEARS)].copy()
    test = d[d.open_time.dt.year.eq(HOLDOUT_YEAR)].copy()

    results = {}
    for kind in ("additive", "pairwise", "surface"):
        p = fit_predict(train, test, kind)
        results[kind] = metrics(test.target.to_numpy(), p)
        results[kind]["delta_auc_vs_additive"] = (
            None if results["additive"]["auc"] is None or results[kind]["auc"] is None
            else float(results[kind]["auc"] - results["additive"]["auc"])
        )

    shared_surface = threshold_surface(train, test)

    path_results = {}
    for path in PATHS:
        tr = train[train.entry_path.eq(path)].copy()
        te = test[test.entry_path.eq(path)].copy()
        row = {"train_n": int(len(tr)), "holdout_n": int(len(te)), "train_events": int(tr.target.sum()), "holdout_events": int(te.target.sum())}
        if tr.target.nunique() == 2 and not te.empty:
            for kind in ("additive", "pairwise", "surface"):
                p = fit_predict(tr, te, kind)
                row[kind] = metrics(te.target.to_numpy(), p)
        else:
            row["note"] = "insufficient two-class training data or empty holdout"
        path_results[path] = row

    # A direct discriminating statistic: does the surface gain survive within paths?
    shared_gain = {}
    for path in PATHS:
        tr = train[train.entry_path.eq(path)].copy()
        te = test[test.entry_path.eq(path)].copy()
        if tr.target.nunique() == 2 and te.target.nunique() == 2:
            a = metrics(te.target.to_numpy(), fit_predict(tr, te, "additive"))
            s = metrics(te.target.to_numpy(), fit_predict(tr, te, "surface"))
            shared_gain[path] = {
                "additive_auc": a["auc"],
                "surface_auc": s["auc"],
                "delta_auc": float(s["auc"] - a["auc"]),
            }
        else:
            shared_gain[path] = None

    payload = {
        "experiment": "hydra_crash72_guard_surface_court_v1",
        "hypothesis": "Crash72 is better described by an interacting hazard/burden/relative-recovery guard surface than by an additive scalar score",
        "canonical_rows": int(len(raw)),
        "discovery_years": list(DISCOVERY_YEARS),
        "holdout_year": HOLDOUT_YEAR,
        "path_counts_all": path_counts(d),
        "model_holdout_2024": results,
        "shared_threshold_surface": shared_surface,
        "path_conditioned": path_results,
        "path_conditioned_surface_gain": shared_gain,
        "python": platform.python_version(),
    }
    out.write_text(json.dumps(payload, indent=2, allow_nan=False))
    print(json.dumps(payload, indent=2, allow_nan=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
