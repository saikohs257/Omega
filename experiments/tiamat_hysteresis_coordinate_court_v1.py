from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

OBS=["SimpleShock","LiveDeficit","RecoveryWeakness_v1","hazard_raw"]
H=6; PURGE=6; HOLDOUT=2024; SEP=168; CAL=0.05


def metric(y,p):
    y=np.asarray(y,int); p=np.clip(np.asarray(p,float),1e-7,1-1e-7)
    return {"n":int(len(y)),"events":int(y.sum()),"auc":float(roc_auc_score(y,p)) if np.unique(y).size==2 else None,
            "pr_auc":float(average_precision_score(y,p)) if y.sum() else None,
            "brier":float(brier_score_loss(y,p)),"logloss":float(log_loss(y,p,labels=[0,1]))}


def model(cols):
    return make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(max_iter=2500,class_weight="balanced",C=0.5,solver="liblinear"))


def prep(raw):
    d=raw.copy(); d.open_time=pd.to_datetime(d.open_time,utc=True,errors="raise"); d=d.sort_values('open_time').reset_index(drop=True)
    for c in OBS: d[c]=pd.to_numeric(d[c],errors='coerce')
    ld=d.LiveDeficit
    for h in [1,6,24,72]: d[f'ld_lag{h}']=ld.shift(h)
    d['ld_delta24']=ld.shift(1)-ld.shift(25)
    d['ld_recovery24']=ld.shift(24)-ld.shift(1)  # positive = LD has fallen over prior 24h
    d['ld_area24']=ld.shift(1).rolling(24,min_periods=12).mean()
    d['ld_peak24']=ld.shift(1).rolling(24,min_periods=12).max()
    d['ld_peak_excess24']=d['ld_peak24']-ld.shift(1)
    d['ld_cross85_age24']=(ld.shift(1)>0.85).rolling(24,min_periods=12).sum()
    x=d[['open_time','entry_path']]; t=x.open_time.to_numpy(dtype='datetime64[ns]'); p=x.entry_path.astype(str).to_numpy(); y=np.zeros(len(x),np.int8)
    for i in range(len(x)):
        j=np.searchsorted(t,t[i]+np.timedelta64(H,'h'),side='right')
        if j>i+1: y[i]=int(np.any(p[i+1:j]=='3_to_4'))
    d['target']=y
    return d


def purge(tr, start): return tr[tr.open_time < start-pd.Timedelta(hours=PURGE)]

def predict(tr,te,cols):
    m=model(cols); m.fit(tr[cols],tr.target); return m.predict_proba(te[cols])[:,1]


def ladder(d):
    configs={
      'state4':OBS,
      'state4_ld_lag24':OBS+['ld_lag24'],
      'state4_delta24':OBS+['ld_delta24'],
      'state4_recovery24':OBS+['ld_recovery24'],
      'state4_area24':OBS+['ld_area24'],
      'state4_peak_excess24':OBS+['ld_peak_excess24'],
      'state4_recovery24_area24':OBS+['ld_recovery24','ld_area24'],
      'state4_recovery24_peak24':OBS+['ld_recovery24','ld_peak_excess24'],
      'state4_24block':OBS+['ld_lag1','ld_lag6','ld_lag24','ld_lag72','ld_delta24','ld_area24','ld_peak_excess24','ld_cross85_age24'],
    }
    hold=d[d.open_time.dt.year==HOLDOUT]; tr=purge(d[d.open_time.dt.year<HOLDOUT],hold.open_time.min())
    out={'holdout':{},'walk_forward':{k:[] for k in configs}}
    for name,cols in configs.items():
        out['holdout'][name]=metric(hold.target.to_numpy(),predict(tr,hold,cols))
        for yr in [2021,2022,2023]:
            te=d[d.open_time.dt.year==yr]; tt=purge(d[d.open_time.dt.year<yr],te.open_time.min())
            if tt.target.nunique()<2: continue
            out['walk_forward'][name].append({'year':yr,'metrics':metric(te.target.to_numpy(),predict(tt,te,cols))})
    base=out['holdout']['state4']['auc']; out['holdout_delta']={k:(v['auc']-base) for k,v in out['holdout'].items()}
    return out


def match_pairs(d, cols):
    train=d[d.open_time.dt.year<HOLDOUT].dropna(subset=cols); hold=d[d.open_time.dt.year==HOLDOUT].dropna(subset=cols+['target']).reset_index(drop=True)
    med=train[cols].median().to_numpy(float); iqr=(train[cols].quantile(.75)-train[cols].quantile(.25)).to_numpy(float); iqr[iqr<=1e-12]=1
    z=(hold[cols].to_numpy(float)-med)/iqr; t=hold.open_time.to_numpy(dtype='datetime64[ns]'); pos=np.flatnonzero(hold.target.to_numpy()==1); neg=np.flatnonzero(hold.target.to_numpy()==0)
    c=[]
    for i in pos:
        gap=np.abs((t[neg]-t[i])/np.timedelta64(1,'h')); dist=np.sqrt(((z[neg]-z[i])**2).sum(1))/np.sqrt(len(cols))
        for k in np.flatnonzero(gap>=SEP):
            if dist[k]<=CAL: c.append((int(i),int(neg[k]),float(dist[k])))
    c.sort(key=lambda x:x[2]); ui=set(); uj=set(); out=[]
    for i,j,dd in c:
        if i in ui or j in uj: continue
        ui.add(i); uj.add(j); out.append((i,j,dd))
    return hold,out


def orient(hold,pairs,col):
    v=pd.to_numeric(hold[col],errors='coerce').to_numpy(float); a=[]
    for i,j,_ in pairs:
        if np.isfinite(v[i]) and np.isfinite(v[j]): a.append(1 if v[i]>v[j] else 0 if v[i]<v[j] else .5)
    return float(np.mean(a)) if a else None


def main(path,out):
    raw=pd.read_csv(path)
    if len(raw)!=43848: raise SystemExit(f'row count {len(raw)}')
    d=prep(raw); starts=int(((d.entry_path=='3_to_4')&(d.episode_age_h==1)).sum())
    if starts!=169: raise SystemExit(f'starts {starts}')
    payload={'experiment':'TIAMAT_HYSTERESIS_COORDINATE_COURT_V1','classification':'experimental/non-authoritative','question':'Does prior-load release/hysteresis explain the residual history signal after present-state matching?','canonical':{'rows':len(d),'h3_starts':starts,'holdout':HOLDOUT},'controls':{'discovery_years':[2020,2021,2022,2023],'holdout_geometry_frozen':True,'purge_hours':PURGE,'pair_separation_hours':SEP,'target_peek':False},'model_ladder':ladder(d)}
    for name,cols in [('state4',OBS),('state4_recovery24',OBS+['ld_recovery24']),('state4_recovery24_area24',OBS+['ld_recovery24','ld_area24']),('state4_recovery24_peak24',OBS+['ld_recovery24','ld_peak_excess24'])]:
        h,p=match_pairs(d,cols); payload.setdefault('matching',{})[name]={'pairs':len(p),'median_distance':float(np.median([x[2] for x in p])) if p else None,'recovery24_orientation':orient(h,p,'ld_recovery24'),'delta24_orientation':orient(h,p,'ld_delta24'),'lag24_orientation':orient(h,p,'ld_lag24'),'peak_excess24_orientation':orient(h,p,'ld_peak_excess24')}
    out.write_text(json.dumps(payload,indent=2,allow_nan=False)); print(json.dumps(payload,indent=2,allow_nan=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',required=True,type=Path); a=ap.parse_args(); main(a.csv,a.out)
