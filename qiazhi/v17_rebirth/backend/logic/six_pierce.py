"""Readonly mirror: six-pierce penetration signal."""
from __future__ import annotations

from typing import Dict, List


def run_six_pierce(*, source_abs: float, target_abs: float, penetration_ratio: float = 0.45) -> Dict[str, float | str]:
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    ratio = min(1.0, max(0.0, float(penetration_ratio or 0.0)))
    damage = min(src, tgt) * ratio
    return {"effect": "pierce", "abs_loss": round(damage, 4), "vector": "penetration"}


def collect_v17_facts(deity_scores: Dict[str, float]) -> List[dict]:
    peer = float(deity_scores.get("比肩", 0.0))
    officer = float(deity_scores.get("正官", 0.0))
    result = run_six_pierce(source_abs=peer, target_abs=officer, penetration_ratio=0.42)
    loss = float(result.get("abs_loss", 0.0))
    if loss < 3.0:
        return []
    return [
        {
            "plugin": "six_pierce",
            "fact": f"六穿态激活，结构穿透损耗约 {loss:.1f}。",
            "label": "关键动作加一层确认，压低冲动决策误差。",
            "priority": min(0.9, 0.5 + loss / 18.0),
        }
    ]
