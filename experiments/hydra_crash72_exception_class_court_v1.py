"""Classify native Crash72 into Core, Transition, and Orphan targets and score existing signals."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,brier_score_loss,log_loss,roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from hydra_relative_recovery_court_v1 import history

PREDICTORS=['rr_recovery_minus_burden','hazard_score','hazard_raw','LiveDeficit','SimpleShock','RecoveryWeakness_v1']
TARGETS=['core','transition','orphan']
DISCOVERY=(2020,2021,2022,2023); HOLDOUT=2024

def fit_predict(tr,te,col,target):
    m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=1600,class_weight='balanced',C=.5,solver='liblinear'))
    m.fit(tr[[col]].astype(float),tr[target].astype(int)); return m.predict_proba(te[[col]].astype(float))[:,1]

def metrics(y,p):
    y=np.asarray(y,int); p=np.clip(np.asarray(p,float),1e-6,1-1e-6)
    return {'n':int(len(y)),'events':int(y.sum()),'prevalence':float(y.mean()),'auc':float(roc_auc_score(y,p)) if np.unique(y).size==2 else None,'pr_auc':float(average_precision_score(y,p)) if np.unique(y).size==2 else None,'brier':float(brier_score_loss(y,p)),'logloss':float(log_loss(y,p,labels=[0,1]))}

def main(csv:Path,out:Path):
    raw=pd.read_csv(csv); d=history(raw).sort_values('open_time').reset_index(drop=True); assert len(raw)==43848
    age=pd.to_numeric(d.episode_age_h,errors='coerce')
    base=(d.entry_path.astype(str).eq('3_to_4') & age.eq(1))
    native=pd.to_numeric(d.Crash72,errors='coerce').fillna(0).astype(int).eq(1)
    ex=native & ~base
    core=(native & base).astype(int)
    transition=(ex & d.entry_path.astype(str).ne('none') & d.entry_path.notna()).astype(int)
    orphan=(ex & (d.entry_path.astype(str).eq('none') | d.entry_path.isna())).astype(int)
    targets={'core':core,'transition':transition,'orphan':orphan}
    for k,v in targets.items(): d[k]=v
    reports={}
    for target in TARGETS:
        years={}
        for year in DISCOVERY:
            tr=d[d.open_time.dt.year<year]; te=d[d.open_time.dt.year==year]
            if tr[target].sum()==0: years[str(year)]={'n':len(te),'events':0,'auc':None}
            else: years[str(year)]=metrics(te[target],fit_predict(tr,te,'rr_recovery_minus_burden',target))
        tr=d[d.open_time.dt.year.isin(DISCOVERY)]; te=d[d.open_time.dt.year==HOLDOUT]
        reports[target]={'discovery_rr':years,'holdout':{c:metrics(te[target],fit_predict(tr,te,c,target)) for c in PREDICTORS}}
    out.write_text(json.dumps({'experiment':'hydra_crash72_exception_class_court_v1','protocol':'mutually exclusive Core/Transition/Orphan targets; predictors fixed in advance; 2024 frozen holdout; strict temporal training','counts':{k:int(v.sum()) for k,v in targets.items()},'reports':reports},indent=2)); print(out.read_text())
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
