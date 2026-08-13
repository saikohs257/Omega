"""Replay recovered TIAMAT machinery against the canonical Layer-1 spine.

Usage:
    python experiments/first_poke/replay_historical_layer1.py PATH_TO_CSV

The historical CSV is intentionally supplied externally: the repository does
not manufacture or silently replace the historical primitive values.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from tiamat.historical_hf8 import build_thehinge, rebuild_entry_path, recovered_active_mask


def main(path: str) -> int:
    csv = Path(path)
    frame = pd.read_csv(csv, parse_dates=["open_time"]).set_index("open_time")
    active = recovered_active_mask(frame)
    entry = rebuild_entry_path(frame, active)
    daily = pd.DataFrame(index=pd.date_range(frame.index.min().normalize(), frame.index.max().normalize(), freq="D"))
    hinge = build_thehinge(frame, daily, active, entry)

    entry_match = entry.eq(frame["entry_path"])
    episode_match = hinge["episode_type"].eq(frame["episode_type"])
    age_mask = frame["episode_age_h"].notna() & hinge["run_age_h"].notna()
    age_match = hinge.loc[age_mask, "run_age_h"].eq(frame.loc[age_mask, "episode_age_h"])

    print(f"rows={len(frame)}")
    print(f"active={int(active.sum())}")
    print(f"starts={int((active & ~active.shift(fill_value=False)).sum())}")
    print(f"entry_mismatches={int((~entry_match).sum())}")
    print(f"episode_mismatches={int((~episode_match).sum())}")
    print(f"age_overlap={int(age_mask.sum())}")
    print(f"age_mismatches={int((~age_match).sum())}")

    # Historical invariants already recovered exactly.
    if not entry_match.all():
        return 1
    if not age_match.all():
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
