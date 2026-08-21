#!/usr/bin/env python3
"""Minimal repository execution probe.

Purpose: establish a deterministic, dependency-free CI execution surface before
adding larger TIAMAT/BentAxis harnesses. Fails closed on invariant violations.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> dict[str, Any]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "returncode": p.returncode,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    }


def main() -> int:
    rel = sorted(
        str(p.relative_to(ROOT))
        for p in ROOT.rglob("*")
        if p.is_file() and ".git" not in p.parts
    )
    digest = hashlib.sha256("\n".join(rel).encode()).hexdigest()

    result: dict[str, Any] = {
        "probe": "omega-execution-probe-v1",
        "python": sys.version.split()[0],
        "cwd": str(ROOT),
        "file_count": len(rel),
        "inventory_sha256": digest,
        "git_status": run(["git", "status", "--short"]),
    }

    required = [".github", "tests", "tools"]
    missing = [x for x in required if not (ROOT / x).exists()]
    result["required_paths"] = {x: x not in missing for x in required}

    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
