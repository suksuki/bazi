from __future__ import annotations

from typing import Any, Dict, List, Tuple


def parse_verdict_body_and_changelog(obj: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """从 LLM JSON 对象解析 verdict_body 与规范化 change_log。"""
    verdict_body = str(obj.get("verdict_body") or "").strip()
    raw_change_log = obj.get("change_log")
    if isinstance(raw_change_log, dict):
        change_log: Dict[str, Any] = {
            "physics_diff": [str(x).strip() for x in (raw_change_log.get("physics_diff") or []) if str(x).strip()],
            "consensus_diff": [str(x).strip() for x in (raw_change_log.get("consensus_diff") or []) if str(x).strip()],
            "text_diff_hint": str(raw_change_log.get("text_diff_hint") or "").strip(),
        }
    else:
        legacy: List[Any] = raw_change_log if isinstance(raw_change_log, list) else []
        change_log = {
            "physics_diff": [],
            "consensus_diff": [],
            "text_diff_hint": "；".join([str(x).strip() for x in legacy if str(x).strip()][:2]),
        }
    return verdict_body, change_log
