#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.practitioner_calibration_training import (  # noqa: E402
    build_practitioner_calibration_training_report,
    read_practitioner_calibration_training_artifact,
    write_practitioner_calibration_training_artifact,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate structured practitioner calibration signals into offline V20 training proposals."
    )
    parser.add_argument("--status", action="store_true", help="Read the latest written local artifact.")
    parser.add_argument("--write", action="store_true", help="Write the report into the local runtime dir.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        progress = (
            lambda message: print(f"[v20-practitioner-calibration] {message}", file=sys.stderr, flush=True)
        ) if args.progress else None
        if args.status:
            return read_practitioner_calibration_training_artifact()
        if args.write:
            return write_practitioner_calibration_training_artifact(progress=progress)
        return build_practitioner_calibration_training_report(progress=progress)

    return run_and_print(
        _run,
        command="run_practitioner_calibration_training.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
