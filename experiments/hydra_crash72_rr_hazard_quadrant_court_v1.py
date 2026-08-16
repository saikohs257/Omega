"""Crash72 Orphan RR/Hazard quadrant court. Frozen taxonomy, prior-year training, 2024 holdout."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from hydra_relative_recovery_court_v1 import history
from hydra_crash72_incremental_orphan_court_v1 import normalized_entry_path

def main(csv,out):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int)
 path=normalized_entry_path(d['entry_path'])
 base=path.eq('3_to_4') & pd.to_numeric(d['episode_age_h'],errors='coerce').eq(1)
 core=y.eq(1)&base
 ex=y.eq(1)&~base; trans=ex&path.ne('<missing>'); orphan=ex&path.eq('<missing>')
 counts={'core':int(core.sum()),'transition':int(trans.sum()),'orphan':int(orphan.sum()),'crash72':int(y.sum())}
 assert counts=={'core':12,'transition':350,'orphan':606,'crash72':968}, f'taxonomy mismatch: {counts}'
 d['orphan']=orphan.astype(int)
 train=d[d.date.dt.year<2024].copy(); test=d[d.date.dt.year==2024].copy()
 rr_train=pd.to_numeric(train['rr_recovery_minus_burden'],errors='coerce'); hz_train=pd.to_numeric(train['hazard_score'],errors='coerce')
 rr_cut=float(rr_train.median()); hz_cut=float(hz_train.median())
 rr=pd.to_numeric(test['rr_recovery_minus_burden'],errors='coerce'); hz=pd.to_numeric(test['hazard_score'],errors='coerce'); yo=test['orphan'].to_numpy(int)
 q=np.where((rr>=rr_cut)&(hz>=hz_cut),'RR_high_Hazard_high',np.where((rr>=rr_cut)&(hz<hz_cut),'RR_high_Hazard_low',np.where((rr<rr_cut)&(hz>=hz_cut),'RR_low_Hazard_high','RR_low_Hazard_low')))
 rows=[]
 for name in ['RR_high_Hazard_high','RR_high_Hazard_low','RR_low_Hazard_high','RR_low_Hazard_low']:
  m=q==name; rows.append({'quadrant':name,'n':int(m.sum()),'orphan_positives':int(yo[m].sum()),'rate':float(yo[m].mean()) if m.any() else None,'rr_median':float(rr[m].median()) if m.any() else None,'hazard_median':float(hz[m].median()) if m.any() else None})
 result={'experiment':'hydra_crash72_rr_hazard_quadrant_court_v3','holdout_year':2024,'train_years':'2020-2023','cuts':{'rr_median_train':rr_cut,'hazard_median_train':hz_cut},'class_counts':counts,'quadrants':rows}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
