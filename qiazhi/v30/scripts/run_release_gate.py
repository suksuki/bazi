from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_release_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 composed release gate.")
    parser.add_argument("--mode", choices=("quick", "standard"), default="quick")
    parser.add_argument("--include-shard", action="store_true")
    parser.add_argument("--shard-id", type=int, default=0)
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--shard-limit", type=int, default=16)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_release_gate(
        mode=args.mode,
        include_shard=args.include_shard,
        shard_id=args.shard_id,
        sample_limit=args.sample_limit,
        shard_limit=args.shard_limit,
    )
    if args.json:
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        print(
            f"{result.run_id}: {result.promotion_signal} "
            f"mode={result.mode} checks={len(result.checks)}"
        )
        for check in result.checks:
            print(f"- {check.check_id}: {check.status}")
            for failure in check.failures:
                print(f"  - {failure}")
    return 0 if result.promotion_signal == "eligible" else 1


if __name__ == "__main__":
    raise SystemExit(main())
