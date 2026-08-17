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
# Canonical Layer1 does not contain live_up_pressure_proxy. Use only canonical columns
# plus causally reconstructed memory of those same canonical observations.
MEMORY=["pressure_delta","deficit_ema","shock_ema","recovery_ema","run_age_h_live"]


def add_memory(d, half_life):
    d=d.copy().sort_values("open_time").reset_index(drop=True)
    age=[]; cur=0; prev=None
    # Prefer canonical run-age if present; otherwise reconstruct from the canonical
    # episode label/path. Never invent an upstream pressure proxy.
    if "run_age_h_live" in d.columns:
        d["run_age_h_live"]=pd.to_numeric(d["run_age_h_live"],errors="coerce").fillna(0.0)
    else:
        keycol="episode_type" if "episode_type" in d.columns else ("entry_path" if "entry_path" in d.columns else None)
        if keycol is None: raise ValueError("canonical input lacks episode_type/entry_path for causal run-age reconstruction")
        for _,r in d.iterrows():
            key=r[keycol]
            if key!=prev: cur=0
            age.append(cur); cur+=1; prev=key
        d["run_age_h_live"]=age
    alpha=1-math.exp(-1/max(half_life,1e-9))
    for c,src in [("deficit_ema","LiveDeficit"),("shock_ema","SimpleShock"),("recovery_ema","RecoveryWeakness_v1")]:
        vals=pd.to_numeric(d[src],errors="coerce").fillna(0).to_numpy(); out=[]; state=0.0
        for i,v in enumerate(vals):
            reset=(i==0 or float(d.iloc[i]["run_age_h_live"])==0)
            state=float(v) if reset else alpha*float(v)+(1-alpha)*state; out.append(state)
        d[c]=out
    # pressure_delta is not fabricated from a missing proxy. Use first difference
    # of the canonical hazard_raw signal as the nearest canonical rate-of-change
    # observable, and report it explicitly as hazard_raw_delta.
    h=pd.to_numeric(d["hazard_raw"],errors="coerce").fillna(0.0)
    d["hazard_raw_delta"]=h-h.shift(1).fillna(h)
    d["pressure_delta"]=d["hazard_raw_delta"]
    d["freshness"]=np.exp(-pd.to_numeric(d["run_age_h_live"],errors="coerce").fillna(0.0)/max(half_life,1e-9))
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
    required=BASE+["LiveDeficit","SimpleShock","RecoveryWeakness_v1","hazard_raw","Crash72"]
    missing=[c for c in required if c not in d.columns]
    if missing: raise ValueError(f"canonical input missing required columns: {missing}")
    if "hazard_score" not in d: d["hazard_score"]=1/(1+np.exp(-pd.to_numeric(d["hazard_raw"],errors="coerce").fillna(0.0)-1.8))
    results={}
    for hl in [6,12,24,36,48,72,120,168,240]:
        x=add_memory(d,hl); folds={}
        for y in DISCOVERY:
            tr=x[x.open_time.dt.year<y]; te=x[x.open_time.dt.year==y]
            folds[str(y)]={"base":fit_score(tr,te,BASE),"full":fit_score(tr,te,BASE+MEMORY)}
        tr=x[x.open_time.dt.year.isin(DISCOVERY)]; te=x[x.open_time.dt.year==HOLDOUT]
        results[str(hl)]={"discovery":folds,"holdout":{"base":fit_score(tr,te,BASE),"full":fit_score(tr,te,BASE+MEMORY)},"conditioned_2024_auc":{m:conditioned_auc(te,m) for m in MEMORY}}
    payload={"experiment":"tiamat_memory_discrimination_v2","base":BASE,"memory":MEMORY,"note":"pressure_delta is canonical hazard_raw first difference; no live_up_pressure_proxy was inferred or fabricated","results":results}
    out.write_text(json.dumps(payload,indent=2,default=str)); print(out.read_text())

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)