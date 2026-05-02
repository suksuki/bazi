#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate V20 active packages from the self-evolution manifest.")
    parser.add_argument("--status", action="store_true", help="Read the latest written active package artifact.")
    parser.add_argument("--write", action="store_true", help="Write a active package artifact.")
    parser.add_argument("--include-rule-batch", action="store_true", help="Include the heavier rule/portrait/question batch phase upstream.")
    parser.add_argument("--corpus-preview", type=int, default=0, help="Optionally preview N full-corpus cases upstream.")
    args = parser.parse_args()

    if args.status:
        payload = read_active_package_artifact()
    else:
        package = build_active_package(
            include_rule_batch=args.include_rule_batch,
            corpus_preview_limit=max(0, args.corpus_preview),
        )
        payload = write_active_package_artifact(package) if args.write else package
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("status") not in {"fail", "blocked"} and payload.get("package_status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
