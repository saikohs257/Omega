"""HYDRA conditional head ablation court V1.

Purpose: test whether candidate heads add independent information after
conditioning on previously retained heads. 2024 is a frozen holdout.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, balanced_accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

TARGET="Crash72"
FORBIDDEN={TARGET,"episode_type","duration_bucket","entry_path","regime_30d","hazard_bucket","recovery_gate","open_time","close"}
YEARS=(2020,2021,2022,2023)
HOLDOUT=2024

HEAD_FEATURES={
 "Hazard":["hazard_score"],
 "Burden":["LiveDeficit__lag6"],
 "Recovery":["RecoveryWeakness_v1__lag6"],
 "Persistence":["age__log","episode_starts24","episode_starts48"],
 "Trajectory":["SimpleShock__mean24","hazard_score__mean6","hazard__accel"],
}


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
 m=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(max_iter=1500,class_weight="balanced",C=.5,solver="liblinear"))
 m.fit(train[cols],train[TARGET].astype(int)); return m.predict_proba(test[cols])[:,1]


def metrics(y,p):
 return {"auc":float(roc_auc_score(y,p)),"pr_auc":float(average_precision_score(y,p)),"brier":float(brier_score_loss(y,p)),"logloss":float(log_loss(y,p,labels=[0,1])),"bacc":float(balanced_accuracy_score(y,p>=.5))}


def eval_nested(d,heads):
 cols=[]
 for h in heads: cols += HEAD_FEATURES[h]
 cols=list(dict.fromkeys(cols))
 rows=[]
 for y in YEARS:
  tr=d[d.open_time.dt.year.isin([x for x in YEARS if x!=y])]
  te=d[d.open_time.dt.year==y]
  if tr[TARGET].nunique()<2 or te[TARGET].nunique()<2: continue
  rows.append(metrics(te[TARGET].to_numpy(),predict(tr,te,cols)))
 return cols,rows


def main(csv,out):
 d=make_history(pd.read_csv(csv)); assert len(d)==43848, f"expected 43848 rows, got {len(d)}"
 starts=((d.entry_path=="3_to_4")&(d.episode_age_h==1)).sum(); assert starts==169, f"expected 169 H3 starts, got {starts}"
 sequence=[[],["Hazard"],["Hazard","Burden"],["Hazard","Burden","Recovery"],["Hazard","Burden","Recovery","Persistence"],["Hazard","Burden","Recovery","Persistence","Trajectory"]]
 results=[]
 for heads in sequence:
  cols,folds=eval_nested(d,heads)
  tr=d[d.open_time.dt.year.isin(YEARS)]; te=d[d.open_time.dt.year==HOLDOUT]
  p=predict(tr,te,cols) if cols else np.full(len(te),tr[TARGET].mean())
  hold=metrics(te[TARGET].to_numpy(),p)
  results.append({"heads":heads,"features":cols,"walk_forward":folds,"holdout_2024":hold})
  print(heads or ["BASELINE"],hold)
 for i in range(1,len(results)):
  a,b=results[i-1],results[i]
  print("DELTA",b["heads"][-1],"AUC",b["holdout_2024"]["auc"]-a["holdout_2024"]["auc"],"PR",b["holdout_2024"]["pr_auc"]-a["holdout_2024"]["pr_auc"],"Brier",b["holdout_2024"]["brier"]-a["holdout_2024"]["brier"],"LogLoss",b["holdout_2024"]["logloss"]-a["holdout_2024"]["logloss"])
 out.write_text(json.dumps(results,indent=2))

if __name__=="__main__":
 ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
