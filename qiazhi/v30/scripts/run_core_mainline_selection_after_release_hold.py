#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.core_mainline_selection_after_release_hold import run_core_mainline_selection_after_release_hold


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MCR3 core mainline selection after REL-S4 release hold.")
    parser.add_argument("--reading-id", default="mcr3-core-mainline-selection")
    parser.add_argument("--rerun-stage-a-review", action="store_true")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--shard-id", type=int, default=7)
    parser.add_argument("--shard-limit", type=int, default=16)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_core_mainline_selection_after_release_hold(
        reading_id=args.reading_id,
        rerun_stage_a_review=args.rerun_stage_a_review,
        sample_limit=args.sample_limit,
        shard_id=args.shard_id,
        shard_limit=args.shard_limit,
    )
    decision = result["decision"]
    next_task = result["next_mainline_selection"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- selected: {next_task['task_id']} {next_task['title']}")
        print(f"- track: {next_task['selected_track']}")
        print(f"- blockers: {','.join(decision['blockers']) or 'none'}")
        print(f"- external_release_allowed: {decision['external_release_allowed']}")
        print(f"- full_pytest_run_now: {next_task.get('full_pytest_run_now', False)}")
    return 0 if decision["core_mainline_selection_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
