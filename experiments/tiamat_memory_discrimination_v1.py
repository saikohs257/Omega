from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

DISCOVERY=(2020,2021,2022,2023); HOLDOUT=2024
BASE=["SimpleShock","LiveDeficit","RecoveryWeakness_v1","hazard_score"]
MEMORY=["freshness","pressure_delta","pressure_ema","deficit_ema","shock_ema","recovery_ema","run_age_h_live"]

def add_memory(d, half_life):
    d=d.copy().sort_values("open_time").reset_index(drop=True)
    if "run_age_h_live" not in d.columns:
        age=[]; cur=0; prev=None
        for _,r in d.iterrows():
            key=r.get("episode_type",r.get("entry_path"))
            if key!=prev: cur=0
            age.append(cur); cur+=1; prev=key
        d["run_age_h_live"]=age
    alpha=1-math.exp(-1/max(half_life,1e-9))
    for c,src in [("pressure_ema","live_up_pressure_proxy"),("deficit_ema","LiveDeficit"),("shock_ema","SimpleShock"),("recovery_ema","RecoveryWeakness_v1")]:
        vals=pd.to_numeric(d[src],errors="coerce").fillna(0).to_numpy(); out=[]; state=0.0
        for i,v in enumerate(vals):
            reset=(i==0 or float(d.iloc[i]["run_age_h_live"])==0)
            state=float(v) if reset else alpha*float(v)+(1-alpha)*state; out.append(state)
        d[c]=out
    p=pd.to_numeric(d["live_up_pressure_proxy"],errors="coerce").fillna(0)
    d["pressure_delta"]=p-p.shift(1).fillna(p)
    d["freshness"]=np.exp(-pd.to_numeric(d["run_age_h_live"],errors="coerce").fillna(0)/half_life)
    return d

def fit_score(tr,te,cols):
    m=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(max_iter=1600,class_weight="balanced",solver="liblinear",C=.5))
    m.fit(tr[cols].astype(float),tr.Crash72.astype(int)); p=m.predict_proba(te[cols].astype(float))[:,1]; y=te.Crash72.astype(int).to_numpy()
    return {"auc":float(roc_auc_score(y,p)),"brier":float(brier_score_loss(y,p)),"logloss":float(log_loss(y,p,labels=[0,1]))}

def conditioned_auc(te,col):
    q=te.copy()
    for c in BASE: q[c+"_bin"]=pd.qcut(q[c],20,duplicates="drop")
    q["stratum"]=q[[c+"_bin" for c in BASE]].astype(str).agg("|".join,axis=1)
    vals=[]
    for _,g in q.groupby("stratum",observed=False):
        if len(g)>=8 and g.Crash72.nunique()==2: vals.append((len(g),roc_auc_score(g.Crash72,g[col])))
    return None if not vals else float(sum(n*a for n,a in vals)/sum(n for n,_ in vals))

def main(csv,out):
    d=pd.read_csv(csv); d["open_time"]=pd.to_datetime(d["open_time"],utc=True); d=d.sort_values("open_time").reset_index(drop=True)
    if "hazard_score" not in d: d["hazard_score"]=0.0
    results={}
    for hl in [6,12,24,36,48,72,120,168,240]:
        x=add_memory(d,hl); folds={}
        for y in DISCOVERY:
            tr=x[x.open_time.dt.year<y]; te=x[x.open_time.dt.year==y]
            folds[str(y)]={"base":fit_score(tr,te,BASE),"full":fit_score(tr,te,BASE+MEMORY)}
        tr=x[x.open_time.dt.year.isin(DISCOVERY)]; te=x[x.open_time.dt.year==HOLDOUT]
        results[str(hl)]={"discovery":folds,"holdout":{"base":fit_score(tr,te,BASE),"full":fit_score(tr,te,BASE+MEMORY)},"conditioned_2024_auc":{m:conditioned_auc(te,m) for m in MEMORY}}
    payload={"experiment":"tiamat_memory_discrimination_v1","base":BASE,"memory":MEMORY,"results":results}
    out.write_text(json.dumps(payload,indent=2,default=str)); print(out.read_text())

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
