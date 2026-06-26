#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.question_dag_training import build_question_dag_training_report  # noqa: E402
from v20.scripts.contract import run_and_print  # noqa: E402
from v20.storage.local_jsonl import local_jsonl_store_from_env  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the V20 question DAG candidate training report.")
    parser.add_argument("--write", action="store_true", help="Write a local training artifact.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.progress:
            print("[v20-question-dag] building candidate policy", file=sys.stderr, flush=True)
        report = build_question_dag_training_report()
        if args.write:
            return _write_report(report)
        return report

    return run_and_print(
        _run,
        command="run_question_dag_training.py",
        args=args,
        runtime_mutation=args.write,
    )


def _write_report(report: dict[str, object]) -> dict[str, object]:
    directory = local_jsonl_store_from_env().runtime_dir / "training" / "question_dag"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"question_dag_training_{stamp}.json"
    payload = report | {"written_at": datetime.now(timezone.utc).isoformat(), "runtime_mutation": True}
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    latest_path.write_text(text, encoding="utf-8")
    run_path.write_text(text, encoding="utf-8")
    return {
        "version": "v20.question_dag_training_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report.get("status", ""),
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_TRAINING_ARTIFACT_ONLY",
            "NO_RUNTIME_POINTER_MUTATION",
            "QUESTION_DAG_POLICY_REMAINS_CANDIDATE",
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
