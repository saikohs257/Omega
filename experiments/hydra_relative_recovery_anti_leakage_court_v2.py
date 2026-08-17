from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score,brier_score_loss
from hydra_relative_recovery_court_v1 import history

TARGET='Crash72'; FEATURE='rr_recovery_minus_burden'; HOLDOUT=2024; HORIZON=72

def model_auc(train,test,col):
 tr=train.dropna(subset=[col,TARGET]); te=test.dropna(subset=[col,TARGET])
 if len(tr)<200 or te[TARGET].nunique()<2:return None
 m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=2000,class_weight='balanced',C=.5,solver='liblinear'))
 m.fit(tr[[col]].astype(float),tr[TARGET].astype(int)); p=m.predict_proba(te[[col]].astype(float))[:,1]
 return float(roc_auc_score(te[TARGET],p))

def nonoverlap(d,offset):
 x=d.sort_values('open_time').copy(); t=(x.open_time.astype('int64')//10**9)//3600
 keep=(t-t.iloc[0]-offset)%HORIZON==0
 return x.loc[keep].copy()

def innovation(d):
 x=d.copy(); x['rr_lag24']=x[FEATURE].shift(24); x['rr_innovation']=x[FEATURE]-x['rr_lag24']; x['rr_lead24']=x[FEATURE].shift(-24); return x

def main(csv,out):
 raw=pd.read_csv(csv); d=innovation(history(raw)); d.open_time=pd.to_datetime(d.open_time,utc=True); d=d.sort_values('open_time').reset_index(drop=True)
 assert len(raw)==43848
 tr=d[d.open_time.dt.year<2024]; te=d[d.open_time.dt.year==2024]
 base={c:model_auc(tr,te,c) for c in [FEATURE,'rr_lag24','rr_lead24','rr_innovation']}
 # Non-overlapping 72h anchor test: repeat over all 72 phase offsets so the result cannot depend on an arbitrary bucket origin.
 offsets=[]
 for off in range(72):
  a=nonoverlap(tr,off); b=nonoverlap(te,off); offsets.append({'offset':off,'real':model_auc(a,b,FEATURE),'innovation':model_auc(a,b,'rr_innovation'),'lead':model_auc(a,b,'rr_lead24'),'lag':model_auc(a,b,'rr_lag24'),'n_test':len(b)})
 def summary(k):
  vals=[r[k] for r in offsets if r[k] is not None]
  return {'n':len(vals),'median':float(np.median(vals)) if vals else None,'mean':float(np.mean(vals)) if vals else None,'p10':float(np.quantile(vals,.1)) if vals else None,'p90':float(np.quantile(vals,.9)) if vals else None}
 payload={'experiment':'HYDRA_RELATIVE_RECOVERY_ANTI_LEAKAGE_COURT_V2','protocol':'2024 frozen holdout; compare causal feature, lag, lead, and one-step temporal innovation; then repeat on non-overlapping 72h anchors across all 72 phase offsets','canonical_rows':len(raw),'base_holdout':base,'nonoverlap_72h':{k:summary(k) for k in ['real','innovation','lead','lag']},'interpretation':'A causal memory claim strengthens only if the real feature remains superior to the lead and its lag/innovation controls after removing overlapping 72h label windows; otherwise treat the apparent signal as temporal persistence or leakage-like structure.'}
 Path(out).write_text(json.dumps(payload,indent=2)); print(json.dumps(payload,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('csv',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();main(a.csv,a.out)
