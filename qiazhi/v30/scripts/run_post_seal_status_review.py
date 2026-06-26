from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import build_post_seal_status_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 post-seal status review.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = build_post_seal_status_review()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        next_task = result["next_mainline_selection"]
        print(f"{result['version']}: {result['status']}")
        print(
            f"core_phase_sealed={result['core_module_summary']['phase_sealed_count']}/"
            f"{result['core_module_summary']['module_count']}"
        )
        print(f"next={next_task['task_id']} {next_task['title']}")
    return 0 if result["status"] == "ready_for_next_mainline" else 1


if __name__ == "__main__":
    raise SystemExit(main())
