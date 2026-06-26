from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.central_brain_session_replay import run_central_brain_session_replay


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 central brain long-session replay gate.")
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    result = run_central_brain_session_replay()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        checks = result["replay_checks"]
        passed = sum(1 for row in checks if row["passed"])
        print(
            f"{result['version']}: "
            f"{'passed' if decision['central_brain_session_replay_ready'] else 'failed'} "
            f"({passed}/{len(checks)}) "
            f"{decision['decision_status']}"
        )
        for row in checks:
            if not row["passed"]:
                print(f"- {row['check_id']}: {row['expected']}")
    return 0 if result["decision"]["central_brain_session_replay_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
