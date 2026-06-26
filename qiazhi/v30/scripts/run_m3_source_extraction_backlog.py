from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_m3_source_extraction_backlog


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 M3-G4 source extraction backlog operationalization.")
    parser.add_argument("--artifact-dir", default=".runtime/validation/m3")
    parser.add_argument("--write-db", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_m3_source_extraction_backlog(
        artifact_dir=args.artifact_dir,
        write_db=args.write_db,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        db_write = result.get("db_write", {})
        db_text = ""
        if isinstance(db_write, dict) and db_write:
            db_text = f" db={db_write.get('backend')} searchable={db_write.get('searchable')}"
        print(
            f"{result['version']}: "
            f"{'passed' if decision['ready_for_source_backlog_review'] else 'blocked'} "
            f"({decision['passed_checks']}/{decision['total_checks']}) "
            f"{decision['decision_status']} "
            f"rows={decision['backlog_row_count']}"
            f"{db_text}"
        )
    return 0 if decision["ready_for_source_backlog_review"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
