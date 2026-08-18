from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score

PRESENT=['SimpleShock','LiveDeficit','RecoveryWeakness_v1','hazard_raw']
LANES=['0_to_4','2_to_4','3_to_4']

def build_lane(d):
    p=d.LiveDeficit.shift(1)
    return np.select([p<=.70,p<=.85],['0_to_4','2_to_4'],default='3_to_4')

def add_targets(d):
    d=d.sort_values('open_time').reset_index(drop=True).copy(); t=d.open_time.to_numpy(dtype='datetime64[ns]'); p=d.entry_path.astype(str).to_numpy() if 'entry_path' in d else np.full(len(d),'')
    for h in (1,6,24):
        y=[]
        for i in range(len(d)):
            j=np.searchsorted(t,t[i]+np.timedelta64(h,'h'),'right'); y.append(int(j>i+1 and np.any(p[i+1:j]=='3_to_4')))
        d[f'y{h}']=y
    return d

def auc(y,s):
    m=np.isfinite(s) & np.isfinite(y)
    if m.sum()<30 or len(np.unique(y[m]))<2:return None
    return float(roc_auc_score(y[m],s[m]))

def main(csv,out):
    d=pd.read_csv(csv); d.open_time=pd.to_datetime(d.open_time,utc=True); assert len(d)==43848
    if not all(c in d for c in PRESENT+['entry_path','LiveDeficit']): raise KeyError('canonical columns missing')
    d['lane']=build_lane(d); d=add_targets(d)
    # Candidate projections are intentionally simple and lane-scoped.
    rec=np.clip(1.0-d.RecoveryWeakness_v1.to_numpy(float),0,1); b=d.LiveDeficit.to_numpy(float); h=d.hazard_raw.to_numpy(float); s=d.SimpleShock.to_numpy(float)
    d['P_b']=b; d['P_hr']=0.5*b+0.5*h; d['P_hbr']=(h+b+rec)/3; d['P_hbsr']=(h+b+s+rec)/4; d['P_resid']=np.maximum(0,b-rec); d['P_inv']=np.maximum(0,b-s)
    candidates={'P_b':'burden','P_hr':'hazard+burden','P_hbr':'hazard+burden+recovery','P_hbsr':'hazard+burden+shock+recovery','P_resid':'residual_burden','P_inv':'recovery_inversion'}
    rows=[]
    for lane in LANES:
        q=d[d.lane==lane]
        for c,name in candidates.items():
            rows.append({'lane':lane,'candidate':name,'n':len(q),'auc_1h':auc(q.y1.to_numpy(float),q[c].to_numpy(float)),'auc_6h':auc(q.y6.to_numpy(float),q[c].to_numpy(float)),'auc_24h':auc(q.y24.to_numpy(float),q[c].to_numpy(float))})
    # Leave-one-year-out is the main discriminating test.
    oos=[]
    for lane in LANES:
      for c,name in candidates.items():
       vals={h:[] for h in (1,6,24)}
       for yr in sorted(d.open_time.dt.year.unique()):
        tr=d[(d.lane==lane)&(d.open_time.dt.year!=yr)]
        te=d[(d.lane==lane)&(d.open_time.dt.year==yr)]
        # No fitted coefficients: use fixed projections; the year is purely a holdout check.
        for hh in (1,6,24):
            a=auc(te[f'y{hh}'].to_numpy(float),te[c].to_numpy(float));
            if a is not None:vals[hh].append(a)
       oos.append({'lane':lane,'candidate':name,'loo_mean_1h':float(np.mean(vals[1])) if vals[1] else None,'loo_min_1h':float(np.min(vals[1])) if vals[1] else None,'loo_mean_6h':float(np.mean(vals[6])) if vals[6] else None,'loo_min_6h':float(np.min(vals[6])) if vals[6] else None,'loo_mean_24h':float(np.mean(vals[24])) if vals[24] else None,'loo_min_24h':float(np.min(vals[24])) if vals[24] else None})
    result={'experiment':'TIAMAT_LANE_NATIVE_PROJECTION_COURT_V1','classification':'experimental/non-authoritative','lane_definition':'fixed previous-hour LiveDeficit buckets <=.70, <=.85, >.85','forbidden_features':['episode_type','duration_bucket','future_entry_path'],'in_sample':rows,'leave_one_year_out':oos,'purpose':'test whether lane-specific projections reproduce the distinct 0_to_4, 2_to_4, and 3_to_4 behavior without a universal scalar'}
    Path(out).write_text(json.dumps(result,indent=2,allow_nan=True));print(json.dumps(result,indent=2,allow_nan=True))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('csv');a.add_argument('--out',required=True);p=a.parse_args();main(a.csv,a.out)
