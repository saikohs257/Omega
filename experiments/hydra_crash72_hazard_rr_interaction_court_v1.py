"""Crash72 Hazard/RR interaction court. Frozen taxonomy, prior-year training, 2024 holdout."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss,log_loss
from hydra_relative_recovery_court_v1 import history
from hydra_crash72_incremental_orphan_court_v1 import normalized_entry_path

def metrics(y,p):
 y=np.asarray(y,int); p=np.clip(np.asarray(p,float),1e-6,1-1e-6)
 return {'n':int(len(y)),'positives':int(y.sum()),'auc':float(roc_auc_score(y,p)) if y.sum()>0 and y.sum()<len(y) else None,'pr_auc':float(average_precision_score(y,p)) if y.sum()>0 else None,'brier':float(brier_score_loss(y,p)),'logloss':float(log_loss(y,p,labels=[0,1]))}
def main(csv,out):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int); path=normalized_entry_path(d['entry_path']); age=pd.to_numeric(d['episode_age_h'],errors='coerce')
 base=path.eq('3_to_4')&age.eq(1); ex=y.eq(1)&~base; core=y.eq(1)&base; transition=ex&path.ne('<missing>'); orphan=ex&path.eq('<missing>')
 counts={'core':int(core.sum()),'transition':int(transition.sum()),'orphan':int(orphan.sum()),'crash72':int(y.sum())}; assert counts=={'core':12,'transition':350,'orphan':606,'crash72':968}, counts
 d['target_core']=core.astype(int); d['target_transition']=transition.astype(int); d['target_orphan']=orphan.astype(int)
 rows=[]
 for year in sorted(d.date.dt.year.unique()):
  if int(year)<2021: continue
  train=d[d.date.dt.year<year]; test=d[d.date.dt.year==year]
  for target in ['target_core','target_transition','target_orphan']:
   ytr=train[target].to_numpy(int); yt=test[target].to_numpy(int)
   if np.unique(ytr).size<2 or np.unique(yt).size<2: continue
   cols=['hazard_score','rr_recovery_minus_burden']; Xtr=train[cols].apply(pd.to_numeric,errors='coerce'); Xte=test[cols].apply(pd.to_numeric,errors='coerce'); med=Xtr.median(); Xtr=Xtr.fillna(med); Xte=Xte.fillna(med)
   hz=Xtr['hazard_score'].to_numpy(); rr=Xtr['rr_recovery_minus_burden'].to_numpy(); hz2=Xte['hazard_score'].to_numpy(); rr2=Xte['rr_recovery_minus_burden'].to_numpy()
   for name,Atr,Ate in [('Hazard',hz.reshape(-1,1),hz2.reshape(-1,1)),('RR',rr.reshape(-1,1),rr2.reshape(-1,1)),('Hazard+RR',np.column_stack([hz,rr]),np.column_stack([hz2,rr2])),('Hazard+RR+Interaction',np.column_stack([hz,rr,hz*rr]),np.column_stack([hz2,rr2,hz2*rr2]))]:
    m=LogisticRegression(max_iter=3000).fit(Atr,ytr); p=m.predict_proba(Ate)[:,1]; rows.append({'year':int(year),'target':str(target),'model':str(name),**metrics(yt,p)})
 result={'experiment':'hydra_crash72_hazard_rr_interaction_court_v1','class_counts':counts,'rows':rows}; out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
