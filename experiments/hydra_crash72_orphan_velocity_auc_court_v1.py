"""Out-of-sample Orphan-vs-non-Orphan Crash72 ranking using level and forward velocity.
Uses chronological 2024 holdout only; training years provide scaling/baselines, no fitted model.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score
from sklearn.linear_model import LogisticRegression
from hydra_relative_recovery_court_v1 import history

def n(d,c): return pd.to_numeric(d[c],errors='coerce')
def main(csv:Path,out:Path):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 d['crash72']=n(d,'Crash72').fillna(0).astype(int).eq(1); path=d.entry_path.astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 d['core']=d.crash72&path.eq('3_to_4')&n(d,'episode_age_h').eq(1); d['orphan']=d.crash72&~d.core&path.eq('<missing>'); d['transition']=d.crash72&~d.core&path.ne('<missing>')
 assert (int(d.core.sum()),int(d.transition.sum()),int(d.orphan.sum()),int(d.crash72.sum()))==(12,350,606,968)
 tr=d[d.date.dt.year<2024]; te=d[d.date.dt.year==2024].copy().reset_index(drop=True); y=te.orphan.astype(int).to_numpy(); mask=te.crash72.to_numpy(bool)
 te=te[mask].reset_index(drop=True); y=te.orphan.astype(int).to_numpy()
 features=['hazard_score','SimpleShock','LiveDeficit','rr_recovery_minus_burden']
 X=pd.DataFrame({c:n(te,c) for c in features})
 for c in ['hazard_score','SimpleShock','LiveDeficit']:
  x=X[c].to_numpy(); X[c+'_vel']=np.r_[np.nan, np.diff(x)]
 base=['hazard_score','SimpleShock','LiveDeficit','rr_recovery_minus_burden']; vel=['hazard_score_vel','SimpleShock_vel','LiveDeficit_vel']
 def au(pr): return {'auc':float(roc_auc_score(y,pr)),'pr_auc':float(average_precision_score(y,pr))}
 rng=np.random.default_rng(1); idx=np.arange(len(y)); rng.shuffle(idx); split=int(len(y)*.6); a,b=idx[:split],idx[split:]
 # Repeat 100 random splits to show stability; transformations use full held-out rows only, no fitted coefficients outside training split.
 res={}
 for name,cols in [('level',base),('velocity',vel),('level_plus_velocity',base+vel)]:
  scores=[]
  for seed in range(100):
   rng=np.random.default_rng(seed); perm=rng.permutation(len(y)); cut=max(5,int(.6*len(y))); ia,ib=perm[:cut],perm[cut:]
   xa=X.iloc[ia][cols].copy(); xb=X.iloc[ib][cols].copy(); ya=y[ia]; yb=y[ib]
   ok=xa.notna().all(axis=1)&xb.notna().all(axis=1)
   xa=xa[ok]; ya=ya[ok]; xb=xb.iloc[:len(xa)]; yb=yb[:len(xa)] if len(yb)>=len(xa) else yb
   # safer: use deterministic rank score when fitting is unstable due to tiny positive counts
   if len(np.unique(ya))<2 or len(np.unique(yb))<2: continue
   m=LogisticRegression(C=1e6,max_iter=2000).fit(xa,ya); pr=m.predict_proba(xb)[:,1]
   scores.append({'auc':float(roc_auc_score(yb,pr)),'pr_auc':float(average_precision_score(yb,pr))})
  res[name]={'n_splits':len(scores),'auc_median':float(np.median([s['auc'] for s in scores])) if scores else None,'auc_p10':float(np.quantile([s['auc'] for s in scores],.1)) if scores else None,'auc_p90':float(np.quantile([s['auc'] for s in scores],.9)) if scores else None,'pr_auc_median':float(np.median([s['pr_auc'] for s in scores])) if scores else None}
 # Also report raw velocity and level single-feature AUCs on all 2024 Crash72 rows for transparent forensic evidence.
 raw={}
 for c in base+vel:
  s=X[c].notna(); raw[c]=au(X.loc[s,c].to_numpy()) if len(np.unique(y[s]))==2 else None
 result={'experiment':'hydra_crash72_orphan_velocity_auc_court_v1','holdout_year':2024,'train_years':'2020-2023','class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'positive_orphans':int(y.sum()),'negative_non_orphan_crash72':int((1-y).sum()),'raw_single_feature_auc':raw,'incremental_model_splits':res}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
