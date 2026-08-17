"""Forensic localization of stored rr_recovery_minus_burden construction.
Find first mismatches against lagged ingredient candidates and report local rows.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd

def n(d,c): return pd.to_numeric(d[c],errors='coerce')
def score(a,b):
 m=a.notna()&b.notna();
 if not m.any(): return {'n':0,'mae':None,'max_abs':None,'exact':False}
 diff=(a[m]-b[m]).abs(); return {'n':int(m.sum()),'mae':float(diff.mean()),'max_abs':float(diff.max()),'exact':bool(np.allclose(a[m].to_numpy(),b[m].to_numpy(),rtol=1e-9,atol=1e-10))}
def main(csv:Path,out:Path):
 d=pd.read_csv(csv); d['open_time']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('open_time').reset_index(drop=True)
 rr=n(d,'rr_recovery_minus_burden')
 rw=n(d,'RecoveryWeakness_v1'); ld=n(d,'LiveDeficit'); ss=n(d,'SimpleShock'); hz=n(d,'hazard_score')
 candidates={}
 for a_name,a in [('rw',rw),('ld',ld),('ss',ss),('hz',hz)]:
  for b_name,b in [('rw',rw),('ld',ld),('ss',ss),('hz',hz)]:
   for lag_a in range(0,7):
    for lag_b in range(0,7):
     candidates[f'{a_name}_l{lag_a}-{b_name}_l{lag_b}']=a.shift(lag_a)-b.shift(lag_b)
 for c in [0.5,1,2,-0.5,-1,-2]:
  candidates[f'rw_l1_plus_{c}_ld_l1']=rw.shift(1)+c*ld.shift(1)
 results=sorted(({'name':k,**score(rr,v)} for k,v in candidates.items()),key=lambda x:(x['mae'] if x['mae'] is not None else 1e99))
 best=results[:20]
 best_name=best[0]['name']; best_series=candidates[best_name]; diff=(rr-best_series).abs(); mismatch=diff.fillna(np.inf)>1e-9
 idx=np.flatnonzero(mismatch.to_numpy())[:20]
 local=[]
 for i in idx:
  lo=max(0,i-2); hi=min(len(d),i+3); cols=['open_time','rr_recovery_minus_burden','RecoveryWeakness_v1','LiveDeficit','SimpleShock','hazard_score']
  local.append({'index':int(i),'rows':d.loc[lo:hi-1,cols].assign(candidate=best_series.loc[lo:hi-1],abs_diff=diff.loc[lo:hi-1]).to_dict('records')})
 result={'experiment':'hydra_rr_formula_forensic_v1','rows':int(len(d)),'stored_rr_nonnull':int(rr.notna().sum()),'top_candidates':best,'first_mismatch_indices':idx.astype(int).tolist(),'best_candidate':best_name,'local_windows':local}
 out.write_text(json.dumps(result,indent=2,allow_nan=False,default=str)); print(json.dumps(result,indent=2,allow_nan=False,default=str))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
