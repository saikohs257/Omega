"""Incremental RR-vs-hazard court for Crash72 Core/Transition/Orphan classes."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss,log_loss
from sklearn.linear_model import LogisticRegression
from hydra_relative_recovery_court_v1 import history

def metrics(y,p):
    y=np.asarray(y,int); p=np.clip(np.asarray(p,float),1e-6,1-1e-6)
    return {'n':int(len(y)),'positives':int(y.sum()),'auc':float(roc_auc_score(y,p)) if y.sum()>0 and y.sum()<len(y) else None,'pr_auc':float(average_precision_score(y,p)) if y.sum()>0 else None,'brier':float(brier_score_loss(y,p)),'logloss':float(log_loss(y,p,labels=[0,1]))}
def main(csv,out):
    d=history(pd.read_csv(csv)); d['date']=d['open_time']; d=d.sort_values('date').reset_index(drop=True)
    assert len(d)==43848
    y0=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int)
    base=((d['entry_path'].astype(str)=='3_to_4')&(pd.to_numeric(d['episode_age_h'],errors='coerce')==1))
    ex=(y0==1)&(~base); trans=ex & d['entry_path'].notna() & d['entry_path'].astype(str).ne('nan'); orphan=ex & ~trans; core=y0.astype(bool)&base
    d['target_core']=core.astype(int); d['target_transition']=trans.astype(int); d['target_orphan']=orphan.astype(int)
    feature_map={'RR':'rr_recovery_minus_burden','Hazard':'hazard_score','LiveDeficit':'LiveDeficit','SimpleShock':'SimpleShock','RecoveryWeakness':'RecoveryWeakness_v1'}
    rows=[]
    for year in sorted(d.date.dt.year.unique()):
        if year<2021: continue
        train=d[d.date.dt.year<year]; test=d[d.date.dt.year==year]
        for target in ['target_core','target_transition','target_orphan']:
            ytr=train[target]; yt=test[target]
            if ytr.nunique()<2 or yt.nunique()<2: continue
            preds={}
            for name,col in feature_map.items():
                med=pd.to_numeric(train[col],errors='coerce').median(); xtr=pd.to_numeric(train[col],errors='coerce').fillna(med).to_numpy().reshape(-1,1); xt=pd.to_numeric(test[col],errors='coerce').fillna(med).to_numpy().reshape(-1,1)
                m=LogisticRegression(max_iter=2000).fit(xtr,ytr); preds[name]=m.predict_proba(xt)[:,1]; rows.append({'year':year,'target':target,'model':name,**metrics(yt,preds[name])})
            cols=['hazard_score','rr_recovery_minus_burden']; med=train[cols].apply(pd.to_numeric,errors='coerce').median(); xtr=train[cols].apply(pd.to_numeric,errors='coerce').fillna(med).to_numpy(); xt=test[cols].apply(pd.to_numeric,errors='coerce').fillna(med).to_numpy(); m=LogisticRegression(max_iter=2000).fit(xtr,ytr); rows.append({'year':year,'target':target,'model':'Hazard+RR',**metrics(yt,m.predict_proba(xt)[:,1])})
    result={'experiment':'hydra_crash72_incremental_orphan_court_v2','rows':rows,'class_counts':{k:int(d[k].sum()) for k in ['target_core','target_transition','target_orphan']}}
    out.write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
