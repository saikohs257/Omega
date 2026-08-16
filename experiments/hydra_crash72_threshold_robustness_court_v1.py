"""Crash72 RR/Hazard threshold robustness court: training-only quantiles -> 2024 holdout."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from hydra_relative_recovery_court_v1 import history
from hydra_crash72_incremental_orphan_court_v1 import normalized_entry_path

QUANTILES=[0.2,0.4,0.6,0.8]

def main(csv:Path,out:Path):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int)
 path=normalized_entry_path(d['entry_path']); base=path.eq('3_to_4') & pd.to_numeric(d['episode_age_h'],errors='coerce').eq(1)
 ex=y.eq(1)&~base; core=y.eq(1)&base; trans=ex&path.ne('<missing>'); orphan=ex&path.eq('<missing>')
 counts={'core':int(core.sum()),'transition':int(trans.sum()),'orphan':int(orphan.sum()),'crash72':int(y.sum())}
 assert counts=={'core':12,'transition':350,'orphan':606,'crash72':968}, f'taxonomy mismatch: {counts}'
 train=d[d.date.dt.year<2024]; test=d[d.date.dt.year==2024].copy(); yo=orphan[d.date.dt.year==2024].to_numpy(int)
 rr_tr=pd.to_numeric(train['rr_recovery_minus_burden'],errors='coerce'); hz_tr=pd.to_numeric(train['hazard_score'],errors='coerce')
 rr_te=pd.to_numeric(test['rr_recovery_minus_burden'],errors='coerce'); hz_te=pd.to_numeric(test['hazard_score'],errors='coerce')
 results=[]
 for qrr in QUANTILES:
  rr_cut=float(rr_tr.quantile(qrr))
  for qhz in QUANTILES:
   hz_cut=float(hz_tr.quantile(qhz))
   for rr_side, rr_cond in [('low',rr_te<rr_cut),('high',rr_te>=rr_cut)]:
    for hz_side,hz_cond in [('low',hz_te<hz_cut),('high',hz_te>=hz_cut)]:
     mask=(rr_cond&hz_cond).to_numpy(); n=int(mask.sum()); pos=int(yo[mask].sum()); results.append({'rr_quantile':qrr,'hazard_quantile':qhz,'rr_side':rr_side,'hazard_side':hz_side,'n':n,'orphan_positives':pos,'rate':float(pos/n) if n else None})
 out.write_text(json.dumps({'experiment':'hydra_crash72_threshold_robustness_court_v1','train_years':'2020-2023','holdout_year':2024,'class_counts':counts,'results':results},indent=2,allow_nan=False)); print(json.dumps({'experiment':'hydra_crash72_threshold_robustness_court_v1','train_years':'2020-2023','holdout_year':2024,'class_counts':counts,'results':results},indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
