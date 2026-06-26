from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.ui_core_reading_product_acceptance import run_ui_core_reading_product_acceptance


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 UI-R1 core Bazi reading product acceptance audit.")
    parser.add_argument("--reading-id", default="ui-review-20260613-001")
    parser.add_argument("--json", action="store_true", help="Print full JSON artifact.")
    args = parser.parse_args()

    result = run_ui_core_reading_product_acceptance(reading_id=args.reading_id)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    decision = result["decision"]
    print(f"{result['version']}: {decision['decision_status']}")
    print(f"product_ready={decision['product_reading_ready']} audit_ready={decision['audit_ready']}")
    print(f"passed={decision['passed_check_count']}/{decision['check_count']}")
    if decision["failed_check_ids"]:
        print("failed=" + ", ".join(decision["failed_check_ids"]))
    next_task = result["next_mainline_selection"]
    print(f"next={next_task['task_id']} {next_task['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
