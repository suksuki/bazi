from __future__ import annotations

from v20.core.context_frame import build_context_binding
from v20.role_view.narrative_prompt_framework import (
    answer_prompt_profile_for_role,
    question_narrative_for_question,
)
from v20.role_view.policy import GUEST_QUESTION_TITLES, POLICY_VERSION, role_view_policy


def apply_role_question_view(
    payload: dict[str, object],
    role_key: str,
    *,
    runtime_pointer: dict[str, object] | None = None,
) -> dict[str, object]:
    policy = role_view_policy(role_key)
    projected = dict(payload)
    questions = [_role_question(row, role_key) for row in projected.get("questions", ()) if isinstance(row, dict)]
    questions = _apply_runtime_question_policy(questions, role_key, runtime_pointer or {})
    projected["questions"] = questions[: policy.question_limit]
    selected = projected.get("selected_question")
    if isinstance(selected, dict):
        projected["selected_question"] = _role_question(selected, role_key)
    return projected


def build_role_view_model(
    result: dict[str, object],
    role_key: str,
    *,
    runtime_pointer: dict[str, object] | None = None,
) -> dict[str, object]:
    return _build_role_view_model(result, role_key, runtime_pointer=runtime_pointer)


def _build_role_view_model(
    result: dict[str, object],
    role_key: str,
    *,
    runtime_pointer: dict[str, object] | None = None,
) -> dict[str, object]:
    policy = role_view_policy(role_key)
    axes = _portrait_axes(result)
    role_axes = [_role_axis(row, role_key) for row in axes[: policy.portrait_limit]]
    context_binding = build_context_binding(
        result.get("bazi_context_frame", {}) if isinstance(result.get("bazi_context_frame"), dict) else {},
        module_key="role_view_model",
        evidence_domains=tuple(str(row.get("domain", "")) for row in role_axes if isinstance(row, dict)),
        feature_ids=tuple(feature_id for row in role_axes if isinstance(row, dict) for feature_id in row.get("feature_ids", ())),
        time_sensitive=any(str(row.get("domain", "")) == "time" for row in role_axes if isinstance(row, dict)),
    )
    return {
        "version": "v20.role_view_model.v1",
        "policy_version": POLICY_VERSION,
        "role_key": policy.role_key,
        "context_binding": context_binding,
        "portrait_profile": {
            "version": "v20.role_portrait_profile.v1",
            "depth": policy.portrait_depth,
            "axis_count": len(role_axes),
            "axes": role_axes,
            "context_binding": context_binding,
            "runtime_mutation": False,
        },
        "question_profile": {
            "version": "v20.role_question_profile.v1",
            "style": policy.question_style,
            "question_limit": policy.question_limit,
            "voice_profile": question_narrative_for_question({}, role_key)["voice_profile"],
            "context_binding": context_binding,
            "runtime_mutation": False,
        },
        "explanation_profile": {
            "version": "v20.role_explanation_profile.v1",
            "style": policy.explanation_style,
            "answer_prompt_profile": answer_prompt_profile_for_role(role_key),
            "runtime_mutation": False,
        },
        "answer_governance_profile": _answer_governance_profile(result, role_key, runtime_pointer=runtime_pointer or {}),
        "visibility_profile": {
            "version": "v20.role_visibility_profile.v1",
            "level": policy.visibility_level,
            "runtime_mutation": False,
        },
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_VIEW_MODEL_DOES_NOT_CHANGE_CHART_FACTS",
            "ROLE_PORTRAIT_IS_PROJECTION_ONLY",
            "ROLE_QUESTIONS_ARE_VIEW_LAYER_ONLY",
            "ROLE_VIEW_INHERITS_BAZI_CONTEXT_BINDING",
        ],
    }


def apply_role_answer_view(
    payload: dict[str, object],
    role_key: str,
    role_view_model: dict[str, object],
    *,
    source_answer: str = "deterministic_answer_text",
) -> dict[str, object]:
    text = payload.get("answer_text")
    if not isinstance(text, str) or not text.strip():
        return payload
    projected = dict(payload)
    governance = role_view_model.get("answer_governance_profile", {})
    projected["answer_text"] = _role_answer_text(text, role_key, governance if isinstance(governance, dict) else {})
    projected["role_answer_profile"] = {
        "version": "v20.role_answer_profile.v1",
        "role_key": role_view_policy(role_key).role_key,
        "explanation_style": _profile_value(role_view_model, "explanation_profile", "style"),
        "answer_governance_profile": governance if isinstance(governance, dict) else {},
        "source_answer": source_answer,
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_ANSWER_IS_VIEW_PROJECTION_ONLY",
            "ROLE_ANSWER_DOES_NOT_CHANGE_CHART_FACTS",
            "ANSWER_GOVERNANCE_STYLE_IS_VIEW_POLICY_ONLY",
        ],
    }
    return projected


def _role_question(question: dict[str, object], role_key: str) -> dict[str, object]:
    row = dict(question)
    original_title = str(row.get("display_title", "") or row.get("title", ""))
    domain = str(row.get("domain", ""))
    source_decision_key = str(row.get("source_decision_key", ""))
    row["source_title"] = original_title
    if source_decision_key.startswith("seed."):
        row["seed_source_key"] = source_decision_key
    if row.get("display_title"):
        row["display_title"] = _role_display_title(row, role_key)
        row["title"] = row["display_title"]
        if role_key == "guest":
            row["question_strategy"] = "guest_entry_question"
            row["role_view_level"] = "entry"
        elif role_key == "user":
            row["question_strategy"] = row.get("question_strategy", "") or "guided_user_question"
            row["role_view_level"] = "guided"
        elif role_key == "analyst":
            row["question_strategy"] = "practitioner_review_question"
            row["role_view_level"] = "technical_review"
        else:
            row["role_view_level"] = "full_observation"
    elif role_key == "guest":
        row["title"] = GUEST_QUESTION_TITLES.get(domain, "先看当前结构最需要关注什么？")
        row["question_strategy"] = "guest_entry_question"
        row["role_view_level"] = "entry"
    elif role_key == "user":
        row["title"] = _user_question_title(original_title, domain)
        row["question_strategy"] = row.get("question_strategy", "") or "guided_user_question"
        row["role_view_level"] = "guided"
    elif role_key == "analyst":
        row["title"] = _analyst_question_title(original_title)
        row["question_strategy"] = "practitioner_review_question"
        row["role_view_level"] = "technical_review"
    else:
        row["role_view_level"] = "full_observation"
    row["role_view_source"] = "role_question_projection"
    row["question_narrative"] = question_narrative_for_question(row, role_key)
    return row


def _role_display_title(row: dict[str, object], role_key: str) -> str:
    display_title = str(row.get("display_title", "") or row.get("title", "")).strip()
    anchor = row.get("question_anchor", {})
    if not isinstance(anchor, dict):
        anchor = {}
    day_master = str(anchor.get("day_master", "")).strip()
    chain = str(anchor.get("primary_dynamic_chain_label", "")).strip()
    time_parts = [
        f"{anchor.get('luck_pillar')}大运" if anchor.get("luck_pillar") else "",
        f"{anchor.get('flow_year_pillar')}流年" if anchor.get("flow_year_pillar") else "",
    ]
    time_text = "、".join(row for row in time_parts if row)
    if role_key == "guest":
        basis = chain or str(row.get("measurement_topic", "") or row.get("domain", ""))
        prefix = f"这盘{day_master}日主" if day_master else "这盘"
        time_suffix = f"，结合{time_text}" if time_text else ""
        return _guest_display_title(row, prefix=prefix, basis=basis, time_suffix=time_suffix)
    if role_key in {"analyst", "practitioner"} and chain:
        if display_title:
            return display_title
        prefix = f"证据检查：{day_master}日主" if day_master else "证据检查：当前原局"
        time_suffix = f"；{time_text}" if time_text else ""
        return f"{prefix} / {chain}{time_suffix}，当前问题证据是否闭合？"
    return display_title


def _guest_display_title(row: dict[str, object], *, prefix: str, basis: str, time_suffix: str) -> str:
    domain = str(row.get("domain", ""))
    if domain == "useful_god":
        return f"{prefix}先看「{basis}」{time_suffix}，调节方向该从哪里入手？"
    if domain == "time":
        return f"{prefix}先看「{basis}」{time_suffix}，最近更容易被哪件事牵动？"
    if domain == "career":
        return f"{prefix}先看「{basis}」{time_suffix}，事业压力和机会哪个更明显？"
    if domain == "wealth":
        return f"{prefix}先看「{basis}」{time_suffix}，财运机会和承接哪个要先确认？"
    if domain == "relationship":
        return f"{prefix}先看「{basis}」{time_suffix}，关系互动和边界哪个更要紧？"
    return f"{prefix}先从「{basis}」看起{time_suffix}，下一步确认什么？"


def _apply_runtime_question_policy(
    questions: list[dict[str, object]],
    role_key: str,
    runtime_pointer: dict[str, object],
) -> list[dict[str, object]]:
    if not runtime_pointer.get("runtime_applied"):
        return questions
    scored: list[tuple[float, int, dict[str, object]]] = []
    for index, question in enumerate(questions):
        boost = _runtime_question_boost(question, role_key, runtime_pointer)
        row = dict(question)
        if boost:
            row["role_view_policy_boost"] = round(boost, 3)
        scored.append((boost, -index, row))
    return [row for _boost, _index, row in sorted(scored, key=lambda item: item[:2], reverse=True)]


def _runtime_question_boost(question: dict[str, object], role_key: str, runtime_pointer: dict[str, object]) -> float:
    payload = runtime_pointer.get("policy_payload", {})
    if not isinstance(payload, dict):
        return 0.0
    boost = 0.0
    domain = str(question.get("domain", ""))
    strategy = str(question.get("question_strategy", ""))
    seed_key = str(question.get("seed_source_key", ""))
    for row in _policy_rows(payload, "domain_boost_policy", role_key):
        if str(row.get("boost_key", "")) == domain:
            boost += 0.18
    for row in _policy_rows(payload, "strategy_boost_policy", role_key):
        if str(row.get("boost_key", "")) == strategy:
            boost += 0.14
    for row in _policy_rows(payload, "seed_fit_policy", role_key):
        if seed_key and str(row.get("seed_key", "")) == seed_key:
            boost += 0.24
    return boost


def _policy_rows(payload: dict[str, object], policy_key: str, role_key: str) -> list[dict[str, object]]:
    rows = payload.get(policy_key, ())
    if not isinstance(rows, list):
        return []
    return [
        row for row in rows
        if isinstance(row, dict) and str(row.get("source_role", "")) == role_key
    ]


def _role_answer_text(text: str, role_key: str, governance: dict[str, object] | None = None) -> str:
    paragraphs = _answer_paragraphs(text)
    governance_line = _role_governance_line(role_key, governance or {})
    if role_key == "guest":
        body = _plain_entry_text(paragraphs)
        return _join_answer_parts("游客简读：先看当前最容易理解的重点。", governance_line, body)
    if role_key == "user":
        return _join_answer_parts("用户解读：下面按当前问题给出重点和边界。", governance_line, text.strip())
    if role_key == "analyst":
        return _join_answer_parts("命理师复核：以下保留结构主线、证据边界和复核口径。", governance_line, text.strip())
    if role_key == "admin":
        return _join_answer_parts("系统观测：以下为角色投影后的完整答案视图，底层事实和中枢判断未被改写。", governance_line, text.strip())
    return text.strip()


def _answer_governance_profile(
    result: dict[str, object],
    role_key: str,
    *,
    runtime_pointer: dict[str, object],
) -> dict[str, object]:
    assist = result.get("llm_assist", {})
    review = assist.get("answer_safety_review", {}) if isinstance(assist, dict) else {}
    quality = review.get("answer_governance_quality", {}) if isinstance(review, dict) else {}
    if not isinstance(quality, dict):
        quality = {}
    dimensions = quality.get("dimensions", {})
    if not isinstance(dimensions, dict):
        dimensions = {}
    score = float(quality.get("quality_score", 0.0) or 0.0)
    band = str(quality.get("quality_band", "")) or "unknown"
    runtime_style = _runtime_answer_governance_style(role_key, runtime_pointer)
    style_policy = str(runtime_style.get("style_policy", "")) or _governance_style_policy(role_key, band)
    style_weight = float(runtime_style.get("style_weight_delta", 0.0) or 0.0)
    return {
        "version": "v20.role_answer_governance_profile.v1",
        "role_key": role_view_policy(role_key).role_key,
        "quality_score": score,
        "quality_band": band,
        "boundary_density": _boundary_density(role_key, score),
        "evidence_density": _evidence_density(role_key, dimensions),
        "next_step_density": _next_step_density(role_key, dimensions),
        "style_policy": style_policy,
        "runtime_style_weight_delta": round(style_weight, 4),
        "runtime_style_policy_applied": bool(runtime_style),
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_ANSWER_GOVERNANCE_PROFILE_IS_VIEW_LAYER",
            "NO_CHART_FACT_MUTATION",
            "ROLE_ANSWER_GOVERNANCE_RUNTIME_WEIGHT_CONSUMED",
        ],
    }


def _runtime_answer_governance_style(role_key: str, runtime_pointer: dict[str, object]) -> dict[str, object]:
    payload = runtime_pointer.get("policy_payload", {}) if isinstance(runtime_pointer, dict) else {}
    if not isinstance(payload, dict):
        return {}
    rows = payload.get("answer_governance_style_policy", ())
    if not isinstance(rows, list):
        return {}
    for row in rows:
        if isinstance(row, dict) and str(row.get("source_role", "")) == role_key:
            return row
    return {}


def _boundary_density(role_key: str, score: float) -> str:
    if role_key == "guest":
        return "plain_boundary"
    if role_key == "analyst":
        return "technical_boundary_review"
    if role_key in {"admin", "lab"}:
        return "full_boundary_observation"
    return "guided_boundary"


def _evidence_density(role_key: str, dimensions: dict[str, object]) -> str:
    has_evidence = float(dimensions.get("evidence_language", 0.0) or 0.0) > 0
    if role_key == "guest":
        return "plain_evidence" if has_evidence else "plain_evidence_required"
    if role_key == "analyst":
        return "evidence_and_counterevidence"
    if role_key in {"admin", "lab"}:
        return "full_evidence_observation"
    return "guided_evidence"


def _next_step_density(role_key: str, dimensions: dict[str, object]) -> str:
    has_next = float(dimensions.get("next_step_guidance", 0.0) or 0.0) > 0
    if role_key == "guest":
        return "one_plain_next_step" if has_next else "one_plain_next_step_required"
    if role_key == "analyst":
        return "review_next_step"
    if role_key in {"admin", "lab"}:
        return "full_next_step_observation"
    return "guided_next_step"


def _governance_style_policy(role_key: str, band: str) -> str:
    if band in {"weak", "thin"}:
        return "increase_boundary_and_next_step"
    if role_key == "guest":
        return "compress_to_plain_boundary"
    if role_key == "analyst":
        return "preserve_review_boundary"
    if role_key in {"admin", "lab"}:
        return "preserve_full_governance_signal"
    return "preserve_guided_boundary"


def _role_governance_line(role_key: str, governance: dict[str, object]) -> str:
    policy = str(governance.get("style_policy", ""))
    trained = bool(governance.get("runtime_style_policy_applied"))
    if role_key == "guest":
        prefix = "训练边界" if trained else "阅读边界"
        return f"{prefix}：只看已经成立的结构线索，不当作确定结果。"
    if role_key == "user":
        prefix = "训练策略" if trained else "回答策略"
        return f"{prefix}：保留证据、边界和下一步复核，不输出确定事件。"
    if role_key == "analyst":
        score = governance.get("quality_score", 0)
        band = governance.get("quality_band", "")
        weight = governance.get("runtime_style_weight_delta", 0)
        return f"治理复核：答案边界质量 {band} / {score}，策略为 {policy or 'preserve_review_boundary'}，训练权重 {weight}。"
    if role_key in {"admin", "lab"}:
        score = governance.get("quality_score", 0)
        band = governance.get("quality_band", "")
        weight = governance.get("runtime_style_weight_delta", 0)
        return f"治理观测：answer_governance_quality={band}:{score}，style_policy={policy or '-'}，runtime_style_weight={weight}。"
    return ""


def _join_answer_parts(*parts: str) -> str:
    return "\n\n".join(str(part).strip() for part in parts if str(part or "").strip())


def _plain_entry_text(paragraphs: list[str]) -> str:
    selected = paragraphs[:3]
    if not selected:
        return "当前只展示入门层摘要，详细结构请进入用户或命理师视图。"
    cleaned = [_plain_entry_terms(row) for row in selected]
    return "\n\n".join(row for row in cleaned if row)


def _plain_entry_terms(text: str) -> str:
    replacements = {
        "命局": "结构",
        "日主": "自身承接力",
        "官杀": "压力和规则",
        "食伤": "表达和输出",
        "印星": "支持和缓冲",
        "比劫": "自身力量",
        "财星": "资源和机会",
        "用神": "适合补强的方向",
        "十神": "结构关系",
        "复核": "再确认",
    }
    cleaned = text
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)
    return cleaned


def _answer_paragraphs(text: str) -> list[str]:
    return [row.strip() for row in str(text or "").split("\n\n") if row.strip()]


def _profile_value(role_view_model: dict[str, object], profile_key: str, value_key: str) -> str:
    profile = role_view_model.get(profile_key)
    if not isinstance(profile, dict):
        return ""
    return str(profile.get(value_key, ""))


def _user_question_title(title: str, domain: str) -> str:
    if not title:
        return "你可以先看当前最明显的主题。"
    if domain in {"career", "wealth", "relationship", "time"}:
        return f"你可以先看：{title}"
    return title


def _analyst_question_title(title: str) -> str:
    if not title:
        return "证据检查：当前主线证据和边界是否闭合？"
    return title if title.startswith("证据检查") else f"证据检查：{title}"


def _portrait_axes(result: dict[str, object]) -> list[dict[str, object]]:
    report = result.get("decision_report", {})
    if not isinstance(report, dict):
        return []
    portrait = report.get("portrait_projection", {})
    if not isinstance(portrait, dict):
        return []
    return [row for row in portrait.get("axes", ()) if isinstance(row, dict)]


def _role_axis(axis: dict[str, object], role_key: str) -> dict[str, object]:
    if role_key == "guest":
        return {
            "label": axis.get("label", axis.get("axis_id", "")),
            "summary": axis.get("summary", ""),
            "domain": axis.get("domain", ""),
            "role_view_level": "entry",
        }
    if role_key == "user":
        return {
            "label": axis.get("label", axis.get("axis_id", "")),
            "summary": axis.get("summary", ""),
            "domain": axis.get("domain", ""),
            "confidence": axis.get("confidence", 0),
            "role_view_level": "guided",
        }
    if role_key == "analyst":
        return {
            "axis_id": axis.get("axis_id", ""),
            "label": axis.get("label", ""),
            "summary": axis.get("summary", ""),
            "domain": axis.get("domain", ""),
            "confidence": axis.get("confidence", 0),
            "evidence_boundaries": axis.get("evidence_boundaries", ()),
            "role_view_level": "technical_review",
        }
    return dict(axis) | {"role_view_level": "full_observation"}
