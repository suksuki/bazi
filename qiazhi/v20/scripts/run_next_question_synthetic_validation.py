#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.scripts.contract import run_and_print  # noqa: E402
from v20.validation.next_question_synthetic import (  # noqa: E402
    build_next_question_synthetic_validation_report,
    write_next_question_synthetic_validation_artifact,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate V20 next-question policy with synthetic role cases.")
    parser.add_argument("--write", action="store_true", help="Write a local training artifact.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.progress:
            print("[v20-next-question] validating role paths and suppression", file=sys.stderr, flush=True)
        return write_next_question_synthetic_validation_artifact() if args.write else build_next_question_synthetic_validation_report()

    return run_and_print(
        _run,
        command="run_next_question_synthetic_validation.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
