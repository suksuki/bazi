#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.scripts.contract import run_and_print  # noqa: E402
from v20.validation.synthetic_bazi_evaluator import evaluate_synthetic_bazi_replay  # noqa: E402
from v20.validation.synthetic_replay import run_synthetic_bazi_replay  # noqa: E402
from v20.validation.synthetic_schema import minimal_synthetic_bazi_cases, synthetic_bazi_coverage_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V20 synthetic bazi replay and evaluation suite.")
    parser.add_argument("--summary", action="store_true", help="Return summary counters without full per-case payloads.")
    parser.add_argument("--max-cases", type=int, default=1, help="Limit replayed cases; use 0 for all cases.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.progress:
            print("[v20-synthetic-suite] running replay", file=sys.stderr, flush=True)
        return _run_suite(max_cases=max(0, args.max_cases), summary=args.summary)

    return run_and_print(
        _run,
        command="run_synthetic_case_suite.py",
        args=args,
        runtime_mutation=False,
    )


def _run_suite(*, max_cases: int, summary: bool) -> dict[str, object]:
    cases = minimal_synthetic_bazi_cases()
    selected = cases[:max_cases] if max_cases > 0 else cases
    replay = run_synthetic_bazi_replay(cases=selected)
    by_id = {case.case_id: case for case in selected}
    evaluations = tuple(
        evaluate_synthetic_bazi_replay(by_id[str(row["case_id"])], row)
        for row in replay["results"]
        if str(row.get("case_id", "")) in by_id
    )
    failure_count = sum(len(row["failures"]) for row in evaluations)
    coverage = synthetic_bazi_coverage_report(cases)
    coverage_gap_count = int(coverage.get("gap_count", 0) or 0)
    payload: dict[str, object] = {
        "version": "v20.synthetic_case_suite_report.v1",
        "status": "needs_review" if failure_count or coverage_gap_count else "pass",
        "case_count": len(selected),
        "evaluated_case_count": len(evaluations),
        "failure_count": failure_count,
        "coverage_gap_count": coverage_gap_count,
        "ok": failure_count == 0 and coverage_gap_count == 0,
        "coverage_report": coverage,
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_CASE_SUITE_IS_OFFLINE",
            "NO_RUNTIME_RULE_MUTATION",
            "NO_POLICY_POINTER_MUTATION",
        ],
    }
    if summary:
        payload["failed_case_ids"] = tuple(row["case_id"] for row in evaluations if row["failures"])
    else:
        payload["replay"] = replay
        payload["evaluations"] = evaluations
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
