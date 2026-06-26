from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.post_seal_status_review import build_post_seal_status_review
from v30.validation.release_boundary_finalization import build_release_boundary_finalization
from v30.validation.release_candidate_gate_review import build_release_candidate_gate_review
from v30.validation.release_gate import run_release_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 R12 release-boundary finalization review.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--shard-id", type=int, default=7)
    parser.add_argument("--shard-limit", type=int, default=16)
    parser.add_argument("--full-pytest-status", choices=("", "passed", "failed"), default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    gate = run_release_gate(
        mode="standard",
        sample_limit=args.sample_limit,
        shard_id=args.shard_id,
        shard_limit=args.shard_limit,
    )
    gate_review = build_release_candidate_gate_review(release_gate_result=gate.model_dump(mode="json"))
    full_pytest_result = {"status": args.full_pytest_status} if args.full_pytest_status else {}
    result = build_release_boundary_finalization(
        post_seal_status_review=build_post_seal_status_review(),
        release_candidate_gate_review=gate_review,
        full_pytest_result=full_pytest_result,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"internal_release_candidate_finalized={decision['internal_release_candidate_finalized']}")
        print(f"external_release_ready={decision['external_release_ready']}")
        print(f"next={result['next_mainline_selection']['task_id']} {result['next_mainline_selection']['title']}")
        if decision["blockers"]:
            print("blockers=" + ",".join(decision["blockers"]))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
