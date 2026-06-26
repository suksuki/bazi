#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.question_source_training import write_question_source_training_artifact  # noqa: E402
from v20.scripts.contract import run_and_print  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V20 question source training report.")
    args = parser.parse_args()
    return run_and_print(
        lambda: write_question_source_training_artifact(),
        command="run_question_source_training.py",
        args=args,
        runtime_mutation=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
