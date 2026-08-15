"""HYDRA Head Incrementality Court V1.

Frozen scientific evaluation of head incrementality. 2024 is untouched until
all configurations are fixed. Every configuration logs discrimination,
probability quality, calibration, prevalence, counts, and walk-forward
stability. No feature selection is performed on the holdout.
"""
from __future__ import annotations
import argparse, json, platform
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
    brier_score_loss, log_loss, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

TARGET="Crash72"
YEARS=(2020,2021,2022,2023); HOLDOUT=2024
HEAD_FEATURES={
 "Hazard":["hazard_score"],
 "Burden":["LiveDeficit__lag6"],
 "Recovery":["RecoveryWeakness_v1__lag6"],
 "Persistence":["age__log","episode_starts24","episode_starts48"],
 "Trajectory":["SimpleShock__mean24","hazard_score__mean6","hazard__accel"],
}
SEQUENCE=[[],["Hazard"],["Hazard","Burden"],["Hazard","Burden","Recovery"],
 ["Hazard","Burden","Recovery","Persistence"],["Hazard","Burden","Recovery","Persistence","Trajectory"]]


def make_history(d):
 d=d.copy(); d["open_time"]=pd.to_datetime(d["open_time"]); d=d.sort_values("open_time").reset_index(drop=True)
 for c in ["SimpleShock","LiveDeficit","RecoveryWeakness_v1","hazard_score"]:
  s=d[c].astype(float)
  for lag in (1,3,6,12,24,48,72): d[f"{c}__lag{lag}"]=s.shift(lag)
  for w in (6,24,48):
   d[f"{c}__mean{w}"]=s.shift(1).rolling(w,min_periods=3).mean()
   d[f"{c}__std{w}"]=s.shift(1).rolling(w,min_periods=3).std()
   d[f"{c}__delta{w}"]=s-s.shift(w)
 d["hazard__accel"]=d["hazard_score"].diff()-d["hazard_score"].diff().shift(1)
 d["age__log"]=np.log1p(np.maximum(d["episode_age_h"].astype(float),0))
 starts=((d["entry_path"]=="3_to_4")&(d["episode_age_h"]==1)).astype(int)
 for w in (24,48,72): d[f"episode_starts{w}"]=starts.shift(1).rolling(w,min_periods=1).sum()
 return d


def predict(train,test,cols):
 if not cols: return np.full(len(test),train[TARGET].mean(),dtype=float)
 m=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(max_iter=1500,class_weight="balanced",C=.5,solver="liblinear"))
 m.fit(train[cols].astype(float),train[TARGET].astype(int)); return m.predict_proba(test[cols].astype(float))[:,1]


def metrics(y,p):
 y=np.asarray(y,dtype=int); p=np.clip(np.asarray(p,dtype=float),1e-6,1-1e-6)
 auc=float(roc_auc_score(y,p)) if np.unique(y).size==2 else .5
 pr=float(average_precision_score(y,p)) if np.unique(y).size==2 else float(y.mean())
 brier=float(brier_score_loss(y,p)); ll=float(log_loss(y,p,labels=[0,1]))
 bacc=float(balanced_accuracy_score(y,p>=.5))
 prevalence=float(y.mean())
 return {"n":int(len(y)),"events":int(y.sum()),"prevalence":prevalence,
  "auc":auc,"pr_auc":pr,"brier":brier,"logloss":ll,"balanced_accuracy":bacc,
  "mean_prediction":float(p.mean()),"prediction_std":float(p.std())}


def cols_for(heads):
 return list(dict.fromkeys(c for h in heads for c in HEAD_FEATURES[h]))


def evaluate(d,heads,year):
 cols=cols_for(heads); tr=d[d.open_time.dt.year.isin([x for x in YEARS if x!=year])]; te=d[d.open_time.dt.year==year]
 p=predict(tr,te,cols); return metrics(te[TARGET].to_numpy(),p)


def holdout(d,heads):
 cols=cols_for(heads); tr=d[d.open_time.dt.year.isin(YEARS)]; te=d[d.open_time.dt.year==HOLDOUT]; p=predict(tr,te,cols)
 return metrics(te[TARGET].to_numpy(),p)


def null_permutation(d,heads,n=100,seed=123):
 cols=cols_for(heads); tr=d[d.open_time.dt.year.isin(YEARS)]; te=d[d.open_time.dt.year==HOLDOUT]; p=predict(tr,te,cols); y=te[TARGET].to_numpy(); rng=np.random.default_rng(seed)
 observed=roc_auc_score(y,p); null=np.array([roc_auc_score(rng.permutation(y),p) for _ in range(n)])
 return {"n":n,"observed_auc":float(observed),"null_mean_auc":float(null.mean()),"null_p95_auc":float(np.quantile(null,.95)),"separation":float(observed-np.quantile(null,.95))}


def main(csv,out):
 raw=pd.read_csv(csv); d=make_history(raw)
 assert len(raw)==43848
 starts=((d.entry_path=="3_to_4")&(d.episode_age_h==1)).sum(); assert int(starts)==169
 results=[]; baseline=None
 for heads in SEQUENCE:
  wf={str(y):evaluate(d,heads,y) for y in YEARS}
  h=holdout(d,heads); row={"heads":heads or ["BASELINE"],"features":cols_for(heads),"walk_forward":wf,"holdout_2024":h,"null_control":null_permutation(d,heads)}
  results.append(row)
  if baseline is not None:
   row["holdout_delta_vs_previous"]={k:h[k]-baseline[k] for k in ("auc","pr_auc","brier","logloss")}
  baseline=h
 for row in results:
  print(json.dumps(row,sort_keys=True))
 payload={"experiment":"hydra_head_incrementality_court_v1","canonical_rows":len(raw),"canonical_h3_starts":int(starts),"discovery_years":list(YEARS),"holdout_year":HOLDOUT,"python":platform.python_version(),"results":results}
 out.write_text(json.dumps(payload,indent=2))

if __name__=="__main__":
 ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
