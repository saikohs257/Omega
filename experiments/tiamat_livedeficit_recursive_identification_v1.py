from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd
from tiamat.dynamics import live_deficit_update


def auc(y,x):
    y=np.asarray(y,int); x=np.asarray(x,float); a=x[y==1]; b=x[y==0]
    if len(a)==0 or len(b)==0:return float('nan')
    order=np.argsort(np.r_[a,b],kind='mergesort'); vals=np.r_[a,b][order]; ranks=np.empty(len(vals),float); i=0
    while i<len(vals):
        j=i+1
        while j<len(vals) and vals[j]==vals[i]:j+=1
        ranks[order[i:j]]=(i+j-1)/2+1;i=j
    return float((ranks[:len(a)].sum()-len(a)*(len(a)+1)/2)/(len(a)*len(b)))

def downside_candidates(x):
    r=x.pct_change().fillna(0.0)*100.0
    # Three deliberately different, non-fitted downside definitions.
    d_roll=r.rolling(24,min_periods=1).apply(lambda z:max(0.0,float(-np.min(z))),raw=True)
    d_mean=(-r.clip(upper=0)).rolling(24,min_periods=1).mean()
    d_zero=pd.Series(0.0,index=x.index)
    return {'rolling_min':d_roll,'mean_downside':d_mean,'none':d_zero}

def run(df, initial, downside):
    out=np.empty(len(df),float); out[0]=initial
    for i in range(1,len(df)):
        out[i]=live_deficit_update(out[i-1],float(df.iloc[i].get('ret_1h',0.0)),float(df.iloc[i]['SimpleShock']),float(downside.iloc[i]))
    return out

def main(csv,out):
    df=pd.read_csv(csv)
    ldcol='LiveDeficit'; ss='SimpleShock'
    if ldcol not in df or ss not in df: raise SystemExit('canonical columns LiveDeficit/SimpleShock required')
    retcol=next((c for c in ['ret_1h','ret_1h_pct','return_1h'] if c in df),None)
    if not retcol: raise SystemExit('no canonical 1h return column found')
    df['ret_1h']=pd.to_numeric(df[retcol],errors='coerce').fillna(0.0)
    df[ldcol]=pd.to_numeric(df[ldcol],errors='coerce'); df[ss]=pd.to_numeric(df[ss],errors='coerce')
    df=df.dropna(subset=[ldcol,ss]).reset_index(drop=True)
    initial=float(df[ldcol].iloc[0]); downs=downside_candidates(df[retcol] if retcol else df['ret_1h'])
    res={'rows':len(df),'initial_native_ld':initial,'models':{}}
    native=df[ldcol].to_numpy(float)
    for name,d in downs.items():
        pred=run(df,initial,d)
        err=pred-native
        res['models'][name]={
          'corr':float(np.corrcoef(pred,native)[0,1]),
          'mae':float(np.mean(np.abs(err))),
          'rmse':float(np.sqrt(np.mean(err*err))),
          'max_abs_error':float(np.max(np.abs(err))),
          'threshold_agreement_070':float(np.mean((pred>.70)==(native>.70))),
          'threshold_agreement_085':float(np.mean((pred>.85)==(native>.85))),
          'lane_agreement':float(np.mean(np.select([native<=.70,native<=.85],[0,2],default=3)==np.select([pred<=.70,pred<=.85],[0,2],default=3))),
          'native_ld_auc':auc((native>.85).astype(int),pred),
        }
    Path(out).write_text(json.dumps(res,indent=2,allow_nan=True)); print(json.dumps(res,indent=2,allow_nan=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('--out',required=True);a=p.parse_args();main(a.csv,a.out)
