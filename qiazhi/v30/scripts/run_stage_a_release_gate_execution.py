#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.stage_a_release_gate_execution import run_stage_a_release_gate_execution


def main() -> int:
    parser = argparse.ArgumentParser(description="Run REL-S3 Stage-A authorized release gates.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--shard-id", type=int, default=7)
    parser.add_argument("--shard-limit", type=int, default=16)
    parser.add_argument("--reading-id", default="rel-s3-stage-a-release-gates")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_stage_a_release_gate_execution(
        sample_limit=args.sample_limit,
        shard_id=args.shard_id,
        shard_limit=args.shard_limit,
        reading_id=args.reading_id,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- passed: {decision['passed_gate_count']}/{decision['gate_count']}")
        print(f"- failed_gate_ids: {','.join(decision['failed_gate_ids']) or 'none'}")
        for gate in result["gate_summaries"]:
            print(f"- {gate['gate_id']}: {gate['status']} executed={gate['executed']} passed={gate['passed']}")
        print(f"- external_release_allowed: {decision['external_release_allowed']}")
        print(f"- next: {result['next_mainline_selection']['task_id']} {result['next_mainline_selection']['title']}")
    return 0 if decision["stage_a_release_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
