from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_bazi_backend_api_journey_acceptance


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 Bazi backend API journey acceptance.")
    parser.add_argument("--reading-id", default="ir2-bazi-backend-api-journey")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_bazi_backend_api_journey_acceptance(reading_id=args.reading_id)
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            "v30.bazi_backend_api_journey_acceptance.v1: "
            f"{'passed' if decision['api_journey_ready'] else 'failed'} "
            f"({decision['passed_check_count']}/{decision['check_count']}) "
            f"{decision['decision_status']}"
        )
    return 0 if decision["api_journey_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
