#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.active_generation import (  # noqa: E402
    build_active_package,
    read_active_package_artifact,
    write_active_package_artifact,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate V20 active packages from the self-evolution manifest.")
    parser.add_argument("--status", action="store_true", help="Read the latest written active package artifact.")
    parser.add_argument("--write", action="store_true", help="Write a active package artifact.")
    parser.add_argument("--include-rule-batch", action="store_true", help="Include the heavier rule/portrait/question batch phase upstream.")
    parser.add_argument("--corpus-preview", type=int, default=0, help="Optionally preview N full-corpus cases upstream.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.status:
            return read_active_package_artifact()
        package = build_active_package(
            include_rule_batch=args.include_rule_batch,
            corpus_preview_limit=max(0, args.corpus_preview),
        )
        return write_active_package_artifact(package) if args.write else package

    return run_and_print(
        _run,
        command="run_active_generation.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
