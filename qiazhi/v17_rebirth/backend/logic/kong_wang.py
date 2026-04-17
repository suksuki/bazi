from __future__ import annotations

from typing import Dict, List


def collect_v17_facts(deity_scores: Dict[str, float]) -> List[dict]:
    peer = float(deity_scores.get("比肩", 0.0))
    rob = float(deity_scores.get("劫财", 0.0))
    officer = float(deity_scores.get("正官", 0.0))
    void_ratio = round((peer + rob + 1.0) / (officer + 6.0), 3)
    if void_ratio < 0.75:
        return []
    return [
        {
            "plugin": "kong_wang",
            "fact": f"空亡波动抬升，信号空转比约 {void_ratio:.2f}。",
            "label": "高风险动作加一层回执确认，避免信息落空。",
            "priority": min(0.9, 0.58 + void_ratio / 4.0),
        }
    ]
