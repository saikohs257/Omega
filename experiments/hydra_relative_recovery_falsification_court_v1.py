"""Temporal falsification controls for recovery-minus-burden.

A real time-local structural signal should weaken when temporal alignment is
intentionally destroyed. We compare the exact signal with 24h/168h feature
lags, a 24h feature lead placebo, and deterministic within-month block shuffles.
No control is promoted; this is a falsification experiment.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from hydra_relative_recovery_court_v1 import history

TARGET="Crash72"; FEATURE="rr_recovery_minus_burden"

def auc_for(train,test,col):
    tr=train.dropna(subset=[col,TARGET]); te=test.dropna(subset=[col,TARGET])
    if len(tr)<200 or tr[TARGET].nunique()<2 or te[TARGET].nunique()<2:return None
    m=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(max_iter=2000,class_weight="balanced",C=.5,solver="liblinear"))
    m.fit(tr[[col]].astype(float),tr[TARGET].astype(int)); p=m.predict_proba(te[[col]].astype(float))[:,1]
    return float(roc_auc_score(te[TARGET],p))

def main(csv:Path,out:Path):
    raw=pd.read_csv(csv); d=history(raw); assert len(raw)==43848
    assert int(((d.entry_path=="3_to_4")&(d.episode_age_h==1)).sum())==169
    d=d.sort_values("open_time").reset_index(drop=True); d["year"]=pd.to_datetime(d.open_time,utc=True).dt.year
    d["rr_lag24"]=d[FEATURE].shift(24); d["rr_lag168"]=d[FEATURE].shift(168); d["rr_lead24"]=d[FEATURE].shift(-24)
    real=auc_for(d[d.year<2024],d[d.year==2024],FEATURE)
    controls={c:auc_for(d[d.year<2024],d[d.year==2024],c) for c in ["rr_lag24","rr_lag168","rr_lead24"]}
    rng=np.random.default_rng(20240815); shuffled=[]
    x=d[FEATURE].to_numpy().copy(); months=d.open_time.dt.to_period("M").astype(str).to_numpy()
    for _ in range(25):
        xs=x.copy()
        for key in np.unique(months):
            idx=np.flatnonzero(months==key); xs[idx]=xs[rng.permutation(idx)]
        d["rr_block_shuffle"]=xs
        shuffled.append(auc_for(d[d.year<2024],d[d.year==2024],"rr_block_shuffle"))
    vals=[v for v in shuffled if v is not None]
    payload={"experiment":"hydra_relative_recovery_falsification_court_v1","protocol":"2024 frozen holdout; feature alignment intentionally shifted or block-shuffled; no control is used for model selection","canonical_rows":43848,"observed_auc":real,"controls":controls,"block_shuffle":{"n":len(vals),"mean_auc":float(np.mean(vals)) if vals else None,"p95_auc":float(np.quantile(vals,.95)) if vals else None,"min_auc":float(np.min(vals)) if vals else None,"max_auc":float(np.max(vals)) if vals else None},"interpretation_rule":"observed signal is stronger evidence if correct-time AUC materially exceeds shifted and block-shuffled controls; a strong lead/shift control is a warning for temporal leakage or broad autocorrelation"}
    out.write_text(json.dumps(payload,indent=2)); print(json.dumps(payload,indent=2))
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
