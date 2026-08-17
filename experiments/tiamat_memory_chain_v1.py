from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

BASE=["SimpleShock","LiveDeficit","RecoveryWeakness_v1","hazard_raw"]
HORIZON_H=6; MIN_SEP_H=168; CALIPER=0.05
BROAD=(2,4,6,8,12,18,24,36,48,72,120,168)
LOCAL=(0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,8,10,12)


def target(d):
    x=d[["open_time","entry_path"]].sort_values("open_time").reset_index()
    t=x.open_time.to_numpy(); p=x.entry_path.astype(str).to_numpy(); y=np.zeros(len(x),np.int8)
    for i in range(len(x)):
        j=np.searchsorted(t,t[i]+np.timedelta64(HORIZON_H,'h'),side='right')
        if j>i+1: y[i]=np.any(p[i+1:j]=='3_to_4')
    return pd.Series(y,index=x['index']).reindex(d.index).fillna(0).astype(int)


def recur(ld, half):
    a=np.exp(-np.log(2)/half); m=np.zeros(len(ld))
    for i in range(len(ld)):
        x=ld[i-1] if i else np.nan
        m[i]=a*m[i-1]+(1-a)*(0.0 if np.isnan(x) else x) if i else (0.0 if np.isnan(x) else x)
    return m


def pairs(q, cols):
    med=np.asarray(q[cols].median().to_numpy(dtype=float,copy=True),dtype=float).copy()
    iqr=np.asarray((q[cols].quantile(.75)-q[cols].quantile(.25)).to_numpy(dtype=float,copy=True),dtype=float).copy()
    iqr[iqr<=1e-12]=1
    vals=np.asarray(q[cols].to_numpy(dtype=float,copy=True),dtype=float).copy(); z=(vals-med)/iqr
    pos=np.flatnonzero(q.target.to_numpy()==1); neg=np.flatnonzero(q.target.to_numpy()==0)
    ts=q.open_time.to_numpy(dtype='datetime64[ns]'); cand=[]
    for i in pos:
        dist=np.sqrt(((z[neg]-z[i])**2).sum(1)/len(cols)); sep=np.abs((ts[neg]-ts[i])/np.timedelta64(1,'h'))
        for k in np.flatnonzero(sep>=MIN_SEP_H):
            if dist[k]<=CALIPER: cand.append((int(i),int(neg[k]),float(dist[k])))
    cand.sort(key=lambda x:x[2]); used_pos=set(); used_neg=set(); out=[]
    for i,j,dist in cand:
        if i in used_pos or j in used_neg: continue
        used_pos.add(i); used_neg.add(j); out.append((i,j,dist))
    return out


def auc(q, ps, col):
    v=q[col].to_numpy(float); s=[]
    for i,j,_ in ps:
        if np.isfinite(v[i]) and np.isfinite(v[j]): s.append(1. if v[i]>v[j] else 0. if v[i]<v[j] else .5)
    return float(np.mean(s)) if s else float('nan')


def prep(csv):
    d=pd.read_csv(csv); d.open_time=pd.to_datetime(d.open_time,utc=True)
    for c in BASE: d[c]=pd.to_numeric(d[c],errors='coerce')
    d['target']=target(d); d['year']=d.open_time.dt.year
    return d


def score(d, half, year, match_cols=BASE):
    q=d[d.year==year].copy(); q[f'memory_{half:g}h']=recur(d.LiveDeficit.to_numpy(float),half)[q.index].astype(float)
    q=q.dropna(subset=match_cols+['target',f'memory_{half:g}h']).reset_index(drop=True)
    ps=pairs(q,match_cols); col=f'memory_{half:g}h'
    return {'year':year,'half_life_h':half,'pairs':len(ps),'memory_auc':auc(q,ps,col),'memory_abs_effect':abs(auc(q,ps,col)-.5) if np.isfinite(auc(q,ps,col)) else float('nan')}


def choose(results):
    valid=[r for r in results if np.isfinite(r['memory_abs_effect']) and r['pairs']>=10]
    if not valid: raise RuntimeError('No candidate produced >=10 matched pairs')
    return max(valid,key=lambda r:(r['memory_abs_effect'],r['pairs']))['half_life_h']


def main(csv,out):
    d=prep(Path(csv))
    # EXPERIMENT 1: broad discovery on 2020-2022 only.
    e1=[score(d,h,2020) for h in BROAD]
    e1 += [score(d,h,2021) for h in BROAD]
    e1 += [score(d,h,2022) for h in BROAD]
    agg=[]
    for h in BROAD:
        rs=[r for r in e1 if r['half_life_h']==h and np.isfinite(r['memory_abs_effect'])]
        agg.append({'half_life_h':h,'mean_abs_effect':float(np.mean([r['memory_abs_effect'] for r in rs])) if rs else float('nan'),'total_pairs':int(sum(r['pairs'] for r in rs))})
    h1=max([r for r in agg if np.isfinite(r['mean_abs_effect'])],key=lambda r:(r['mean_abs_effect'],r['total_pairs']))['half_life_h']

    # EXPERIMENT 2: validation refines only around E1 winner, using 2023.
    neighbors=sorted(set([h for h in LOCAL if abs(h-h1)<=3]+[h1]))
    e2=[score(d,h,2023) for h in neighbors]
    h2=choose(e2)

    # EXPERIMENT 3: locked 2024 test; h2 is frozen before touching 2024.
    final=score(d,h2,2024)
    # Compare the locked memory state against the raw current LD under identical matching.
    q=d[d.year==2024].copy(); m=recur(d.LiveDeficit.to_numpy(float),h2); q['memory']=m[q.index]; q=q.dropna(subset=BASE+['target','memory']).reset_index(drop=True)
    ps=pairs(q,BASE); baseline=auc(q,ps,'LiveDeficit'); mem=auc(q,ps,'memory')
    state_pairs=pairs(q,BASE+['memory']); residual=auc(q,state_pairs,'LiveDeficit')
    final.update({'baseline_live_deficit_auc':baseline,'memory_auc_recomputed':mem,'pairs_after_memory_matching':len(state_pairs),'ld_residual_after_memory_match_auc':residual})

    result={'experiment':'TIAMAT_MEMORY_CHAIN_V1','classification':'experimental/non-authoritative','target':'future_3_to_4_within_6h','caliper':CALIPER,'minimum_temporal_separation_h':MIN_SEP_H,'chain':[{'stage':1,'purpose':'broad_discovery','years':[2020,2021,2022],'candidates_h':BROAD,'selected_h':h1,'results':agg},{'stage':2,'purpose':'out_of_sample_local_refinement','year':2023,'candidates_h':neighbors,'selected_h':h2,'results':e2},{'stage':3,'purpose':'locked_final_holdout','year':2024,'frozen_h':h2,'result':final}]}
    Path(out).write_text(json.dumps(result,indent=2,allow_nan=True)); print(json.dumps(result,indent=2,allow_nan=True))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--out',required=True); a=ap.parse_args(); main(a.csv,a.out)
