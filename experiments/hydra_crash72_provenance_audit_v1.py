"""Forensic provenance audit for the native Crash72 label.

Do not invent a new target. Compare native Crash72 against several mechanically
plausible reconstructions from the canonical episode fields, then characterize
where/when the disagreements occur. This is diagnostic only; no model selection.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

N=43848

def target_from_times(times, events, h):
    ts=times.view("int64")//10**9
    ev=np.sort(pd.to_datetime(events,utc=True).astype("int64").to_numpy()//10**9)
    out=np.zeros(len(ts),dtype=np.int8)
    for i,t in enumerate(ts):
        j=np.searchsorted(ev,t,side="right")
        out[i]=int(j<len(ev) and ev[j] <= t+h*3600)
    return out

def agreement(y,p):
    y=np.asarray(y,int); p=np.asarray(p,int)
    return {"agreement":float(np.mean(y==p)),"mismatches":int(np.sum(y!=p)),
            "tp":int(np.sum((y==1)&(p==1))),"fp":int(np.sum((y==0)&(p==1))),
            "fn":int(np.sum((y==1)&(p==0))),"tn":int(np.sum((y==0)&(p==0)))}

def main(csv:Path,out:Path):
    d=pd.read_csv(csv); assert len(d)==N and "Crash72" in d
    d["open_time"]=pd.to_datetime(d.open_time,utc=True); d=d.sort_values("open_time").reset_index(drop=True)
    y=pd.to_numeric(d.Crash72,errors="coerce").fillna(0).astype(int).to_numpy()
    # Candidate event definitions, intentionally predeclared.
    candidates={
      "entry_3_to_4_age1": d.loc[(d.entry_path=="3_to_4")&(d.episode_age_h==1),"open_time"],
      "entry_3_to_4_any_age": d.loc[d.entry_path=="3_to_4","open_time"],
      "age1_any_path": d.loc[d.episode_age_h==1,"open_time"],
      "episode_type_3_to_4_age1": d.loc[(d.episode_type=="3_to_4")&(d.episode_age_h==1),"open_time"] if "episode_type" in d else pd.Series([],dtype="datetime64[ns, UTC]"),
    }
    results={}
    for name,ev in candidates.items():
        p=target_from_times(d.open_time,ev,72); results[name]=agreement(y,p)
    # Native-positive and reconstructed-positive run-length diagnostics.
    def runs(x):
        x=np.asarray(x,int); starts=np.where((x==1)&(np.r_[0,x[:-1]]==0))[0]; ends=np.where((x==1)&(np.r_[x[1:],0]==0))[0]
        return [int(e-s+1) for s,e in zip(starts,ends)]
    p=target_from_times(d.open_time,candidates["entry_3_to_4_age1"],72)
    diagnostics={"native_positive_rows":int(y.sum()),"reconstructed_positive_rows":int(p.sum()),
                 "native_positive_runs":runs(y),"reconstructed_positive_runs":runs(p)}
    # Mismatch localization by calendar year/month.
    mm=(y!=p); d["mismatch"]=mm; d["native_positive"]=y; d["recon_positive"]=p
    by_year=d.groupby(d.open_time.dt.year).mismatch.agg(["sum","count","mean"]).reset_index().to_dict("records")
    by_month=d.groupby(d.open_time.dt.to_period("M").astype(str)).mismatch.agg(["sum","count","mean"]).reset_index().to_dict("records")
    # For each native positive mismatch, distance to nearest declared event start.
    ev=np.sort(pd.to_datetime(candidates["entry_3_to_4_age1"],utc=True).astype("int64").to_numpy()/1e9)
    ts=d.open_time.astype("int64").to_numpy()/1e9
    distances=[]
    for t in ts[mm]:
        if len(ev): distances.append(float(np.min(np.abs(ev-t))/3600))
    payload={"experiment":"hydra_crash72_provenance_audit_v1","canonical_rows":N,
      "native_crash72_prevalence":float(y.mean()),"candidate_reconstructions":results,
      "primary_diagnostics":diagnostics,"mismatch_by_year":by_year,"mismatch_by_month":by_month,
      "primary_mismatch_nearest_event_distance_hours_summary":({"n":len(distances),"min":float(np.min(distances)),"median":float(np.median(distances)),"p90":float(np.percentile(distances,90)),"max":float(np.max(distances))} if distances else None),
      "protocol":"predeclared mechanical reconstructions only; no target/model selected; audit hard-fails if canonical shape changes"}
    out.write_text(json.dumps(payload,indent=2,default=str)); print(json.dumps(payload,indent=2,default=str))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); main(a.csv,a.out)
