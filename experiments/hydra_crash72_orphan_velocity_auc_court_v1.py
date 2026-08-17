"""Continuous velocity-vs-level test for 2024 Crash72 Orphans.
Velocity is computed on the full chronological hourly holdout BEFORE selecting Crash72 rows.
Each split drops missing rows jointly; no positional truncation is allowed.
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
 d['crash72']=n(d,'Crash72').fillna(0).astype(int).eq(1)
 path=d.entry_path.astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 d['core']=d.crash72&path.eq('3_to_4')&n(d,'episode_age_h').eq(1); d['orphan']=d.crash72&~d.core&path.eq('<missing>'); d['transition']=d.crash72&~d.core&path.ne('<missing>')
 assert (int(d.core.sum()),int(d.transition.sum()),int(d.orphan.sum()),int(d.crash72.sum()))==(12,350,606,968)
 te=d[d.date.dt.year==2024].copy().reset_index(drop=True); crash=te.crash72.to_numpy(bool)
 y=te.loc[crash,'orphan'].astype(int).to_numpy()
 base=['hazard_score','SimpleShock','LiveDeficit','rr_recovery_minus_burden']; vel=['hazard_score_vel','SimpleShock_vel','LiveDeficit_vel']
 Xall=pd.DataFrame({c:n(te,c) for c in base})
 for c in ['hazard_score','SimpleShock','LiveDeficit']:
  Xall[c+'_vel']=Xall[c].diff()
 X=Xall.loc[crash].reset_index(drop=True)
 def au(x,yv):
  s=x.notna() & np.isfinite(x.to_numpy()); xx=x.loc[s].to_numpy(); yy=yv[s.to_numpy()]
  return {'auc':float(roc_auc_score(yy,xx)),'pr_auc':float(average_precision_score(yy,xx))} if len(np.unique(yy))==2 else None
 raw={c:au(X[c],y) for c in base+vel}
 res={}
 for name,cols in [('level',base),('velocity',vel),('level_plus_velocity',base+vel)]:
  scores=[]
  for seed in range(100):
   rng=np.random.default_rng(seed); perm=rng.permutation(len(y)); cut=max(5,int(.6*len(y))); ia,ib=perm[:cut],perm[cut:]
   train=X.iloc[ia][cols].copy(); test=X.iloc[ib][cols].copy(); yt=y[ia]; yv=y[ib]
   ok_train=train.notna().all(axis=1)&np.isfinite(train.to_numpy()).all(axis=1); ok_test=test.notna().all(axis=1)&np.isfinite(test.to_numpy()).all(axis=1)
   train=train.loc[ok_train]; yt=yt[ok_train.to_numpy()]; test=test.loc[ok_test]; yv=yv[ok_test.to_numpy()]
   if len(np.unique(yt))<2 or len(np.unique(yv))<2: continue
   m=LogisticRegression(C=1e6,max_iter=2000).fit(train,yt); pr=m.predict_proba(test)[:,1]
   scores.append({'auc':float(roc_auc_score(yv,pr)),'pr_auc':float(average_precision_score(yv,pr))})
  av=[s['auc'] for s in scores]; pv=[s['pr_auc'] for s in scores]
  res[name]={'n_splits':len(scores),'auc_median':float(np.median(av)) if av else None,'auc_p10':float(np.quantile(av,.1)) if av else None,'auc_p90':float(np.quantile(av,.9)) if av else None,'pr_auc_median':float(np.median(pv)) if pv else None}
 result={'experiment':'hydra_crash72_orphan_velocity_auc_court_v2','holdout_year':2024,'train_years':'2020-2023','class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'positive_orphans':int(y.sum()),'negative_non_orphan_crash72':int((1-y).sum()),'raw_single_feature_auc':raw,'incremental_model_splits':res,'velocity_definition':'hourly diff computed on full chronological 2024 holdout before Crash72 selection'}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
