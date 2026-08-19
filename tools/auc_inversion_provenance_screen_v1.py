"""Provenance-deduplicated second pass over low-AUC archaeology.

Only explicitly identified AUC/ROC-AUC values are eligible. Markdown tables
are parsed only when the header establishes an AUC/ROC-AUC column.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

AUC_RE = re.compile(r"(?i)(?:ROC[- ]?AUC|ROC_AUC|AUC)\s*[:=]\s*([01]\.\d{3,6})")
HEADER_TOKEN_RE = re.compile(r"(?i)(?:ROC[- ]?AUC|ROC_AUC|\bAUC\b)")
TEXT_EXT={".md",".txt",".json",".csv",".py",".yml",".yaml",".rst",".toml"}
SKIP={".git","node_modules","__pycache__",".venv","venv"}

def table_auc_index(header:str):
    if "|" not in header: return None
    cells=[c.strip() for c in header.strip().strip("|").split("|")]
    for idx,cell in enumerate(cells):
        if HEADER_TOKEN_RE.search(cell): return idx
    return None

def numeric(cell:str):
    m=re.fullmatch(r"\s*([01]\.\d{3,6})\s*",cell)
    return float(m.group(1)) if m else None

def scan(root:Path):
    rows=[]
    for p in root.rglob("*"):
        if not p.is_file() or any(part in SKIP for part in p.parts) or p.suffix.lower() not in TEXT_EXT or p.stat().st_size>2_000_000: continue
        try: lines=p.read_text(errors="ignore").splitlines()
        except OSError: continue
        auc_col=None
        for i,line in enumerate(lines,1):
            for m in AUC_RE.finditer(line):
                auc=float(m.group(1))
                if 0<auc<0.5:
                    rows.append({"file":str(p.relative_to(root)),"line":i,"auc":auc,"reflected_auc":1-auc,"context":line.strip()[:500],"source_mode":"explicit_label"})
            if "|" in line:
                idx=table_auc_index(line)
                if idx is not None:
                    auc_col=idx; continue
                if auc_col is not None:
                    cells=[c.strip() for c in line.strip().strip("|").split("|")]
                    if auc_col<len(cells):
                        auc=numeric(cells[auc_col])
                        if auc is not None and auc<0.5:
                            rows.append({"file":str(p.relative_to(root)),"line":i,"auc":auc,"reflected_auc":1-auc,"context":line.strip()[:500],"source_mode":"table_auc_column"})
    return rows

def family_key(r):
    f=r["file"]
    f=re.sub(r"_202\d{8}","",f); f=re.sub(r"_V\d+","",f); f=re.sub(r"_COURT_V\d+","",f,flags=re.I)
    if "HYDRA_HEAD_CONDITIONAL_ABLATION" in f or "HYDRA_CONDITIONAL_ABLATION" in f: family="HYDRA_CONDITIONAL_ABLATION"
    elif "TIAMAT_HISTORICAL_VARIABLE_TEST" in f: family="TIAMAT_HISTORICAL_VARIABLE_TEST"
    else: family=f
    ctx=re.sub(r"\s+"," ",r["context"])
    ctx=re.sub(r"\b0\.\d{3,6}\b","<NUM>",ctx)
    return family,ctx[:180]

def main(root:Path,out:Path):
    rows=scan(root)
    for r in rows:r["family"],r["provenance_key"]=family_key(r)
    groups={}
    for r in rows:groups.setdefault(r["provenance_key"],[]).append(r)
    unique=[]
    for k,items in groups.items():
        unique.append({"provenance_key":k,"family":items[0]["family"],"n_observations":len(items),"min_auc":min(x["auc"] for x in items),"max_auc":max(x["auc"] for x in items),"max_reflected_auc":max(x["reflected_auc"] for x in items),"near_perfect":any(0.04<=x["auc"]<=0.053 and x["reflected_auc"]>=0.947 for x in items),"sources":[{"file":x["file"],"line":x["line"],"auc":x["auc"],"source_mode":x["source_mode"]} for x in items]})
    unique.sort(key=lambda x:(-x["max_reflected_auc"],x["family"],x["provenance_key"]))
    payload={"experiment":"OMEGA_PRELIMINARY_AUC_INVERSION_PROVENANCE_SCREEN_V2","status":"archaeological_screen_only","raw_sub_0_50":len(rows),"provenance_groups":len(unique),"near_perfect_groups":sum(x["near_perfect"] for x in unique),"raw_near_perfect":sum(0.04<=x["auc"]<=0.053 and x["reflected_auc"]>=0.947 for x in rows),"groups":unique,"interpretation":"Only explicitly labeled AUC/ROC-AUC values are screened; generic table cells such as Brier, PR-AUC, or log loss are never treated as AUC. Repeated observations are grouped by result provenance. Groups remain candidates until computation is rerun with explicit sign controls."}
    out.write_text(json.dumps(payload,indent=2)); print(json.dumps(payload,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.root,a.out)
