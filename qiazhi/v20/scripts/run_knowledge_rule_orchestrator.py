#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning_orchestrator.knowledge_rule_orchestrator import (  # noqa: E402
    build_knowledge_rule_orchestrator_plan,
    read_knowledge_rule_orchestrator_artifact,
    write_knowledge_rule_orchestrator_artifact,
)
from v20.scripts.contract import run_and_print  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V20 central knowledge-rule generation and validation orchestrator.")
    parser.add_argument("--write", action="store_true", help="Write orchestrator and child training artifacts.")
    parser.add_argument("--status", action="store_true", help="Read latest written orchestrator artifact.")
    parser.add_argument("--progress", action="store_true", help="Print progress to stderr.")
    parser.add_argument("--run-validation", action="store_true", help="Execute validation in foreground for dry-run mode.")
    parser.add_argument("--limit-per-domain", type=int, default=2, help="Rule proposal limit per core domain.")
    parser.add_argument("--synthetic-case-limit", type=int, default=8, help="Synthetic rule cases to validate; use 0 for all.")
    parser.add_argument("--overlay-limit", type=int, default=24, help="Knowledge-rule overlay rule limit; use 0 for all.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        progress = (
            lambda message: print(f"[v20-knowledge-rule-orchestrator] {message}", file=sys.stderr, flush=True)
        ) if args.progress else None
        if args.status:
            return read_knowledge_rule_orchestrator_artifact()
        if args.write:
            return write_knowledge_rule_orchestrator_artifact(
                limit_per_domain=max(1, args.limit_per_domain),
                synthetic_case_limit=max(0, args.synthetic_case_limit),
                overlay_limit=max(0, args.overlay_limit),
                progress=progress,
            )
        return build_knowledge_rule_orchestrator_plan(
            limit_per_domain=max(1, args.limit_per_domain),
            synthetic_case_limit=max(0, args.synthetic_case_limit),
            overlay_limit=max(0, args.overlay_limit),
            run_validation=args.run_validation,
            progress=progress,
        )

    return run_and_print(
        _run,
        command="run_knowledge_rule_orchestrator.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
