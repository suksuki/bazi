#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.question_ranking_learning import (
    build_question_ranking_learning_report,
    read_question_ranking_learning_artifact,
    write_question_ranking_learning_artifact,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V20 shadow learning for question ranking priorities")
    parser.add_argument("--status", action="store_true", help="Read latest local shadow ranking artifact.")
    parser.add_argument("--write", action="store_true", help="Write latest ranking report to local runtime artifacts.")
    parser.add_argument("--top-k", type=int, default=8, help="Top-K rank penalty threshold for report metrics.")
    parser.add_argument("--max-cases", type=int, default=48, help="Maximum training cases to evaluate.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    parser.add_argument("--use-shadow-prefix", action="store_true", help="Enable prefix-based rule weighting in proposals.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.status:
            return read_question_ranking_learning_artifact()
        if args.write:
            return write_question_ranking_learning_artifact(
                top_k=max(1, args.top_k),
                max_cases=max(1, args.max_cases),
            )
        progress = (
            lambda message: print(f"[v20-question-ranking] {message}", file=sys.stderr, flush=True)
        ) if args.progress else None
        if progress is not None:
            progress("start question ranking learning")

        if progress is not None:
            progress(f"cases=manual_or_default top_k={args.top_k} max_cases={args.max_cases}")
        report = build_question_ranking_learning_report(
            top_k=max(1, args.top_k),
            max_cases=max(1, args.max_cases),
            use_shadow_prefix=args.use_shadow_prefix,
            collect_quality_findings=True,
        )
        if progress is not None:
            progress("question ranking learning report complete")
        return report

    return run_and_print(
        _run,
        command="run_question_ranking_training.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
