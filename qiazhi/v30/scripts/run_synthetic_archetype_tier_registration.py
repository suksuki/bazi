#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.synthetic_archetype_tier_registration import run_synthetic_archetype_tier_registration


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SYN-CAL2 synthetic archetype tier registration.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_synthetic_archetype_tier_registration()
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- passed: {decision['passed_check_count']}/{decision['check_count']}")
        print(f"- queue_items: {decision['calibration_queue_item_count']}")
        print(f"- failed_check_ids: {','.join(decision['failed_check_ids']) or 'none'}")
        print(f"- external_release_allowed: {decision['external_release_allowed']}")
        print(f"- next: {result['next_mainline_selection']['task_id']} {result['next_mainline_selection']['title']}")
    return 0 if decision["synthetic_archetype_tier_registration_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
