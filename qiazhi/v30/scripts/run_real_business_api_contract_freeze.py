from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.real_business_api_contract_freeze import run_real_business_api_contract_freeze


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 business reading API contract freeze.")
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    result = run_real_business_api_contract_freeze()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        summary = result["freeze_summary"]
        print(
            f"{result['version']}: "
            f"{'passed' if decision['api_contract_freeze_ready'] else 'failed'} "
            f"({summary['passed_gate_count']}/{summary['gate_count']}) "
            f"{decision['decision_status']}"
        )
        for gate in result["business_acceptance_gates"]:
            if not gate["passed"]:
                print(f"- {gate['gate_id']}: {gate['decision_status']}")
    return 0 if result["decision"]["api_contract_freeze_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
