from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_brain_training_synthetic_closeout


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 brain/training/synthetic support-system closeout.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--shard-id", type=int, default=7)
    parser.add_argument("--shard-limit", type=int, default=16)
    parser.add_argument("--artifact-dir", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_brain_training_synthetic_closeout(
        sample_limit=args.sample_limit,
        shard_id=args.shard_id,
        shard_limit=args.shard_limit,
        artifact_dir=args.artifact_dir,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            "v30.brain_training_synthetic_closeout.v1: "
            f"{'passed' if decision['closeout_ready'] else 'failed'} "
            f"({decision['passed_check_count']}/{decision['check_count']}) "
            f"{decision['decision_status']}"
        )
    return 0 if decision["closeout_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
