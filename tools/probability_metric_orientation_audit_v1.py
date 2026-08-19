"""Probability metric orientation audit.

Searches tracked result artifacts for explicit Brier/log-loss metrics and
checks whether their reported direction is consistent with the lower-is-better
contract. It also provides an executable synthetic control proving that
complementing probabilities (1-p) does not create a universal metric reflection
for losses.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

B = re.compile(r"(?i)\bbrier\b[^\n|]*?[:=|]\s*([0-9]+(?:\.[0-9]+)?)")
L = re.compile(r"(?i)\blog(?:\s|-)?loss\b[^\n|]*?[:=|]\s*([0-9]+(?:\.[0-9]+)?)")

def files(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".md",".txt",".json",".csv"} and p.stat().st_size <= 2_000_000 and ".git" not in p.parts:
            yield p

def synthetic_control():
    # For binary y, compare correct p with complemented 1-p.
    y = [0, 0, 1, 1]
    p = [0.1, 0.2, 0.8, 0.9]
    pc = [1-x for x in p]
    def brier(q): return sum((a-b)**2 for a,b in zip(y,q))/len(y)
    def ll(q):
        import math
        return -sum(a*math.log(b)+(1-a)*math.log(1-b) for a,b in zip(y,q))/len(y)
    return {"brier_p": brier(p), "brier_1_minus_p": brier(pc), "logloss_p": ll(p), "logloss_1_minus_p": ll(pc)}

def main(root: Path, out: Path):
    rows=[]
    for p in files(root):
        try:text=p.read_text(errors='ignore')
        except OSError: continue
        for i,line in enumerate(text.splitlines(),1):
            for metric,rx in (("brier",B),("logloss",L)):
                for m in rx.finditer(line):
                    rows.append({"file":str(p.relative_to(root)),"line":i,"metric":metric,"value":float(m.group(1)),"context":line.strip()[:500]})
    payload={
        "experiment":"OMEGA_PROBABILITY_METRIC_ORIENTATION_AUDIT_V1",
        "status":"archaeological_screen_only",
        "contract":{"brier":"lower_is_better","logloss":"lower_is_better"},
        "counts":{"brier":sum(r['metric']=='brier' for r in rows),"logloss":sum(r['metric']=='logloss' for r in rows)},
        "rows":rows,
        "synthetic_control":synthetic_control(),
        "interpretation":"There is no universal 1-metric reflection for Brier or log loss. Orientation errors must be tested by prediction ordering, paired probability complements, and stated optimization direction.",
    }
    out.write_text(json.dumps(payload,indent=2)); print(json.dumps(payload,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main(a.root,a.out)
