"""HYDRA Crash-Horizon Boundary Court.

Reconstruct horizon labels from immutable native 3_to_4 event starts, then
first validate that the 72h reconstruction reproduces the native Crash72 label.
Only after that validation do we compare RR directionality across 24/72/168h.
No horizon is selected for modeling.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, brier_score_loss
from hydra_relative_recovery_court_v1 import history

FEATURE = "rr_recovery_minus_burden"
HORIZONS = (24, 72, 168)
OFFSETS = (-168, -72, -48, -24, -12, -6, -1, 0, 1, 6, 12, 24, 48, 72, 168)


def fit_auc(train, test, feature, target):
    tr=train.dropna(subset=[feature,target]); te=test.dropna(subset=[feature,target])
    if len(tr)<200 or tr[target].nunique()<2 or te[target].nunique()<2:return None
    m=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(max_iter=2000,class_weight="balanced",C=.5,solver="liblinear"))
    m.fit(tr[[feature]].astype(float),tr[target].astype(int)); p=m.predict_proba(te[[feature]].astype(float))[:,1]
    return {"auc":float(roc_auc_score(te[target],p)),"brier":float(brier_score_loss(te[target],p)),"n":int(len(te)),"events":int(te[target].sum()),"prevalence":float(te[target].mean())}


def build_targets(d):
    t=pd.to_datetime(d.open_time,utc=True).astype("int64")//10**9
    event_times=pd.to_datetime(d.loc[(d.entry_path=="3_to_4") & (d.episode_age_h==1),"open_time"],utc=True).astype("int64").to_numpy()/1e9
    out={}
    arr=t.to_numpy()
    for h in HORIZONS:
        horizon_seconds=h*3600
        out[f"Crash{h}"]=np.array([np.any((event_times>ts) & (event_times<=ts+horizon_seconds)) for ts in arr],dtype=int)
    return out


def main(csv:Path,out:Path):
    raw=pd.read_csv(csv); d=history(raw); assert len(raw)==43848
    d=d.sort_values("open_time").reset_index(drop=True); d["year"]=pd.to_datetime(d.open_time,utc=True).dt.year
    targets=build_targets(d)
    for k,v in targets.items(): d[k]=v
    agreement=float((d["Crash72"]==d["Crash72"]).mean())
    native_72=pd.to_numeric(raw["Crash72"],errors="coerce").fillna(0).astype(int).to_numpy()
    recon_72=d["Crash72"].to_numpy()
    exact=float(np.mean(native_72==recon_72)); xor=int(np.sum(native_72!=recon_72))
    if exact < 0.95:
        raise SystemExit(json.dumps({"status":"HARD_STOP","reason":"reconstructed Crash72 does not reproduce native Crash72","agreement":exact,"mismatches":xor},indent=2))
    tr=d[d.year<2024]; te=d[d.year==2024]
    rows={}
    for h in HORIZONS:
        target=f"Crash{h}"
        vals=[]
        for off in OFFSETS:
            c=f"rr_{off:+d}h"; d[c]=d[FEATURE].shift(off)
            r=fit_auc(tr,te,c,target)
            vals.append({"offset_h":off,**(r or {"auc":None,"brier":None,"n":0,"events":0,"prevalence":None})})
        rows[target]=vals
    payload={"experiment":"hydra_crash_horizon_boundary_court_v1","protocol":"native 3_to_4 starts reconstruct Crash24/72/168; Crash72 reconstruction must agree >=95% with native label; frozen 2024; dense lead/lag sweep; no horizon selected","canonical_rows":43848,"h3_starts":int(((d.entry_path=="3_to_4")&(d.episode_age_h==1)).sum()),"crash72_reconstruction_agreement":exact,"crash72_reconstruction_mismatches":xor,"results":rows}
    out.write_text(json.dumps(payload,indent=2)); print(json.dumps(payload,indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
