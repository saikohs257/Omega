"""Event-aligned trajectory test for 2024 Crash72 Orphans vs non-Orphan Crash72.
Uses the same frozen 2020-2023 state cuts. Reports per-event slopes/deltas in a
window around each Orphan/Crash72 row, avoiding a fitted predictor.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from hydra_relative_recovery_court_v1 import history

def num(d,c): return pd.to_numeric(d[c],errors='coerce') if c in d.columns else pd.Series(np.nan,index=d.index)
def main(csv:Path,out:Path):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 d['crash72']=num(d,'Crash72').fillna(0).astype(int).eq(1)
 path=d['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 d['core']=d.crash72&path.eq('3_to_4')&num(d,'episode_age_h').eq(1); d['orphan']=d.crash72&~d.core&path.eq('<missing>'); d['transition']=d.crash72&~d.core&path.ne('<missing>')
 assert (int(d.core.sum()),int(d.transition.sum()),int(d.orphan.sum()),int(d.crash72.sum()))==(12,350,606,968)
 train=d[d.date.dt.year<2024]; test=d[d.date.dt.year==2024].copy().reset_index(drop=True)
 rr_cut=float(num(train,'rr_recovery_minus_burden').quantile(.20)); hz_cut=float(num(train,'hazard_score').quantile(.80))
 rr=num(test,'rr_recovery_minus_burden'); hz=num(test,'hazard_score'); state=(rr<rr_cut)&(hz>hz_cut)
 features=['rr_recovery_minus_burden','hazard_score','SimpleShock','LiveDeficit','RecoveryWeakness_v1']
 def event_records(mask,label):
  rows=[]
  for i in np.flatnonzero(mask.to_numpy(bool)):
   rec={'i':int(i),'label':label,'age_h':float(num(test,'episode_age_h').iloc[i]) if pd.notna(num(test,'episode_age_h').iloc[i]) else None}
   # signed level and change from t-1 to t, t to t+1, and t-2 to t+2
   for c in features:
    x=num(test,c); v=x.iloc[i]
    rec[c]=float(v) if pd.notna(v) else None
    for a,b,k in [(i-1,i,'d_m1_0'),(i,i+1,'d_0_p1'),(i-2,i+2,'d_m2_p2')]:
     rec[k+'_'+c]=float(x.iloc[b]-x.iloc[a]) if 0<=a<len(test) and 0<=b<len(test) and pd.notna(x.iloc[a]) and pd.notna(x.iloc[b]) else None
   # state status before/at/after event
   rec['state_m1']=bool(state.iloc[i-1]) if i>0 else False; rec['state_0']=bool(state.iloc[i]); rec['state_p1']=bool(state.iloc[i+1]) if i+1<len(test) else False
   rows.append(rec)
  return pd.DataFrame(rows)
 oe=event_records(test.orphan,'orphan'); ce=event_records(test.crash72&~test.orphan,'non_orphan_crash72')
 def summary(f):
  out={'n':int(len(f))}
  for c in features:
   for k in [c,'d_m1_0_'+c,'d_0_p1_'+c,'d_m2_p2_'+c]:
    x=pd.to_numeric(f[k],errors='coerce').dropna() if k in f else pd.Series(dtype=float)
    out[k]={'median':float(x.median()) if len(x) else None,'mean':float(x.mean()) if len(x) else None,'p10':float(x.quantile(.1)) if len(x) else None,'p90':float(x.quantile(.9)) if len(x) else None}
  for k in ['state_m1','state_0','state_p1']:
   out[k+'_rate']=float(f[k].mean()) if len(f) else None
  return out
 result={'experiment':'hydra_crash72_orphan_trajectory_court_v1','holdout_year':2024,'train_years':'2020-2023','cuts':{'rr_p20_train':rr_cut,'hazard_p80_train':hz_cut},'class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'orphan_trajectory':summary(oe),'non_orphan_crash72_trajectory':summary(ce)}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
