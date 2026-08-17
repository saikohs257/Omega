from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

BASE=["SimpleShock","LiveDeficit","RecoveryWeakness_v1","hazard_raw"]
HORIZON_H=6; CALIPER=0.05; MIN_SEP_H=168; MIN_PAIRS=15
EXP=(1,2,3,4,6,8,12,18,24,36,48,72,120,168)
WIN=(2,4,6,8,12,18,24,36,48,72)
TRI=(2,4,6,8,12,18,24,36,48,72)


def target(d):
    x=d[["open_time","entry_path"]].sort_values("open_time").reset_index(); t=x.open_time.to_numpy(); p=x.entry_path.astype(str).to_numpy(); y=np.zeros(len(x),np.int8)
    for i in range(len(x)):
        j=np.searchsorted(t,t[i]+np.timedelta64(HORIZON_H,'h'),side='right')
        if j>i+1: y[i]=np.any(p[i+1:j]=='3_to_4')
    return pd.Series(y,index=x['index']).reindex(d.index).fillna(0).astype(int)


def memory(x, family, scale):
    x=np.nan_to_num(np.asarray(x,dtype=float),nan=0.0)
    if family=='exp':
        a=np.exp(-np.log(2)/scale); out=np.zeros(len(x))
        for i in range(1,len(x)): out[i]=a*out[i-1]+(1-a)*x[i-1]
        out[0]=x[0]; return out
    n=int(scale); n=max(1,n)
    if family=='window':
        return pd.Series(x).shift(1).rolling(n,min_periods=1).mean().to_numpy()
    # triangular fading kernel: recent history gets linearly greater weight
    w=np.arange(1,n+1,dtype=float); w/=w.sum(); z=pd.Series(x).shift(1)
    return z.rolling(n,min_periods=1).apply(lambda a: np.dot(a,w[-len(a):])/w[-len(a):].sum(),raw=True).to_numpy()


def pairs(q, cols):
    med=np.asarray(q[cols].median().to_numpy(dtype=float,copy=True)); iqr=np.asarray((q[cols].quantile(.75)-q[cols].quantile(.25)).to_numpy(dtype=float,copy=True)); iqr[iqr<=1e-12]=1
    z=(np.asarray(q[cols].to_numpy(dtype=float,copy=True))-med)/iqr
    pos=np.flatnonzero(q.target.to_numpy()==1); neg=np.flatnonzero(q.target.to_numpy()==0); ts=q.open_time.to_numpy(dtype='datetime64[ns]'); cand=[]
    for i in pos:
        dist=np.sqrt(((z[neg]-z[i])**2).sum(1)/len(cols)); sep=np.abs((ts[neg]-ts[i])/np.timedelta64(1,'h'))
        for k in np.flatnonzero(sep>=MIN_SEP_H):
            if dist[k]<=CALIPER: cand.append((int(i),int(neg[k]),float(dist[k])))
    cand.sort(key=lambda z:z[2]); used1=set(); used2=set(); out=[]
    for i,j,d in cand:
        if i in used1 or j in used2: continue
        used1.add(i); used2.add(j); out.append((i,j,d))
    return out


def auc(q,ps,col):
    v=q[col].to_numpy(float); s=[]
    for i,j,_ in ps:
        if np.isfinite(v[i]) and np.isfinite(v[j]): s.append(1 if v[i]>v[j] else 0 if v[i]<v[j] else .5)
    return float(np.mean(s)) if s else float('nan')


def prep(csv):
    d=pd.read_csv(csv); d.open_time=pd.to_datetime(d.open_time,utc=True)
    for c in BASE: d[c]=pd.to_numeric(d[c],errors='coerce')
    d['target']=target(d); d['year']=d.open_time.dt.year; return d


def score(d,family,scale,year):
    m=memory(d.LiveDeficit.to_numpy(float),family,scale); q=d[d.year==year].copy(); q['memory']=m[q.index]
    q=q.dropna(subset=BASE+['target','memory']).reset_index(drop=True); ps=pairs(q,BASE); a=auc(q,ps,'memory')
    return {'family':family,'scale':scale,'year':year,'pairs':len(ps),'auc':a,'effect':a-.5 if np.isfinite(a) else float('nan')}


def select(rows):
    groups={}
    for r in rows: groups.setdefault((r['family'],r['scale']),[]).append(r)
    cand=[]
    for key,rs in groups.items():
        rs=[r for r in rs if r['pairs']>=MIN_PAIRS and np.isfinite(r['effect'])]
        if len(rs)<2: continue
        signs=[np.sign(r['effect']) for r in rs]
        if 0 in signs or len(set(signs))!=1: continue
        weak=min(abs(r['effect']) for r in rs); mean=float(np.mean([abs(r['effect']) for r in rs])); pairs=sum(r['pairs'] for r in rs)
        cand.append((weak,mean,pairs,key))
    if not cand: raise RuntimeError('No memory family/scale met consistency and pair-count requirements')
    cand.sort(reverse=True); return cand[0][3],cand


def main(csv,out):
    d=prep(Path(csv))
    # Stage 1: competing memory families on 2020-2021. This is inspired by fading-memory kernels: do not assume exponential decay is canonical.
    e1=[score(d,f,s,y) for f,scales in [('exp',EXP),('window',WIN),('tri',TRI)] for s in scales for y in (2020,2021)]
    k1,rank1=select(e1)
    # Stage 2: refine only the winning family, using untouched 2022-2023 and a local neighborhood.
    f1,s1=k1; pool=EXP if f1=='exp' else WIN if f1=='window' else TRI
    local=sorted(set(s for s in pool if abs(float(s)-float(s1))<=max(3,float(s1)*0.5))|{s1})
    e2=[score(d,f1,s,y) for s in local for y in (2022,2023)]
    k2,rank2=select(e2); f2,s2=k2
    # Stage 3: locked 2024. No parameter selection is allowed here.
    final=score(d,f2,s2,2024); m=memory(d.LiveDeficit.to_numpy(float),f2,s2); q=d[d.year==2024].copy(); q['memory']=m[q.index]
    q=q.dropna(subset=BASE+['target','memory']).reset_index(drop=True); basepairs=pairs(q,BASE); statepairs=pairs(q,BASE+['memory'])
    final['baseline_ld_auc']=auc(q,basepairs,'LiveDeficit'); final['residual_ld_auc_after_memory_match']=auc(q,statepairs,'LiveDeficit'); final['state_completed_pairs']=len(statepairs)
    result={'experiment':'TIAMAT_MEMORY_CHAIN_V2','classification':'experimental/non-authoritative','selection':'consistent signed effect across discovery years; maximize weakest absolute effect','chain':[
      {'stage':1,'years':[2020,2021],'purpose':'competing_kernel_family_discovery','selected_family':f1,'selected_scale':s1,'results':e1,'ranking':rank1[:15]},
      {'stage':2,'years':[2022,2023],'purpose':'locked-family_local_refinement','selected_family':f2,'selected_scale':s2,'candidates':local,'results':e2,'ranking':rank2[:15]},
      {'stage':3,'year':2024,'purpose':'locked_holdout_and_state_completion','frozen_family':f2,'frozen_scale':s2,'result':final}
    ],'guardrails':{'caliper':CALIPER,'min_separation_h':MIN_SEP_H,'min_pairs':MIN_PAIRS,'holdout_not_used_for_selection':True}}
    Path(out).write_text(json.dumps(result,indent=2,allow_nan=True)); print(json.dumps(result,indent=2,allow_nan=True))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--out',required=True); a=ap.parse_args(); main(a.csv,a.out)
