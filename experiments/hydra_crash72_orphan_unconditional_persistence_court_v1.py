"""Compare persistence of low-RR/high-Hazard state for Orphans vs all non-Crash72 2024 rows."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from hydra_relative_recovery_court_v1 import history

def runs(mask):
 out=np.zeros(len(mask),dtype=int); starts=[]; i=0
 while i<len(mask):
  if not mask[i]: i+=1; continue
  j=i
  while j<len(mask) and mask[j]: j+=1
  out[i:j]=np.arange(1,j-i+1); starts.append(j-i); i=j
 return out,starts

def main(csv,out):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 d['crash72']=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int).eq(1)
 path=d['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 d['core']=d['crash72']&path.eq('3_to_4')&pd.to_numeric(d['episode_age_h'],errors='coerce').eq(1)
 d['orphan']=d['crash72']&~d['core']&path.eq('<missing>'); d['transition']=d['crash72']&~d['core']&path.ne('<missing>')
 assert (int(d.core.sum()),int(d.transition.sum()),int(d.orphan.sum()),int(d.crash72.sum()))==(12,350,606,968)
 train=d[d.date.dt.year<2024]; test=d[d.date.dt.year==2024].copy().reset_index(drop=True)
 rr_cut=float(pd.to_numeric(train['rr_recovery_minus_burden'],errors='coerce').quantile(.20)); hz_cut=float(pd.to_numeric(train['hazard_score'],errors='coerce').quantile(.80))
 rr=pd.to_numeric(test['rr_recovery_minus_burden'],errors='coerce'); hz=pd.to_numeric(test['hazard_score'],errors='coerce'); state=((rr<rr_cut)&(hz>hz_cut)).to_numpy(bool); run,_=runs(state)
 orphan=test.orphan.to_numpy(bool); noncrash=~test.crash72.to_numpy(bool)
 # Event persistence: run length at every row in each population. Non-Crash72 rows are the unconditional control population.
 od=run[orphan]; cd=run[noncrash]
 def summary(x): return {'n':int(len(x)),'median_h':float(np.median(x)) if len(x) else None,'mean_h':float(np.mean(x)) if len(x) else None,'p90_h':float(np.quantile(x,.9)) if len(x) else None,'max_h':int(np.max(x)) if len(x) else 0,'ge_1h':int((x>=1).sum()),'ge_6h':int((x>=6).sum()),'ge_12h':int((x>=12).sum()),'ge_24h':int((x>=24).sum())}
 # Also compare only rows actually inside the state, avoiding the mass of zero-duration controls.
 control_state=cd[cd>0]; orphan_state=od[od>0]
 result={'experiment':'hydra_crash72_orphan_unconditional_persistence_court_v1','holdout_year':2024,'train_years':'2020-2023','cuts':{'rr_p20_train':rr_cut,'hazard_p80_train':hz_cut},'class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'orphan_event_rows':summary(od),'noncrash_rows':summary(cd),'orphan_state_rows':summary(orphan_state),'noncrash_state_rows':summary(control_state),'state_prevalence':{'orphan_state_rows':int(len(orphan_state)),'orphan_total':int(len(od)),'noncrash_state_rows':int(len(control_state)),'noncrash_total':int(len(cd))}}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
