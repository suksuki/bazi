#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.dynamic_decision_training import (  # noqa: E402
    read_dynamic_decision_training_artifact,
    run_dynamic_decision_training_batch,
    write_dynamic_decision_training_artifact,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run V20 dynamic decision training/validation batch without touching runtime rules."
    )
    parser.add_argument("--status", action="store_true", help="Read the latest written local training artifact.")
    parser.add_argument("--write", action="store_true", help="Write the report into the local runtime dir.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    args = parser.parse_args()

    progress = (
        lambda message: print(f"[v20-dynamic-decision] {message}", file=sys.stderr, flush=True)
    ) if args.progress else None
    if args.status:
        payload = read_dynamic_decision_training_artifact()
    elif args.write:
        payload = write_dynamic_decision_training_artifact(progress=progress)
    else:
        payload = run_dynamic_decision_training_batch(progress=progress)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("status") not in {"fail", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
