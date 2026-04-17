from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


_TECH_FACT_ID_RE = re.compile(r"\b[a-z]+(?:[_-][a-z0-9]+){1,}\b", re.I)


def _as_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _as_float(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _find_energy(physics_tensor: Dict[str, Any], key: str) -> float:
    k = str(key or "").strip().lower()
    if not k:
        return 0.0
    axes = _as_dict(physics_tensor.get("energy_axes"))
    for src in (
        axes,
        _as_dict(physics_tensor.get("meta")).get("energy_axes")
        if isinstance(_as_dict(physics_tensor.get("meta")).get("energy_axes"), dict)
        else {},
    ):
        if not isinstance(src, dict):
            continue
        for kk, vv in src.items():
            if str(kk).strip().lower() == k:
                return _as_float(vv)
    return 0.0


def _extract_active_will(metadata: Dict[str, Any], physics_tensor: Dict[str, Any]) -> str:
    md = _as_dict(metadata)
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = _as_dict(pt.get("meta"))
    bundle = _as_dict(meta.get("semantic_label_bundle_v1"))
    pl = _as_dict(md.get("persistence_layer"))
    will_ctx = _as_dict(pl.get("will_intention_context"))
    cands = [
        str(bundle.get("active_intention") or "").strip(),
        str(_as_dict(meta.get("intention_context")).get("active_intention") or "").strip(),
        str(will_ctx.get("active_intention") or "").strip(),
        str(md.get("user_intention") or "").strip(),
    ]
    for x in cands:
        if x:
            return x
    return ""


def _will_coloring_terms(active_will: str) -> List[str]:
    s = str(active_will or "")
    if "稳健避险" in s or "保守" in s:
        return ["宜收缩", "根基动摇", "隐忧"]
    if "激进求财" in s or "进取" in s:
        return ["博取", "动中求财", "势在必得"]
    return []


def _extract_will_weight(metadata: Dict[str, Any], physics_tensor: Dict[str, Any]) -> float:
    md = _as_dict(metadata)
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = _as_dict(pt.get("meta"))
    bundle = _as_dict(meta.get("semantic_label_bundle_v1"))
    for src in (
        bundle,
        _as_dict(meta.get("intention_context")),
        _as_dict(_as_dict(md.get("persistence_layer")).get("will_intention_context")),
    ):
        if not isinstance(src, dict):
            continue
        for k in ("will_weight", "intention_weight", "will_score", "will_strength"):
            if k in src:
                try:
                    return max(0.0, min(1.0, float(src.get(k))))
                except (TypeError, ValueError):
                    pass
    mults = _as_dict(_as_dict(meta.get("intention_context")).get("pattern_affinity_multipliers"))
    if mults:
        try:
            peak = max(float(v) for v in mults.values())
            # 经验缩放：1.0->0.5，1.6->0.8，2.0->1.0
            return max(0.0, min(1.0, (peak - 1.0) / 1.25 + 0.5))
        except Exception:
            return 0.0
    return 0.0


def _infer_style_mode(metadata: Dict[str, Any], physics_tensor: Dict[str, Any]) -> str:
    md = _as_dict(metadata)
    li = _as_dict(md.get("logic_introspection"))
    manual = str(li.get("narrative_style") or md.get("narrative_style") or "").strip().lower()
    if manual in {"ziping_classical", "modern_workplace"}:
        return manual
    hit = str(_as_dict(physics_tensor.get("meta")).get("hit_pattern_name") or "")
    if "官" in hit or "杀" in hit:
        return "modern_workplace"
    return "ziping_classical"


def build_style_anchor(physics_tensor: Dict[str, Any], metadata: Dict[str, Any]) -> Tuple[str, str]:
    mode = _infer_style_mode(metadata, physics_tensor)
    if mode == "modern_workplace":
        return (
            mode,
            "风格锚点：职场现代。语言直白、决策导向、强调代价与执行。"
            "禁止使用干支古语（如“气机”）与术语“化解/冲克/大运”，"
            "统一改写为“能量结构/对冲策略/负向反馈/时间周期”。",
        )
    return mode, "风格锚点：子平古语。辞气凝练、象法入断、重骨法与气势。"


def adapt_lines_for_style(lines: List[str], style_mode: str) -> List[str]:
    mode = str(style_mode or "").strip().lower()
    out = [str(x or "") for x in (lines or []) if str(x or "").strip()]
    if mode != "modern_workplace":
        return out
    replace_map = {
        "气机": "能量结构",
        "命局": "结构态势",
        "格门": "结构门槛",
        "象法": "结构语义",
        "化解": "对冲策略",
        "冲克": "负向反馈",
        "大运": "时间周期",
    }
    cooked: List[str] = []
    for ln in out:
        s = ln
        for k, v in replace_map.items():
            s = s.replace(k, v)
        cooked.append(s)
    return cooked


def build_data_imagery_mapping_lines(physics_tensor: Dict[str, Any], metadata: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    md = _as_dict(metadata)
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = _as_dict(pt.get("meta"))
    tc = _as_dict(md.get("temporal_context"))
    season = str(meta.get("season") or tc.get("season") or tc.get("season_name") or "").strip().lower()

    water = _find_energy(pt, "water")
    fire = _find_energy(pt, "fire")
    metal = _find_energy(pt, "metal")
    wood = _find_energy(pt, "wood")
    earth = _find_energy(pt, "earth")

    if water > 10 and ("winter" in season or "冬" in season):
        out.append("寒湿、冷寂、潜藏")
    if fire > 10 and ("summer" in season or "夏" in season):
        out.append("燥烈、外放、急进")
    if wood > 10:
        out.append("生发、扩张、求变")
    if metal > 10:
        out.append("规整、决断、收束")
    if earth > 10:
        out.append("承载、稳守、迟滞")

    tension = _as_float(meta.get("tension_index") or _as_dict(meta.get("causal_routing")).get("tension_index"))
    if tension >= 0.7:
        out.append("拉扯并存、进退两难")
    elif 0 < tension <= 0.25:
        out.append("气机平顺、可稳步推进")

    cm = _as_dict(md.get("conflict_matrix"))
    points = cm.get("points") if isinstance(cm.get("points"), list) else []
    conflict_blob = " ".join(str(_as_dict(p).get("detail") or "") for p in points if isinstance(p, dict))
    conflict_map = {
        "寅巳穿": "效率折损、内部损耗",
        "穿": "暗耗加剧、执行折损",
        "冲": "节奏破局、关系拉扯",
        "刑": "自我牵制、反复内耗",
        "害": "隐性掣肘、信任磨损",
    }
    for k, v in conflict_map.items():
        if k and k in conflict_blob:
            out.append(v)
    active_will = _extract_active_will(md, pt)
    will_weight = _extract_will_weight(md, pt)
    will_terms = _will_coloring_terms(active_will)
    if will_terms:
        out.insert(0, f"意志色彩({active_will})：" + "、".join(will_terms))
    if will_terms and will_weight > 0.8:
        out.insert(0, f"CRITICAL_WILL_OVERRIDE={active_will}|weight={will_weight:.2f}|裁断首句必须体现：{'、'.join(will_terms[:2])}")
    return list(dict.fromkeys([x for x in out if x]))


def build_pattern_specialized_prompt_lines(physics_tensor: Dict[str, Any]) -> List[str]:
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = _as_dict(pt.get("meta"))
    hit = str(meta.get("hit_pattern_name") or meta.get("l2_pattern_result_summary_v1") or "").strip()
    s = hit.lower()
    lines: List[str] = []
    if "财格" in hit or "wealth" in s:
        lines.append("若判为财格，必须围绕“损益得失、进退取舍、财路开合”展开。")
    if "官格" in hit or "杀格" in hit or "official" in s:
        lines.append("若判为官格/官杀格，必须谈“贵贱位序、名责压力、规则代价”。")
    if "食伤" in hit or "食神" in hit or "伤官" in hit:
        lines.append("若判为食伤格，必须谈“才华施展、表达代价、折损边界”。")
    return lines


def translate_to_human_terms(physics_meta: Dict[str, Any]) -> List[str]:
    """V13.50：将 branch_interaction_audit 等技术字段翻译为可读「气场冲突描述」。"""
    meta = _as_dict(physics_meta)
    raw = meta.get("branch_interaction_audit")
    rows = raw if isinstance(raw, list) else []
    out: List[str] = []
    for row in rows[:16]:
        r = _as_dict(row)
        relation = str(r.get("relation") or r.get("kind") or r.get("type") or "").strip()
        detail = str(r.get("detail") or r.get("summary") or "").strip()
        impact = str(r.get("impact") or r.get("effect") or "").strip()
        if detail:
            detail = _TECH_FACT_ID_RE.sub("气场剧震", detail)
        if relation:
            relation = _TECH_FACT_ID_RE.sub("气场剧震", relation)
        if impact:
            impact = _TECH_FACT_ID_RE.sub("气场剧震", impact)
        parts = [x for x in (relation, detail, impact) if x]
        if not parts:
            out.append("气场冲突描述：气场剧震")
            continue
        line = "气场冲突描述：" + "；".join(parts)
        line = _TECH_FACT_ID_RE.sub("气场剧震", line)
        out.append(line)
    if not out and isinstance(meta.get("branch_interaction_summary"), str):
        s = str(meta.get("branch_interaction_summary") or "").strip()
        if s:
            out.append("气场冲突描述：" + _TECH_FACT_ID_RE.sub("气场剧震", s))
    if not out:
        out.append("气场冲突描述：气场剧震")
    return out

