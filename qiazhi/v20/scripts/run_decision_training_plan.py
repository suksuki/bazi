#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.decision_training import build_decision_training_plan  # noqa: E402
from v20.scripts.contract import run_and_print


def main() -> int:
    return run_and_print(
        build_decision_training_plan,
        command="run_decision_training_plan.py",
        args=argparse.Namespace(),
        runtime_mutation=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())
