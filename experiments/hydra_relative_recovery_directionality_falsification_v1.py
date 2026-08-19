"""Directionality-aware falsification for recovery-minus-burden.

Runs the original feature with both orientations and compares the result under
several scoring modes. This isolates sign inversion from genuine absence of
information without changing the canonical spine.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from hydra_relative_recovery_court_v1 import history

TARGET = "Crash72"
FEATURE = "rr_recovery_minus_burden"
HOLDOUT = 2024
PERIOD = 72

def fit_auc(train: pd.DataFrame, test: pd.DataFrame, col: str, sign: float = 1.0):
    a = train.dropna(subset=[col, TARGET]).copy()
    b = test.dropna(subset=[col, TARGET]).copy()
    if a[TARGET].nunique() != 2 or b[TARGET].nunique() != 2:
        return None
    model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=1600, class_weight="balanced", C=.5, solver="liblinear"))
    model.fit((a[[col]] * sign).astype(float), a[TARGET].astype(int))
    p = model.predict_proba((b[[col]] * sign).astype(float))[:, 1]
    return float(roc_auc_score(b[TARGET].astype(int), p))

def rank_auc(train: pd.DataFrame, test: pd.DataFrame, col: str, sign: float = 1.0):
    a = train.dropna(subset=[col, TARGET]).copy(); b = test.dropna(subset=[col, TARGET]).copy()
    if a[TARGET].nunique() != 2 or b[TARGET].nunique() != 2 or len(a[a[TARGET]==0]) < 20 or len(a[a[TARGET]==1]) < 5:
        return None
    x0 = (a.loc[a[TARGET]==0, col].astype(float) * sign).to_numpy()
    x1 = (a.loc[a[TARGET]==1, col].astype(float) * sign).to_numpy()
    vals = b[col].astype(float).to_numpy() * sign
    p = np.array([(np.mean(x1 <= v) + np.mean(x0 <= v))/2 for v in vals])
    return float(roc_auc_score(b[TARGET].astype(int), p))

def nonoverlap(d, offset):
    x = d.sort_values("open_time").reset_index(drop=True).copy()
    h = pd.to_datetime(x.open_time, utc=True).astype("int64") // 10**9 // 3600
    x["_anchor"] = ((h-offset)//PERIOD)*PERIOD + offset
    return x.groupby("_anchor", as_index=False).first()

def main(csv: Path, out: Path):
    d = history(pd.read_csv(csv))
    rows=[]
    for off in range(PERIOD):
        x = nonoverlap(d, off)
        tr = x[x.open_time.dt.year < HOLDOUT]
        te = x[x.open_time.dt.year == HOLDOUT]
        for sign in (1.0, -1.0):
            rows.append({"offset":off,"sign":sign,"logistic_auc":fit_auc(tr,te,FEATURE,sign),"rank_auc":rank_auc(tr,te,FEATURE,sign)})
    frame = pd.DataFrame(rows)
    payload={
        "experiment":"hydra_relative_recovery_directionality_falsification_v1",
        "feature":FEATURE,
        "protocol":"2024 frozen holdout; 72 non-overlap phase offsets; original logistic estimator and original rank court, both feature orientations",
        "summary":{
            "logistic_plus_median":float(frame.loc[frame.sign==1,'logistic_auc'].median()),
            "logistic_minus_median":float(frame.loc[frame.sign==-1,'logistic_auc'].median()),
            "rank_plus_median":float(frame.loc[frame.sign==1,'rank_auc'].median()),
            "rank_minus_median":float(frame.loc[frame.sign==-1,'rank_auc'].median()),
        },
        "offsets":rows,
    }
    out.write_text(json.dumps(payload,indent=2,allow_nan=True)); print(json.dumps(payload,indent=2,allow_nan=True))

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
