"""HF9 TIAMAT native route extractor V1.

Builds a common hourly runtime table from the canonical Layer1 spine.

Important path rule:
  start_transition_path is the legacy TheHinge doorway (0_to_4/2_to_4/3_to_4).
  topology_path is the TIAMAT head route and may additionally be 4_to_4.

H0/H2/H3 are reconstructed from episode starts (episode_age_h == 1).
H4 is NEVER inferred from entry_path; a true 4_to_4 source must be supplied
as --h4. Without it the audit remains PARTIAL rather than silently relabeling.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

HEAD_FORMULAS = {
    "H0_FalseCalmIgnition": lambda d: d["SimpleShock"] + 0.05*d["hazard_raw"],
    "H2_ResetDragRelease": lambda d: d["LiveDeficit"],
    "H3_RecoveryInversion": lambda d: d["LiveDeficit"] + 0.05*d["hazard_raw"] - d["SimpleShock_0_4h_max_exact"],
    "H4_CeilingTrap": lambda d: d["LiveDeficit"] + 0.20*d["hazard_raw"] + 0.10*d["SimpleShock"],
}
PATH_TO_HEAD = {"0_to_4":"H0_FalseCalmIgnition", "2_to_4":"H2_ResetDragRelease", "3_to_4":"H3_RecoveryInversion", "4_to_4":"H4_CeilingTrap"}

REQUIRED_BASE = ["open_time","SimpleShock","LiveDeficit","hazard_raw","entry_path","episode_age_h","regime_30d","Crash72"]
OUTPUT_COLUMNS = [
    "episode_id","chain_id","open_time","start_time","end_time","year","regime",
    "source_name","source_window","start_transition_path","topology_path","tiamat_head",
    "runtime_hour_t","is_alive_at_cp15","is_long_gt21","target",
    "survive_next_1h","survive_next_3h","survive_next_6h","survive_next_12h","survive_next_24h",
    "cp15_LiveDeficit","cp15_SimpleShock","cp15_hazard_raw",
    "SimpleShock_0_4h_max_exact","hazard_raw_0_4h_max","ExitBridgeDeficit","PriorCarryDeficit",
    "raw_score",
]

def _clean_num(s):
    return pd.to_numeric(s, errors="coerce")

def _episode_blocks(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    d = d.sort_values("open_time").reset_index(drop=True)
    age = _clean_num(d["episode_age_h"])
    starts = age.eq(1).to_numpy()
    start_idx = np.flatnonzero(starts)
    rows = []
    for eid, i in enumerate(start_idx, start=1):
        j = start_idx[eid] if eid < len(start_idx) else len(d)
        block = d.iloc[i:j].copy().reset_index(drop=True)
        if block.empty:
            continue
        path = str(block.loc[0,"entry_path"]) if pd.notna(block.loc[0,"entry_path"]) else "<missing>"
        if path not in PATH_TO_HEAD or path == "<missing>":
            continue
        rows.append((eid, path, block))
    out=[]
    for eid,path,b in rows:
        start_time=b.loc[0,"open_time"]; end_time=b.loc[len(b)-1,"open_time"]
        dur=len(b)
        regime=b.loc[0,"regime_30d"]
        ss=_clean_num(b["SimpleShock"]); hr=_clean_num(b["hazard_raw"])
        ss04=float(ss.iloc[:5].max()) if ss.iloc[:5].notna().any() else np.nan
        hr04=float(hr.iloc[:5].max()) if hr.iloc[:5].notna().any() else np.nan
        cp15_idx=14 if len(b)>=15 else None
        cp15_ld=float(_clean_num(b["LiveDeficit"]).iloc[cp15_idx]) if cp15_idx is not None else np.nan
        cp15_ss=float(ss.iloc[cp15_idx]) if cp15_idx is not None else np.nan
        cp15_hr=float(hr.iloc[cp15_idx]) if cp15_idx is not None else np.nan
        for k,r in b.iterrows():
            remain=dur-(k+1)
            row={
                "episode_id":f"E{eid:06d}","chain_id":None,"open_time":r.open_time,
                "start_time":start_time,"end_time":end_time,"year":int(start_time.year),
                "regime":regime,"source_name":"Layer1_episode_start_reconstruction","source_window":"TheHinge_start_transition_proxy",
                "start_transition_path":path,"topology_path":path,"tiamat_head":PATH_TO_HEAD[path],
                "runtime_hour_t":int(k+1),"is_alive_at_cp15":bool(dur>=15),"is_long_gt21":bool(dur>21),"target":int(dur>21),
                "survive_next_1h":bool(remain>=1),"survive_next_3h":bool(remain>=3),"survive_next_6h":bool(remain>=6),
                "survive_next_12h":bool(remain>=12),"survive_next_24h":bool(remain>=24),
                "cp15_LiveDeficit":cp15_ld,"cp15_SimpleShock":cp15_ss,"cp15_hazard_raw":cp15_hr,
                "SimpleShock_0_4h_max_exact":ss04,"hazard_raw_0_4h_max":hr04,
                "ExitBridgeDeficit":np.nan,"PriorCarryDeficit":np.nan,
            }
            base={c:r[c] if c in r.index else np.nan for c in ["SimpleShock","LiveDeficit","hazard_raw"]}
            calc=pd.DataFrame([base])
            calc["SimpleShock_0_4h_max_exact"]=ss04
            row["raw_score"] = float(HEAD_FORMULAS[PATH_TO_HEAD[path]](calc).iloc[0]) if calc.notna().any(axis=None) else np.nan
            out.append(row)
    return pd.DataFrame(out, columns=OUTPUT_COLUMNS)

def _load_h4(path: Path|None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    h4=pd.read_csv(path)
    missing=[c for c in OUTPUT_COLUMNS if c not in h4.columns]
    if missing:
        raise ValueError(f"H4 source missing required canonical columns: {missing}")
    h4=h4[OUTPUT_COLUMNS].copy()
    h4["topology_path"]="4_to_4"; h4["tiamat_head"]="H4_CeilingTrap"
    if h4["start_transition_path"].notna().any():
        raise ValueError("H4 source must not overload start_transition_path")
    return h4

def extract(layer1: Path, h4: Path|None, out: Path, cp15_out: Path, audit_out: Path):
    d=pd.read_csv(layer1)
    missing=[c for c in REQUIRED_BASE if c not in d.columns]
    if missing: raise ValueError(f"Layer1 missing required columns: {missing}")
    h123=_episode_blocks(d)
    h4=_load_h4(h4)
    allh=pd.concat([h123,h4],ignore_index=True)
    allh["open_time"]=pd.to_datetime(allh["open_time"],utc=True)
    allh=allh.sort_values(["open_time","tiamat_head"]).reset_index(drop=True)
    cp15=allh[allh["runtime_hour_t"].eq(15)].copy()
    allh.to_csv(out,index=False)
    cp15.to_csv(cp15_out,index=False)
    audit={
        "experiment":"HF9_TIAMAT_NATIVE_ROUTE_EXTRACTOR_V1",
        "input_rows":int(len(d)),"output_rows":int(len(allh)),"cp15_rows":int(len(cp15)),
        "head_counts":allh["tiamat_head"].value_counts(dropna=False).to_dict(),
        "topology_path_counts":allh["topology_path"].value_counts(dropna=False).to_dict(),
        "h4_present":bool((allh["topology_path"]=="4_to_4").any()),
        "status":"PASS" if (allh["topology_path"]=="4_to_4").any() else "PARTIAL_H4_SOURCE_REQUIRED",
        "h4_rule":"4_to_4 must come from a true H4 source; never infer from entry_path",
    }
    audit_out.write_text(pd.Series(audit).to_json(indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("layer1",type=Path); ap.add_argument("--h4",type=Path); ap.add_argument("--out",type=Path,required=True); ap.add_argument("--cp15-out",type=Path,required=True); ap.add_argument("--audit",type=Path,required=True); a=ap.parse_args(); extract(a.layer1,a.h4,a.out,a.cp15_out,a.audit)
