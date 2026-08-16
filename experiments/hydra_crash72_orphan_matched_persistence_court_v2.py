"""Matched-control persistence test with explicit 2024 control population."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from hydra_relative_recovery_court_v1 import history

def main(csv: Path,out: Path):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 d['is_crash72']=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int).eq(1)
 path=d['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 d['is_core']=path.eq('3_to_4')&pd.to_numeric(d['episode_age_h'],errors='coerce').eq(1)&d['is_crash72']
 d['is_orphan']=d['is_crash72']&~d['is_core']&path.eq('<missing>')
 d['is_transition']=d['is_crash72']&~d['is_core']&path.ne('<missing>')
 assert (int(d.is_core.sum()),int(d.is_transition.sum()),int(d.is_orphan.sum()),int(d.is_crash72.sum()))==(12,350,606,968)
 train=d[d.date.dt.year<2024]; test=d[d.date.dt.year==2024].copy().reset_index(drop=True)
 rr_cut=float(pd.to_numeric(train['rr_recovery_minus_burden'],errors='coerce').quantile(.20)); hz_cut=float(pd.to_numeric(train['hazard_score'],errors='coerce').quantile(.80))
 rr=pd.to_numeric(test['rr_recovery_minus_burden'],errors='coerce'); hz=pd.to_numeric(test['hazard_score'],errors='coerce'); age=pd.to_numeric(test['episode_age_h'],errors='coerce')
 state=((rr<rr_cut)&(hz>hz_cut)).to_numpy(bool); run=np.zeros(len(test),int)
 for i,v in enumerate(state): run[i]=run[i-1]+1 if v and i else (1 if v else 0)
 orphan_mask=test['is_orphan'].to_numpy(bool); crash_mask=test['is_crash72'].to_numpy(bool)
 controls=[]; per_orphan=[]
 rr_sd=float(rr.std()) or 1.0; hz_sd=float(hz.std()) or 1.0
 for oi in np.where(orphan_mask)[0]:
  a=age.iloc[oi]; r=rr.iloc[oi]; h=hz.iloc[oi]
  # Explicit 2024 population: non-Crash72 rows only, and never the Orphan's own row.
  mask=(~crash_mask)&(~orphan_mask)&age.notna()&age.sub(a).abs().le(2)
  idx=np.flatnonzero(mask.to_numpy())
  if len(idx)==0: continue
  dist=(rr.iloc[idx]-r).abs()/rr_sd+(hz.iloc[idx]-h).abs()/hz_sd
  order=idx[np.argsort(dist.to_numpy())[:min(5,len(idx))]]
  vals=run[order].astype(int); controls.extend(vals.tolist())
  per_orphan.append({'orphan_index':int(oi),'n_controls':int(len(vals)),'orphan_persistence_h':int(run[oi]),'control_persistence_h':vals.tolist()})
 if not controls:
  raise RuntimeError('CONTROL_POOL_EMPTY: no valid non-Crash72 2024 controls within episode-age +/-2h')
 c=np.array(controls,int); od=run[orphan_mask]
 result={'experiment':'hydra_crash72_orphan_matched_persistence_court_v3','holdout_year':2024,'train_years':'2020-2023','cuts':{'rr_p20_train':rr_cut,'hazard_p80_train':hz_cut},'class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'orphans':{'n':int(len(od)),'median_h':float(np.median(od)),'mean_h':float(np.mean(od)),'p90_h':float(np.quantile(od,.9))},'matched_controls':{'n':int(len(c)),'controls_per_orphan_median':float(np.median([x['n_controls'] for x in per_orphan])),'median_h':float(np.median(c)),'mean_h':float(np.mean(c)),'p90_h':float(np.quantile(c,.9))},'paired_cases':per_orphan}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
