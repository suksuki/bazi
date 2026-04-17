from __future__ import annotations

from typing import Dict, List

_STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]


def collect_v17_facts(deity_scores: Dict[str, float]) -> List[dict]:
    total = sum(float(v or 0.0) for v in deity_scores.values())
    if total <= 0:
        return []
    strongest = max(deity_scores.items(), key=lambda kv: float(kv[1] or 0.0))
    stage_idx = int(abs(total + float(strongest[1]))) % 12
    stage = _STAGES[stage_idx]
    score = float(strongest[1] or 0.0)
    return [
        {
            "plugin": "chang_sheng_12",
            "fact": f"长生十二宫映射至「{stage}」位，主轴神 {strongest[0]} 强度 {score:.1f}。",
            "label": "按阶段推进：先完成当前位阶任务，再切换策略节拍。",
            "priority": min(0.88, 0.5 + score / 80.0),
        }
    ]
