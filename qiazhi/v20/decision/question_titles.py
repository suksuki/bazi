from __future__ import annotations

from collections.abc import Callable

from v20.answer.measurement_policy import domain_label


def runtime_decision_question_title(
    domain: str,
    decision: dict[str, object],
    *,
    question_key: str = "",
    explicit_title: Callable[[str], str] | None = None,
) -> str:
    if question_key in {"q_strength_assessment", "q_useful_god_candidates", "q_health_balance_boundary"} and explicit_title is not None:
        return explicit_title(question_key)
    state = str(decision.get("structural_state", "candidate"))
    core = _fusion_state_prefix(state)
    label = _runtime_public_label(domain, decision)
    evidence = tuple(
        row
        for row in (
            _runtime_public_evidence(str(item))
            for item in decision.get("evidence_summary", ())
            if str(item)
        )
        if row
    )
    boundary = _runtime_public_boundary(str(decision.get("user_facing_boundary", "")).strip())
    if not label:
        return _runtime_domain_question(domain, state)
    if evidence:
        return f"{_trim_signature(label)}。{_trim_signature(evidence[0])}更先观察哪一步？"
    if label == _runtime_domain_label(domain, state):
        return _runtime_domain_question(domain, state)
    if boundary:
        return f"{_trim_signature(label)}。{_trim_signature(boundary)}"
    return f"{core}{_trim_signature(label)}，先核对证据和反向约束。"


def portrait_tag_question_title(axis: dict[str, object]) -> str:
    domain = str(axis.get("domain", ""))
    tag = str(axis.get("structural_anchor", "")).strip() or str(axis.get("label", "")).strip() or domain_label(domain)
    tags = tuple(str(row) for row in axis.get("profile_tags", ()) if str(row))
    focus = "、".join(tags[1:3] or tags[:2] or (domain_label(domain),))
    axis_tier = str(axis.get("axis_tier", "macro"))
    axis_state = str(axis.get("axis_state", "candidate"))
    tier_title = {
        "micro": "先读这条骨架轴",
        "decision": "先读这条裁决路径",
        "macro": "先读这条场景轴",
        "time": "先读这条时序轴",
    }.get(axis_tier, "先读这条结构轴")
    state_phrase = {
        "confirmed": "结构较稳",
        "chain_review": "链条牵引",
        "mixed": "成而不纯",
        "candidate": "候选成立",
        "weak_candidate": "偏弱成立",
        "requires_review": "低置信定向",
        "volatile": "岁运引动",
        "countered": "反证干扰",
        "blocked": "范围受限",
    }.get(axis_state, "需确认")
    prefix = f"{tier_title}（{state_phrase}）"
    if domain == "wealth":
        return f"{prefix}，{tag}下先分财务机会、承接与竞争路径？"
    if domain == "career":
        return f"{prefix}，{tag}下先看角色压力、表达和缓冲结构？"
    if domain == "relationship":
        return f"{prefix}，{tag}下先看互动方式、现实承接与冲突处理？"
    if domain == "strength":
        return f"{prefix}，{tag}下先判断支撑、泄耗、通关先后？"
    if domain == "time":
        return f"{prefix}，{tag}下近期先看大运、流年、流月哪个更先牵动？"
    if domain == "useful_god":
        return f"{prefix}，{tag}下这个盘的用神和调节方向是什么？"
    if domain == "pattern":
        return f"{prefix}，{tag}下先看主轴是否清楚、做功是否连续？"
    if domain == "health":
        return f"{prefix}，{tag}下先看偏枯与压力分布？"
    if domain == "branch":
        return f"{prefix}，{tag}下先看冲合刑害中哪类牵动最大？"
    if domain == "element":
        return f"{prefix}，{tag}下先看偏旺、偏弱、失衡路径？"
    if domain == "ten_god":
        return f"{prefix}，{tag}下先看透出、藏干还是制化？"
    if domain == "romance":
        return f"{prefix}，{tag}下先看配偶关系、互动方式与现实约束？"
    if focus:
        return f"{prefix}，先围绕{focus}追问哪个方向？"
    return f"{prefix}，下一步先围绕哪条结构方向展开？"


def _fusion_state_prefix(state: str) -> str:
    return {
        "confirmed": "已形成",
        "candidate": "候选",
        "chain_review": "链式",
        "weak_candidate": "偏弱",
        "mixed": "并行",
        "volatile": "牵动",
        "requires_review": "低置信",
        "countered": "受反制",
        "blocked": "被拦截",
    }.get(state, "结构")


def _runtime_public_label(domain: str, decision: dict[str, object]) -> str:
    raw = str(decision.get("user_facing_decision", "")).strip()
    if not raw or _looks_like_rule_debug(raw):
        return _runtime_domain_label(domain, str(decision.get("structural_state", "")))
    return _sanitize_runtime_text(raw)


def _runtime_public_evidence(value: str) -> str:
    text = _sanitize_runtime_text(value)
    if not text or _looks_like_rule_debug(text):
        return ""
    return text


def _runtime_public_boundary(value: str) -> str:
    text = _sanitize_runtime_text(value)
    if not text or _looks_like_rule_debug(text):
        return ""
    return text


def _runtime_domain_label(domain: str, state: str) -> str:
    state_phrase = {
        "confirmed": "已经成形",
        "candidate": "方向成立",
        "weak_candidate": "偏弱成立",
        "mixed": "主次并存",
        "chain_review": "链条成形",
        "volatile": "被岁运牵动",
        "requires_review": "低置信定向",
        "countered": "存在反向约束",
        "blocked": "被结构压制",
    }.get(state, "已经定向")
    if domain == "wealth":
        return f"财富结构{state_phrase}"
    if domain == "career":
        return f"事业结构{state_phrase}"
    if domain == "relationship":
        return f"关系互动{state_phrase}"
    if domain == "strength":
        return f"日主承载轴{state_phrase}"
    if domain == "useful_god":
        return f"用神取向{state_phrase}"
    if domain == "pattern":
        return f"格局秩序轴{state_phrase}"
    if domain == "branch":
        return f"地支牵引轴{state_phrase}"
    if domain == "element":
        return f"五行气势轴{state_phrase}"
    if domain == "time":
        return f"岁运触发轴{state_phrase}"
    if domain == "health":
        return f"身心平衡轴{state_phrase}"
    return f"{domain_label(domain)}{state_phrase}"


def _runtime_domain_question(domain: str, state: str) -> str:
    label = _runtime_domain_label(domain, state)
    if domain == "wealth":
        return f"{label}，先看机会、承接还是波动？"
    if domain == "career":
        return f"{label}，先分角色压力、表达还是缓冲？"
    if domain == "relationship":
        return f"{label}，先看互动方式、现实承接还是冲突处理？"
    if domain == "pattern":
        return f"{label}，先看主轴、做功还是破局点？"
    if domain == "branch":
        return f"{label}，冲合刑害里哪类牵动最大？"
    if domain == "element":
        return f"{label}，偏旺偏弱先影响哪条主线？"
    if domain == "time":
        return f"{label}，先看大运、流年还是原局回响？"
    return f"{label}，下一步先看哪条结构？"


def _sanitize_runtime_text(value: str) -> str:
    text = str(value or "").strip()
    replacements = (
        ("当前主线入口，RuleSpec 裁决主线，主规则为", ""),
        ("RuleSpec 裁决主线，", ""),
        ("主规则为", ""),
        ("明确成立", "成立"),
        ("弱候选", "偏弱成立"),
        ("需复核", "低置信定向"),
        ("材料可见", "线索可见"),
        ("材料来源", "线索来源"),
        ("触发边界", "触发条件"),
        ("承接边界", "现实承接"),
        ("互动边界", "互动方式"),
        ("反制边界", "反向约束"),
        ("证据边界", "依据范围"),
        ("边界", "范围"),
        ("材料", "线索"),
        ("规则：", ""),
        ("规则", ""),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text.strip(" 。；;，,")


def _looks_like_rule_debug(value: str) -> bool:
    lowered = str(value or "").lower()
    return any(
        token in lowered
        for token in (
            "rulespec",
            "rule.",
            "feature:",
            "feature.",
            "evidence.",
            "条件成立",
            "/3",
            "3/3",
            "2/3",
            "1/3",
            "主规则",
            "联动",
            "形成结构主线",
            "主题投射",
            "可作为本次测算",
        )
    )


def _trim_signature(value: str, limit: int = 28) -> str:
    text = str(value or "").strip().rstrip("。；;！!")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
