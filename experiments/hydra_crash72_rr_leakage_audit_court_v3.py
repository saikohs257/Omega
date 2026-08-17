"""Self-contained RR provenance audit with canonical 2024 Orphan taxonomy."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score
from hydra_relative_recovery_court_v1 import history

def auc(y,x):
 x=pd.to_numeric(x,errors='coerce'); y=np.asarray(y,int); m=x.notna().to_numpy()&np.isfinite(x.to_numpy()); xx=x.to_numpy()[m]; yy=y[m]
 if len(np.unique(yy))<2:return None
 return {'auc':float(roc_auc_score(yy,xx)),'auc_reversed':float(roc_auc_score(yy,-xx)),'pr_auc':float(average_precision_score(yy,xx))}

def taxonomy(d):
 y=pd.to_numeric(d['Crash72'],errors='coerce').fillna(0).astype(int); p=d['entry_path'].astype('string').fillna('<missing>').str.strip().replace({'':'<missing>','nan':'<missing>','None':'<missing>','none':'<missing>'}); a=pd.to_numeric(d['episode_age_h'],errors='coerce')
 core=y.eq(1)&p.eq('3_to_4')&a.eq(1); orphan=y.eq(1)&~core&p.eq('<missing>'); trans=y.eq(1)&~core&p.ne('<missing>')
 return y,p,a,core,orphan,trans

def main(csv:Path,out:Path):
 raw=pd.read_csv(csv); d=history(raw); assert len(raw)==43848
 y,p,a,core,orphan,trans=taxonomy(d); assert (int(core.sum()),int(trans.sum()),int(orphan.sum()),int(y.sum()))==(12,350,606,968)
 test=d[d.open_time.dt.year==2024].copy().reset_index(drop=True); yt,tp,ta,tc,to,tt=taxonomy(test)
 counts={'rows':int(len(test)),'crash72':int(yt.sum()),'core':int(tc.sum()),'orphan':int(to.sum()),'transition':int(tt.sum())}
 rr=pd.to_numeric(test['rr_recovery_minus_burden'],errors='coerce'); rw=pd.to_numeric(test['RecoveryWeakness_v1'],errors='coerce'); ld=pd.to_numeric(test['LiveDeficit'],errors='coerce'); rebuilt=rw.shift(1)-ld.shift(1)
 assert np.isclose(rr.to_numpy(dtype=float),rebuilt.to_numpy(dtype=float),equal_nan=True).all()
 result={'experiment':'hydra_crash72_rr_leakage_audit_court_v3','canonical_rows':int(len(raw)),'global_taxonomy':{'core':int(core.sum()),'transition':int(trans.sum()),'orphan':int(orphan.sum()),'crash72':int(y.sum())},'holdout_2024_taxonomy':counts,'holdout_time':{'min':str(test.open_time.min()),'max':str(test.open_time.max())},'rr_provenance':{'formula':'RecoveryWeakness_v1.shift(1) - LiveDeficit.shift(1)','rebuild_matches_original':True,'uses_target_column':False,'uses_entry_path':False,'uses_episode_age':False,'source_columns':['RecoveryWeakness_v1','LiveDeficit']},'rr_holdout_discrimination':{'vs_crash72':auc(yt,rr),'vs_orphan':auc(to,rr),'vs_non_orphan_crash72':auc((yt.eq(1)&~to).to_numpy(),rr.loc[yt.eq(1)|to].reset_index(drop=True) if False else pd.Series(dtype=float))},'orphan_timestamps':test.loc[to,'open_time'].astype(str).tolist()}
 out.write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('csv',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
