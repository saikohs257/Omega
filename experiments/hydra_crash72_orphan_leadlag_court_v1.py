"""Crash72 Orphan Hazard/RR lead-lag court on 2024 holdout."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from hydra_relative_recovery_court_v1 import history
from hydra_crash72_incremental_orphan_court_v1 import normalized_entry_path

def main(csv,out):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int); path=normalized_entry_path(d['entry_path'])
 core=y.eq(1)&path.eq('3_to_4')&pd.to_numeric(d['episode_age_h'],errors='coerce').eq(1); ex=y.eq(1)&~core; orphan=ex&path.eq('<missing>'); trans=ex&path.ne('<missing>')
 counts={'core':int(core.sum()),'transition':int(trans.sum()),'orphan':int(orphan.sum()),'crash72':int(y.sum())}; assert counts=={'core':12,'transition':350,'orphan':606,'crash72':968}, counts
 h=pd.to_numeric(d['hazard_score'],errors='coerce'); rr=pd.to_numeric(d['rr_recovery_minus_burden'],errors='coerce')
 # Use training-only quantiles for anomaly thresholds; event windows are holdout-only.
 train=d[d.date.dt.year<2024].copy(); ht=pd.to_numeric(train['hazard_score'],errors='coerce'); rt=pd.to_numeric(train['rr_recovery_minus_burden'],errors='coerce')
 h_hi=float(ht.quantile(.8)); rr_lo=float(rt.quantile(.2))
 test=d[d.date.dt.year==2024].copy(); op=test.index[test['entry_path'].isna()] if False else test.index
 # Orphan event rows are defined by the frozen taxonomy, not missing raw values in the test slice.
 test_orphan=orphan.loc[test.index]
 event_idx=test.index[test_orphan.astype(bool)]
 # For each event, inspect T-24..T0. Define first threshold crossing and first directional move.
 rows=[]
 for idx in event_idx:
  pos=d.index.get_loc(idx); start=max(0,pos-24); win=d.iloc[start:pos+1]
  hi=(pd.to_numeric(win['hazard_score'],errors='coerce')>=h_hi); lo=(pd.to_numeric(win['rr_recovery_minus_burden'],errors='coerce')<=rr_lo)
  # first crossing hour relative to T0
  hpos=np.flatnonzero(hi.to_numpy()); rpos=np.flatnonzero(lo.to_numpy())
  hfirst=int(hpos[0]-len(win)+1) if len(hpos) else None
  rfirst=int(rpos[0]-len(win)+1) if len(rpos) else None
  rows.append({'event_index':int(idx),'open_time':str(d.loc[idx,'open_time']),'hazard_first_t':hfirst,'rr_first_t':rfirst,'lead':'hazard' if hfirst is not None and (rfirst is None or hfirst<rfirst) else ('rr' if rfirst is not None and (hfirst is None or rfirst<hfirst) else ('tie' if hfirst is not None else 'neither')),'hazard_t0':float(h.loc[idx]),'rr_t0':float(rr.loc[idx]),'hazard_tminus24':float(h.loc[win.index[0]]),'rr_tminus24':float(rr.loc[win.index[0]])})
 lead_counts={k:sum(r['lead']==k for r in rows) for k in ['hazard','rr','tie','neither']}
 result={'experiment':'hydra_crash72_orphan_leadlag_court_v1','train_years':'2020-2023','holdout_year':2024,'thresholds':{'hazard_hi_q80_train':h_hi,'rr_lo_q20_train':rr_lo},'class_counts':counts,'event_count':len(rows),'lead_counts':lead_counts,'events':rows}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
