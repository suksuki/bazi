"""Readonly mirror: ten-god pattern judgement seed."""
from __future__ import annotations

from typing import Dict, List


def judge_ten_god_pattern(deity_scores: Dict[str, float]) -> str:
    if not deity_scores:
        return "未定格"
    top = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
    name, score = top[0]
    if name == "正官" and score >= 40:
        return "正官格势强"
    if name in {"食神", "伤官"} and score >= 35:
        return "食伤外放格"
    if name in {"偏财", "正财"} and score >= 35:
        return "财星主导格"
    return f"{name}主轴格"


def collect_v17_facts(deity_scores: Dict[str, float]) -> List[dict]:
    pattern = judge_ten_god_pattern(deity_scores)
    if pattern == "未定格":
        return []
    return [
        {
            "plugin": "ten_god_pattern",
            "fact": f"十神格局判定：{pattern}。",
            "label": "围绕主轴格局统一资源优先级，避免多线分散。",
            "priority": 0.78,
        }
    ]
