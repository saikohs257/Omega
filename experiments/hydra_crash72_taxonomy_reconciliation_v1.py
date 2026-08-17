"""Reconcile canonical Crash72 taxonomy across raw vs history-derived frames.
No assertions about expected 2024 counts; this is a pure diagnostic.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import pandas as pd
from hydra_relative_recovery_court_v1 import history

def clean_json(x):
    if isinstance(x, dict): return {str(k):clean_json(v) for k,v in x.items()}
    if isinstance(x, list): return [clean_json(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x): return None
    return x

def classify(d):
 y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int).eq(1)
 path=d['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 age=pd.to_numeric(d['episode_age_h'],errors='coerce')
 core=y&path.eq('3_to_4')&age.eq(1)
 orphan=y&~core&path.eq('<missing>')
 trans=y&~core&path.ne('<missing>')
 return {'rows':int(len(d)),'crash72':int(y.sum()),'core':int(core.sum()),'orphan':int(orphan.sum()),'transition':int(trans.sum()),'path_counts':path.value_counts(dropna=False).to_dict(),'crash_path_counts':path[y].value_counts(dropna=False).to_dict(),'crash_age_counts':age[y].value_counts(dropna=False).sort_index().to_dict()}

def main(csv:Path,out:Path):
 raw=pd.read_csv(csv)
 hist=history(raw)
 raw['open_time']=pd.to_datetime(raw['open_time'],utc=True); hist['open_time']=pd.to_datetime(hist['open_time'],utc=True)
 raw=raw.sort_values('open_time').reset_index(drop=True); hist=hist.sort_values('open_time').reset_index(drop=True)
 raw24=raw[raw.open_time.dt.year==2024].copy(); hist24=hist[hist.open_time.dt.year==2024].copy()
 result={'experiment':'hydra_crash72_taxonomy_reconciliation_v1','raw_global':classify(raw),'history_global':classify(hist),'raw_2024':classify(raw24),'history_2024':classify(hist24),'timestamp_bounds':{'raw_2024_min':str(raw24.open_time.min()),'raw_2024_max':str(raw24.open_time.max()),'history_2024_min':str(hist24.open_time.min()),'history_2024_max':str(hist24.open_time.max())},'raw_vs_history_label_equal':bool(raw['Crash72'].reset_index(drop=True).equals(hist['Crash72'].reset_index(drop=True))),'raw_vs_history_path_equal':bool(raw['entry_path'].reset_index(drop=True).equals(hist['entry_path'].reset_index(drop=True))),'raw_vs_history_age_equal':bool(raw['episode_age_h'].reset_index(drop=True).equals(hist['episode_age_h'].reset_index(drop=True)))}
 result=clean_json(result)
 out.write_text(json.dumps(result,indent=2,allow_nan=False,default=str)); print(json.dumps(result,indent=2,allow_nan=False,default=str))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
