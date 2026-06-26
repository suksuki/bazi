from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_m3_core_spine_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Snapshot V30 M3 K/R/P, rules, portraits, synthetic, and optional 518K coverage.")
    parser.add_argument("--include-518k-sample", action="store_true")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--artifact-dir", default=".runtime/validation/m3")
    parser.add_argument("--no-db", action="store_true", help="Do not attempt Postgres write.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    snapshot = run_m3_core_spine_snapshot(
        include_518k_sample=args.include_518k_sample,
        sample_limit=args.sample_limit,
        write_db=not args.no_db,
        artifact_dir=args.artifact_dir,
    )
    if args.json:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    else:
        inventory = snapshot["inventory"]
        db_write = snapshot.get("db_write", {})
        print(
            f"{snapshot['snapshot_id']}: "
            f"krp={inventory['krp_unit_count']} "
            f"rules={inventory['rule_spec_count']} "
            f"portrait_assets={inventory['portrait_asset_count']} "
            f"synthetic={snapshot['synthetic_validation']['passed_count']}/{snapshot['synthetic_validation']['case_count']}"
        )
        print(f"- artifact: {snapshot.get('artifact_uri', '-')}")
        if isinstance(db_write, dict) and db_write:
            print(f"- db: {db_write.get('backend')} searchable={db_write.get('searchable')} rows={db_write.get('rows', {})}")
        if snapshot["validation_518k"].get("included"):
            print(
                f"- 518k: {snapshot['validation_518k']['run_id']} "
                f"cases={snapshot['validation_518k']['case_count']} "
                f"{snapshot['validation_518k']['promotion_signal']}"
            )
    return 0 if snapshot["synthetic_validation"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
