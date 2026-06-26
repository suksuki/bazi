from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_518k_validation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 518K validation tiers.")
    parser.add_argument("--mode", choices=("sample", "shard", "full"), default="sample")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--shard-id", type=int, default=None)
    parser.add_argument("--source-path", default=None)
    parser.add_argument("--confirm-full", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_518k_validation(
        mode=args.mode,
        limit=args.limit,
        shard_id=args.shard_id,
        source_path=args.source_path,
        confirm_full=args.confirm_full,
    )
    if args.json:
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        print(
            f"{result.run_id}: {result.promotion_signal} "
            f"mode={result.mode} cases={result.case_count} shards={','.join(map(str, result.shard_ids))}"
        )
        if result.artifact_uri:
            print(f"- artifact: {result.artifact_uri}")
        if result.index_uri:
            print(f"- index: {result.index_uri}")
        if result.artifact_record_id:
            print(f"- artifact record: {result.artifact_record_id} ({result.artifact_search_backend})")
    return 0 if result.promotion_signal == "eligible" else 1


if __name__ == "__main__":
    raise SystemExit(main())
