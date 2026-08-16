"""Strict rolling-origin generalization test for the frozen relative-recovery signal.

Question: does rr_recovery_minus_burden recur out of sample across time when both
model fitting and probability calibration are learned only from prior years?
2024 is a final frozen holdout; 2021-2023 are rolling test years.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler
from hydra_relative_recovery_court_v1 import history

TARGET = "Crash72"
FEATURE = "rr_recovery_minus_burden"

def fit_raw(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    tr = train.dropna(subset=[FEATURE, TARGET])
    if tr[TARGET].nunique() < 2:
        return np.full(len(test), np.nan)
    sc = StandardScaler(); m = LogisticRegression(max_iter=2000, class_weight="balanced", C=.5)
    X = sc.fit_transform(tr[[FEATURE]].astype(float)); m.fit(X, tr[TARGET].astype(int))
    Xt = sc.transform(test[[FEATURE]].fillna(tr[FEATURE].median()).astype(float))
    return m.predict_proba(Xt)[:,1]

def fold_oof(train: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    parts = []
    years = sorted(pd.to_datetime(train.open_time, utc=True).dt.year.unique())
    for year in years[1:]:
        tr = train[pd.to_datetime(train.open_time, utc=True).dt.year < year]
        va = train[pd.to_datetime(train.open_time, utc=True).dt.year == year]
        if tr[TARGET].nunique() < 2 or va.empty: continue
        p = fit_raw(tr, va)
        ok = np.isfinite(p)
        parts.append((p[ok], va.loc[ok, TARGET].astype(int).to_numpy()))
    if not parts: return np.array([]), np.array([])
    return np.concatenate([x for x,_ in parts]), np.concatenate([y for _,y in parts])

def platt_fit(oof_p: np.ndarray, oof_y: np.ndarray):
    x = np.log(np.clip(oof_p,1e-7,1-1e-7)/(1-np.clip(oof_p,1e-7,1-1e-7))).reshape(-1,1)
    m = LogisticRegression(max_iter=2000); m.fit(x,oof_y); return m

def score(y,p):
    p=np.clip(np.asarray(p,float),1e-7,1-1e-7); y=np.asarray(y,int)
    return {
      "n":int(len(y)),"events":int(y.sum()),"prevalence":float(y.mean()),
      "auc":float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
      "pr_auc":float(average_precision_score(y,p)) if y.sum()>0 else None,
      "brier":float(brier_score_loss(y,p)),"logloss":float(log_loss(y,p,labels=[0,1])),
      "mean_prediction":float(p.mean())}

def main(csv: Path, out: Path):
    raw=pd.read_csv(csv); d=history(raw)
    assert len(raw)==43848
    assert int(((d.entry_path=="3_to_4")&(d.episode_age_h==1)).sum())==169
    d["year"]=pd.to_datetime(d.open_time,utc=True).dt.year
    results=[]
    for year in (2021,2022,2023,2024):
        tr=d[d.year<year].copy(); te=d[d.year==year].copy()
        if tr.empty or te.empty: continue
        rawp=fit_raw(tr,te); ok=np.isfinite(rawp)
        y=te.loc[ok,TARGET].astype(int).to_numpy(); rawp=rawp[ok]
        oof_p,oof_y=fold_oof(tr)
        if len(oof_y)>0 and len(np.unique(oof_y))==2:
            cal=platt_fit(oof_p,oof_y)
            z=np.log(np.clip(rawp,1e-7,1-1e-7)/(1-np.clip(rawp,1e-7,1-1e-7)))
            calp=cal.predict_proba(z.reshape(-1,1))[:,1]
        else: calp=rawp
        results.append({"year":year,"raw":score(y,rawp),"platt":score(y,calp),"oof_rows":int(len(oof_y)),"oof_events":int(oof_y.sum())})
    payload={"experiment":"hydra_relative_recovery_generalization_court_v1","feature":FEATURE,"protocol":"strict rolling-origin; each fold trained only on prior years; Platt calibration fit on prior-year OOF only","final_holdout":2024,"folds":results}
    out.write_text(json.dumps(payload,indent=2)); print(json.dumps(payload,indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
