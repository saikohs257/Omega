"""HF9 TIAMAT native route extractor V1.

Canonical rule: never overload the legacy entry_path with 4_to_4.
H0/H2/H3 are reconstructed from age-1 native starts in the canonical spine.
H4 must arrive from a separately verified true-4_to-4 hourly source.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PATH_TO_HEAD = {
    "0_to_4": "H0_FalseCalmIgnition",
    "2_to_4": "H2_ResetDragRelease",
    "3_to_4": "H3_RecoveryInversion",
    "4_to_4": "H4_CeilingTrap",
}
EXPECTED_START_COUNTS = {"0_to_4": 63, "2_to_4": 221, "3_to_4": 169}
REQUIRED_BASE = [
    "open_time", "SimpleShock", "LiveDeficit", "hazard_raw",
    "entry_path", "episode_age_h", "regime_30d", "Crash72",
]
OUTPUT_COLUMNS = [
    "episode_id", "chain_id", "open_time", "start_time", "end_time", "year", "regime",
    "source_name", "source_window", "start_transition_path", "topology_path", "tiamat_head",
    "runtime_hour_t", "is_alive_at_cp15", "is_long_gt21", "target",
    "survive_next_1h", "survive_next_3h", "survive_next_6h", "survive_next_12h", "survive_next_24h",
    "cp15_LiveDeficit", "cp15_SimpleShock", "cp15_hazard_raw",
    "SimpleShock_0_4h_max_exact", "hazard_raw_0_4h_max", "ExitBridgeDeficit", "PriorCarryDeficit",
    "raw_score",
]


def _clean_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _episode_blocks(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    d = d.sort_values("open_time").reset_index(drop=True)
    age = _clean_num(d["episode_age_h"])
    start_idx = np.flatnonzero(age.eq(1).to_numpy())
    if len(start_idx) != 453:
        raise ValueError(f"Canonical invariant failed: expected 453 episode starts, got {len(start_idx)}")

    start_paths = d.iloc[start_idx]["entry_path"].astype("string").fillna("<missing>").tolist()
    counts = pd.Series(start_paths).value_counts().to_dict()
    for path, expected in EXPECTED_START_COUNTS.items():
        got = int(counts.get(path, 0))
        if got != expected:
            raise ValueError(f"Canonical start invariant failed for {path}: expected {expected}, got {got}")
    if any(p not in EXPECTED_START_COUNTS for p in start_paths):
        raise ValueError("Canonical start invariant failed: unexpected/missing start-transition path")

    rows = []
    for eid, i in enumerate(start_idx, start=1):
        j = start_idx[eid] if eid < len(start_idx) else len(d)
        block = d.iloc[i:j].copy().reset_index(drop=True)
        path = str(block.loc[0, "entry_path"])
        rows.append((eid, path, block))

    out = []
    for eid, path, b in rows:
        start_time = b.loc[0, "open_time"]
        end_time = b.loc[len(b) - 1, "open_time"]
        dur = int(len(b))
        regime = b.loc[0, "regime_30d"]
        ss = _clean_num(b["SimpleShock"])
        ld = _clean_num(b["LiveDeficit"])
        hr = _clean_num(b["hazard_raw"])
        ss04 = float(ss.iloc[:5].max()) if ss.iloc[:5].notna().any() else np.nan
        hr04 = float(hr.iloc[:5].max()) if hr.iloc[:5].notna().any() else np.nan
        cp15_idx = 14 if dur >= 15 else None
        cp15_ld = float(ld.iloc[cp15_idx]) if cp15_idx is not None else np.nan
        cp15_ss = float(ss.iloc[cp15_idx]) if cp15_idx is not None else np.nan
        cp15_hr = float(hr.iloc[cp15_idx]) if cp15_idx is not None else np.nan

        for k, r in b.iterrows():
            remain = dur - (k + 1)
            head = PATH_TO_HEAD[path]
            if head == "H0_FalseCalmIgnition":
                raw_score = float(r["SimpleShock"] + 0.05 * r["hazard_raw"])
            elif head == "H2_ResetDragRelease":
                raw_score = float(r["LiveDeficit"])
            elif head == "H3_RecoveryInversion":
                raw_score = float(r["LiveDeficit"] + 0.05 * r["hazard_raw"] - ss04)
            else:
                raise AssertionError("H4 cannot be reconstructed from the legacy start-transition seat")

            out.append({
                "episode_id": f"E{eid:06d}",
                "chain_id": None,
                "open_time": r.open_time,
                "start_time": start_time,
                "end_time": end_time,
                "year": int(start_time.year),
                "regime": regime,
                "source_name": "Layer1_episode_start_reconstruction",
                "source_window": "canonical_start_age1",
                "start_transition_path": path,
                "topology_path": path,
                "tiamat_head": head,
                "runtime_hour_t": int(k + 1),
                "is_alive_at_cp15": bool(dur >= 15),
                "is_long_gt21": bool(dur > 21),
                "target": int(dur > 21),
                "survive_next_1h": bool(remain >= 1),
                "survive_next_3h": bool(remain >= 3),
                "survive_next_6h": bool(remain >= 6),
                "survive_next_12h": bool(remain >= 12),
                "survive_next_24h": bool(remain >= 24),
                "cp15_LiveDeficit": cp15_ld,
                "cp15_SimpleShock": cp15_ss,
                "cp15_hazard_raw": cp15_hr,
                "SimpleShock_0_4h_max_exact": ss04,
                "hazard_raw_0_4h_max": hr04,
                "ExitBridgeDeficit": np.nan,
                "PriorCarryDeficit": np.nan,
                "raw_score": raw_score,
            })
    return pd.DataFrame(out, columns=OUTPUT_COLUMNS)


def _load_h4(path: Path | None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    h4 = pd.read_csv(path)
    missing = [c for c in OUTPUT_COLUMNS if c not in h4.columns]
    if missing:
        raise ValueError(f"H4 source missing required canonical columns: {missing}")
    h4 = h4[OUTPUT_COLUMNS].copy()
    h4["topology_path"] = "4_to_4"
    h4["tiamat_head"] = "H4_CeilingTrap"
    if h4["start_transition_path"].notna().any():
        raise ValueError("H4 source must not overload start_transition_path")
    return h4


def _write_audit(audit: dict, json_path: Path, md_path: Path) -> None:
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True, allow_nan=False))
    lines = [
        "# HF9 TIAMAT Native Route Extractor V1 Audit", "",
        f"- Status: **{audit['status']}**",
        f"- Input rows: {audit['input_rows']}",
        f"- Output rows: {audit['output_rows']}",
        f"- CP15 rows: {audit['cp15_rows']}",
        f"- Episode starts: {audit['episode_starts']}",
        "", "## Start-transition counts",
    ]
    lines += [f"- {k}: {v}" for k, v in sorted(audit["start_transition_counts"].items())]
    lines += ["", "## Topology/head counts"]
    lines += [f"- {k}: {v}" for k, v in sorted(audit["topology_path_counts"].items())]
    lines += ["", f"- H4 source present: `{audit['h4_present']}`", f"- H4 rule: {audit['h4_rule']}"]
    md_path.write_text("\n".join(lines) + "\n")


def extract(layer1: Path, h4: Path | None, out: Path, cp15_out: Path, audit_json: Path, audit_md: Path) -> None:
    d = pd.read_csv(layer1)
    if len(d) != 43848:
        raise ValueError(f"Canonical invariant failed: expected 43848 rows, got {len(d)}")
    missing = [c for c in REQUIRED_BASE if c not in d.columns]
    if missing:
        raise ValueError(f"Layer1 missing required columns: {missing}")

    h123 = _episode_blocks(d)
    h4df = _load_h4(h4)
    allh = pd.concat([h123, h4df], ignore_index=True)
    allh["open_time"] = pd.to_datetime(allh["open_time"], utc=True)
    allh = allh.sort_values(["open_time", "tiamat_head"]).reset_index(drop=True)
    cp15 = allh[allh["runtime_hour_t"].eq(15)].copy()
    allh.to_csv(out, index=False)
    cp15.to_csv(cp15_out, index=False)

    audit = {
        "experiment": "HF9_TIAMAT_NATIVE_ROUTE_EXTRACTOR_V1",
        "input_rows": int(len(d)),
        "output_rows": int(len(allh)),
        "cp15_rows": int(len(cp15)),
        "episode_starts": 453,
        "start_transition_counts": EXPECTED_START_COUNTS,
        "topology_path_counts": allh["topology_path"].value_counts(dropna=False).to_dict(),
        "head_counts": allh["tiamat_head"].value_counts(dropna=False).to_dict(),
        "h4_present": bool((allh["topology_path"] == "4_to_4").any()),
        "status": "PASS" if (allh["topology_path"] == "4_to_4").any() else "PARTIAL_H4_SOURCE_REQUIRED",
        "h4_rule": "4_to_4 must come from a true H4 source; never infer from entry_path",
    }
    _write_audit(audit, audit_json, audit_md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("layer1", type=Path)
    ap.add_argument("--h4", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cp15-out", type=Path, required=True)
    ap.add_argument("--audit-json", type=Path, required=True)
    ap.add_argument("--audit-md", type=Path, required=True)
    args = ap.parse_args()
    extract(args.layer1, args.h4, args.out, args.cp15_out, args.audit_json, args.audit_md)
