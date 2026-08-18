from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd
HISTORY=[1,6,24,72]
def auc(y,x):
 y=np.asarray(y,int); x=np.asarray(x,float); a=x[y==1]; b=x[y==0]
 if len(a)==0 or len(b)==0:return float('nan')
 order=np.argsort(np.r_[a,b],kind='mergesort'); vals=np.r_[a,b][order]; ranks=np.empty(len(vals),float); i=0
 while i<len(vals):
  j=i+1
  while j<len(vals) and vals[j]==vals[i]:j+=1
  ranks[order[i:j]]=(i+j-1)/2+1; i=j
 return float((ranks[:len(a)].sum()-len(a)*(len(a)+1)/2)/(len(a)*len(b)))
def pick(df,names):
 low={str(c).strip().lower():c for c in df.columns}
 for n in names:
  if n.lower() in low:return low[n.lower()]
 return None
def main(csv,out):
 df=pd.read_csv(csv); ld=pick(df,['LiveDeficit','live_deficit','liveDeficit'])
 if ld is None:raise SystemExit(f'missing LiveDeficit; columns={list(df.columns)}')
 tc=pick(df,['timestamp','timestamp_utc','datetime','date','time','ts'])
 if tc is None: df['_row_time']=np.arange(len(df)); tc='_row_time'
 else:
  p=pd.to_datetime(df[tc],utc=True,errors='coerce')
  if p.notna().sum()<max(10,int(.9*len(df))):df['_row_time']=np.arange(len(df));tc='_row_time'
  else:df[tc]=p
 df=df.sort_values(tc).reset_index(drop=True); x=pd.to_numeric(df[ld],errors='coerce')
 for k in HISTORY:df[f'ld_lag{k}']=x.shift(k)
 et=pick(df,['episode_type','mode','episode','state'])
 if et is None:raise SystemExit(f'missing native transition label; columns={list(df.columns)}')
 s=df[et].astype(str).str.strip(); y=(s.eq('3')&s.shift(-1).eq('4')).astype(int); df['target']=y
 res={'rows':int(len(df)),'target_rows':int(y.sum()),'time_column':str(tc),'ld_column':str(ld),'target_column':str(et),'lags':{}}
 for k in HISTORY:
  z=df.dropna(subset=[f'ld_lag{k}','target']);res['lags'][str(k)]={'n':int(len(z)),'positives':int(z.target.sum()),'auc':auc(z.target,z[f'ld_lag{k}'])}
 df['ld_delta1']=x-x.shift(1);df['ld_area24']=x.rolling(24,min_periods=24).mean();df['ld_above85_h24']=(x>.85).rolling(24,min_periods=24).sum()
 for c in ['ld_delta1','ld_area24','ld_above85_h24']:
  z=df.dropna(subset=[c,'target']);res[c]={'n':int(len(z)),'positives':int(z.target.sum()),'auc':auc(z.target,z[c])}
 Path(out).write_text(json.dumps(res,indent=2,allow_nan=True));print(json.dumps(res,indent=2,allow_nan=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('--out',required=True);a=p.parse_args();main(a.csv,a.out)
