"""OMEGA full-system deposit audit V1.

This is a repository archaeology/control tool, not a semantic proof engine.
It checks whether known subsystem terms and known source-artifact names have
some representation in the repository and emits a machine-readable manifest.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SUBSYSTEM_TERMS = {
    "omega": ["omega", "CONSTITUTION"],
    "bentaxis": ["bentaxis", "bent compress", "axiscontrol", "bax"],
    "tesseract": ["tesseract", "tesseract_circuit", "q4 board", "CircuitTrace"],
    "tiamat": ["tiamat", "LiveDeficit", "SimpleShock", "hazard_score", "RecoveryWeakness"],
    "senate": ["senate", "B1_entry", "flip_risk_24h", "family_gate"],
    "blackadder": ["blackadder", "decision friction", "path_tax", "spine confidence"],
    "seam": ["seam", "seam_watch_pressure", "seam_confidence"],
    "hinge": ["hinge"],
    "chug": ["chug"],
    "compass": ["compass"],
    "domino_utv": ["domino", "utv", "undertow", "turbulence", "vortex"],
    "pattern_shift_sift": ["patternshift", "patternsift"],
    "necronomicon": ["necronomicon", "failure memory"],
    "governance": ["authority", "promotion", "demotion", "no-steer", "negative authority"],
}

KNOWN_SOURCE_NAMES = [
    "BENTAXIS_CIRCUIT_PROOF_CORE_V1_20260628.tar.zst",
    "BENTAXIS_WHOLE_SYSTEM_HANDOFF_V1_20260614.tar.zst",
    "BENTAXIS_TIAMAT_TESSERACT_AMBITIOUS_PLAN_20260614.md",
    "BENT_COMPRESS_AXISCONTROL_HANDOFF_20260607.md",
    "TIAMAT_CIRCUIT_ZIP_A_SOURCE_VERDICT_V0_20260703.tar.gz",
    "TIAMAT_SOURCE_PACKAGE_20260403_2211.zip",
    "IMPLEMENTATION_AUDIT_AND_PATCH_NOTE.md",
    "decision_friction_seat_v0_patched.py",
    "senate_spine_v1.csv",
    "ORACLE_SUPER_HANDOFF_260331_v02.md",
    "FINAL_DELIVERABLE_SUMMARY_2026_04_10.md",
    "MASTER_STATE_2026_03_28.md",
    "DB_PROTOCOL_260330_v01.md",
    "QUICK_REFERENCE_ANTIPATTERNS_2026_04_02.md",
    "NAVIGATION_GUIDE_2026_04_02.md",
    "HF9_TIAMAT_V21_HIDDEN_PATTERN_AUDIT_V1_HANDOFF.md",
    "CLAUDE_HANDOFF_TESSERACT_Q4_V7_REVIEW_REQUEST_20260629.md",
    "COMPASS_ASSESSMENT_20260615-1.md",
    "02_THE_CHUG_PROJECT_HANDOFF_110_DETAIL_2026_03_26.md",
]


def walk_paths(root: Path) -> list[str]:
    out: list[str] = []
    for p in root.rglob("*"):
        if p.is_file():
            if any(part in {".git", ".venv", "venv", "node_modules", "__pycache__"} for part in p.parts):
                continue
            out.append(str(p.relative_to(root)))
    return sorted(out)


def text_hits(root: Path, terms: list[str], max_bytes: int = 1_500_000) -> list[str]:
    hits: list[str] = []
    pats = [re.compile(re.escape(t), re.I) for t in terms]
    for rel in walk_paths(root):
        p = root / rel
        try:
            if p.stat().st_size > max_bytes:
                continue
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        if any(pat.search(text) for pat in pats):
            hits.append(rel)
    return hits


def source_name_hits(paths: list[str], source_name: str) -> list[str]:
    needle = source_name.lower()
    base = source_name.rsplit("/", 1)[-1].lower()
    return [p for p in paths if base in p.lower() or needle in p.lower()]


def main(root: Path, out: Path) -> None:
    paths = walk_paths(root)
    subsystems = {}
    for subsystem, terms in SUBSYSTEM_TERMS.items():
        hits = text_hits(root, terms)
        subsystems[subsystem] = {
            "status": "PRESENT" if hits else "NOT_FOUND_BY_TERM_SCAN",
            "terms": terms,
            "hit_count": len(hits),
            "sample_paths": hits[:40],
        }

    sources = []
    for name in KNOWN_SOURCE_NAMES:
        hits = source_name_hits(paths, name)
        sources.append({
            "original_name": name,
            "status": "PRESENT" if hits else "MISSING_SOURCE_OR_RENAMED",
            "repository_hits": hits[:20],
        })

    payload = {
        "experiment": "OMEGA_FULL_SYSTEM_DEPOSIT_AUDIT_V1",
        "status": "repository_presence_scan_only",
        "repository_file_count": len(paths),
        "subsystems": subsystems,
        "known_sources": sources,
        "interpretation_rule": "Absence from a term scan is not proof of semantic absence; it is a queue for manual reconciliation.",
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.root, args.out)
