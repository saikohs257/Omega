"""Preliminary historical AUC inversion screen.

Scans tracked text artifacts for explicit AUC/ROC-AUC values, computes the
mathematical reflected AUC (1-AUC), and ranks sub-0.5 observations by inversion
plausibility. This is an archaeological screen, not a promotion test.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

AUC_RE = re.compile(r"(?i)(?:ROC[- ]?AUC|ROC_AUC|AUC)\s*[:=|]\s*([01]\.\d{3,6})")
TABLE_RE = re.compile(r"\|\s*([^|\n]{1,120}?)\s*\|\s*([01]\.\d{3,6})\s*\|")

TEXT_EXT = {".md", ".txt", ".json", ".csv", ".py", ".yml", ".yaml", ".rst", ".toml"}
SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file() or any(part in SKIP for part in p.parts):
            continue
        if p.suffix.lower() in TEXT_EXT and p.stat().st_size <= 2_000_000:
            yield p


def main(root: Path, out: Path):
    rows = []
    seen = set()
    for p in files(root):
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            candidates = []
            for m in AUC_RE.finditer(line):
                candidates.append((m.group(1), line.strip()))
            for m in TABLE_RE.finditer(line):
                candidates.append((m.group(2), f"{m.group(1).strip()} | {line.strip()}"))
            for raw, context in candidates:
                auc = float(raw)
                if not 0.0 < auc < 1.0:
                    continue
                key = (str(p), i, raw, context)
                if key in seen:
                    continue
                seen.add(key)
                if auc < 0.5:
                    rows.append({
                        "file": str(p.relative_to(root)),
                        "line": i,
                        "auc": auc,
                        "reflected_auc": round(1.0 - auc, 6),
                        "inversion_gain": round((1.0 - auc) - 0.5, 6),
                        "near_perfect_inversion": 0.04 <= auc <= 0.053 and (1.0 - auc) >= 0.947,
                        "context": context[:500],
                    })

    rows.sort(key=lambda r: (-r["reflected_auc"], r["file"], r["line"]))
    counts = {
        "sub_0_50": len(rows),
        "0_40_to_0_53": sum(0.40 <= r["auc"] <= 0.53 for r in rows),
        "0_04_to_0_053": sum(0.04 <= r["auc"] <= 0.053 for r in rows),
        "reflected_gt_0_55": sum(r["reflected_auc"] > 0.55 for r in rows),
        "reflected_gt_0_70": sum(r["reflected_auc"] > 0.70 for r in rows),
        "reflected_gt_0_90": sum(r["reflected_auc"] > 0.90 for r in rows),
        "near_perfect_inversion": sum(r["near_perfect_inversion"] for r in rows),
    }
    payload = {
        "experiment": "OMEGA_PRELIMINARY_AUC_INVERSION_SCREEN_V1",
        "status": "archaeological_screen_only",
        "definition": "For any observed AUC a, polarity reflection is 1-a; this does not establish that the underlying variable is truly inverted.",
        "counts": counts,
        "rows": rows,
    }
    out.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.root, args.out)
