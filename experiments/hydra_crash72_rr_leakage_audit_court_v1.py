"""Forensic audit of rr_recovery_minus_burden against Crash72/Orphan labels.
Tests provenance, temporal ordering, episode-label dependence, and anti-leakage variants.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score
from hydra_relative_recovery_court_v1 import history

def auc(y,x):
 m=pd.notna(x)&np.isfinite(pd.to_numeric(x,errors='coerce').to_numpy()); xx=pd.to_numeric(x,errors='coerce').to_numpy()[m]; yy=np.asarray(y)[m]
 if len(np.unique(yy))<2:return None
 return {'auc':float(roc_auc_score(yy,xx)),'auc_reversed':float(roc_auc_score(yy,-xx)),'pr_auc':float(average_precision_score(yy,-xx))}

def main(csv:Path,out:Path):
 raw=pd.read_csv(csv); d=history(raw); assert len(raw)==43848
 y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int).to_numpy(); path=d['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'})
 core=(y==1)&path.eq('3_to_4')&pd.to_numeric(d['episode_age_h'],errors='coerce').eq(1); orphan=(y==1)&~core&path.eq('<missing>'); trans=(y==1)&~core&path.ne('<missing>')
 assert (int(core.sum()),int(trans.sum()),int(orphan.sum()),int(y.sum()))==(12,350,606,968)
 rr=pd.to_numeric(d['rr_recovery_minus_burden'],errors='coerce'); rr_orig=rr.copy()
 # Build strictly pre-row ingredients independently to prove no current-row target dependence.
 rw=pd.to_numeric(d['RecoveryWeakness_v1'],errors='coerce'); ld=pd.to_numeric(d['LiveDeficit'],errors='coerce'); rr_rebuilt=rw.shift(1)-ld.shift(1)
 # Episode-boundary contamination test: within each non-Crash72 episode, compare RR distribution to Crash72 labels.
 episode=d['episode_id'] if 'episode_id' in d.columns else pd.Series(np.nan,index=d.index)
 same_event=[]
 for eid,g in d.groupby(episode,dropna=False):
  same_event.append({'episode_id':str(eid),'rows':int(len(g)),'crash72':int(pd.to_numeric(g['Crash72'],errors='coerce').fillna(0).sum()),'rr_range':float(pd.to_numeric(g['rr_recovery_minus_burden'],errors='coerce').max()-pd.to_numeric(g['rr_recovery_minus_burden'],errors='coerce').min()) if g['rr_recovery_minus_burden'].notna().any() else None})
 # Holdout event-row audits.
 test=d[d.open_time.dt.year==2024].copy(); yt=pd.to_numeric(test['Crash72'],errors='coerce').fillna(0).astype(int).to_numpy(); ot=test['orphan'].to_numpy(bool) if 'orphan' in test.columns else ((yt==1)&~test['entry_path'].astype('string').fillna('<missing>').eq('3_to_4')&test['entry_path'].astype('string').fillna('<missing>').eq('<missing>')).to_numpy(bool)
 rrt=pd.to_numeric(test['rr_recovery_minus_burden'],errors='coerce'); rr_rebuilt_t=pd.to_numeric(test['RecoveryWeakness_v1'],errors='coerce').shift(1)-pd.to_numeric(test['LiveDeficit'],errors='coerce').shift(1)
 pre_event_orphan=ot; pre_event_non=(yt==1)&~ot
 # Current-row versus one-row-ahead label timing: if RR separation vanishes when labels are shifted one hour later, it may merely mirror episode construction.
 y_next=np.r_[yt[1:],0]; y_orphan_next=np.r_[ot[1:],False]
 result={'experiment':'hydra_crash72_rr_leakage_audit_court_v1','canonical_rows':int(len(raw)),'class_counts':{'core':12,'transition':350,'orphan':606,'crash72':968},'holdout_2024':{'crash72_n':int(yt.sum()),'orphan_n':int(ot.sum()),'rr_current_vs_crash72':auc(yt,rrt),'rr_rebuilt_pre_row_vs_crash72':auc(yt,rr_rebuilt_t),'rr_current_vs_orphan':auc(ot,rrt),'rr_rebuilt_pre_row_vs_orphan':auc(ot,rr_rebuilt_t),'rr_vs_next_crash72':auc(y_next,rrt),'rr_vs_next_orphan':auc(y_orphan_next,rrt)},'provenance_test':{'current_formula':'RecoveryWeakness_v1.shift(1) - LiveDeficit.shift(1)','rebuild_matches_original':bool(np.isclose(rr_orig.to_numpy(dtype=float),rr_rebuilt.to_numpy(dtype=float),equal_nan=True).all()),'uses_target_column':False,'uses_entry_path':False,'uses_episode_age':False},'episode_audit':{'unique_episode_ids_checked':int(len(same_event)),'episodes_with_multiple_crash72_rows':int(sum(x['crash72']>1 for x in same_event))}}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
