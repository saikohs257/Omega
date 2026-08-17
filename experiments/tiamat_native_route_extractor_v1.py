"""HF9 TIAMAT native route extractor V1.1.

Three-lane semantics are enforced:
  Lane 1 = strict hourly topology physics.
  Lane 2 = episode route / lineage.
  Lane 3 = run motif / temporal shape (not emitted here).

H0/H2/H3 are episode-route heads from episode_age_h == 1 starts.
H4 is admitted ONLY from strict contiguous topology_state 4 -> 4 rows.
The extractor never infers H4 from entry_path.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED_BASE = [
    "open_time", "SimpleShock", "LiveDeficit", "hazard_raw",
    "entry_path", "episode_age_h", "regime_30d", "Crash72"
]

TOPOLOGY_ALIASES = ["topology_state", "state", "topology", "runtime_state"]

PATH_TO_HEAD = {
    "0_to_4": "H0_FalseCalmIgnition",
    "2_to_4": "H2_ResetDragRelease",
    "3_to_4": "H3_RecoveryInversion",
}

HEAD_FORMULAS = {
    "H0_FalseCalmIgnition": lambda r, ss04: float(r["SimpleShock"]) + 0.05 * float(r["hazard_raw"]),
    "H2_ResetDragRelease": lambda r, ss04: float(r["LiveDeficit"]),
    "H3_RecoveryInversion": lambda r, ss04: float(r["LiveDeficit"]) + 0.05 * float(r["hazard_raw"]) - ss04,
    "H4_CeilingTrap": lambda r, ss04: float(r["LiveDeficit"]) + 0.20 * float(r["hazard_raw"]) + 0.10 * float(r["SimpleShock"]),
}

OUTPUT_COLUMNS = [
    "episode_id","chain_id","open_time","start_time","end_time","year","regime",
    "lane","source_name","source_window","start_transition_path","episode_route",
    "strict_prev_state","strict_state","strict_adjacency_path","topology_path","tiamat_head",
    "runtime_hour_t","is_alive_at_cp15","is_long_gt21","target",
    "survive_next_1h","survive_next_3h","survive_next_6h","survive_next_12h","survive_next_24h",
    "cp15_LiveDeficit","cp15_SimpleShock","cp15_hazard_raw",
    "SimpleShock_0_4h_max_exact","hazard_raw_0_4h_max","ExitBridgeDeficit","PriorCarryDeficit",
    "raw_score",
]


def num(s):
    return pd.to_numeric(s, errors="coerce")


def choose_topology_column(d: pd.DataFrame) -> str | None:
    for c in TOPOLOGY_ALIASES:
        if c in d.columns:
            return c
    return None


def episode_rows(d: pd.DataFrame) -> pd.DataFrame:
    """Lane-2 episode route reconstruction for H0/H2/H3."""
    d = d.copy()
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    d = d.sort_values("open_time").reset_index(drop=True)
    starts = num(d["episode_age_h"]).eq(1).to_numpy()
    idx = np.flatnonzero(starts)
    out = []
    for n, i in enumerate(idx, start=1):
        j = idx[n] if n < len(idx) else len(d)
        block = d.iloc[i:j].copy().reset_index(drop=True)
        if block.empty:
            continue
        path = str(block.loc[0, "entry_path"]) if pd.notna(block.loc[0, "entry_path"]) else "<missing>"
        if path not in PATH_TO_HEAD:
            continue
        eid = f"E{n:06d}"
        dur = len(block)
        ss = num(block["SimpleShock"])
        hr = num(block["hazard_raw"])
        ss04 = float(ss.iloc[:5].max()) if ss.iloc[:5].notna().any() else np.nan
        hr04 = float(hr.iloc[:5].max()) if hr.iloc[:5].notna().any() else np.nan
        cp15 = 14 if dur >= 15 else None
        cp15_ld = float(num(block["LiveDeficit"]).iloc[cp15]) if cp15 is not None else np.nan
        cp15_ss = float(ss.iloc[cp15]) if cp15 is not None else np.nan
        cp15_hr = float(hr.iloc[cp15]) if cp15 is not None else np.nan
        for k, r in block.iterrows():
            remain = dur - (k + 1)
            head = PATH_TO_HEAD[path]
            out.append({
                "episode_id": eid, "chain_id": None, "open_time": r.open_time,
                "start_time": block.loc[0, "open_time"], "end_time": block.loc[dur-1, "open_time"],
                "year": int(block.loc[0, "open_time"].year), "regime": r.get("regime_30d"),
                "lane": "episode_route", "source_name": "Layer1_episode_start_reconstruction",
                "source_window": "TheHinge_start_transition_episode", "start_transition_path": path,
                "episode_route": path, "strict_prev_state": np.nan, "strict_state": np.nan,
                "strict_adjacency_path": None, "topology_path": path, "tiamat_head": head,
                "runtime_hour_t": int(k + 1), "is_alive_at_cp15": bool(dur >= 15),
                "is_long_gt21": bool(dur > 21), "target": int(dur > 21),
                "survive_next_1h": bool(remain >= 1), "survive_next_3h": bool(remain >= 3),
                "survive_next_6h": bool(remain >= 6), "survive_next_12h": bool(remain >= 12),
                "survive_next_24h": bool(remain >= 24), "cp15_LiveDeficit": cp15_ld,
                "cp15_SimpleShock": cp15_ss, "cp15_hazard_raw": cp15_hr,
                "SimpleShock_0_4h_max_exact": ss04, "hazard_raw_0_4h_max": hr04,
                "ExitBridgeDeficit": np.nan, "PriorCarryDeficit": np.nan,
                "raw_score": HEAD_FORMULAS[head](r, ss04),
            })
    return pd.DataFrame(out, columns=OUTPUT_COLUMNS)


def strict_h4_rows(d: pd.DataFrame, topology_col: str | None) -> pd.DataFrame:
    """Lane-1 strict 4->4 physics rows; requires contiguous hourly observations."""
    if topology_col is None:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    x = d.copy()
    x["open_time"] = pd.to_datetime(x["open_time"], utc=True)
    x = x.sort_values("open_time").reset_index(drop=True)
    s = num(x[topology_col])
    dt = x["open_time"].diff().dt.total_seconds().div(3600)
    prev = s.shift(1)
    curr = s
    mask = dt.eq(1) & prev.eq(4) & curr.eq(4)
    rows = []
    for i in np.flatnonzero(mask.to_numpy()):
        r = x.iloc[i]
        rows.append({
            "episode_id": None, "chain_id": None, "open_time": r.open_time,
            "start_time": r.open_time - pd.Timedelta(hours=1), "end_time": r.open_time,
            "year": int(r.open_time.year), "regime": r.get("regime_30d"),
            "lane": "strict_adjacency", "source_name": "Layer1_strict_topology_adjacency",
            "source_window": "contiguous_hourly_topology_state", "start_transition_path": None,
            "episode_route": None, "strict_prev_state": 4, "strict_state": 4,
            "strict_adjacency_path": "4_to_4", "topology_path": "4_to_4", "tiamat_head": "H4_CeilingTrap",
            "runtime_hour_t": np.nan, "is_alive_at_cp15": np.nan, "is_long_gt21": np.nan, "target": np.nan,
            "survive_next_1h": np.nan, "survive_next_3h": np.nan, "survive_next_6h": np.nan,
            "survive_next_12h": np.nan, "survive_next_24h": np.nan,
            "cp15_LiveDeficit": np.nan, "cp15_SimpleShock": np.nan, "cp15_hazard_raw": np.nan,
            "SimpleShock_0_4h_max_exact": np.nan, "hazard_raw_0_4h_max": np.nan,
            "ExitBridgeDeficit": np.nan, "PriorCarryDeficit": np.nan,
            "raw_score": HEAD_FORMULAS["H4_CeilingTrap"](r, np.nan),
        })
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def extract(layer1: Path, out: Path, audit: Path, cp15_out: Path):
    d = pd.read_csv(layer1)
    missing = [c for c in REQUIRED_BASE if c not in d.columns]
    if missing:
        raise ValueError(f"Layer1 missing required columns: {missing}")
    h123 = episode_rows(d)
    topo_col = choose_topology_column(d)
    h4 = strict_h4_rows(d, topo_col)
    allh = pd.concat([h123, h4], ignore_index=True)
    allh["open_time"] = pd.to_datetime(allh["open_time"], utc=True)
    allh = allh.sort_values(["open_time", "lane", "tiamat_head"], na_position="last").reset_index(drop=True)
    cp15 = allh[allh["runtime_hour_t"].eq(15)].copy()
    audit_obj = {
        "experiment": "HF9_TIAMAT_NATIVE_ROUTE_EXTRACTOR_V1_1",
        "input_rows": int(len(d)),
        "episode_route_rows": int(len(h123)),
        "strict_h4_rows": int(len(h4)),
        "topology_column": topo_col,
        "topology_semantics": "strict contiguous hourly adjacency only",
        "head_counts": allh["tiamat_head"].value_counts(dropna=False).to_dict(),
        "lane_counts": allh["lane"].value_counts(dropna=False).to_dict(),
        "h4_required_count_from_contract": 3501,
        "status": "PASS" if len(h4) == 3501 else ("PARTIAL_H4_SOURCE_MISSING" if topo_col is None else "H4_COUNT_MISMATCH"),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    allh.to_csv(out, index=False)
    cp15.to_csv(cp15_out, index=False)
    audit.write_text(json.dumps(audit_obj, indent=2, default=str))
    print(json.dumps(audit_obj, indent=2, default=str))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("layer1", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--audit", type=Path, required=True)
    ap.add_argument("--cp15-out", type=Path, required=True)
    args = ap.parse_args()
    extract(args.layer1, args.out, args.audit, args.cp15_out)
