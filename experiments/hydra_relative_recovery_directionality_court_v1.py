"""Temporal directionality sweep for recovery-minus-burden.

Measures frozen-2024 discrimination as the feature is shifted across a dense
lead/lag grid. The feature is never selected from the sweep; this is a
pre-registered diagnostic of temporal locality and possible leakage.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from hydra_relative_recovery_court_v1 import history
from hydra_relative_recovery_falsification_court_v1 import auc_for

TARGET="Crash72"; FEATURE="rr_recovery_minus_burden"
OFFSETS=[-720,-336,-168,-72,-48,-24,-12,-6,-1,0,1,6,12,24,48,72,168,336,720]

def main(csv:Path,out:Path):
    raw=pd.read_csv(csv); d=history(raw); assert len(raw)==43848
    d=d.sort_values("open_time").reset_index(drop=True)
    d["year"]=pd.to_datetime(d.open_time,utc=True).dt.year
    rows=[]
    for h in OFFSETS:
        c=f"rr_shift_{h:+d}h"
        d[c]=d[FEATURE].shift(h)
        rows.append({"offset_h":h,"auc":auc_for(d[d.year<2024],d[d.year==2024],c)})
    payload={"experiment":"hydra_relative_recovery_directionality_court_v1","protocol":"frozen 2024 holdout; dense pre-registered lead/lag sweep; no offset selected for modeling","canonical_rows":43848,"feature":FEATURE,"offsets":rows}
    out.write_text(json.dumps(payload,indent=2)); print(json.dumps(payload,indent=2))
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
