"""Anti-leakage court V2 for recovery-minus-burden.

The target is binary by construction: Crash72 == 1 only for the 72h event
window and 0 otherwise. We refuse multiclass coercion. Evaluation uses
non-overlapping 72h anchors across every phase offset, with 2024 held out.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score

TARGET='Crash72'; FEATURE='rr_recovery_minus_burden'; PERIOD=72

def score(tr,te,col):
 tr=tr.dropna(subset=[col,TARGET]); te=te.dropna(subset=[col,TARGET])
 classes=set(pd.to_numeric(tr[TARGET],errors='coerce').dropna().astype(int).unique())
 teclasses=set(pd.to_numeric(te[TARGET],errors='coerce').dropna().astype(int).unique())
 if classes != {0,1} or not teclasses.issubset({0,1}) or len(teclasses)<2:return None
 x0,x1=tr.loc[tr[TARGET]==0,col].astype(float),tr.loc[tr[TARGET]==1,col].astype(float)
 if len(x0)<20 or len(x1)<5:return None
 # Matched rank probability; avoids introducing a multiclass model entirely.
 vals=te[col].astype(float).to_numpy(); ref=x1.to_numpy(); ref0=x0.to_numpy()
 p=np.array([(np.mean(ref<=v)+np.mean(ref0<=v))/2 for v in vals])
 return float(roc_auc_score(te[TARGET].astype(int),p))

def nonoverlap(d,offset):
 x=d.sort_values('open_time').reset_index(drop=True).copy(); h=pd.to_datetime(x.open_time,utc=True).astype('int64')//10**9//3600
 anchor=((h-offset)//PERIOD)*PERIOD+offset
 x['_anchor']=anchor; return x.groupby('_anchor',as_index=False).first()

def main(csv:Path,out:Path):
 raw=pd.read_csv(csv); d=raw.copy(); d.open_time=pd.to_datetime(d.open_time,utc=True)
 assert len(d)==43848
 if TARGET not in d or FEATURE not in d: raise KeyError(f'missing {TARGET} or {FEATURE}')
 d[TARGET]=pd.to_numeric(d[TARGET],errors='coerce')
 bad=set(d[TARGET].dropna().astype(int).unique())-{0,1}
 if bad: raise ValueError(f'non-binary {TARGET} classes: {sorted(bad)}')
 d['year']=d.open_time.dt.year
 d['rr_lag24']=d[FEATURE].shift(24); d['rr_lag168']=d[FEATURE].shift(168); d['rr_lead24']=d[FEATURE].shift(-24); d['rr_innov24']=d[FEATURE]-d[FEATURE].shift(24)
 controls=[FEATURE,'rr_lag24','rr_lag168','rr_lead24','rr_innov24']; rows=[]
 for off in range(PERIOD):
  x=nonoverlap(d,off); tr=x[x.year<2024]; te=x[x.year==2024]
  for c in controls:
   a=score(tr,te,c)
   if a is not None: rows.append({'offset':off,'feature':c,'auc':a,'n_train':len(tr),'n_test':len(te),'train_classes':sorted(set(tr[TARGET].astype(int))), 'test_classes':sorted(set(te[TARGET].astype(int)))})
 frame=pd.DataFrame(rows)
 summary=[]
 for c in controls:
  q=frame[frame.feature==c].auc.dropna(); summary.append({'feature':c,'valid_offsets':int(len(q)),'median_auc':float(q.median()) if len(q) else None,'q25':float(q.quantile(.25)) if len(q) else None,'q75':float(q.quantile(.75)) if len(q) else None,'min':float(q.min()) if len(q) else None,'max':float(q.max()) if len(q) else None})
 payload={'experiment':'hydra_relative_recovery_falsification_court_v2','protocol':'2024 frozen holdout; 72 non-overlap phase offsets; binary-target guard; no offset or control selected','canonical_rows':len(d),'summary':summary,'offsets':rows,'interpretation_rule':'real-time memory is stronger evidence only if its distribution materially exceeds lag, lead, and innovation controls across offsets; invalid offsets are reported, never coerced to multiclass'}
 out.write_text(json.dumps(payload,indent=2,allow_nan=True)); print(json.dumps(payload,indent=2,allow_nan=True))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('csv',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();main(a.csv,a.out)
