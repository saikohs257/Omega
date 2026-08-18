from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd

HISTORY = [1, 6, 24, 72]

def auc(y, x):
    y=np.asarray(y,int); x=np.asarray(x,float)
    a=x[y==1]; b=x[y==0]
    if len(a)==0 or len(b)==0: return float('nan')
    # Mann-Whitney AUC
    order=np.argsort(np.r_[a,b], kind='mergesort'); vals=np.r_[a,b][order]
    ranks=np.empty(len(vals),float); i=0
    while i<len(vals):
        j=i+1
        while j<len(vals) and vals[j]==vals[i]: j+=1
        ranks[order[i:j]]=(i+j-1)/2+1; i=j
    return float((ranks[:len(a)].sum()-len(a)*(len(a)+1)/2)/(len(a)*len(b)))

def main(csv,out):
    df=pd.read_csv(csv)
    need=['timestamp','LiveDeficit']
    for c in need:
        if c not in df: raise SystemExit(f'missing {c}')
    df['timestamp']=pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
    df=df.sort_values('timestamp').reset_index(drop=True)
    for k in HISTORY: df[f'ld_lag{k}']=df['LiveDeficit'].shift(k)
    if 'episode_type' in df:
        # Conservative transition target: native 3->4 if available, otherwise no fabricated label.
        y=(df['episode_type'].shift(-1).astype(str).eq('4') & df['episode_type'].astype(str).eq('3')).astype(int)
    elif 'mode' in df:
        y=(df['mode'].shift(-1).astype(str).eq('4') & df['mode'].astype(str).eq('3')).astype(int)
    else:
        raise SystemExit('missing native transition label episode_type/mode')
    df['target']=y
    res={'rows':int(len(df)),'target_rows':int(y.sum()),'lags':{}}
    for k in HISTORY:
        z=df.dropna(subset=[f'ld_lag{k}','target'])
        res['lags'][str(k)]={'n':int(len(z)),'positives':int(z.target.sum()),'auc':auc(z.target,z[f'ld_lag{k}'])}
    # Recent trajectory summaries, kept descriptive rather than tuned.
    x=df['LiveDeficit']
    df['ld_delta1']=x-x.shift(1)
    df['ld_area24']=x.rolling(24,min_periods=24).mean()
    df['ld_above85_h24']=(x>0.85).rolling(24,min_periods=24).sum()
    for c in ['ld_delta1','ld_area24','ld_above85_h24']:
        z=df.dropna(subset=[c,'target']); res[c]={'n':int(len(z)),'positives':int(z.target.sum()),'auc':auc(z.target,z[c])}
    Path(out).write_text(json.dumps(res,indent=2,allow_nan=True))
    print(json.dumps(res,indent=2,allow_nan=True))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('csv'); p.add_argument('--out',required=True); a=p.parse_args(); main(a.csv,a.out)
