"""Preliminary historical AUC inversion screen.

Only values explicitly identified as AUC/ROC-AUC are eligible. Markdown table
rows are parsed only when the table header establishes an AUC/ROC-AUC column.
This is an archaeological screen, not a promotion test.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

AUC_RE = re.compile(r"(?i)(?:ROC[- ]?AUC|ROC_AUC|AUC)\s*[:=]\s*([01]\.\d{3,6})")
HEADER_TOKEN_RE = re.compile(r"(?i)(?:ROC[- ]?AUC|ROC_AUC|\bAUC\b)")
TEXT_EXT = {".md", ".txt", ".json", ".csv", ".py", ".yml", ".yaml", ".rst", ".toml"}
SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file() or any(part in SKIP for part in p.parts):
            continue
        if p.suffix.lower() in TEXT_EXT and p.stat().st_size <= 2_000_000:
            yield p


def table_auc_index(header: str):
    if "|" not in header:
        return None
    cells = [c.strip() for c in header.strip().strip("|").split("|")]
    for idx, cell in enumerate(cells):
        if HEADER_TOKEN_RE.search(cell):
            return idx
    return None


def numeric(cell: str):
    m = re.fullmatch(r"\s*([01]\.\d{3,6})\s*", cell)
    return float(m.group(1)) if m else None


def main(root: Path, out: Path):
    rows = []
    seen = set()
    for p in files(root):
        try:
            lines = p.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        auc_col = None
        for i, line in enumerate(lines, 1):
            explicit = [(m.group(1), line.strip()) for m in AUC_RE.finditer(line)]
            for raw, context in explicit:
                auc = float(raw)
                if 0.0 < auc < 1.0 and auc < 0.5:
                    key = (str(p), i, raw, "explicit")
                    if key not in seen:
                        seen.add(key)
                        rows.append({
                            "file": str(p.relative_to(root)), "line": i,
                            "auc": auc, "reflected_auc": round(1.0 - auc, 6),
                            "inversion_gain": round((1.0 - auc) - 0.5, 6),
                            "near_perfect_inversion": 0.04 <= auc <= 0.053 and (1.0 - auc) >= 0.947,
                            "source_mode": "explicit_label", "context": context[:500],
                        })
            if "|" in line:
                idx = table_auc_index(line)
                if idx is not None:
                    auc_col = idx
                    continue
                if auc_col is not None:
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    if auc_col < len(cells):
                        auc = numeric(cells[auc_col])
                        if auc is not None and auc < 0.5:
                            context = line.strip()
                            key = (str(p), i, cells[auc_col], "table_auc")
                            if key not in seen:
                                seen.add(key)
                                rows.append({
                                    "file": str(p.relative_to(root)), "line": i,
                                    "auc": auc, "reflected_auc": round(1.0 - auc, 6),
                                    "inversion_gain": round((1.0 - auc) - 0.5, 6),
                                    "near_perfect_inversion": 0.04 <= auc <= 0.053 and (1.0 - auc) >= 0.947,
                                    "source_mode": "table_auc_column", "context": context[:500],
                                })
                elif re.fullmatch(r"\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)+\|?\s*", line):
                    continue
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
        "experiment": "OMEGA_PRELIMINARY_AUC_INVERSION_SCREEN_V2",
        "status": "archaeological_screen_only",
        "definition": "Only explicitly labeled AUC/ROC-AUC values are screened; generic numeric table cells are never treated as AUC.",
        "counts": counts, "rows": rows,
    }
    out.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("root", type=Path); ap.add_argument("--out", type=Path, required=True); args = ap.parse_args(); main(args.root, args.out)
