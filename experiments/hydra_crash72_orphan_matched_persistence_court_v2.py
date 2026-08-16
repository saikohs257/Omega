"""Matched-control persistence test with episode-age/state nearest neighbors."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from hydra_relative_recovery_court_v1 import history

def main(csv,out):
 d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
 y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int); path=d['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 base=path.eq('3_to_4')&pd.to_numeric(d['episode_age_h'],errors='coerce').eq(1); ex=y.eq(1)&~base; trans=ex&path.ne('<missing>'); orphan=ex&path.eq('<missing>'); core=y.eq(1)&base
 assert (int(core.sum()),int(trans.sum()),int(orphan.sum()),int(y.sum()))==(12,350,606,968)
 train=d[d.date.dt.year<2024]; test=d[d.date.dt.year==2024].copy(); ot=orphan.loc[test.index].to_numpy(bool)
 rrcut=float(pd.to_numeric(train['rr_recovery_minus_burden'],errors='coerce').quantile(.20)); hzcut=float(pd.to_numeric(train['hazard_score'],errors='coerce').quantile(.80))
 rr=pd.to_numeric(test['rr_recovery_minus_burden'],errors='coerce'); hz=pd.to_numeric(test['hazard_score'],errors='coerce'); age=pd.to_numeric(test['episode_age_h'],errors='coerce')
 state=((rr<rrcut)&(hz>hzcut)).to_numpy(bool); run=np.zeros(len(test),int)
 for i,v in enumerate(state): run[i]=run[i-1]+1 if v and i else (1 if v else 0)
 # controls: non-Crash72, different episode preferred, age +/- 2h; rank by normalized RR/Hazard distance.
 controls=[]; per_orphan=[]
 for oi in np.where(ot)[0]:
  a=age.iloc[oi]; r=rr.iloc[oi]; h=hz.iloc[oi]
  mask=(~ot)&y.loc[test.index].eq(0).to_numpy()&(age.sub(a).abs()<=2).to_numpy()
  idx=np.where(mask)[0]
  if len(idx)==0: continue
  dist=((rr.iloc[idx]-r).abs()/(rr.std()+1e-9)+(hz.iloc[idx]-h).abs()/(hz.std()+1e-9))
  order=idx[np.argsort(dist.to_numpy())[:min(5,len(idx))]]
  vals=run[order]; controls.extend(vals.tolist()); per_orphan.append({'orphan_index':int(oi),'n_controls':int(len(vals)),'orphan_persistence_h':int(run[oi]),'control_persistence_h':vals.tolist()})
 c=np.array(controls,int); od=run[ot]
 result={'experiment':'hydra_crash72_orphan_matched_persistence_court_v2','holdout_year':2024,'train_years':'2020-2023','cuts':{'rr_p20_train':rrcut,'hazard_p80_train':hzcut},'class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'orphans':{'n':int(len(od)),'median_h':float(np.median(od)),'mean_h':float(np.mean(od)),'p90_h':float(np.quantile(od,.9))},'matched_controls':{'n':int(len(c)),'controls_per_orphan_median':float(np.median([x['n_controls'] for x in per_orphan])) if per_orphan else 0,'median_h':float(np.median(c)) if len(c) else None,'mean_h':float(np.mean(c)) if len(c) else None,'p90_h':float(np.quantile(c,.9)) if len(c) else None},'paired_cases':per_orphan}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
