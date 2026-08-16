"""Compare state-entry geometry for 2024 Orphans vs ordinary state entries."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from hydra_relative_recovery_court_v1 import history

def main(csv:Path,out:Path):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 d['crash72']=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int).eq(1)
 path=d['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 d['core']=d.crash72&path.eq('3_to_4')&pd.to_numeric(d.episode_age_h,errors='coerce').eq(1)
 d['orphan']=d.crash72&~d.core&path.eq('<missing>'); d['transition']=d.crash72&~d.core&path.ne('<missing>')
 assert (int(d.core.sum()),int(d.transition.sum()),int(d.orphan.sum()),int(d.crash72.sum()))==(12,350,606,968)
 train=d[d.date.dt.year<2024]; test=d[d.date.dt.year==2024].copy().reset_index(drop=True)
 rr_cut=float(pd.to_numeric(train.rr_recovery_minus_burden,errors='coerce').quantile(.20)); hz_cut=float(pd.to_numeric(train.hazard_score,errors='coerce').quantile(.80))
 rr=pd.to_numeric(test.rr_recovery_minus_burden,errors='coerce'); hz=pd.to_numeric(test.hazard_score,errors='coerce'); age=pd.to_numeric(test.episode_age_h,errors='coerce')
 state=((rr<rr_cut)&(hz>hz_cut)).to_numpy(bool); prev=np.r_[False,state[:-1]]; entry=state&~prev
 idx=np.flatnonzero(entry); orphan_entry=np.array([bool(test.orphan.iloc[i]) for i in idx]); normal_entry=~test.crash72.iloc[idx].to_numpy(bool)
 # Geometry at entry and one-hour change: shock, recovery, hazard, RR plus acceleration where columns exist.
 cols=['rr_recovery_minus_burden','hazard_score','SimpleShock','LiveDeficit','RecoveryWeakness_v1','episode_age_h']
 def numeric(frame,c): return pd.to_numeric(frame[c],errors='coerce') if c in frame.columns else pd.Series(np.nan,index=frame.index)
 rows=[]
 for i in idx:
  rec={'i':int(i),'orphan':bool(test.orphan.iloc[i]),'age':float(age.iloc[i]) if pd.notna(age.iloc[i]) else None}
  for c in cols:
   x=numeric(test,c); rec[c]=float(x.iloc[i]) if pd.notna(x.iloc[i]) else None; rec[c+'_d1']=float(x.iloc[i+1]-x.iloc[i]) if i+1<len(test) and pd.notna(x.iloc[i]) and pd.notna(x.iloc[i+1]) else None
  rows.append(rec)
 ed=pd.DataFrame(rows)
 def summary(frame):
  out={'n':int(len(frame))}
  for c in cols:
   if c in frame:
    x=pd.to_numeric(frame[c],errors='coerce').dropna(); out[c]={'median':float(x.median()) if len(x) else None,'mean':float(x.mean()) if len(x) else None,'p10':float(x.quantile(.1)) if len(x) else None,'p90':float(x.quantile(.9)) if len(x) else None}
   dc=c+'_d1'
   if dc in frame:
    x=pd.to_numeric(frame[dc],errors='coerce').dropna(); out[dc]={'median':float(x.median()) if len(x) else None,'mean':float(x.mean()) if len(x) else None}
  return out
 oe=ed[ed.orphan]; ne=ed[~ed.orphan]
 result={'experiment':'hydra_crash72_orphan_entry_geometry_court_v1','holdout_year':2024,'train_years':'2020-2023','cuts':{'rr_p20_train':rr_cut,'hazard_p80_train':hz_cut},'class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'state_entries':{'total':int(len(ed)),'orphan':int(len(oe)),'non_orphan':int(len(ne)),'orphan_entry_rate':float(len(oe)/len(ed)) if len(ed) else None},'orphan_entry_geometry':summary(oe),'non_orphan_entry_geometry':summary(ne)}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
