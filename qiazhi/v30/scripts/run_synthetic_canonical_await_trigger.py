from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_synthetic_canonical_await_trigger


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SCAL-S3-WAIT synthetic canonical trigger status.")
    parser.add_argument(
        "--trigger",
        action="append",
        default=[],
        help="Known trigger id: rbd_change, m3_change, m5_change, iq_change, release_boundary.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_synthetic_canonical_await_trigger(active_triggers=args.trigger)
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            "v30.synthetic_canonical_await_trigger.v1: "
            f"{'passed' if decision['synthetic_canonical_await_trigger_ready'] else 'blocked'} "
            f"({decision['passed_check_count']}/{decision['check_count']}) "
            f"{decision['decision_status']} "
            f"waiting={decision['waiting_for_synthetic_canonical_trigger']} "
            f"run_required={decision['synthetic_canonical_gate_run_required']} "
            f"next={result['next_mainline_selection']['next_task']}"
        )
    return 0 if decision["synthetic_canonical_await_trigger_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
