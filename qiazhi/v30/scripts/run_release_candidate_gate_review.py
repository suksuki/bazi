from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.release_candidate_gate_review import build_release_candidate_gate_review
from v30.validation.release_gate import run_release_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 R11 standard release-candidate gate review.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--shard-id", type=int, default=7)
    parser.add_argument("--shard-limit", type=int, default=16)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    gate = run_release_gate(
        mode="standard",
        sample_limit=args.sample_limit,
        shard_id=args.shard_id,
        shard_limit=args.shard_limit,
    )
    result = build_release_candidate_gate_review(release_gate_result=gate.model_dump(mode="json"))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"release_boundary_ready={decision['release_boundary_ready']}")
        print(f"next={result['next_mainline_selection']['task_id']} {result['next_mainline_selection']['title']}")
        if decision["blockers"]:
            print("blockers=" + ",".join(decision["blockers"]))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
