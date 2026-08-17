"""Forensic audit of RR provenance and Orphan taxonomy on the canonical holdout."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score
from hydra_relative_recovery_court_v1 import history

def auc(y,x):
 x=pd.to_numeric(x,errors='coerce'); y=np.asarray(y,int); m=x.notna().to_numpy()&np.isfinite(x.to_numpy())
 xx=x.to_numpy()[m]; yy=y[m]
 if len(np.unique(yy))<2:return None
 return {'auc':float(roc_auc_score(yy,xx)),'auc_reversed':float(roc_auc_score(yy,-xx)),'pr_auc':float(average_precision_score(yy,xx))}

def main(csv:Path,out:Path):
 raw=pd.read_csv(csv); d=history(raw); assert len(raw)==43848
 y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int)
 path=d['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 age=pd.to_numeric(d['episode_age_h'],errors='coerce')
 core=y.eq(1)&path.eq('3_to_4')&age.eq(1); orphan=y.eq(1)&~core&path.eq('<missing>'); trans=y.eq(1)&~core&path.ne('<missing>')
 assert (int(core.sum()),int(trans.sum()),int(orphan.sum()),int(y.sum()))==(12,350,606,968)
 test=d[d.open_time.dt.year==2024].copy().reset_index(drop=True)
 yt=pd.to_numeric(test['Crash72'],errors='coerce').fillna(0).astype(int); tp=test['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'}); ta=pd.to_numeric(test['episode_age_h'],errors='coerce')
 tc=yt.eq(1)&tp.eq('3_to_4')&ta.eq(1); to=yt.eq(1)&~tc&tp.eq('<missing>'); tt=yt.eq(1)&~tc&tp.ne('<missing>')
 hold_counts={'rows':int(len(test)),'crash72':int(yt.sum()),'core':int(tc.sum()),'orphan':int(to.sum()),'transition':int(tt.sum()),'year_min':str(test.open_time.min()),'year_max':str(test.open_time.max())}
 print('HOLDOUT_COUNTS='+json.dumps(hold_counts,sort_keys=True))
 if not (int(yt.sum())==67 and int(to.sum())==29 and int(tt.sum())==26 and int(tc.sum())==12):
  result={'experiment':'hydra_crash72_rr_leakage_audit_court_v3_diagnostic','canonical_rows':int(len(raw)),'global_taxonomy':{'core':int(core.sum()),'transition':int(trans.sum()),'orphan':int(orphan.sum()),'crash72':int(y.sum())},'holdout_2024_actual':hold_counts,'diagnosis':'Holdout taxonomy differs from previously observed 67/29/26/12; stop before RR AUC and reconcile chronology/filtering.'}
  out.write_text(json.dumps(result,indent=2,allow_nan=False)); raise RuntimeError(json.dumps(result))
 rr=pd.to_numeric(test['rr_recovery_minus_burden'],errors='coerce'); rw=pd.to_numeric(test['RecoveryWeakness_v1'],errors='coerce'); ld=pd.to_numeric(test['LiveDeficit'],errors='coerce'); rr_rebuilt=rw.shift(1)-ld.shift(1)
 assert np.isclose(rr.to_numpy(dtype=float),rr_rebuilt.to_numpy(dtype=float),equal_nan=True).all()
 event_orphan=to.to_numpy(bool); event_crash=yt.to_numpy(bool); rr1=rr; rr0=rr.shift(-1)
 result={'experiment':'hydra_crash72_rr_leakage_audit_court_v3','canonical_rows':int(len(raw)),'global_taxonomy':{'core':int(core.sum()),'transition':int(trans.sum()),'orphan':int(orphan.sum()),'crash72':int(y.sum())},'holdout_2024_taxonomy':{'core':int(tc.sum()),'transition':int(tt.sum()),'orphan':int(to.sum()),'crash72':int(yt.sum()),'orphan_timestamps':test.loc[to,'open_time'].astype(str).tolist()},'rr_provenance':{'formula':'RecoveryWeakness_v1.shift(1) - LiveDeficit.shift(1)','rebuild_matches_original':True,'uses_target_column':False,'uses_entry_path':False,'uses_episode_age':False,'source_columns':['RecoveryWeakness_v1','LiveDeficit'],'forbidden_columns':['Crash72','entry_path','episode_age_h']},'holdout_rr':{'rr_vs_crash72':auc(event_crash,rr1),'rr_vs_orphan':auc(event_orphan,rr1),'rr_predecessor_vs_orphan':auc(event_orphan,rr0)},'consistency_assertions':{'global_taxonomy_pass':True,'holdout_67_29_26_12_pass':True,'rr_formula_pass':True}}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
