from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_customer_surface_bazi_context_reconciliation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 MCR2 customer surface and BaziContext reconciliation.")
    parser.add_argument("--reading-id", default="mcr2-customer-surface-bazi-context")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_customer_surface_bazi_context_reconciliation(reading_id=args.reading_id)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    decision = result["decision"]
    next_task = result["next_mainline_selection"]
    print(
        f"{result['version']}: {decision['decision_status']} "
        f"({decision['passed_count']}/{decision['check_count']})"
    )
    print(
        "next="
        f"{next_task['task_id']} full_pytest={next_task['full_pytest_run_now']} "
        f"synthetic_all={next_task['synthetic_all_run_now']} full_518k={next_task['full_518k_run_now']}"
    )
    return 0 if decision["customer_surface_bazi_context_reconciled"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
