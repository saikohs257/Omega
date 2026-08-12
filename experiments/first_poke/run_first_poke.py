from __future__ import annotations

import json
import os
from pathlib import Path

from tiamat.engine import TiamatEngine
from tiamat.state import TiamatState


def run_case(engine: TiamatEngine, name: str, evidence: dict[str, float]):
    initial = TiamatState()
    diagnosis = engine.diagnose(initial, evidence)
    return {"name": name, "initial": initial.to_dict(), "evidence": evidence, "diagnosis": diagnosis}


def main() -> None:
    engine = TiamatEngine()
    baseline = run_case(engine, "baseline", {"B": 0.0, "V": 0.0, "D": 0.0})
    poke = run_case(engine, "poke_v_1e-9", {"B": 0.0, "V": 1e-9, "D": 0.0})
    result = {
        "experiment": "omega-first-poke-v1",
        "commit": os.environ.get("GITHUB_SHA", "unknown"),
        "baseline": baseline,
        "poke": poke,
        "delta": {
            "mode": [baseline["diagnosis"]["state"]["mode"], poke["diagnosis"]["state"]["mode"]],
            "B": [baseline["diagnosis"]["state"]["B"], poke["diagnosis"]["state"]["B"]],
            "V": [baseline["diagnosis"]["state"]["V"], poke["diagnosis"]["state"]["V"]],
            "D": [baseline["diagnosis"]["state"]["D"], poke["diagnosis"]["state"]["D"]],
            "pressure": [baseline["diagnosis"]["observables"]["pressure"], poke["diagnosis"]["observables"]["pressure"]],
            "hazard_score": [baseline["diagnosis"]["observables"]["hazard_score"], poke["diagnosis"]["observables"]["hazard_score"]],
        },
    }
    out = Path("experiments/first_poke/first_poke_result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
