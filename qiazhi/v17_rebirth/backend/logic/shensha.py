from __future__ import annotations

from typing import Dict, List


def collect_v17_facts(deity_scores: Dict[str, float]) -> List[dict]:
    officer = float(deity_scores.get("正官", 0.0))
    print_star = float(deity_scores.get("偏印", 0.0))
    wealth = float(deity_scores.get("正财", 0.0) + deity_scores.get("偏财", 0.0))
    shensha_heat = round((officer * 0.45 + print_star * 0.35 + wealth * 0.2) / 10.0, 3)
    if shensha_heat <= 1.2:
        return []
    return [
        {
            "plugin": "shensha",
            "fact": f"神煞场显化增强，护持/扰动强度 {shensha_heat:.2f}。",
            "label": "先校准边界与节奏，再决定扩张或防守。",
            "priority": min(0.95, 0.55 + shensha_heat / 5.0),
        }
    ]
