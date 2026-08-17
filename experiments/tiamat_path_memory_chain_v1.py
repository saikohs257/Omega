from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd

BASE=['SimpleShock','LiveDeficit','RecoveryWeakness_v1','hazard_raw']
H=6; SEP=168; CAL=.05; YEAR_TEST=2024

def target(d):
 d=d.sort_values('open_time').reset_index(drop=True); t=d.open_time.to_numpy(); p=d.entry_path.astype(str).to_numpy(); y=np.zeros(len(d),int)
 for i in range(len(d)):
  j=np.searchsorted(t,t[i]+np.timedelta64(H,'h'),'right')
  if j>i+1:y[i]=np.any(p[i+1:j]=='3_to_4')
 return y

def features(d):
 x=d.copy(); ld=x.LiveDeficit.to_numpy(float); sh=x.SimpleShock.to_numpy(float); rec=x.RecoveryWeakness_v1.to_numpy(float)
 x['ld_slope6']=pd.Series(ld).diff(6).to_numpy(); x['ld_peak24']=pd.Series(ld).rolling(24,min_periods=1).max().to_numpy(); x['ld_area6']=pd.Series(ld).rolling(6,min_periods=1).mean().to_numpy(); x['hours_ld_high']=pd.Series(ld>.7).rolling(24,min_periods=1).sum().to_numpy(); x['hours_shock_high']=pd.Series(sh>.7).rolling(24,min_periods=1).sum().to_numpy(); x['since_ld_peak']=0.0; last=-1
 for i,v in enumerate(ld):
  if i and v>=np.nanmax(ld[max(0,i-24):i+1]): last=i
  x.loc[i,'since_ld_peak']=i-last if last>=0 else 999
 x['recent_excursions']=(pd.Series(ld>.7).astype(int).diff().fillna(0).gt(0)).rolling(48,min_periods=1).sum().to_numpy()
 x['path_class']=pd.cut(x.ld_slope6,[-np.inf,-.05,.05,np.inf],labels=['falling','flat','rising']).astype(str)
 x['target']=target(x); return x

def match(q,cols):
 med=q[cols].median().to_numpy(float); iqr=np.asarray(q[cols].quantile(.75)-q[cols].quantile(.25),float).copy(); iqr[iqr<=1e-12]=1; z=(q[cols].to_numpy(float)-med)/iqr; pos=np.flatnonzero(q.target.to_numpy()==1); neg=np.flatnonzero(q.target.to_numpy()==0); ts=q.open_time.to_numpy(dtype='datetime64[ns]'); c=[]
 for i in pos:
  dist=np.sqrt(((z[neg]-z[i])**2).mean(1)); sep=np.abs((ts[neg]-ts[i])/np.timedelta64(1,'h'))
  for k in np.flatnonzero(sep>=SEP):
   if dist[k]<=CAL:c.append((i,int(neg[k]),float(dist[k])))
 c.sort(key=lambda z:z[2]); used=set();out=[]
 for a,b,_ in c:
  if a in used or b in used:continue
  used|={a,b};out.append((a,b))
 return out

def auc(q,p,col):
 v=q[col].to_numpy(float); z=[1 if v[a]>v[b] else 0 if v[a]<v[b] else .5 for a,b in p if np.isfinite(v[a]) and np.isfinite(v[b])]; return float(np.mean(z)) if z else np.nan

def main(inp,out):
 d=pd.read_csv(inp);d.open_time=pd.to_datetime(d.open_time,utc=True);x=features(d); rows=[]
 # Stage 1: discovery of path variables on 2020-2021, separately by year.
 candidates=['ld_slope6','ld_peak24','ld_area6','hours_ld_high','hours_shock_high','since_ld_peak','recent_excursions']
 disc=x[x.open_time.dt.year.isin([2020,2021])].copy()
 for c in candidates:
  vals=[]
  for y in [2020,2021]:
   q=disc[disc.open_time.dt.year==y].dropna(subset=BASE+['target',c]); p=match(q,BASE); vals.append(auc(q,p,c))
  rows.append({'stage':1,'candidate':c,'year1_auc':vals[0],'year2_auc':vals[1],'mean_abs_effect':np.nanmean([abs(v-.5) for v in vals])})
 best=max(rows,key=lambda r:r['mean_abs_effect'])['candidate']
 # Stage 2: refine only the chosen path family using 2022-2023 and nearby variants.
 variants=[best]
 q=x[x.open_time.dt.year.isin([2022,2023])].copy()
 for c in variants:
  vals=[]
  for y in [2022,2023]:
   z=q[q.open_time.dt.year==y].dropna(subset=BASE+['target',c]);p=match(z,BASE);vals.append(auc(z,p,c))
  rows.append({'stage':2,'candidate':c,'year1_auc':vals[0],'year2_auc':vals[1],'mean_abs_effect':np.nanmean([abs(v-.5) for v in vals])})
 # Stage 3: locked 2024 test; no selection on it.
 test=x[x.open_time.dt.year==YEAR_TEST].dropna(subset=BASE+['target',best]).copy(); p=match(test,BASE); outp=match(test,BASE+[best]);
 result={'experiment':'TIAMAT_PATH_MEMORY_CHAIN_V1','classification':'experimental/non-authoritative','stage1_candidates':rows[:7],'stage2':rows[7:],'selected_path_variable':best,'locked_test':{'year':YEAR_TEST,'base_pairs':len(p),'path_auc':auc(test,p,best),'state_conditioned_pairs':len(outp),'ld_residual_auc':auc(test,outp,'LiveDeficit')}}
 Path(out).write_text(json.dumps(result,indent=2,allow_nan=True));print(json.dumps(result,indent=2,allow_nan=True))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('csv');a.add_argument('--out',required=True);z=a.parse_args();main(z.csv,z.out)
