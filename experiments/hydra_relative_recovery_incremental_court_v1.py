"""Nested temporal incrementality test for the frozen relative-recovery coordinate.

Question: does recovery-minus-burden add information beyond Hazard and Burden,
rather than merely rediscovering one of them?
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from hydra_relative_recovery_court_v1 import history

TARGET="Crash72"
CONFIGS={
 "Hazard":["hazard_l1"],
 "Hazard+Burden":["hazard_l1","burden_l1"],
 "Hazard+RR":["hazard_l1","rr_recovery_minus_burden"],
 "Hazard+Burden+RR":["hazard_l1","burden_l1","rr_recovery_minus_burden"],
}

def model():
    return make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(max_iter=2000,class_weight="balanced",C=.5,solver="liblinear"))

def fit_predict(tr,te,cols):
    m=model(); m.fit(tr[cols].astype(float),tr[TARGET].astype(int)); return m.predict_proba(te[cols].astype(float))[:,1]

def score(y,p):
    p=np.clip(np.asarray(p,float),1e-7,1-1e-7); y=np.asarray(y,int)
    return {"n":int(len(y)),"events":int(y.sum()),"prevalence":float(y.mean()),"auc":float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,"pr_auc":float(average_precision_score(y,p)) if y.sum()>0 else None,"brier":float(brier_score_loss(y,p)),"logloss":float(log_loss(y,p,labels=[0,1])),"mean_prediction":float(p.mean())}

def main(csv:Path,out:Path):
    raw=pd.read_csv(csv); d=history(raw); assert len(raw)==43848
    assert int(((d.entry_path=="3_to_4")&(d.episode_age_h==1)).sum())==169
    d["year"]=pd.to_datetime(d.open_time,utc=True).dt.year
    discovery={}
    for year in (2021,2022,2023):
        tr=d[d.year<year]; te=d[d.year==year]
        for name,cols in CONFIGS.items():
            if len(tr)<200 or te.empty or tr[TARGET].nunique()<2: continue
            discovery.setdefault(name,[]).append({"year":year,"metrics":score(te[TARGET],fit_predict(tr,te,cols))})
    hold=d[d.year==2024]; tr=d[d.year<2024]
    holdout={name:score(hold[TARGET],fit_predict(tr,hold,cols)) for name,cols in CONFIGS.items()}
    base=holdout["Hazard+Burden"]["auc"]; rr=holdout["Hazard+Burden+RR"]["auc"]
    payload={"experiment":"hydra_relative_recovery_incremental_court_v1","question":"Does recovery-minus-burden add information beyond Hazard and Burden?","selection":"No feature selection; configs fixed before holdout","discovery_walk_forward":discovery,"holdout_2024":holdout,"incremental_holdout":{"auc_delta_vs_hazard_burden":None if base is None or rr is None else float(rr-base),"brier_delta_vs_hazard_burden":float(holdout["Hazard+Burden+RR"]["brier"]-holdout["Hazard+Burden"]["brier"]),"logloss_delta_vs_hazard_burden":float(holdout["Hazard+Burden+RR"]["logloss"]-holdout["Hazard+Burden"]["logloss"])}}
    out.write_text(json.dumps(payload,indent=2)); print(json.dumps(payload,indent=2))
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
