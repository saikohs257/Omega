"""Stratified RR falsification: core Crash72 vs exception Crash72.

This court does not alter the canonical spine and reconstructs RR from strictly
pre-event source columns via hydra_relative_recovery_court_v1.history().
2024 is the frozen holdout. Core has only 12 expected cases, so core results are
reported descriptively and are not promoted by AUC alone.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score
from hydra_relative_recovery_court_v1 import history

TARGET = "Crash72"
FEATURE = "rr_recovery_minus_burden"


def safe_metrics(y, x):
    y = np.asarray(y, int); x = np.asarray(x, float)
    ok = np.isfinite(x)
    y, x = y[ok], x[ok]
    out = {"n": int(len(y)), "events": int(y.sum()) if len(y) else 0}
    if len(y) == 0:
        return out
    out["mean_feature"] = float(x.mean())
    out["median_feature"] = float(np.median(x))
    if np.unique(y).size == 2:
        out["auc"] = float(roc_auc_score(y, x))
        out["pr_auc"] = float(average_precision_score(y, x))
    else:
        out["auc"] = None; out["pr_auc"] = None
    return out


def cohort_summary(d):
    crash = pd.to_numeric(d[TARGET], errors="coerce").fillna(0).astype(int)
    age = pd.to_numeric(d["episode_age_h"], errors="coerce")
    core = (crash.eq(1) & d["entry_path"].astype(str).eq("3_to_4") & age.eq(1))
    exception = crash.eq(1) & ~core
    return core, exception


def matched_controls(d, cases):
    """Deterministic controls: same year, entry_path, and episode_age_h when possible."""
    y = pd.to_datetime(d.open_time, utc=True).dt.year
    age = pd.to_numeric(d.episode_age_h, errors="coerce")
    target = pd.to_numeric(d[TARGET], errors="coerce").fillna(0).astype(int)
    pool = d[target.eq(0)].copy()
    pool["_year"] = y[target.eq(0)].to_numpy()
    pool["_age"] = age[target.eq(0)].to_numpy()
    pool["_path"] = d.loc[target.eq(0), "entry_path"].astype(str).to_numpy()
    selected = []
    used = set()
    for idx, row in cases.iterrows():
        key = (pd.to_datetime(row.open_time, utc=True).year, str(row.entry_path), float(row.episode_age_h) if pd.notna(row.episode_age_h) else np.nan)
        cand = pool[(pool._year == key[0]) & (pool._path == key[1])]
        if pd.notna(key[2]):
            exact = cand[cand._age == key[2]]
            if not exact.empty: cand = exact
        cand = cand[~cand.index.isin(used)]
        if cand.empty:
            continue
        # deterministic nearest timestamp within the matched stratum
        ct = pd.to_datetime(cand.open_time, utc=True)
        delta = (ct - pd.to_datetime(row.open_time, utc=True)).abs().dt.total_seconds()
        pick = cand.index[int(delta.argmin())]
        used.add(pick); selected.append(pick)
    return d.loc[selected].copy()


def evaluate(d, cases, label):
    controls = matched_controls(d, cases)
    cases = cases.copy(); controls = controls.copy()
    return {
        "label": label,
        "cases": safe_metrics(np.ones(len(cases), int), cases[FEATURE]),
        "controls": safe_metrics(np.zeros(len(controls), int), controls[FEATURE]),
        "case_control": safe_metrics(np.r_[np.ones(len(cases), int), np.zeros(len(controls), int)], np.r_[cases[FEATURE], controls[FEATURE]]),
        "control_count": int(len(controls)),
        "control_shortfall": int(len(cases) - len(controls)),
    }


def main(csv: Path, out: Path):
    raw = pd.read_csv(csv)
    d = history(raw)
    assert len(raw) == 43848
    assert "rr_recovery_minus_burden" in d
    core, exception = cohort_summary(d)
    y = pd.to_datetime(d.open_time, utc=True).dt.year
    hold = y.eq(2024)
    result = {
        "experiment": "hydra_core_exception_rr_falsification_v1",
        "canonical_rows": int(len(raw)),
        "feature": FEATURE,
        "information_rule": "history() only; all RR inputs are shifted before prediction row",
        "taxonomy_counts_all_years": {"core": int(core.sum()), "exception": int(exception.sum()), "native_crash72": int(pd.to_numeric(d[TARGET], errors="coerce").fillna(0).sum())},
        "holdout_2024_counts": {"core": int((core & hold).sum()), "exception": int((exception & hold).sum()), "native_crash72": int((pd.to_numeric(d[TARGET], errors="coerce").fillna(0).astype(int).eq(1) & hold).sum())},
        "all_years": {}, "holdout_2024": {}
    }
    for mask, label in [(core, "core"), (exception, "exception")]:
        result["all_years"][label] = evaluate(d, d.loc[mask], label)
        hm = mask & hold
        result["holdout_2024"][label] = evaluate(d.loc[hold], d.loc[hm], label)
    result["guard"] = "Core has only 12 expected cases; no promotion decision is made from core AUC."
    out.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv", type=Path); ap.add_argument("--out", type=Path, required=True); a = ap.parse_args(); main(a.csv, a.out)
