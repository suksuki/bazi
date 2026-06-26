from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import build_production_replay_intake_batch, run_synthetic_tier
from v30.storage.production_replay_store import build_production_replay_store


def main() -> int:
    parser = argparse.ArgumentParser(description="Build metadata-safe V30 production replay intake rows.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--selection-status", default="")
    parser.add_argument("--calendar-type", default="")
    parser.add_argument("--boundary-tag", default="")
    parser.add_argument("--module-ready", default="")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    synthetic = run_synthetic_tier("real_case_calibration_pack")
    metadata_rows = [
        row.observed.get("production_replay_metadata", {})
        for row in synthetic.results
        if isinstance(row.observed.get("production_replay_metadata"), dict)
        and row.observed.get("production_replay_metadata")
    ]
    result = build_production_replay_intake_batch(metadata_rows)
    if args.persist:
        store = build_production_replay_store()
        write = store.upsert_batch(result)
        search = store.search(
            selection_status=args.selection_status,
            calendar_type=args.calendar_type,
            boundary_tag=args.boundary_tag,
            module_ready=args.module_ready,
            limit=args.limit,
        )
        result = {
            **result,
            "store_write": write,
            "store_search": search,
        }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        summary = result["summary"]
        print(f"{result['version']}: rows={summary['row_count']} calibration_ready={summary['calibration_ready_count']}")
        print(f"pending={summary['hold_pending_count']} blocked={summary['blocked_count']}")
        if args.persist:
            print(f"stored={result['store_write']['stored_count']} total={result['store_write']['total_count']}")
            print(f"search_count={result['store_search']['count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
