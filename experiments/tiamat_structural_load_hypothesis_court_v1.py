"""TIAMAT structural-load hypothesis court V1.

Identification experiment, not canonical generator. Tests whether explicit
burden-vs-recovery state explains native admission/path behavior better than
LiveDeficit alone. No target-derived feature is used.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr

PATH_ORDER={'0_to_4':0,'2_to_4':1,'3_to_4':2}

def build(d):
    x=d.sort_values('open_time').reset_index(drop=True).copy()
    ld=pd.to_numeric(x['LiveDeficit'],errors='coerce').astype(float)
    rw=pd.to_numeric(x['RecoveryWeakness_v1'],errors='coerce').astype(float)
    recovery_capacity=1.0-rw
    x['recovery_capacity']=recovery_capacity
    x['residual_load']=np.maximum(0.0,ld-recovery_capacity)
    x['load_pressure']=ld*rw
    x['load_balance']=ld/(recovery_capacity.clip(lower=1e-6))
    x['ld_only']=ld
    x['recovery_only']=recovery_capacity
    x['year']=x.open_time.dt.year
    x['is_start']=x['episode_type'].ne('none') & x['episode_type'].shift(1,fill_value='none').eq('none')
    x['path_rank']=x['entry_path'].map(PATH_ORDER)
    return x

def start_scores(x,year,feature):
    s=x[(x.year==year)&x.is_start&x.path_rank.notna()].copy()
    return {'n':int(len(s)),'spearman':float(spearmanr(s[feature],s.path_rank).statistic) if len(s)>=3 else None,'means':{k:float(s.loc[s.path_rank==v,feature].mean()) if (s.path_rank==v).any() else None for k,v in PATH_ORDER.items()}}

def active_auc(x,year,feature):
    s=x[(x.year==year)&x.is_start&x[feature].notna()].copy()
    c=x[(x.year==year)&(~x.is_start)&(x.episode_type=='none')&x[feature].notna()].copy()
    if not len(s) or not len(c): return None
    rng=np.random.default_rng(17)
    c=c.iloc[rng.permutation(len(c))[:min(len(c),len(s)*20)]]
    y=np.r_[np.ones(len(s)),np.zeros(len(c))]; v=np.r_[s[feature].to_numpy(),c[feature].to_numpy()]
    return float(roc_auc_score(y,v))

def main(csv,out):
    d=pd.read_csv(csv); d.open_time=pd.to_datetime(d.open_time,utc=True)
    req={'open_time','LiveDeficit','RecoveryWeakness_v1','episode_type','entry_path'}
    missing=req-set(d.columns)
    if missing: raise KeyError(sorted(missing))
    x=build(d); feats=['ld_only','recovery_only','residual_load','load_pressure','load_balance']
    locked={}
    for f in feats:
        locked[f]={'2020':active_auc(x,2020,f),'2021':active_auc(x,2021,f),'2022':active_auc(x,2022,f),'2023':active_auc(x,2023,f),'2024':active_auc(x,2024,f),'path_2024':start_scores(x,2024,f)}
    q=x[(x.year==2024)&x.LiveDeficit.notna()&x.RecoveryWeakness_v1.notna()&x.hazard_raw.notna()&x.SimpleShock.notna()].copy()
    cols=['SimpleShock','LiveDeficit','RecoveryWeakness_v1','hazard_raw']
    z=(q[cols]-q[cols].median())/(q[cols].quantile(.75)-q[cols].quantile(.25)).replace(0,1)
    pos=np.flatnonzero(q.is_start.to_numpy()); neg=np.flatnonzero((q.episode_type=='none').to_numpy()); t=q.open_time.to_numpy(dtype='datetime64[ns]'); rows=[]
    for i in pos:
        dist=np.sqrt(((z.iloc[neg].to_numpy()-z.iloc[i].to_numpy())**2).mean(1)); sep=np.abs((t[neg]-t[i])/np.timedelta64(1,'h')); ok=np.where(sep>=168)[0]
        if len(ok): j=ok[np.argmin(dist[ok])]; rows.append((i,neg[j]))
    pair_summary={}
    for f in feats:
        vals=[]
        for a,b in rows:
            va,vb=float(q.iloc[a][f]),float(q.iloc[b][f]); vals.append(1.0 if va>vb else .0 if va<vb else .5)
        pair_summary[f]={'pairs':len(vals),'orientation_auc':float(np.mean(vals)) if vals else None}
    payload={'experiment':'TIAMAT_STRUCTURAL_LOAD_HYPOTHESIS_COURT_V1','classification':'experimental/non-authoritative','hypothesis':'prediction is a byproduct of an inferred burden/recovery structural-load state','definitions':{'recovery_capacity':'1-RecoveryWeakness_v1','residual_load':'max(0, LiveDeficit-recovery_capacity)','load_pressure':'LiveDeficit*RecoveryWeakness_v1','load_balance':'LiveDeficit/recovery_capacity'},'annual':locked,'matched_2024':pair_summary,'interpretation':'A structural-load candidate is interesting only if it improves over LiveDeficit on locked 2024 behavior and survives 168h matched-state orientation. No candidate is promoted as recovered TIAMAT logic.'}
    Path(out).write_text(json.dumps(payload,indent=2,allow_nan=True)); print(json.dumps(payload,indent=2,allow_nan=True))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('csv')
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    main(args.csv,args.out)
