"""裁决人语义反馈：追加写入 JSONL，供进化引擎作适应度信号。"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict


def _feedback_path() -> Path:
    raw = os.environ.get("QIAZHI_SKILL_FEEDBACK_PATH", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path(__file__).resolve().parents[2] / "data" / "skill_feedback.jsonl"


def append_skill_feedback(record: Dict[str, Any]) -> Path:
    p = _feedback_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    row = {**record, "recorded_at": time.time()}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return p
