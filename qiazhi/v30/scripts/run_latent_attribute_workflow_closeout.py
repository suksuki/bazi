#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_latent_attribute_workflow_closeout


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 latent attribute workflow closeout.")
    parser.add_argument("--closeout-id", default="")
    parser.add_argument("--artifact-dir", default=".runtime/validation/latent-attribute-closeout")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_latent_attribute_workflow_closeout(
        closeout_id=args.closeout_id,
        artifact_dir=args.artifact_dir,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- passed: {decision['passed_check_count']}/{decision['check_count']}")
        print(f"- failed: {','.join(decision['failed_check_ids']) or 'none'}")
        print(f"- next: {result['next_mainline_selection']['task_id']}")
    return 0 if result["decision"]["closeout_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
