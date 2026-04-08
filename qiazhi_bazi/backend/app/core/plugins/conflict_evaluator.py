"""Evaluate plugin divergence on verdict-ready stage."""
from __future__ import annotations

from typing import Any, Dict, List


def _polarity(text: str) -> int:
    s = str(text or "")
    pos_words = ("可转化", "顺势", "稳定", "得", "推进")
    neg_words = ("风险", "锁死", "闭锁", "止损", "受阻", "坍塌")
    score = 0
    if any(w in s for w in pos_words):
        score += 1
    if any(w in s for w in neg_words):
        score -= 1
    return 1 if score > 0 else (-1 if score < 0 else 0)


def evaluate_plugin_conflict(
    *,
    plugin_outputs: Dict[str, Dict[str, Any]],
    plugin_weights: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    outputs = plugin_outputs or {}
    weights = plugin_weights or {}
    rows: List[Dict[str, Any]] = []
    for pid, payload in outputs.items():
        verdict = str(payload.get("verdict") or "")
        conf = float(payload.get("confidence_score", 0.7) or 0.7)
        w = float(weights.get(pid, 1.0) or 1.0)
        rows.append({"plugin_id": pid, "polarity": _polarity(verdict), "weighted": conf * w, "verdict": verdict})

    if len(rows) < 2:
        return {
            "tension_level": 0.0,
            "zone": "BLUE",
            "has_polarity_reversal": False,
            "divergence_notes": ["插件数不足，默认低冲突。"],
        }

    pos = sum(r["weighted"] for r in rows if r["polarity"] > 0)
    neg = sum(r["weighted"] for r in rows if r["polarity"] < 0)
    total = max(1e-6, pos + neg)
    gap = abs(pos - neg) / total
    tension = 1.0 - gap

    if tension > 0.66 and pos > 0 and neg > 0:
        zone = "RED"
        note = "高张力冲突：多流派吉凶极性对冲，需先止损后推进。"
    elif tension > 0.33:
        zone = "YELLOW"
        note = "中等背离：结论方向接近但力度分歧较大。"
    else:
        zone = "BLUE"
        note = "高共振：多流派结论一致性较高。"
    return {
        "tension_level": round(float(tension), 4),
        "zone": zone,
        "has_polarity_reversal": bool(pos > 0 and neg > 0),
        "divergence_notes": [note] + [f"{r['plugin_id']}: {r['verdict']}" for r in rows[:3]],
    }

