#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning_orchestrator.run_plan import build_learning_orchestrator_run_plan  # noqa: E402
from v20.scripts.contract import run_and_print  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a V20 learning orchestrator run plan.")
    parser.add_argument("--job", default="nightly", choices=("fast", "nightly", "weekly", "full"))
    args = parser.parse_args()

    return run_and_print(
        lambda: build_learning_orchestrator_run_plan(args.job),
        command="run_learning_orchestrator_plan.py",
        args=args,
        runtime_mutation=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())
