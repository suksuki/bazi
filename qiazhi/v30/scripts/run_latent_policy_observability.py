#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_latent_policy_observability_readiness


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 latent policy observability readiness.")
    parser.add_argument("--reading-id", default="hf-r25-latent-policy-observability")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_latent_policy_observability_readiness(reading_id=args.reading_id)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- passed: {decision['passed_check_count']}/{decision['check_count']}")
        print(f"- failed: {','.join(decision['failed_check_ids']) or 'none'}")
        print(f"- next: {result['next_mainline_selection']['task_id']}")
    return 0 if result["decision"]["readiness_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
