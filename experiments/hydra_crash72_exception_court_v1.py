"""Forensic audit of native Crash72 positives missed by the 97.79% episode-state reconstruction."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from hydra_relative_recovery_court_v1 import history

TARGET='Crash72'
BASE='episode_type_3_to_4_age1'

def main(csv:Path,out:Path):
    raw=pd.read_csv(csv); d=history(raw).sort_values('open_time').reset_index(drop=True)
    y=pd.to_numeric(d[TARGET],errors='coerce').fillna(0).astype(int)
    base=((d['episode_type'].astype(str)=='3_to_4') & (pd.to_numeric(d['run_age_h'],errors='coerce')==1)).astype(int)
    ex=d[(y==1)&(base==0)].copy()
    ex['gap_prev_h']=pd.to_datetime(ex.open_time,utc=True).diff().dt.total_seconds().div(3600)
    ex['year']=pd.to_datetime(ex.open_time,utc=True).dt.year
    ex['month']=pd.to_datetime(ex.open_time,utc=True).dt.month
    summary={'experiment':'hydra_crash72_exception_court_v1','canonical_rows':len(raw),'native_positive_rows':int(y.sum()),'base_positive_rows':int(base.sum()),'exception_rows':len(ex),'base_reproduces_all_native':bool(((y==1)&(base==0)).sum()==0),'episode_type_counts':ex['episode_type'].value_counts(dropna=False).to_dict(),'run_age_counts':ex['run_age_h'].value_counts(dropna=False).head(25).to_dict(),'year_counts':ex['year'].value_counts().sort_index().to_dict(),'month_counts':ex['month'].value_counts().sort_index().to_dict(),'contiguous_gap_h':ex['gap_prev_h'].describe().to_dict()}
    # summarize available state/feature columns without inventing a classifier
    for c in ['hazard_raw','hazard_score','SimpleShock','LiveDeficit','RecoveryWeakness_v1','rr_recovery_minus_burden','episode_type','run_age_h','open_time']:
        if c in ex.columns:
            if pd.api.types.is_numeric_dtype(ex[c]): summary.setdefault('numeric',{})[c]=ex[c].describe().to_dict()
            else: summary.setdefault('categorical',{})[c]=ex[c].value_counts(dropna=False).head(20).to_dict()
    out.write_text(json.dumps(summary,indent=2,default=str)); print(json.dumps(summary,indent=2,default=str))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
