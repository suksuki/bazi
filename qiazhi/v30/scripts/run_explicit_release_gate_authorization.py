#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.explicit_release_gate_authorization import run_explicit_release_gate_authorization


def main() -> int:
    parser = argparse.ArgumentParser(description="Run REL-S2 explicit release gate authorization decision.")
    parser.add_argument("--authorization-decision", choices=("authorize_stage_a", "defer_all"), default="authorize_stage_a")
    parser.add_argument("--reading-id", default="rel-s2-explicit-release-gate-authorization")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_explicit_release_gate_authorization(
        authorization_decision=args.authorization_decision,
        reading_id=args.reading_id,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- authorized_gate_ids: {','.join(decision['authorized_gate_ids']) or 'none'}")
        print(f"- deferred_gate_ids: {','.join(decision['deferred_gate_ids']) or 'none'}")
        print(f"- runs_triggered: {decision['runs_triggered']}")
        print(f"- external_release_allowed: {decision['external_release_allowed']}")
        print(f"- next: {result['next_mainline_selection']['task_id']} {result['next_mainline_selection']['title']}")
    return 0 if decision["authorization_recorded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
