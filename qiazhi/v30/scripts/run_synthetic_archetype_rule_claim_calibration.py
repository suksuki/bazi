#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.synthetic_archetype_rule_claim_calibration import (
    run_synthetic_archetype_rule_claim_calibration,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SYN-CAL1 synthetic archetype rule-claim calibration.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_synthetic_archetype_rule_claim_calibration()
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- cases: {decision['passed_case_count']}/{decision['case_count']}")
        print(f"- failed_case_ids: {','.join(decision['failed_case_ids']) or 'none'}")
        print(f"- queue_items: {len(result['calibration_queue'])}")
        print(f"- external_release_allowed: {decision['external_release_allowed']}")
        print(f"- next: {result['next_mainline_selection']['task_id']} {result['next_mainline_selection']['title']}")
    return 0 if decision["synthetic_archetype_calibration_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
