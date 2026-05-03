#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.knowledge.completion import build_knowledge_completion_report  # noqa: E402
from v20.scripts.contract import run_and_print


def main() -> int:
    def _run() -> dict[str, object]:
        payload = build_knowledge_completion_report()
        if payload.get("mainline_complete") is True:
            return payload | {"status": "pass"}
        # 纵向推进优先：主线不完整时也允许写入和演进，只记录为需要迭代的运行态。
        return payload | {"status": "needs_work", "iteration_mode": "continuous_learning"}

    return run_and_print(
        _run,
        command="run_knowledge_completion.py",
        args=argparse.Namespace(),
        runtime_mutation=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())
