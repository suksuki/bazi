from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.learning import DEFAULT_AUTO_TRAINING_FAMILIES, run_auto_apply_training


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 auto-apply training loop.")
    parser.add_argument("--training-run-id", default=None)
    parser.add_argument("--family", action="append", choices=DEFAULT_AUTO_TRAINING_FAMILIES)
    parser.add_argument("--promotion-validation-mode", choices=("strict", "smoke"), default="strict")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    families = tuple(args.family) if args.family else DEFAULT_AUTO_TRAINING_FAMILIES
    result = run_auto_apply_training(
        families=families,
        training_run_id=args.training_run_id,
        promotion_validation_mode=args.promotion_validation_mode,
    )
    if args.json:
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        print(
            f"{result.training_run_id}: {result.status} "
            f"({result.metrics['promoted_count']}/{result.metrics['candidate_count']} promoted)"
        )
        for family, artifact_id in result.active_policy_versions.items():
            print(f"- {family}: {artifact_id}")
        for failure in result.failures:
            print(f"- failure: {failure}")
    return 0 if result.status == "applied" else 1


if __name__ == "__main__":
    raise SystemExit(main())
