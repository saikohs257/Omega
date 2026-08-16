"""Measure persistence of low-RR/high-Hazard state before 2024 Crash72 Orphans."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from hydra_relative_recovery_court_v1 import history

def main(csv,out):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int)
 path=d['entry_path'].astype('string').fillna('<missing>').str.strip(); path=path.replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 base=path.eq('3_to_4') & pd.to_numeric(d['episode_age_h'],errors='coerce').eq(1)
 ex=y.eq(1)&~base; trans=ex&path.ne('<missing>'); orphan=ex&path.eq('<missing>'); core=y.eq(1)&base
 assert int(core.sum())==12 and int(trans.sum())==350 and int(orphan.sum())==606 and int(y.sum())==968
 train=d[d.date.dt.year<2024].copy(); test=d[d.date.dt.year==2024].copy()
 rr_cut=float(pd.to_numeric(train['rr_recovery_minus_burden'],errors='coerce').quantile(.20)); hz_cut=float(pd.to_numeric(train['hazard_score'],errors='coerce').quantile(.80))
 rr=pd.to_numeric(test['rr_recovery_minus_burden'],errors='coerce'); hz=pd.to_numeric(test['hazard_score'],errors='coerce')
 state=(rr<rr_cut)&(hz>hz_cut)
 test=test.copy(); test['orphan']=orphan[d.date.dt.year.eq(2024)].to_numpy(int); test['state']=state.to_numpy(bool)
 rows=[]
 for typ in ['orphan','core','transition']:
  if typ=='orphan': target=test['orphan'].eq(1)
  elif typ=='core': target=(test.index.to_series().map(lambda i: bool(core.iloc[i])) if False else pd.Series(False,index=test.index))
  else: target=pd.Series(False,index=test.index)
  # Persistence ending at T0 for every target event; non-target rows are summarized by state-run distribution separately.
  durations=[]
  for idx in test.index[target]:
   pos=d.index[d.index==idx][0]; dur=0
   j=pos
   while j>=0 and d.loc[j,'date'].year==2024:
    r=float(pd.to_numeric(pd.Series([d.loc[j,'rr_recovery_minus_burden']),errors='coerce').iloc[0]); h=float(pd.to_numeric(pd.Series([d.loc[j,'hazard_score']),errors='coerce').iloc[0])
    if not (r<rr_cut and h>hz_cut): break
    dur+=1; j-=1
   durations.append(dur)
  if typ=='orphan': rows.append({'class':'orphan','n':len(durations),'durations_h':durations,'median_h':float(np.median(durations)) if durations else None,'mean_h':float(np.mean(durations)) if durations else None,'max_h':int(max(durations)) if durations else 0})
 # Distribution of consecutive state-run lengths in 2024, and orphan capture by minimum persistence.
 runs=[]; start=None
 vals=state.to_numpy()
 for i,v in enumerate(vals.tolist()+[False]):
  if v and start is None: start=i
  if not v and start is not None: runs.append(i-start); start=None
 thresholds=[1,2,4,6,12,24,48,72]
 capture=[]
 otarget=test['orphan'].eq(1).to_numpy()
 for th in thresholds:
  m=np.zeros(len(test),dtype=bool)
  for i in range(len(vals)):
   if vals[i]:
    j=i
    while j>=0 and vals[j]: j-=1
    if i-j>=th: m[i]=True
  capture.append({'min_persistence_h':th,'orphan_captured':int((m&otarget).sum()),'orphan_total':int(otarget.sum()),'capture_rate':float((m&otarget).sum()/max(1,otarget.sum()))})
 result={'experiment':'hydra_crash72_orphan_persistence_court_v1','holdout_year':2024,'train_years':'2020-2023','cuts':{'rr_p20_train':rr_cut,'hazard_p80_train':hz_cut},'class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'orphan_persistence':rows,'state_run_lengths_summary':{'n_runs':len(runs),'median_h':float(np.median(runs)) if runs else None,'p90_h':float(np.quantile(runs,.9)) if runs else None,'max_h':int(max(runs)) if runs else 0},'capture_by_threshold':capture}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
