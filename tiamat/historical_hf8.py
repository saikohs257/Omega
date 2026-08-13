"""Recovered historical HF8/TIAMAT machinery (research-only).

This module preserves the recovered historical timing seats and state-building
chain without claiming to recreate the missing native LiveDeficit generator.
It consumes historical primitive fields when they already exist in the input
spine, then reconstructs admission, entry lineage, TheHinge run state, age,
Hinge, and the promoted V41E admission gate.

NOT canonical runtime. Do not import this from the live engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd


ACTIVE_REQUIRED = ("hazard_raw", "hazard_score", "LiveDeficit", "SimpleShock")
ENTRY_REQUIRED = ACTIVE_REQUIRED
HINGE_REQUIRED = ("tightness_z", "age_z")


@dataclass(frozen=True)
class HistoricalState:
    active: bool
    entry_path: str
    episode_type: str
    run_age_h: float | None


def _require(frame: pd.DataFrame, cols: tuple[str, ...]) -> None:
    missing = [c for c in cols if c not in frame.columns]
    if missing:
        raise ValueError(f"missing historical HF8 fields: {missing}")


def recovered_active_mask(frame: pd.DataFrame) -> pd.Series:
    """Exact recovered active/admission edge machine on the historical spine."""
    _require(frame, ACTIVE_REQUIRED)
    raw_d1 = pd.to_numeric(frame["hazard_raw"], errors="coerce").diff()
    score_d1 = pd.to_numeric(frame["hazard_score"], errors="coerce").diff()
    ld = pd.to_numeric(frame["LiveDeficit"], errors="coerce")
    shock = pd.to_numeric(frame["SimpleShock"], errors="coerce")
    start = ((raw_d1 > 1.00) & (ld > 0.85) & (shock > 0.50)).fillna(False)
    exit_ = ((score_d1 <= -0.17) & (shock.shift(6) > 0.33)).fillna(False)
    out: list[bool] = []
    active = False
    for i in range(len(frame)):
        if active and bool(exit_.iloc[i]):
            active = False
        elif not active and bool(start.iloc[i]):
            active = True
        out.append(active)
    return pd.Series(out, index=frame.index, name="active_recovered")


def entry_path_at_start(prev_live_deficit: float, prev_simple_shock: float) -> str:
    if pd.isna(prev_live_deficit):
        return "none"
    if prev_live_deficit <= 0.70:
        path = "0_to_4"
    elif prev_live_deficit <= 0.85:
        path = "2_to_4"
    else:
        path = "3_to_4"
    if path == "3_to_4" and pd.notna(prev_simple_shock) and prev_simple_shock > 0.50:
        return "2_to_4"
    return path


def rebuild_entry_path(frame: pd.DataFrame, active: pd.Series | None = None) -> pd.Series:
    _require(frame, ENTRY_REQUIRED)
    if active is None:
        active = recovered_active_mask(frame)
    active = pd.Series(active, index=frame.index).fillna(False).astype(bool)
    starts = active & ~active.shift(fill_value=False)
    prev_ld = pd.to_numeric(frame["LiveDeficit"], errors="coerce").shift(1)
    prev_shock = pd.to_numeric(frame["SimpleShock"], errors="coerce").shift(1)
    out: list[str] = []
    current = "none"
    for i in range(len(frame)):
        if not bool(active.iloc[i]):
            current = "none"
        elif bool(starts.iloc[i]):
            current = entry_path_at_start(prev_ld.iloc[i], prev_shock.iloc[i])
        out.append(current)
    return pd.Series(out, index=frame.index, name="entry_path_recovered")


def _gate_3to4(ts: pd.Timestamp, hourly: pd.DataFrame, daily: pd.DataFrame, starts: pd.DatetimeIndex) -> str:
    hs = float(hourly.loc[ts, "hazard_score"]) if pd.notna(hourly.loc[ts, "hazard_score"]) else 0.85
    shock = float(hourly.loc[ts, "SimpleShock"]) if pd.notna(hourly.loc[ts, "SimpleShock"]) else 0.75
    if hs >= 0.966:
        return "trapped"
    pre = hourly.loc[:ts, "hazard_score"].to_numpy()[-7:-1]
    peak_6h = float(np.nanmax(pre)) if len(pre) else 0.5
    date = ts.normalize()
    vr = []
    for lag in range(4, -1, -1):
        d = date - pd.Timedelta(days=lag)
        if d in daily.index and pd.notna(daily.loc[d, "volratio"]):
            vr.append(float(daily.loc[d, "volratio"]))
    vr_exp = (vr[-1] - min(vr)) / min(vr) if len(vr) >= 3 and min(vr) > 0 else 0.5
    n24 = int(((starts >= ts - pd.Timedelta(hours=24)) & (starts < ts)).sum())
    n48 = int(((starts >= ts - pd.Timedelta(hours=48)) & (starts < ts)).sum())
    score = int(shock <= 0.70) * 2
    score += int(vr_exp < 0.40)
    score += int(peak_6h > 0.80)
    score -= int(shock > 0.80)
    score -= int(vr_exp > 0.80)
    if n24 >= 3 and shock <= 0.70:
        score += 4
    elif n48 >= 4 and shock <= 0.70:
        score += 3
    return "phasic" if score >= 1 else "mixed"


def classify_entry(path: str, ts: pd.Timestamp, hourly: pd.DataFrame, daily: pd.DataFrame, starts: pd.DatetimeIndex) -> str:
    hs = float(hourly.loc[ts, "hazard_score"]) if pd.notna(hourly.loc[ts, "hazard_score"]) else 0.85
    ld = float(hourly.loc[ts, "LiveDeficit"]) if pd.notna(hourly.loc[ts, "LiveDeficit"]) else 0.88
    if path == "3_to_4":
        return _gate_3to4(ts, hourly, daily, starts)
    if path == "2_to_4":
        if hs >= 0.88 and ld >= 0.90:
            return "trapped"
        if hs >= 0.95:
            return "trapped"
        return "mixed"
    if path == "0_to_4":
        return "trapped" if hs >= 0.92 else "mixed"
    return "mixed"


def build_thehinge(hourly: pd.DataFrame, daily: pd.DataFrame, active: pd.Series | None = None, entry: pd.Series | None = None) -> pd.DataFrame:
    """Reconstruct episode_type and run_age_h with the historical gate order."""
    _require(hourly, ACTIVE_REQUIRED)
    if active is None:
        active = recovered_active_mask(hourly)
    if entry is None:
        entry = rebuild_entry_path(hourly, active)
    active = pd.Series(active, index=hourly.index).astype(bool)
    entry = pd.Series(entry, index=hourly.index)
    starts = hourly.index[active & ~active.shift(fill_value=False)]
    ep = np.full(len(hourly), "none", dtype=object)
    age = np.full(len(hourly), np.nan)
    running = False
    run_age = 0
    current_type = "none"
    entry_values = entry.to_numpy()
    for i, ts in enumerate(hourly.index):
        if not bool(active.iloc[i]):
            running = False
            run_age = 0
            current_type = "none"
        elif not running:
            running = True
            run_age = 1
            current_path = entry_values[i] if entry_values[i] != "none" else "2_to_4"
            current_type = classify_entry(current_path, ts, hourly, daily, pd.DatetimeIndex(starts))
        else:
            run_age += 1
            if current_type == "phasic" and run_age > 8:
                current_type = "trapped"
        if running:
            ep[i] = current_type
            age[i] = float(run_age)
    return pd.DataFrame({"episode_type": ep, "run_age_h": age}, index=hourly.index)


def build_age_chain(run_age_h: pd.Series, episode_type: pd.Series) -> pd.DataFrame:
    qualified = run_age_h.where(episode_type != "none")
    day_max = qualified.resample("1D").max()
    age_7d = day_max.rolling(7, min_periods=3).mean()
    mu = age_7d.rolling(180, min_periods=30).mean()
    sd = age_7d.rolling(180, min_periods=30).std(ddof=1)
    age_z = (age_7d - mu) / sd.replace(0, np.nan)
    return pd.DataFrame({"day_max_age_h": day_max, "age_7d": age_7d, "age_z": age_z})


def compute_hinge(tightness_z: pd.Series, age_z: pd.Series) -> pd.Series:
    combined = pd.DataFrame({"tightness_z": tightness_z, "age_z": age_z})
    return 0.70 * combined["tightness_z"] + 0.30 * combined["age_z"]


def promote_v41e(row: Mapping[str, Any]) -> dict[str, Any]:
    """Recovered promoted V41E gate, kept research-only here."""
    required = ("hazard_raw_0_4h_max_from_l1", "SimpleShock_0_4h_max_from_l1", "prev_active_exit_SimpleShock")
    missing = [k for k in required if k not in row]
    if missing:
        raise KeyError(f"missing V41E inputs: {missing}")
    h = float(row["hazard_raw_0_4h_max_from_l1"])
    s = float(row["SimpleShock_0_4h_max_from_l1"])
    p = float(row["prev_active_exit_SimpleShock"])
    if h <= 4.650000095367432:
        selected = s > 0.6608663201332092
        branch = "low_hazard"
    elif s <= 0.8352259397506714:
        selected = h <= 5.75
        branch = "mid_shock"
    else:
        selected = p <= 0.5060606896877289
        branch = "high_shock"
    return {"selected": bool(selected), "posture": "short_watch" if selected else "not_short_watch", "branch": branch, "authority": "canonical_admission_gate", "version": "v41e_gate_v1"}
