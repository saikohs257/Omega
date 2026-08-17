from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

BASE=["SimpleShock","LiveDeficit","RecoveryWeakness_v1","hazard_raw"]
HORIZON_H=6; HOLDOUT_YEAR=2024; MIN_SEP_H=168; CALIPER=0.05; NULL_N=2000
HALF_LIVES=(2,4,6,8,12,18,24,36,48,72,120,168)

def target(d):
    x=d[["open_time","entry_path"]].sort_values("open_time").reset_index(); t=x.open_time.to_numpy(); p=x.entry_path.astype(str).to_numpy(); y=np.zeros(len(x),np.int8)
    for i in range(len(x)):
        j=np.searchsorted(t,t[i]+np.timedelta64(HORIZON_H,'h'),side='right')
        if j>i+1: y[i]=np.any(p[i+1:j]=='3_to_4')
    return pd.Series(y,index=x['index']).reindex(d.index).fillna(0).astype(int)

def recur(ld, half):
    a=np.exp(-np.log(2)/half); m=np.zeros(len(ld));
    for i in range(len(ld)):
        x=ld[i-1] if i else np.nan
        m[i]=a*m[i-1]+(1-a)*(0.0 if np.isnan(x) else x) if i else (0.0 if np.isnan(x) else x)
    return m

def pairs(q, cols):
    med=np.asarray(q[cols].median().to_numpy(dtype=float, copy=True),dtype=float).copy()
    iqr=np.asarray((q[cols].quantile(.75)-q[cols].quantile(.25)).to_numpy(dtype=float, copy=True),dtype=float).copy()
    iqr[iqr<=1e-12]=1
    vals=np.asarray(q[cols].to_numpy(dtype=float, copy=True),dtype=float).copy()
    z=(vals-med)/iqr
    pos=np.flatnonzero(q.target.to_numpy()==1); neg=np.flatnonzero(q.target.to_numpy()==0); ts=q.open_time.to_numpy(dtype='datetime64[ns]')
    cand=[]
    for i in pos:
        dist=np.sqrt(((z[neg]-z[i])**2).sum(1)/len(cols)); sep=np.abs((ts[neg]-ts[i])/np.timedelta64(1,'h'))
        for k in np.flatnonzero(sep>=MIN_SEP_H):
            if dist[k]<=CALIPER: cand.append((int(i),int(neg[k]),float(dist[k])))
    cand.sort(key=lambda x:x[2]); up=set(); un=set(); out=[]
    for i,j,d in cand:
        if i in up or j in un: continue
        up.add(i); un.add(j); out.append((i,j,d))
    return out

def pair_auc(q, ps, col):
    v=q[col].to_numpy(float); s=[]
    for i,j,_ in ps:
        if np.isfinite(v[i]) and np.isfinite(v[j]): s.append(1. if v[i]>v[j] else 0. if v[i]<v[j] else .5)
    return float(np.mean(s)) if s else float('nan')

def pnull(q, ps, col, obs, rng):
    v=q[col].to_numpy(float); use=[(i,j) for i,j,_ in ps if np.isfinite(v[i]) and np.isfinite(v[j])]
    if not use or not np.isfinite(obs): return float('nan')
    n=np.empty(NULL_N)
    for k in range(NULL_N):
        w=0
        for i,j in use:
            a,b=(v[i],v[j]) if rng.integers(2)==0 else (v[j],v[i]); w+=1 if a>b else 0 if a<b else .5
        n[k]=w/len(use)
    return float((1+np.sum(np.abs(n-.5)>=abs(obs-.5)))/(NULL_N+1))

def run(csv:Path)->dict:
    d=pd.read_csv(csv); d.open_time=pd.to_datetime(d.open_time,utc=True)
    for c in BASE: d[c]=pd.to_numeric(d[c],errors='coerce')
    d['target']=target(d); d['year']=d.open_time.dt.year
    ld=d.LiveDeficit.to_numpy(float)
    full_states={f'memory_half_life_{h}h':recur(ld,h) for h in HALF_LIVES}
    d2=d.copy()
    for c,v in full_states.items(): d2[c]=v
    te=d2[d2.year==HOLDOUT_YEAR].reset_index(drop=True)
    rng=np.random.default_rng(20260818); out=[]
    for h in HALF_LIVES:
        col=f'memory_half_life_{h}h'; q=te.dropna(subset=BASE+['target',col]).reset_index(drop=True)
        ps=pairs(q,BASE)
        auc=pair_auc(q,ps,col); pv=pnull(q,ps,col,auc,rng)
        ps2=pairs(q,BASE+[col]); burden_auc=pair_auc(q,ps2,'LiveDeficit')
        out.append({'half_life_h':h,'pairs_base_match':len(ps),'memory_pair_auc':auc,'memory_permutation_p':pv,'pairs_state_completed':len(ps2),'ld_residual_after_memory_match_auc':burden_auc})
    return {'experiment':'TIAMAT_RECURSIVE_MEMORY_COURT_V1','classification':'experimental/non-authoritative','holdout_year':HOLDOUT_YEAR,'target':'future_3_to_4_within_6h','base_present_features':BASE,'caliper':CALIPER,'minimum_temporal_separation_h':MIN_SEP_H,'half_lives_h':HALF_LIVES,'results':out,'null':{'type':'within_pair_orientation_swap','n':NULL_N,'seed':20260818}}

def main(csv,out):
    p=run(Path(csv)); Path(out).write_text(json.dumps(p,indent=2,allow_nan=True)); print(json.dumps(p,indent=2,allow_nan=True))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--out',required=True); a=ap.parse_args(); main(a.csv,a.out)
