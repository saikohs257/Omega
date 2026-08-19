"""Provenance-deduplicated second pass over low-AUC archaeology.

The first screen counted every reported AUC row. This pass groups observations
that appear to come from the same result family, target, and model context so
we can distinguish repeated manifestations of one scoring defect from
independent candidate variables.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

AUC_RE = re.compile(r"(?i)(?:ROC[- ]?AUC|ROC_AUC|AUC)\s*[:=|]\s*([01]\.\d{3,6})")
TABLE_RE = re.compile(r"\|\s*([^|\n]{1,160}?)\s*\|\s*([01]\.\d{3,6})\s*\|")
TEXT_EXT={".md",".txt",".json",".csv",".py",".yml",".yaml",".rst",".toml"}
SKIP={".git","node_modules","__pycache__",".venv","venv"}

def scan(root: Path):
    rows=[]
    for p in root.rglob("*"):
        if not p.is_file() or any(part in SKIP for part in p.parts) or p.suffix.lower() not in TEXT_EXT or p.stat().st_size>2_000_000:
            continue
        try:text=p.read_text(errors="ignore")
        except OSError:continue
        for i,line in enumerate(text.splitlines(),1):
            matches=[]
            matches += [(m.group(1),line.strip()) for m in AUC_RE.finditer(line)]
            matches += [(m.group(2),f"{m.group(1).strip()} | {line.strip()}") for m in TABLE_RE.finditer(line)]
            for raw,ctx in matches:
                auc=float(raw)
                if 0<auc<0.5:
                    rows.append({"file":str(p.relative_to(root)),"line":i,"auc":auc,"reflected_auc":1-auc,"context":ctx[:500]})
    return rows

def family_key(r):
    f=r["file"]
    # Collapse result files into an experiment family.
    f=re.sub(r"_202\d{8}","",f)
    f=re.sub(r"_V\d+","",f)
    f=re.sub(r"_COURT_V\d+","",f,flags=re.I)
    if "HYDRA_HEAD_CONDITIONAL_ABLATION" in f or "HYDRA_CONDITIONAL_ABLATION" in f:
        family="HYDRA_CONDITIONAL_ABLATION"
    elif "TIAMAT_HISTORICAL_VARIABLE_TEST" in f:
        family="TIAMAT_HISTORICAL_VARIABLE_TEST"
    else:
        family=f
    ctx=re.sub(r"\s+"," ",r["context"])
    # Strip numeric fields so adjacent metrics do not create fake independence.
    ctx=re.sub(r"\b0\.\d{3,6}\b","<NUM>",ctx)
    return family,ctx[:180]

def main(root:Path,out:Path):
    rows=scan(root)
    for r in rows:r["family"],r["provenance_key"]=family_key(r)
    groups={}
    for r in rows:groups.setdefault(r["provenance_key"],[]).append(r)
    unique=[]
    for k,items in groups.items():
        unique.append({
            "provenance_key":k,
            "family":items[0]["family"],
            "n_observations":len(items),
            "min_auc":min(x["auc"] for x in items),
            "max_auc":max(x["auc"] for x in items),
            "max_reflected_auc":max(x["reflected_auc"] for x in items),
            "near_perfect":any(0.04<=x["auc"]<=0.053 and x["reflected_auc"]>=0.947 for x in items),
            "sources":[{"file":x["file"],"line":x["line"],"auc":x["auc"]} for x in items],
        })
    unique.sort(key=lambda x:(-x["max_reflected_auc"],x["family"],x["provenance_key"]))
    payload={
        "experiment":"OMEGA_PRELIMINARY_AUC_INVERSION_PROVENANCE_SCREEN_V1",
        "status":"archaeological_screen_only",
        "raw_sub_0_50":len(rows),
        "provenance_groups":len(unique),
        "near_perfect_groups":sum(x["near_perfect"] for x in unique),
        "raw_near_perfect":sum(0.04<=x["auc"]<=0.053 and x["reflected_auc"]>=0.947 for x in rows),
        "groups":unique,
        "interpretation":"Repeated observations from one result family are not counted as independent variables. A group is only an inversion candidate, not a confirmed inversion, until the underlying computation is re-run with explicit sign controls."
    }
    out.write_text(json.dumps(payload,indent=2));print(json.dumps(payload,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();main(a.root,a.out)
