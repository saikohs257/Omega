from __future__ import annotations

"""TIAMAT lane-family tournament.

Research-only. Searches lane-local family pairs and A×B interactions using
out-of-sample scoring. AUC, Brier, interaction gain, and year stability are
reported separately; no authority promotion occurs here.
"""
import json, os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, PolynomialFeatures

DATA=Path(os.environ.get("TIAMAT_LAYER1_CSV","data/layer1_structured_hazard_arm_timeseries.csv"))
OUT=Path(os.environ.get("TIAMAT_LANE_TOURNAMENT_OUT","tiamat_lane_family_tournament_results.json"))
HEADS={"H0":"0_to_4","H2":"2_to_4","H3":"3_to_4","H4":"4_to_4"}
FAMILIES={
 "BURDEN":["LiveDeficit"],
 "HAZARD":["hazard_raw"],
 "SHOCK":["SimpleShock"],
 "RECOVERY":["RecoveryWeakness_v1"],
 "AGE":["episode_age_h"],
}
YEARS=[2020,2021,2022,2023,2024]

def target(df,h=15):
 a=df.entry_path.ne("none").to_numpy(); t=df.open_time.to_numpy(); y=np.full(len(df),np.nan)
 for i in range(len(df)-h):
  if not a[i]: continue
  exp=t[i]+np.arange(1,h+1).astype("timedelta64[h]")
  if np.array_equal(t[i+1:i+h+1],exp): y[i]=float(np.all(a[i+1:i+h+1]))
 return pd.Series(y,index=df.index)

def seats(df):
 a=df.entry_path.ne("none"); start=a & ~a.shift(1,fill_value=False); df=df.copy(); df["seat"]=None
 for h,p in HEADS.items():
  if h!="H4": df.loc[start & df.entry_path.eq(p),"seat"]=h
 df.loc[a & ~start,"seat"]="H4"; return df

def model(cols,interaction=False):
 steps=[("imp",SimpleImputer(strategy="median")),("scale",StandardScaler())]
 if interaction: steps.append(("poly",PolynomialFeatures(degree=2,include_bias=False)))
 steps += [("lr",LogisticRegression(max_iter=3000,C=1.0))]
 return Pipeline(steps)

def score(train,test,cols,interaction=False):
 m=model(cols,interaction); m.fit(train[cols],train.y); p=m.predict_proba(test[cols])[:,1]
 if test.y.nunique()<2:return np.nan,np.nan
 return float(roc_auc_score(test.y,p)),float(brier_score_loss(test.y,p))

def main():
 df=pd.read_csv(DATA,parse_dates=["open_time"]).sort_values("open_time").reset_index(drop=True); df["year"]=df.open_time.dt.year; df["y"]=target(df); df=seats(df); base=df[df.seat.notna() & df.y.notna()].copy()
 out={"dataset":str(DATA),"rows":len(df),"target":"15h active survival","families":FAMILIES,"heads":{},"selection":"Pareto reporting of AUC/Brier/stability; no arbitrary combined score"}
 for h in HEADS:
  g=base[base.seat.eq(h)].copy(); out["heads"][h]={"n":len(g),"pairs":[]}
  for fa,ca in FAMILIES.items():
   for fb,cb in FAMILIES.items():
    if fa>=fb: continue
    cols=ca+cb
    if len(g)<20 or g.y.nunique()<2: continue
    auc,brier=score(g,g,cols,False); iauc,ibrier=score(g,g,cols,True)
    gains=[]
    for yr in YEARS:
     tr=g[g.year!=yr]; te=g[g.year==yr]
     if len(tr)<20 or len(te)<5 or tr.y.nunique()<2 or te.y.nunique()<2: continue
     a,b=score(tr,te,cols,False); ia,ib=score(tr,te,cols,True); gains.append({"year":yr,"auc":a,"brier":b,"interaction_auc":ia,"interaction_brier":ib})
    out["heads"][h]["pairs"].append({"A":fa,"B":fb,"in_sample_auc":auc,"in_sample_brier":brier,"interaction_auc":iauc,"interaction_brier":ibrier,"interaction_gain":iauc-auc if np.isfinite(iauc) and np.isfinite(auc) else np.nan,"oos":gains})
  out["heads"][h]["pairs"].sort(key=lambda x:(-(x["interaction_gain"] if np.isfinite(x["interaction_gain"]) else -999),x["in_sample_brier"]))
 OUT.write_text(json.dumps(out,indent=2,default=float)); print(json.dumps(out,indent=2,default=float))
if __name__=="__main__":main()
