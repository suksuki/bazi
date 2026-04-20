from __future__ import annotations

from typing import Any, Dict, List


def fact_row(item: Any) -> Dict[str, Any]:
    if isinstance(item, dict):
        text = str(item.get("fact") or item.get("text") or "").strip()
        try:
            weight = float(item.get("weight", item.get("salience_weight", 0.5)) or 0.5)
        except (TypeError, ValueError):
            weight = 0.5
        return {"fact": text, "weight": max(0.0, min(1.0, weight))}
    text = str(item or "").strip()
    return {"fact": text, "weight": 0.5 if text else 0.0}


def sorted_fact_rows(facts: List[Any]) -> List[Dict[str, Any]]:
    rows = [fact_row(x) for x in facts]
    rows = [r for r in rows if r.get("fact")]
    rows.sort(key=lambda x: float(x.get("weight", 0.0)), reverse=True)
    return rows[:80] if len(rows) > 100 else rows


def build_fact_fragments(
    deity_scores: Dict[str, float],
    facts: List[Any],
    *,
    total_energy_index: float = 0.0,
) -> List[str]:
    ranked = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
    lead = [f"{k}偏强" for k, _ in ranked[:2]]
    sorted_rows = sorted_fact_rows(facts)
    top10 = [str(x.get("fact") or "") for x in sorted_rows[:10] if str(x.get("fact") or "").strip()]
    tail_anchor = [str(x.get("fact") or "") for x in sorted_rows[:3] if str(x.get("fact") or "").strip()]
    middle = [str(x.get("fact") or "") for x in sorted_rows[10:] if str(x.get("fact") or "").strip()]
    tail_anchor = [x for x in tail_anchor if x not in top10 and x not in middle]
    energy_hint = (
        f"当前十神能量为绝对物理强度，Total Energy Index={total_energy_index:.2f}。"
        "若总能量偏低，应偏向漂泊、谨慎；若总能量偏高，应偏向刚毅、掌控。"
    )
    return [
        "以下提供的 160 条事实已按显著性（Salience）降序排列。排序越靠前的事实对命局的影响越具决定性。请务必优先回应前 10 条核心事实，将其作为你裁决的第一物理支点。",
        energy_hint,
        ("、".join(lead) + "，局势进入再平衡阶段") if lead else "当前能量分布尚在收敛",
        *top10,
        *middle,
        *tail_anchor,
    ]


def build_physics_trace(raw_physics: Dict[str, Any], *, causal_anchor: str) -> Dict[str, Any]:
    pt = raw_physics if isinstance(raw_physics, dict) else {}
    import json

    try:
        fingerprint = str(abs(hash(json.dumps(pt, ensure_ascii=False, sort_keys=True, default=str))))
    except Exception:
        fingerprint = "0"
    return {
        "causal_anchor": str(causal_anchor or "local_memory"),
        "physics_fingerprint": fingerprint,
    }
