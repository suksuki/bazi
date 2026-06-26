from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_m3_source_backlog_review_surface


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 M3-G5 source backlog admin review surface.")
    parser.add_argument("--source-family-id", default="")
    parser.add_argument("--priority", default="")
    parser.add_argument("--queue-state", default="")
    parser.add_argument("--review-status", default="")
    parser.add_argument("--target-domain", default="")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--write-db", action="store_true")
    parser.add_argument("--artifact-dir", default=".runtime/validation/m3")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_m3_source_backlog_review_surface(
        source_family_id=args.source_family_id,
        priority=args.priority,
        queue_state=args.queue_state,
        review_status=args.review_status,
        target_domain=args.target_domain,
        limit=args.limit,
        write_db=args.write_db,
        artifact_dir=args.artifact_dir,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['version']}: "
            f"{'passed' if decision['ready_for_admin_review_surface'] else 'blocked'} "
            f"({decision['passed_checks']}/{decision['total_checks']}) "
            f"{decision['decision_status']} "
            f"rows={decision['row_count']} "
            f"backend={result['query_summary']['backend']}"
        )
    return 0 if decision["ready_for_admin_review_surface"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
