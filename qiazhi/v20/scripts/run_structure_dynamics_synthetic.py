#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.scripts.contract import run_and_print  # noqa: E402
from v20.validation.structure_dynamics_synthetic import (  # noqa: E402
    STRUCTURE_DYNAMICS_SYNTHETIC_CASES,
    run_structure_dynamics_synthetic_suite,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V20 structure dynamics v2 synthetic validation.")
    parser.add_argument("--summary", action="store_true", help="Return summary counters without per-case details.")
    parser.add_argument("--max-cases", type=int, default=0, help="Limit cases; use 0 for all cases.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        cases = STRUCTURE_DYNAMICS_SYNTHETIC_CASES[: args.max_cases] if args.max_cases > 0 else STRUCTURE_DYNAMICS_SYNTHETIC_CASES
        if args.progress:
            print(f"[v20-sde-synthetic] running structure dynamics cases [1/{max(1, len(cases))}]", file=sys.stderr, flush=True)
        report = run_structure_dynamics_synthetic_suite(cases=cases)
        if args.summary:
            return {
                key: value
                for key, value in report.items()
                if key not in {"results"}
            }
        return report

    return run_and_print(
        _run,
        command="run_structure_dynamics_synthetic.py",
        args=args,
        runtime_mutation=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())
