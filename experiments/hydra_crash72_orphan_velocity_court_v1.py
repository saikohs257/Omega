"""Test whether Orphans are moderate-and-rising vs high-and-falling Crash72 events."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from hydra_relative_recovery_court_v1 import history

def n(d,c): return pd.to_numeric(d[c],errors='coerce')
def main(csv:Path,out:Path):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 d['crash72']=n(d,'Crash72').fillna(0).astype(int).eq(1); path=d.entry_path.astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 d['core']=d.crash72&path.eq('3_to_4')&n(d,'episode_age_h').eq(1); d['orphan']=d.crash72&~d.core&path.eq('<missing>'); d['transition']=d.crash72&~d.core&path.ne('<missing>')
 assert (int(d.core.sum()),int(d.transition.sum()),int(d.orphan.sum()),int(d.crash72.sum()))==(12,350,606,968)
 train=d[d.date.dt.year<2024]; test=d[d.date.dt.year==2024].copy().reset_index(drop=True)
 rr_cut=float(n(train,'rr_recovery_minus_burden').quantile(.20)); hz_cut=float(n(train,'hazard_score').quantile(.80))
 cols=['hazard_score','SimpleShock','LiveDeficit']; rr=n(test,'rr_recovery_minus_burden'); vals={c:n(test,c) for c in cols}
 def one(i):
  v={c:float(vals[c].iloc[i]) if pd.notna(vals[c].iloc[i]) else np.nan for c in cols}; rr0=float(rr.iloc[i]) if pd.notna(rr.iloc[i]) else np.nan
  dh=v['hazard_score']-(float(vals['hazard_score'].iloc[i-1]) if i>0 and pd.notna(vals['hazard_score'].iloc[i-1]) else np.nan)
  ds=v['SimpleShock']-(float(vals['SimpleShock'].iloc[i-1]) if i>0 and pd.notna(vals['SimpleShock'].iloc[i-1]) else np.nan)
  dl=v['LiveDeficit']-(float(vals['LiveDeficit'].iloc[i-1]) if i>0 and pd.notna(vals['LiveDeficit'].iloc[i-1]) else np.nan)
  fdh=(float(vals['hazard_score'].iloc[i+1])-v['hazard_score']) if i+1<len(test) and pd.notna(vals['hazard_score'].iloc[i+1]) else np.nan
  fds=(float(vals['SimpleShock'].iloc[i+1])-v['SimpleShock']) if i+1<len(test) and pd.notna(vals['SimpleShock'].iloc[i+1]) else np.nan
  fdl=(float(vals['LiveDeficit'].iloc[i+1])-v['LiveDeficit']) if i+1<len(test) and pd.notna(vals['LiveDeficit'].iloc[i+1]) else np.nan
  V=np.nanmean([fdh,fds,fdl]); Vprev=np.nanmean([dh,ds,dl]); level=np.nanmean([v['hazard_score'],v['SimpleShock'],v['LiveDeficit']])
  if level>=np.nanmean([hz_cut,0.70,0.85]) and V<0: regime='high_falling'
  elif level<np.nanmean([hz_cut,0.70,0.85]) and V>0: regime='moderate_rising'
  elif V>0: regime='high_rising'
  else: regime='moderate_falling'
  return {'i':i,'orphan':bool(test.orphan.iloc[i]),'hazard':v['hazard_score'],'shock':v['SimpleShock'],'deficit':v['LiveDeficit'],'rr':rr0,'velocity_forward':V,'velocity_pre':Vprev,'level':level,'regime':regime}
 rows=[one(i) for i in range(len(test)) if bool(test.crash72.iloc[i])]
 ed=pd.DataFrame(rows); oe=ed[ed.orphan]; ne=ed[~ed.orphan]
 def summary(f):
  x=pd.to_numeric(f.velocity_forward,errors='coerce').dropna(); return {'n':int(len(f)),'velocity_median':float(x.median()) if len(x) else None,'velocity_mean':float(x.mean()) if len(x) else None,'positive_velocity_rate':float((x>0).mean()) if len(x) else None,'regime_counts':f.regime.value_counts().to_dict()}
 result={'experiment':'hydra_crash72_orphan_velocity_court_v1','holdout_year':2024,'train_years':'2020-2023','cuts':{'rr_p20_train':rr_cut,'hazard_p80_train':hz_cut},'class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'orphan':summary(oe),'non_orphan_crash72':summary(ne)}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
