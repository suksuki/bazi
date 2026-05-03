#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.arbitration_loop import (  # noqa: E402
    build_arbitration_loop_report,
    read_arbitration_loop_artifact,
    write_arbitration_loop_artifact,
)
from v20.scripts.contract import run_and_print  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V20 arbitration/conflict learning snapshots.")
    parser.add_argument("--status", action="store_true", help="Read the latest local arbitration artifact.")
    parser.add_argument("--write", action="store_true", help="Write local arbitration artifact.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        progress = (
            lambda message: print(f"[v20-arbitration] {message}", file=sys.stderr, flush=True)
        ) if args.progress else None
        if args.status:
            return read_arbitration_loop_artifact()
        if args.write:
            return write_arbitration_loop_artifact(progress=progress)
        return build_arbitration_loop_report(progress=progress)

    return run_and_print(
        _run,
        command="run_arbitration_loop.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
