#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.stage_a_evidence_review import run_stage_a_evidence_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run REL-S4 Stage-A evidence review and external-release hold.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--shard-id", type=int, default=7)
    parser.add_argument("--shard-limit", type=int, default=16)
    parser.add_argument("--reading-id", default="rel-s4-stage-a-evidence-review")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_stage_a_evidence_review(
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
        print(f"- reviewed_gate_ids: {','.join(decision['reviewed_gate_ids']) or 'none'}")
        print(f"- blockers: {','.join(decision['blockers']) or 'none'}")
        print(f"- external_release_allowed: {decision['external_release_allowed']}")
        print(f"- return_to_core_module_mainline: {decision['return_to_core_module_mainline']}")
        print(f"- next: {result['next_mainline_selection']['task_id']} {result['next_mainline_selection']['title']}")
    return 0 if decision["stage_a_evidence_review_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
