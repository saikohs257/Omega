from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

BASE=["SimpleShock","LiveDeficit","RecoveryWeakness_v1","hazard_raw"]
HORIZON_H=6; MIN_SEP_H=168; CALIPER=0.05
BROAD=(1,2,3,4,6,8,12,18,24,36,48,72,120,168)
LOCAL=(0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,8,9,10,12)
MIN_PAIRS=15


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
    cand.sort(key=lambda x:x[2]); up=set(); un=set(); out=[]
    for i,j,dist in cand:
        if i in up or j in un: continue
        up.add(i); un.add(j); out.append((i,j,dist))
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
    q=d[d.year==year].copy()
    m=recur(d.LiveDeficit.to_numpy(float),half)
    q['memory']=m[q.index].astype(float)
    q=q.dropna(subset=match_cols+['target','memory']).reset_index(drop=True)
    ps=pairs(q,match_cols); a=auc(q,ps,'memory')
    return {'year':year,'half_life_h':half,'pairs':len(ps),'memory_auc':a,
            'signed_effect':(a-.5) if np.isfinite(a) else float('nan'),
            'abs_effect':abs(a-.5) if np.isfinite(a) else float('nan')}


def select_consistent(rows):
    # Robust selection: require the effect to point in the same direction in every
    # discovery year, then maximize the weakest yearly effect. This prevents a
    # long-memory candidate from winning merely because one year has a large AUC.
    by={}
    for r in rows: by.setdefault(r['half_life_h'],[]).append(r)
    candidates=[]
    for h,rs in by.items():
        rs=[r for r in rs if r['pairs']>=MIN_PAIRS and np.isfinite(r['signed_effect'])]
        if len(rs)<2: continue
        signs=[np.sign(r['signed_effect']) for r in rs]
        if 0 in signs or len(set(signs))!=1: continue
        weakest=min(abs(r['signed_effect']) for r in rs)
        mean_abs=float(np.mean([abs(r['signed_effect']) for r in rs]))
        total_pairs=sum(r['pairs'] for r in rs)
        candidates.append((weakest,mean_abs,total_pairs,h))
    if not candidates: raise RuntimeError('No half-life had >=15 pairs and a consistent direction across discovery years')
    return max(candidates)[3], sorted(candidates,reverse=True)


def main(csv,out):
    d=prep(Path(csv))

    # STAGE 1: broad discovery. 2020-2021 are the only data allowed to choose
    # the coarse memory family.  2022 is deliberately held out for Stage 2.
    e1=[score(d,h,y) for h in BROAD for y in (2020,2021)]
    h1,rank1=select_consistent(e1)

    # STAGE 2: chained refinement.  Use the untouched 2022 data plus 2023 to
    # choose a local timescale. The local neighborhood is defined by Stage 1,
    # not by looking at 2024.
    neighbors=sorted(set(h for h in LOCAL if abs(h-h1)<=3) | {h1})
    e2=[score(d,h,y) for h in neighbors for y in (2022,2023)]
    h2,rank2=select_consistent(e2)

    # STAGE 3: 2024 is locked before evaluation. h2 cannot be changed here.
    final=score(d,h2,2024)
    q=d[d.year==2024].copy(); m=recur(d.LiveDeficit.to_numpy(float),h2); q['memory']=m[q.index]
    q=q.dropna(subset=BASE+['target','memory']).reset_index(drop=True)
    ps=pairs(q,BASE); baseline=auc(q,ps,'LiveDeficit'); mem=auc(q,ps,'memory')
    state_pairs=pairs(q,BASE+['memory']); residual=auc(q,state_pairs,'LiveDeficit')
    final.update({'baseline_live_deficit_auc':baseline,'memory_auc_recomputed':mem,
                  'pairs_after_memory_matching':len(state_pairs),
                  'ld_residual_after_memory_match_auc':residual,
                  'residual_abs_effect':abs(residual-.5) if np.isfinite(residual) else float('nan')})

    result={'experiment':'TIAMAT_MEMORY_CHAIN_V2','classification':'experimental/non-authoritative',
      'target':'future_3_to_4_within_6h','caliper':CALIPER,'minimum_temporal_separation_h':MIN_SEP_H,
      'selection_rule':'same-direction effect in every discovery year; maximize weakest yearly absolute effect; tie-break mean effect then pair count',
      'chain':[
        {'stage':1,'purpose':'broad_discovery','years':[2020,2021],'candidates_h':BROAD,'selected_h':h1,
         'results':e1,'ranking':rank1[:10]},
        {'stage':2,'purpose':'chained_out_of_sample_local_refinement','years':[2022,2023],'candidates_h':neighbors,'selected_h':h2,
         'results':e2,'ranking':rank2[:10]},
        {'stage':3,'purpose':'locked_final_holdout','year':2024,'frozen_h':h2,'result':final}
      ]}
    Path(out).write_text(json.dumps(result,indent=2,allow_nan=True)); print(json.dumps(result,indent=2,allow_nan=True))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--out',required=True); a=ap.parse_args(); main(a.csv,a.out)
