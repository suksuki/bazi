#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.validation.rule_synthetic import (  # noqa: E402
    build_rule_synthetic_training_report,
    read_rule_synthetic_training_artifact,
    run_rule_synthetic_suite,
    write_rule_synthetic_training_artifact,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V20 synthetic rule validation/training gate.")
    parser.add_argument("--suite", action="store_true", help="Print the synthetic rule validation suite only.")
    parser.add_argument("--status", action="store_true", help="Read the latest written local training artifact.")
    parser.add_argument("--write", action="store_true", help="Write the training report into the local runtime dir.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.status:
            return read_rule_synthetic_training_artifact()
        if args.suite:
            return run_rule_synthetic_suite()
        if args.write:
            return write_rule_synthetic_training_artifact()
        return build_rule_synthetic_training_report()

    return run_and_print(
        _run,
        command="run_rule_synthetic_training.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
