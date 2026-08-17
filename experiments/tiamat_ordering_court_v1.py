from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_raw"]
HORIZON_H = 6
MATCH_CALIPER = 0.05
MIN_SEPARATION_H = 168
NULL_N = 2000
HISTORY_WINDOWS = (12, 24, 48)


def make_features(d: pd.DataFrame) -> pd.DataFrame:
    d = d.sort_values("open_time").reset_index(drop=True).copy()
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    for c in BASE:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    for w in HISTORY_WINDOWS:
        prev = d["LiveDeficit"].shift(1)
        d[f"ld_area{w}"] = prev.rolling(w, min_periods=max(6, w // 2)).mean()
        # first-vs-last ordering summaries; these preserve burden but encode ordering direction
        d[f"ld_firsthalf_lastdiff{w}"] = (
            prev.rolling(w, min_periods=max(6, w // 2)).apply(
                lambda x: float(np.mean(x[: len(x)//2]) - np.mean(x[len(x)//2:])), raw=True
            )
        )
        d[f"ld_slope{w}"] = prev.rolling(w, min_periods=max(6, w // 2)).apply(
            lambda x: float(np.polyfit(np.arange(len(x)), x, 1)[0]) if len(x) >= 3 else 0.0,
            raw=True,
        )
    return d


def future_target(d: pd.DataFrame) -> pd.Series:
    x = d[["open_time", "entry_path"]].sort_values("open_time").reset_index()
    t = x.open_time.to_numpy()
    p = x.entry_path.astype(str).to_numpy()
    y = np.zeros(len(x), dtype=np.int8)
    for i in range(len(x)):
        j = np.searchsorted(t, t[i] + np.timedelta64(HORIZON_H, "h"), side="right")
        if j > i + 1:
            y[i] = np.any(p[i + 1:j] == "3_to_4")
    return pd.Series(y, index=x["index"]).reindex(d.index).fillna(0).astype(int)


def robust_pair_candidates(q: pd.DataFrame, match_cols: list[str], caliper: float) -> list[tuple[int,int,float]]:
    med = q[match_cols].median().to_numpy(float)
    q1 = q[match_cols].quantile(.25).to_numpy(float)
    iqr = q1*0 + (q[match_cols].quantile(.75).to_numpy(float)-q1)
    iqr[iqr <= 1e-12] = 1.0
    z = (q[match_cols].to_numpy(float)-med)/iqr
    pos = np.flatnonzero(q.target.to_numpy()==1)
    neg = np.flatnonzero(q.target.to_numpy()==0)
    ts = q.open_time.to_numpy(dtype="datetime64[ns]")
    cand=[]
    for i in pos:
        delta=z[neg]-z[i]
        dist=np.sqrt(np.sum(delta*delta,axis=1))/np.sqrt(len(match_cols))
        sep=np.abs((ts[neg]-ts[i])/np.timedelta64(1,"h"))
        for k in np.flatnonzero(sep>=MIN_SEPARATION_H):
            if dist[k] <= caliper:
                cand.append((int(i),int(neg[k]),float(dist[k])))
    cand.sort(key=lambda x:x[2])
    used_p=set(); used_n=set(); pairs=[]
    for i,j,d in cand:
        if i in used_p or j in used_n: continue
        used_p.add(i); used_n.add(j); pairs.append((i,j,d))
    return pairs


def pair_auc(q: pd.DataFrame, pairs: list[tuple[int,int,float]], col: str) -> float:
    v=q[col].to_numpy(float); vals=[]
    for i,j,_ in pairs:
        if np.isfinite(v[i]) and np.isfinite(v[j]):
            vals.append(1.0 if v[i]>v[j] else 0.0 if v[i]<v[j] else .5)
    return float(np.mean(vals)) if vals else float("nan")


def permutation_p(q, pairs, col, observed, rng, n=NULL_N):
    v=q[col].to_numpy(float); usable=[(i,j) for i,j,_ in pairs if np.isfinite(v[i]) and np.isfinite(v[j])]
    if not usable or not np.isfinite(observed): return float("nan")
    null=np.empty(n)
    for k in range(n):
        wins=0.
        for i,j in usable:
            a,b=(v[i],v[j]) if rng.integers(2)==0 else (v[j],v[i])
            wins += 1. if a>b else 0. if a<b else .5
        null[k]=wins/len(usable)
    return float((1+np.sum(np.abs(null-.5)>=abs(observed-.5)))/(n+1))


def run(csv: Path) -> dict:
    d=make_features(pd.read_csv(csv))
    d["target"]=future_target(d)
    d["year"]=d.open_time.dt.year
    q=d[d.year==2024].dropna(subset=BASE+["target"]+[f"ld_area{w}" for w in HISTORY_WINDOWS]).reset_index(drop=True)
    # Match current state + 24h integrated LD burden. Then history-order variables are tested.
    match_cols=BASE+["ld_area24"]
    pairs=robust_pair_candidates(q,match_cols,MATCH_CALIPER)
    rng=np.random.default_rng(20260818)
    histories=[]
    for w in HISTORY_WINDOWS:
        histories += [f"ld_firsthalf_lastdiff{w}", f"ld_slope{w}"]
    results=[]
    for h in histories:
        obs=pair_auc(q,pairs,h)
        results.append({"history_order_variable":h,"pairs":len(pairs),"pair_auc":obs,"permutation_p":permutation_p(q,pairs,h,obs,rng)})
    return {"experiment":"TIAMAT_ORDERING_COURT_V1","classification":"experimental/non-authoritative","holdout_year":2024,"target":"future_3_to_4_within_6h","match_features":match_cols,"caliper":MATCH_CALIPER,"minimum_temporal_separation_h":MIN_SEPARATION_H,"pairs":len(pairs),"tests":results,"null":{"type":"within_pair_orientation_swap","n":NULL_N,"seed":20260818}}


def main(csv: Path,out: Path):
    payload=run(csv); out.write_text(json.dumps(payload,indent=2,allow_nan=True)); print(out.read_text())

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
