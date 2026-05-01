#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V20 synthetic rule validation/training gate.")
    parser.add_argument("--suite", action="store_true", help="Print the synthetic rule validation suite only.")
    parser.add_argument("--status", action="store_true", help="Read the latest written local training artifact.")
    parser.add_argument("--write", action="store_true", help="Write the training report into the local runtime dir.")
    args = parser.parse_args()

    if args.status:
        payload = read_rule_synthetic_training_artifact()
    elif args.suite:
        payload = run_rule_synthetic_suite()
    elif args.write:
        payload = write_rule_synthetic_training_artifact()
    else:
        payload = build_rule_synthetic_training_report()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("status") not in {"fail", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
