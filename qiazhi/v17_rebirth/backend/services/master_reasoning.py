from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Tuple

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import STEM_ELEMENT


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _physics_scores(physics_tensor: Dict[str, Any]) -> Dict[str, float]:
    scores = physics_tensor.get("ten_gods_base_l0")
    if not isinstance(scores, dict):
        scores = physics_tensor.get("ten_gods_absolute")
    if not isinstance(scores, dict):
        return {}
    return {str(k): _safe_float(v) for k, v in scores.items() if str(k).strip()}


def _four_pillars(physics_tensor: Dict[str, Any]) -> Dict[str, str]:
    fp = physics_tensor.get("four_pillars")
    return fp if isinstance(fp, dict) else {}


def _day_master(physics_tensor: Dict[str, Any]) -> str:
    stem = str(physics_tensor.get("day_master_stem") or "").strip()
    if stem:
        return stem
    day_gz = str(_four_pillars(physics_tensor).get("day") or "").strip()
    return day_gz[0] if len(day_gz) >= 2 else ""


def _visible_stem_rows(physics_tensor: Dict[str, Any]) -> List[Tuple[str, str]]:
    fp = _four_pillars(physics_tensor)
    rows = [
        ("year", str(fp.get("year") or "").strip()),
        ("month", str(fp.get("month") or "").strip()),
        ("day", str(fp.get("day") or "").strip()),
        ("hour", str(fp.get("hour") or "").strip()),
        ("luck", str(physics_tensor.get("luck_pillar") or "").strip()),
        ("flow", str(physics_tensor.get("flow_pillar") or "").strip()),
    ]
    out: List[Tuple[str, str]] = []
    for scope, gz in rows:
        if len(gz) >= 2:
            out.append((scope, gz[0]))
    return out


def _visible_element_summary(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    counts = Counter()
    scoped_counts = Counter()
    for scope, stem in _visible_stem_rows(physics_tensor):
        element = STEM_ELEMENT.get(stem, "")
        if not element:
            continue
        counts[element] += 1
        scoped_counts[f"{element}:{scope}"] += 1
    return {
        "by_element": dict(counts),
        "by_scope": dict(scoped_counts),
    }


def _collect_sanhe_rows(meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    interaction_v2 = meta.get("interaction_v2")
    if not isinstance(interaction_v2, dict):
        return []
    rows = interaction_v2.get("san_he")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _top_sanhe_row(meta: Dict[str, Any]) -> Dict[str, Any]:
    rows = _collect_sanhe_rows(meta)
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            _safe_float(row.get("strength")),
            _safe_float(row.get("pivot_factor")),
            _safe_int(row.get("duplicate_count")),
        ),
    )


def _reasoning_steps(
    *,
    physics_tensor: Dict[str, Any],
    meta: Dict[str, Any],
) -> List[Dict[str, Any]]:
    scores = _physics_scores(physics_tensor)
    visible = _visible_element_summary(physics_tensor)
    top_sanhe = _top_sanhe_row(meta)
    steps: List[Dict[str, Any]] = []

    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if sorted_scores:
        top_gods = [{"god": god, "score": round(score, 2)} for god, score in sorted_scores[:4]]
        steps.append(
            {
                "stage": "body",
                "title": "先看体",
                "summary": "先看原局与基线十神主轴，确认命盘当前最强的体用分布。",
                "evidence": {
                    "top_gods": top_gods,
                },
            }
        )

    steps.append(
        {
            "stage": "visible_stems",
            "title": "再看透干",
            "summary": "区分纯透、旁助与虚浮透干，明干对判断方向的加持不可一概而论。",
            "evidence": visible,
        }
    )

    if top_sanhe:
        steps.append(
            {
                "stage": "formation",
                "title": "再看成局",
                "summary": "三合/半合等成局关系应按中神、库神、生地方位与重复支累积分层评估。",
                "evidence": {
                    "group": list(top_sanhe.get("group") or []),
                    "matched_branches": list(top_sanhe.get("matched_branches") or []),
                    "branch_counts": dict(top_sanhe.get("branch_counts") or {}),
                    "mid_branch": str(top_sanhe.get("mid_branch") or ""),
                    "duplicate_count": _safe_int(top_sanhe.get("duplicate_count")),
                    "pivot_factor": round(_safe_float(top_sanhe.get("pivot_factor")), 3),
                    "strength": round(_safe_float(top_sanhe.get("strength")), 3),
                    "origin_type": str(top_sanhe.get("origin_type") or ""),
                },
            }
        )

    luck_pillar = str(physics_tensor.get("luck_pillar") or "").strip()
    flow_pillar = str(physics_tensor.get("flow_pillar") or "").strip()
    steps.append(
        {
            "stage": "runtime",
            "title": "再看运引",
            "summary": "大运偏背景延续，流年偏引动触发；同元素透干与纯十神透干应分开处理。",
            "evidence": {
                "luck_pillar": luck_pillar,
                "flow_pillar": flow_pillar,
            },
        }
    )

    interaction_v2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    suppressors = {
        "liu_chong": len(interaction_v2.get("liu_chong") or []),
        "liu_hai": len(interaction_v2.get("liu_hai") or []),
        "liu_po": len(interaction_v2.get("liu_po") or []),
        "sanxing": len(interaction_v2.get("sanxing") or []),
    }
    steps.append(
        {
            "stage": "suppression",
            "title": "最后看冲破",
            "summary": "冲、害、破、刑应作为成局后的抑制层，而不是先验地掐灭主结构。",
            "evidence": suppressors,
        }
    )
    return steps


def build_master_reasoning_trace(
    *,
    physics_tensor: Dict[str, Any],
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    scores = _physics_scores(physics_tensor)
    visible = _visible_element_summary(physics_tensor)
    top_sanhe = _top_sanhe_row(meta)
    day_master = _day_master(physics_tensor)

    dominant = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    dominant_evidence: List[Dict[str, Any]] = []
    if top_sanhe:
        dominant_evidence.append(
            {
                "kind": "sanhe_structure",
                "group": list(top_sanhe.get("group") or []),
                "matched_branches": list(top_sanhe.get("matched_branches") or []),
                "mid_branch": str(top_sanhe.get("mid_branch") or ""),
                "duplicate_count": _safe_int(top_sanhe.get("duplicate_count")),
                "pivot_factor": round(_safe_float(top_sanhe.get("pivot_factor")), 3),
                "strength": round(_safe_float(top_sanhe.get("strength")), 3),
            }
        )
    dominant_evidence.extend(
        {"kind": "god_score", "god": god, "score": round(score, 2)}
        for god, score in dominant[:3]
    )

    learning_hooks = {
        "requires_human_review": bool(top_sanhe),
        "review_axes": [
            "中神/墓库/生地位权重",
            "纯透十神与同元素旁助的区分",
            "重复支如何累加到成局稳定度",
            "冲破是抑制层还是毁局层",
        ],
        "feedback_slots": {
            "structure_judgement": "",
            "support_order": "",
            "suppression_order": "",
            "final_strength_verdict": "",
        },
    }

    return {
        "version": "v17.master_reasoning.v1",
        "day_master": day_master,
        "summary": {
            "dominant_ten_gods": [{"god": god, "score": round(score, 2)} for god, score in dominant[:5]],
            "visible_elements": visible.get("by_element", {}),
            "top_sanhe_group": list(top_sanhe.get("group") or []),
            "top_sanhe_strength": round(_safe_float(top_sanhe.get("strength")), 3),
        },
        "reasoning_steps": _reasoning_steps(physics_tensor=physics_tensor, meta=meta),
        "dominant_evidence": dominant_evidence,
        "suppressed_evidence": [
            {
                "kind": "relation_suppression",
                "liu_chong": len((meta.get("interaction_v2") or {}).get("liu_chong") or []),
                "liu_hai": len((meta.get("interaction_v2") or {}).get("liu_hai") or []),
                "liu_po": len((meta.get("interaction_v2") or {}).get("liu_po") or []),
                "sanxing": len((meta.get("interaction_v2") or {}).get("sanxing") or []),
            }
        ],
        "learning_hooks": learning_hooks,
    }
