"""Matched-control test of low-RR/high-Hazard persistence for 2024 Crash72 Orphans."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from hydra_relative_recovery_court_v1 import history

def main(csv: Path, out: Path):
    d=history(pd.read_csv(csv)); d['date']=pd.to_datetime(d['open_time'],utc=True); d=d.sort_values('date').reset_index(drop=True)
    y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int)
    path=d['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
    base=path.eq('3_to_4') & pd.to_numeric(d['episode_age_h'],errors='coerce').eq(1)
    ex=y.eq(1)&~base; trans=ex&path.ne('<missing>'); orphan=ex&path.eq('<missing>'); core=y.eq(1)&base
    assert (int(core.sum()),int(trans.sum()),int(orphan.sum()),int(y.sum()))==(12,350,606,968)
    train=d[d.date.dt.year<2024]; test=d[d.date.dt.year==2024].copy(); ot=orphan.loc[test.index].to_numpy(bool)
    rr=pd.to_numeric(train['rr_recovery_minus_burden'],errors='coerce'); hz=pd.to_numeric(train['hazard_score'],errors='coerce')
    rr_cut=float(rr.quantile(.20)); hz_cut=float(hz.quantile(.80))
    rr_t=pd.to_numeric(test['rr_recovery_minus_burden'],errors='coerce'); hz_t=pd.to_numeric(test['hazard_score'],errors='coerce'); state=((rr_t<rr_cut)&(hz_t>hz_cut)).to_numpy(bool)
    run=np.zeros(len(test),dtype=int)
    for i,v in enumerate(state): run[i]=(run[i-1]+1 if v and i else (1 if v else 0))
    orphan_dur=run[ot]
    candidates=np.where(~ot & (test['episode_age_h'].between(1,999999, inclusive='both')).to_numpy())[0]
    rng=np.random.default_rng(72); controls=[]
    for oi in np.where(ot)[0]:
        age=float(test.iloc[oi]['episode_age_h']); r=float(rr_t.iloc[oi]); h=float(hz_t.iloc[oi]); day=test.iloc[oi]['date'].date()
        mask=(~ot)&(test['episode_age_h'].sub(age).abs()<=1)&(test['date'].dt.date==day)
        idx=np.where(mask.to_numpy())[0]
        if len(idx)==0: mask=(~ot)&(test['episode_age_h'].sub(age).abs()<=2); idx=np.where(mask.to_numpy())[0]
        if len(idx):
            dist=(rr_t.iloc[idx]-r).abs()+(hz_t.iloc[idx]-h).abs(); pick=idx[int(np.argmin(dist.to_numpy()))]; controls.append(run[pick])
    controls=np.array(controls,dtype=int)
    result={'experiment':'hydra_crash72_orphan_matched_persistence_court_v1','holdout_year':2024,'train_years':'2020-2023','cuts':{'rr_p20_train':rr_cut,'hazard_p80_train':hz_cut},'class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'orphans':{'n':int(len(orphan_dur)),'median_persistence_h':float(np.median(orphan_dur)),'mean_persistence_h':float(np.mean(orphan_dur)),'p90_h':float(np.quantile(orphan_dur,.9))},'matched_controls':{'n':int(len(controls)),'median_persistence_h':float(np.median(controls)) if len(controls) else None,'mean_persistence_h':float(np.mean(controls)) if len(controls) else None,'p90_h':float(np.quantile(controls,.9)) if len(controls) else None},'paired_delta':{'median_orphan_minus_control_h':float(np.median(orphan_dur[:len(controls)]-controls)) if len(controls) else None,'mean_orphan_minus_control_h':float(np.mean(orphan_dur[:len(controls)]-controls)) if len(controls) else None}}
    out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
