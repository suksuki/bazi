#!/usr/bin/env python3.12
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.decision_training import build_decision_training_plan  # noqa: E402


def main() -> int:
    payload = build_decision_training_plan()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
