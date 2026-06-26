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
    parser = argparse.ArgumentParser(description="Run V30 M3-G1 source-governed calibration tags.")
    parser.add_argument("--include-518k-sample", action="store_true")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--artifact-dir", default=".runtime/validation/m3")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    snapshot = run_m3_core_spine_snapshot(
        include_518k_sample=args.include_518k_sample,
        sample_limit=args.sample_limit,
        write_db=False,
        artifact_dir=args.artifact_dir,
    )
    calibration = snapshot["source_governed_calibration"]
    coverage = calibration["coverage"]
    if args.json:
        print(json.dumps(calibration, ensure_ascii=False, indent=2))
    else:
        print(
            f"{calibration['version']}: {calibration['status']} "
            f"groups={coverage['tag_group_count']} "
            f"real_case_tags={coverage['real_case_tag_count']} "
            f"domain_tags={coverage['domain_depth_tag_count']} "
            f"source_queue={coverage['source_queue_count']} "
            f"518k={coverage['has_518k_distribution']}"
        )
    return 0 if calibration["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
