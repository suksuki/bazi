#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.ops.training_tasks import run_training_task_worker  # noqa: E402
from v20.scripts.contract import run_and_print  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a V20 admin training task worker.")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--task-key", required=True)
    args, extra = parser.parse_known_args()

    def _run() -> dict[str, object]:
        result = run_training_task_worker(args.task_id, args.task_key, tuple(extra))
        if result.get("status") == "succeeded":
            return result | {"status": "pass", "worker_status": "succeeded"}
        return result | {"ok": False}

    return run_and_print(
        _run,
        command="run_admin_training_task.py",
        args=args,
        runtime_mutation=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
