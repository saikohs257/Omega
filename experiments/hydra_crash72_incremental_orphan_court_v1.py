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

def normalized_entry_path(s):
    p=s.astype('string').str.strip().str.lower()
    return p.replace({'':'<missing>','nan':'<missing>','none':'<missing>','null':'<missing>','<na>':'<missing>'}).fillna('<missing>')

def main(csv,out):
    d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
    assert len(d)==43848
    y0=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int)
    path=normalized_entry_path(d['entry_path'])
    base=(path.eq('3_to_4') & pd.to_numeric(d['episode_age_h'],errors='coerce').eq(1))
    ex=(y0==1)&(~base)
    core=(y0==1)&base
    transition=ex & path.ne('<missing>')
    orphan=ex & path.eq('<missing>')
    counts={'target_core':int(core.sum()),'target_transition':int(transition.sum()),'target_orphan':int(orphan.sum())}
    # Hard reconciliation against the canonical exception court: 12 + 350 + 606 = 968.
    assert int(y0.sum())==968, f'native Crash72 positives changed: {int(y0.sum())}'
    assert counts=={'target_core':12,'target_transition':350,'target_orphan':606}, f'class reconciliation failed: {counts}'
    assert int(core.sum()+transition.sum()+orphan.sum())==int(y0.sum())
    d['target_core']=core.astype(int); d['target_transition']=transition.astype(int); d['target_orphan']=orphan.astype(int)
    feature_map={'RR':'rr_recovery_minus_burden','Hazard':'hazard_score','LiveDeficit':'LiveDeficit','SimpleShock':'SimpleShock','RecoveryWeakness':'RecoveryWeakness_v1'}
    rows=[]
    for year in sorted(d.date.dt.year.unique()):
        if int(year)<2021: continue
        train=d[d.date.dt.year<year]; test=d[d.date.dt.year==year]
        for target in ['target_core','target_transition','target_orphan']:
            ytr=train[target]; yt=test[target]
            if ytr.nunique()<2 or yt.nunique()<2: continue
            for name,col in feature_map.items():
                med=pd.to_numeric(train[col],errors='coerce').median(); xtr=pd.to_numeric(train[col],errors='coerce').fillna(med).to_numpy().reshape(-1,1); xt=pd.to_numeric(test[col],errors='coerce').fillna(med).to_numpy().reshape(-1,1)
                m=LogisticRegression(max_iter=2000).fit(xtr,ytr); p=m.predict_proba(xt)[:,1]
                rows.append({'year':int(year),'target':str(target),'model':str(name),**metrics(yt,p)})
            cols=['hazard_score','rr_recovery_minus_burden']; med=train[cols].apply(pd.to_numeric,errors='coerce').median(); xtr=train[cols].apply(pd.to_numeric,errors='coerce').fillna(med).to_numpy(); xt=test[cols].apply(pd.to_numeric,errors='coerce').fillna(med).to_numpy(); m=LogisticRegression(max_iter=2000).fit(xtr,ytr); p=m.predict_proba(xt)[:,1]
            rows.append({'year':int(year),'target':str(target),'model':'Hazard+RR',**metrics(yt,p)})
    result={'experiment':'hydra_crash72_incremental_orphan_court_v4','class_counts':counts,'native_positive_rows':int(y0.sum()),'rows':rows}
    out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
