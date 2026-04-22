from __future__ import annotations

from typing import Any, Dict, List

_VALID_ARBITERS = {"system", "llm", "user"}


def _normalized(value: Any) -> str:
    return str(value or "").strip().lower()


def _default_arbiter_for_severity(severity: str) -> str:
    value = str(severity or "").strip().upper()
    if value == "P1":
        return "user"
    if value == "P2":
        return "llm"
    return "system"


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _normalize_weight_map(raw: Any) -> Dict[str, float]:
    if not isinstance(raw, dict):
        return {name: 0.0 for name in _VALID_ARBITERS}
    normalized: Dict[str, float] = {}
    total = 0.0
    for name in _VALID_ARBITERS:
        value = _safe_float(raw.get(name))
        normalized[name] = max(0.0, value)
        total += normalized[name]
    if total <= 0.0:
        return {name: 0.0 for name in _VALID_ARBITERS}
    return {name: normalized[name] / total for name in _VALID_ARBITERS}


def _choose_best_arbiter(scores: Dict[str, float], fallback: str) -> str:
    best = fallback
    best_score = _safe_float(scores.get(fallback))
    for name, value in scores.items():
        if name not in _VALID_ARBITERS:
            continue
        score = _safe_float(value)
        if score > best_score + 0.015:
            best_score = score
            best = name
    return best


def _base_policy_score(row: Dict[str, Any]) -> Dict[str, float]:
    severity = str(row.get("severity") or "P3").strip().upper()
    conflict_type = str(row.get("conflict_type") or "").strip().lower()

    # severity baseline: P1→user, P2→llm, P3→system
    if severity == "P1":
        base = {"system": 0.20, "llm": 0.34, "user": 0.81}
    elif severity == "P2":
        base = {"system": 0.38, "llm": 0.72, "user": 0.22}
    else:
        base = {"system": 0.80, "llm": 0.36, "user": 0.14}

    if severity == "P3":
        # 同事件轻冲突更偏 system；除非命中强逆向证据。
        if conflict_type in {"pattern_family_exclusive", "cross_layer_override"}:
            base = {"system": 0.66, "llm": 0.41, "user": 0.24}
        elif conflict_type in {"same_target_opposite_sign"}:
            base["system"] = 0.58
            base["llm"] = 0.44
    elif severity == "P2":
        if conflict_type in {"cross_layer_override", "pattern_family_exclusive"}:
            base = {"system": 0.31, "llm": 0.46, "user": 0.63}

    # 冲突类型是“同层同场逆向”时轻微提高 llm
    if conflict_type == "same_target_opposite_sign":
        base["llm"] = max(base["llm"], base["llm"] + 0.10)

    total = base["system"] + base["llm"] + base["user"]
    if total <= 0:
        return {"system": 1 / 3, "llm": 1 / 3, "user": 1 / 3}
    return {name: base[name] / total for name in _VALID_ARBITERS}


def _finalize_routing_reason(
    *,
    row: Dict[str, Any],
    resolved: str,
    explicit: str,
    scores: Dict[str, float],
    score: float,
) -> str:
    if explicit and explicit in _VALID_ARBITERS and explicit == resolved:
        return "显式路由保留（用户或外部策略已给定）；并融合会话偏好与反馈得分。"
    if resolved == "user" and (row.get("conflict_type") in {"cross_layer_override", "pattern_family_exclusive"} or str(row.get("severity") or "").strip().upper() == "P1"):
        return "高优先级或跨层/互斥冲突，转入人工审核。"
    if resolved == "llm" and score >= 0.82:
        return "中高强度冲突，基于反馈学习偏好与置信度转入 LLM 裁决。"
    if resolved == "system":
        return "低风险/低冲突批次默认系统处理，优先保持稳定。"
    return "基于严重度 + 会话学习评分的自动路由。"


def route_conflicts(
    *,
    conflicts: List[Dict[str, Any]],
    knowledge_snapshot: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    snapshot = knowledge_snapshot if isinstance(knowledge_snapshot, dict) else {}
    conflict_history = snapshot.get("conflict_history") if isinstance(snapshot.get("conflict_history"), dict) else {}
    claim_history = snapshot.get("claim_history") if isinstance(snapshot.get("claim_history"), dict) else {}
    current_targets = claim_history.get("current_targets") if isinstance(claim_history.get("current_targets"), dict) else {}
    preferred = conflict_history.get("recommended_arbiters") if isinstance(conflict_history.get("recommended_arbiters"), dict) else {}
    feedback_preference = conflict_history.get("feedback_arbiters") if isinstance(conflict_history.get("feedback_arbiters"), dict) else {}
    feedback_scores = conflict_history.get("feedback_arbiter_scores") if isinstance(conflict_history.get("feedback_arbiter_scores"), dict) else {}

    normalized_preferred = _normalize_weight_map(preferred)
    normalized_feedback_preference = _normalize_weight_map(feedback_preference)
    feedback_scores_norm = {
        name: _clamp(_safe_float(value), -2.0, 2.0)
        for name, value in feedback_scores.items()
    }

    def _weighted_score(name: str) -> float:
        base = _safe_float(normalized_preferred.get(name))
        pref = _safe_float(normalized_feedback_preference.get(name))
        score = _safe_float(feedback_scores_norm.get(name))
        # 经验系数：优先采用比例化计数，再叠加残差质量
        return 0.55 * base + 0.30 * pref + 0.30 * (0.5 + 0.25 * score)

    has_session_preference = any(_safe_float(v) > 0.0 for v in normalized_preferred.values())
    has_feedback_preference = any(_safe_float(v) > 0.0 for v in normalized_feedback_preference.values())
    has_feedback_scores = any(_safe_float(v) != 0.0 for v in feedback_scores_norm.values())
    has_feedback = has_feedback_preference or has_feedback_scores

    out: List[Dict[str, Any]] = []
    for row in conflicts:
        cloned = dict(row)
        severity = str(cloned.get("severity") or "").strip().upper()
        explicit = _normalized(cloned.get("recommended_arbiter"))
        explicit = explicit if explicit in _VALID_ARBITERS else ""
        resolved = explicit or _default_arbiter_for_severity(severity)
        try:
            score = float(cloned.get("conflict_score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        score = _clamp(float(score or 0.0), 0.0, 1.0)

        conflict_type = str(cloned.get("conflict_type") or "").strip().lower()
        target_god = _normalized(cloned.get("target_god"))
        target_state = current_targets.get(target_god) if isinstance(current_targets.get(target_god), dict) else {}
        live_tension = _safe_float(target_state.get("flux_tension_load"))
        live_reinforce = _safe_float(target_state.get("flux_reinforce_load"))
        live_contest = _safe_float(target_state.get("contest_pressure"))
        live_judgement_use = _safe_float(target_state.get("judgement_use_bias"))
        live_judgement_taboo = _safe_float(target_state.get("judgement_taboo_bias"))
        live_judgement_entries = _safe_float(target_state.get("judgement_entry_count"))
        live_stage_use = _safe_float(target_state.get("stage_use_boost"))
        live_stage_taboo = _safe_float(target_state.get("stage_taboo_boost"))
        live_stage_stability = _safe_float(target_state.get("stage_stability_boost"))
        live_stage_volatility = _safe_float(target_state.get("stage_volatility_boost"))
        authority_profile = _normalized(target_state.get("authority_profile"))
        # 基础策略 -> 会话学习反馈 -> 置信度后处理
        base_scores = _base_policy_score(cloned)
        candidate_scores: Dict[str, float] = {}
        for name in _VALID_ARBITERS:
            policy_score = _safe_float(base_scores.get(name))
            history_score = 0.40 * _weighted_score(name)
            conflict_boost = score * 0.22 if name == "llm" else score * 0.12
            if conflict_type == "cross_layer_override" and name == "user":
                conflict_boost = max(conflict_boost, 0.20)
            if conflict_type == "pattern_family_exclusive" and name == "user":
                conflict_boost = max(conflict_boost, 0.16)
            if conflict_type == "same_target_opposite_sign":
                if name == "llm":
                    conflict_boost += min(0.26, live_tension * 0.58 + live_contest * 0.10)
                    conflict_boost += min(0.16, min(live_judgement_use, live_judgement_taboo) * 0.42 + live_judgement_entries * 0.03)
                elif name == "user" and live_tension >= 0.42:
                    conflict_boost += min(0.18, live_tension * 0.22)
                    if authority_profile == "高能躁动":
                        conflict_boost += min(0.12, live_stage_volatility * 0.24 + live_judgement_entries * 0.02)
                elif name == "system":
                    conflict_boost -= min(0.16, live_tension * 0.34)
                    conflict_boost -= min(0.08, min(live_judgement_use, live_judgement_taboo) * 0.18)
            if conflict_type == "pattern_family_exclusive" and name == "llm":
                conflict_boost += min(0.16, live_tension * 0.32)
                conflict_boost += min(0.14, live_judgement_entries * 0.04 + (live_judgement_use + live_judgement_taboo) * 0.14)
            if conflict_type == "pattern_family_exclusive" and name == "user" and authority_profile == "高能躁动":
                conflict_boost += min(0.12, live_stage_volatility * 0.22 + live_tension * 0.08)
            if conflict_type == "same_event_duplicate" and name == "system":
                conflict_boost += min(0.08, live_stage_stability * 0.12 + max(live_stage_use, live_stage_taboo) * 0.08)
            if severity == "P1" and name == "user":
                conflict_boost += 0.24
            if severity == "P3" and name == "system":
                conflict_boost += 0.10
            candidate_scores[name] = _clamp(policy_score + history_score + conflict_boost, 0.0, 1.3)

        best = _choose_best_arbiter(candidate_scores, fallback=resolved)

        # 明确规则兜底：P1/跨层互斥必须走人工，除非明确指定用户外部输入为 system/llm。
        if (
            (severity == "P1")
            or conflict_type in {"cross_layer_override", "pattern_family_exclusive"}
        ) and not explicit:
            best = "user"

        # 系统显式标签不再强制占用路由位，避免把“默认/回退”意见误写死。
        # 人工与 LLM 显式仍按建议保留，但保留给系统的兜底仅在没有更强学习偏好的情况下。
        if explicit == "user":
            best = explicit
        elif explicit == "llm":
            if not (
                severity in {"P1"}
                or (
                    has_feedback
                    and _safe_float(candidate_scores.get("system", 0.0))
                    > _safe_float(candidate_scores.get("llm", 0.0)) + 0.25
                )
            ):
                best = explicit

        resolved = best if best in _VALID_ARBITERS else resolved
        resolved = resolved if resolved in _VALID_ARBITERS else "system"

        system_score = _weighted_score("system")
        llm_score = _weighted_score("llm")
        user_score = _weighted_score("user")

        cloned["recommended_arbiter"] = resolved
        cloned["routing_reason"] = _finalize_routing_reason(
            row=cloned,
            resolved=resolved,
            explicit=explicit,
            scores={"system": system_score, "llm": llm_score, "user": user_score},
            score=score,
        )
        cloned["routing_policy"] = (
            "severity_plus_feedback_pref"
            if has_feedback
            else "severity_plus_session_preference"
        )
        cloned["routing_scores"] = {
            "system": round(system_score, 6),
            "llm": round(llm_score, 6),
            "user": round(user_score, 6),
            "final_system": round(_safe_float(candidate_scores.get("system")), 6),
            "final_llm": round(_safe_float(candidate_scores.get("llm")), 6),
            "final_user": round(_safe_float(candidate_scores.get("user")), 6),
            "conflict_score": round(score, 6),
            "live_tension": round(live_tension, 6),
            "live_reinforce": round(live_reinforce, 6),
            "live_contest": round(live_contest, 6),
            "live_judgement_use": round(live_judgement_use, 6),
            "live_judgement_taboo": round(live_judgement_taboo, 6),
            "live_judgement_entries": round(live_judgement_entries, 6),
            "live_stage_use": round(live_stage_use, 6),
            "live_stage_taboo": round(live_stage_taboo, 6),
            "live_stage_stability": round(live_stage_stability, 6),
            "live_stage_volatility": round(live_stage_volatility, 6),
        }
        cloned["live_target_tension"] = round(live_tension, 4)
        cloned["live_target_reinforce"] = round(live_reinforce, 4)
        cloned["live_target_contest"] = round(live_contest, 4)
        cloned["live_target_judgement_use"] = round(live_judgement_use, 4)
        cloned["live_target_judgement_taboo"] = round(live_judgement_taboo, 4)
        cloned["live_target_judgement_entries"] = round(live_judgement_entries, 4)
        cloned["live_target_stage_use"] = round(live_stage_use, 4)
        cloned["live_target_stage_taboo"] = round(live_stage_taboo, 4)
        cloned["live_target_stage_stability"] = round(live_stage_stability, 4)
        cloned["live_target_stage_volatility"] = round(live_stage_volatility, 4)
        out.append(cloned)
    return out
