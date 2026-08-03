from __future__ import annotations

import pathlib
import subprocess
import sys


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent
    cmd = [sys.executable, "-m", "pytest", str(root / "tests")]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
