from __future__ import annotations

import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

BASE_OBS = ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_raw"]
TARGET_HISTORY = "ld_area24"
CANDIDATES = [
    "ld_lag1", "ld_lag6", "ld_lag24", "ld_delta1", "ld_delta6",
    "ld_area6", "ld_area12", "ld_area24", "ld_area48", "ld_area72",
    "ld_above85_24", "ld_max24", "ld_distance_from_max24",
    "ld_recovery_slope24", "shock_excess24", "hazard_peak24",
]
CALIPER = 0.05
MIN_SEP_H = 168
HOLDOUT_YEAR = 2024
NULL_N = 2000


def zscale(train, cols):
    med = train[cols].median().to_numpy(float)
    q1 = train[cols].quantile(.25).to_numpy(float)
    q3 = train[cols].quantile(.75).to_numpy(float)
    iqr = q3-q1; iqr[iqr <= 1e-12] = 1.0
    return med, iqr


def add_features(d):
    d=d.sort_values('open_time').reset_index(drop=True).copy()
    for c in BASE_OBS: d[c]=pd.to_numeric(d[c],errors='coerce')
    ld=d.LiveDeficit; ss=d.SimpleShock; hz=d.hazard_raw
    prev=ld.shift(1)
    d['ld_lag1']=ld.shift(1); d['ld_lag6']=ld.shift(6); d['ld_lag24']=ld.shift(24)
    d['ld_delta1']=ld.shift(1)-ld.shift(2); d['ld_delta6']=ld.shift(1)-ld.shift(7)
    for h in (6,12,24,48,72): d[f'ld_area{h}']=prev.rolling(h,min_periods=max(3,h//2)).mean()
    d['ld_above85_24']=(prev>.85).rolling(24,min_periods=12).sum()
    d['ld_max24']=prev.rolling(24,min_periods=12).max()
    d['ld_distance_from_max24']=d['ld_max24']-prev
    d['ld_recovery_slope24']=prev-prev.shift(24)
    d['shock_excess24']=(ss.shift(1)-.5).clip(lower=0).rolling(24,min_periods=12).sum()
    d['hazard_peak24']=hz.shift(1).rolling(24,min_periods=12).max()
    # causal future target
    x=d[['open_time','entry_path']].sort_values('open_time').reset_index()
    t=x.open_time.to_numpy(); p=x.entry_path.astype(str).to_numpy(); y=np.zeros(len(x),dtype=np.int8)
    for i in range(len(x)):
        j=np.searchsorted(t,t[i]+np.timedelta64(6,'h'),side='right')
        if j>i+1: y[i]=np.any(p[i+1:j]=='3_to_4')
    d['target']=pd.Series(y,index=x['index'].to_numpy()).reindex(d.index).fillna(0).astype(int)
    return d


def pair_metrics(q, match_cols, med, iqr, hist):
    z=(q[match_cols].to_numpy(float)-med)/iqr
    vals=q[hist].to_numpy(float)
    times=q.open_time.dt.tz_convert('UTC').dt.tz_localize(None).to_numpy(dtype='datetime64[ns]')
    pos=np.flatnonzero(q.target.to_numpy()==1); neg=np.flatnonzero(q.target.to_numpy()==0)
    cand=[]
    for i in pos:
        delta=z[neg]-z[i]; dist=np.sqrt(np.sum(delta*delta,axis=1))/np.sqrt(len(match_cols))
        gap=np.abs((times[neg]-times[i])/np.timedelta64(1,'h'))
        for k in np.flatnonzero(gap>=MIN_SEP_H): cand.append((int(i),int(neg[k]),float(dist[k])))
    cand.sort(key=lambda x:x[2])
    used_i=set(); used_j=set(); pairs=[]
    for i,j,dist in cand:
        if dist>CALIPER: break
        if i in used_i or j in used_j: continue
        if np.isfinite(vals[i]) and np.isfinite(vals[j]):
            used_i.add(i); used_j.add(j); pairs.append((i,j,dist))
    if not pairs: return {'pairs':0,'auc':np.nan,'null_mean':np.nan,'p':np.nan,'min_dist':np.nan}
    wins=[]
    for i,j,_ in pairs:
        wins.append(1.0 if vals[i]>vals[j] else 0.0 if vals[i]<vals[j] else .5)
    auc=float(np.mean(wins)); rng=np.random.default_rng(20260817)
    null=np.empty(NULL_N)
    for k in range(NULL_N):
        w=0.0
        for i,j,_ in pairs:
            a,b=(vals[i],vals[j]) if rng.integers(2)==0 else (vals[j],vals[i])
            w += 1 if a>b else 0 if a<b else .5
        null[k]=w/len(pairs)
    p=(1+np.sum(np.abs(null-.5)>=abs(auc-.5)))/(NULL_N+1)
    return {'pairs':len(pairs),'auc':auc,'null_mean':float(null.mean()),'p':float(p),'min_dist':float(min(x[2] for x in pairs))}


def run(csv):
    d=pd.read_csv(csv); d.open_time=pd.to_datetime(d.open_time,utc=True); d=add_features(d); q=d[d.open_time.dt.year==HOLDOUT_YEAR].dropna(subset=BASE_OBS+[TARGET_HISTORY]).copy().reset_index(drop=True)
    out=[]
    base_med,base_iqr=zscale(q,BASE_OBS)
    base=pair_metrics(q,BASE_OBS,base_med,base_iqr,TARGET_HISTORY)
    out.append({'state_candidate':'NONE_BASE_STATE','matching_features':BASE_OBS,'result':base})
    for c in CANDIDATES:
        cols=BASE_OBS+[c]; qq=q.dropna(subset=cols).reset_index(drop=True); med,iqr=zscale(qq,cols)
        r=pair_metrics(qq,cols,med,iqr,TARGET_HISTORY)
        out.append({'state_candidate':c,'matching_features':cols,'result':r})
    return {
      'experiment':'TIAMAT_STATE_COMPLETION_COURT_V1','classification':'experimental/non-authoritative',
      'holdout_year':HOLDOUT_YEAR,'target':'future_3_to_4_within_6h','history_tested':TARGET_HISTORY,
      'base_present_features':BASE_OBS,'candidate_state_coordinates':CANDIDATES,
      'caliper':CALIPER,'minimum_temporal_separation_h':MIN_SEP_H,
      'forbidden_predictors':['entry_path','episode_type','duration_bucket','Crash72'],
      'results':out
    }

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    a.out.write_text(json.dumps(run(a.csv),indent=2,allow_nan=True)); print(a.out.read_text())
