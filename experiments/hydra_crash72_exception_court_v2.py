"""Crash72 exception audit using canonical episode_state columns."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from hydra_relative_recovery_court_v1 import history

def main(csv:Path,out:Path):
    raw=pd.read_csv(csv); d=history(raw).sort_values('open_time').reset_index(drop=True)
    y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int)
    age=pd.to_numeric(d['episode_age_h'],errors='coerce')
    base=((d['entry_path'].astype(str)=='3_to_4')&(age==1)).astype(int)
    ex=d[(y==1)&(base==0)].copy(); ts=pd.to_datetime(ex.open_time,utc=True)
    ex['gap_prev_h']=ts.diff().dt.total_seconds().div(3600); ex['year']=ts.dt.year; ex['month']=ts.dt.month
    s={'experiment':'hydra_crash72_exception_court_v2','canonical_rows':len(raw),'native_positive_rows':int(y.sum()),'base_positive_rows':int(base.sum()),'exception_rows':len(ex),'agreement':float((y==base).mean()),'entry_path_counts':ex['entry_path'].value_counts(dropna=False).to_dict(),'episode_type_counts':ex['episode_type'].value_counts(dropna=False).to_dict(),'episode_age_counts':ex['episode_age_h'].value_counts(dropna=False).head(25).to_dict(),'year_counts':ex.year.value_counts().sort_index().to_dict(),'month_counts':ex.month.value_counts().sort_index().to_dict(),'gap_stats':ex.gap_prev_h.describe().to_dict()}
    for c in ['hazard_raw','hazard_score','SimpleShock','LiveDeficit','RecoveryWeakness_v1','rr_recovery_minus_burden']:
        if c in ex: s.setdefault('numeric',{})[c]=ex[c].describe().to_dict()
    out.write_text(json.dumps(s,indent=2,default=str)); print(json.dumps(s,indent=2,default=str))
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('csv',type=Path); p.add_argument('--out',type=Path,required=True); a=p.parse_args(); main(a.csv,a.out)
