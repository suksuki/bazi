from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from v20.answer.measurement_policy import domain_label, measurement_stage
from v20.features.schema import FeatureLayer
from v20.measurement.dimensions import dimension_payload


DECISION_MODEL_VERSION = "v20.defeasible_decision_model.v1"

ROLE_BY_LAYER = {
    "foundation": "foundation_context",
    "core_mechanism": "mainline_candidate",
    "core_symbol": "mainline_candidate",
    "core_relation": "structure_context",
    "core_arbitration": "mainline_candidate",
    "core_projection": "projection_context",
    "time": "time_context",
    "application": "applied_projection",
    "archive": "archive_boundary",
    "governance": "safety_boundary",
}

STATE_FROM_MATCH = {
    "matched": "confirmed",
    "partial": "weak_candidate",
    "review_required": "requires_review",
    "blocked": "blocked",
    "archive_only": "out_of_scope",
    "not_matched": "out_of_scope",
}

MAINLINE_DOMAIN_PRIORITY = {
    "strength": 96,
    "useful_god": 92,
    "pattern": 88,
    "wealth": 86,
    "career": 85,
    "relationship": 78,
    "romance": 76,
    "health": 70,
    "time": 84,
    "branch": 74,
    "ten_god": 72,
    "element": 68,
    "blind_lifa": 66,
}


def build_defeasible_decision_model(
    rule_runtime_report: dict[str, Any],
    feature_layer: FeatureLayer,
) -> dict[str, Any]:
    rules = tuple(row for row in rule_runtime_report.get("rules", ()) if isinstance(row, dict))
    argument_nodes = tuple(_argument_node(row, feature_layer) for row in rules)
    decision_states = tuple(_decision_state(row) for row in argument_nodes)
    topic_projections = tuple(_topic_projection(row) for row in argument_nodes if _should_project(row))
    rule_decisions = tuple(_rule_decision_candidate(row) for row in argument_nodes if _should_emit_decision(row))
    mainlines = _mainline_candidates(argument_nodes)
    state_counts = Counter(str(row["state"]) for row in decision_states)
    domain_counts = Counter(str(row["domain"]) for row in rule_decisions)
    return {
        "version": DECISION_MODEL_VERSION,
        "status": "ready" if argument_nodes else "empty",
        "source": "RuleSpecRuntime+EvidenceAtom+FeatureLayer",
        "algorithm": "defeasible_argumentation_certainty_phase1",
        "rule_runtime_version": rule_runtime_report.get("version", ""),
        "argument_count": len(argument_nodes),
        "decision_state_count": len(decision_states),
        "rule_decision_candidate_count": len(rule_decisions),
        "mainline_candidate_count": len(mainlines),
        "topic_projection_count": len(topic_projections),
        "state_counts": dict(sorted(state_counts.items())),
        "decision_domain_counts": dict(sorted(domain_counts.items())),
        "argument_nodes": argument_nodes,
        "decision_states": decision_states,
        "rule_decision_candidates": rule_decisions,
        "mainline_candidates": mainlines,
        "topic_projections": topic_projections,
        "score_policy": {
            "version": "v20.defeasible_score_policy.v1",
            "formula": "match_score + status_weight + evidence_weight + projection_weight - counter_penalty - blocked_penalty",
            "runtime_mutation": False,
        },
        "runtime_mutation": False,
        "guardrails": (
            "RULESPEC_RUNTIME_IS_DECISION_SOURCE",
            "ARGUMENT_NODES_SUPPORT_AND_ATTACK_DECISION_STATES",
            "DECISION_STATE_IS_STRUCTURAL_NOT_FORTUNE_VERDICT",
            "LLM_MAY_EXPLAIN_NOT_DECIDE",
        ),
    }


def _argument_node(rule: dict[str, Any], feature_layer: FeatureLayer) -> dict[str, Any]:
    support_ids = tuple(str(row) for row in rule.get("matched_evidence_atom_ids", ()) if str(row))
    counters = tuple(row for row in rule.get("counter_evidence", ()) if isinstance(row, dict))
    projections = tuple(row for row in rule.get("projections", ()) if isinstance(row, dict))
    state = _structural_state(rule)
    domain = str(rule.get("domain", ""))
    return {
        "argument_id": str(rule.get("rule_id", "")).replace("rule.", "argument."),
        "rule_id": rule.get("rule_id", ""),
        "title": rule.get("title", ""),
        "domain": domain,
        "layer": rule.get("layer", ""),
        "directory_node": rule.get("directory_node", ""),
        "match_status": rule.get("match_status", ""),
        "runtime_status": rule.get("runtime_status", ""),
        "state": state,
        "role": ROLE_BY_LAYER.get(str(rule.get("layer", "")), "supporting_path"),
        "score": _argument_score(rule, state, support_ids, counters, projections),
        "support_evidence_atom_ids": support_ids,
        "support": _support_text(rule, support_ids),
        "attack_counter_ids": tuple(str(row.get("counter_id", "")) for row in counters if row.get("counter_id")),
        "counter_effects": tuple(str(row.get("effect", "")) for row in counters if row.get("effect")),
        "projection_topics": tuple(str(row.get("topic_domain", "")) for row in projections if row.get("topic_domain")),
        "feature_ids": _feature_ids(feature_layer, domain),
        "certainty": _certainty_label(rule, state),
        "boundary": _boundary(rule, state),
        "runtime_mutation": False,
    }


def _decision_state(argument: dict[str, Any]) -> dict[str, Any]:
    return {
        "state_id": str(argument["argument_id"]).replace("argument.", "decision_state."),
        "state": argument["state"],
        "domain": argument["domain"],
        "rule_id": argument["rule_id"],
        "title": argument["title"],
        "score": argument["score"],
        "support_evidence_atom_ids": argument["support_evidence_atom_ids"],
        "attack_counter_ids": argument["attack_counter_ids"],
        "certainty": argument["certainty"],
    }


def _rule_decision_candidate(argument: dict[str, Any]) -> dict[str, Any]:
    domain = str(argument["domain"])
    return {
        "decision_key": str(argument["rule_id"]).replace("rule.", "decision.rulespec."),
        "rule_key": argument["rule_id"],
        "label": _decision_label(argument),
        "domain": domain,
        "status": argument["state"],
        "role": argument["role"],
        "score": argument["score"],
        "support": argument["support"],
        **dimension_payload(domain),
        "weakening": argument["attack_counter_ids"],
        "feature_ids": argument["feature_ids"],
        "portrait_tags": (_portrait_label(argument),),
        "question_seeds": (_question_seed(argument),),
        "practitioner_control_keys": _control_keys(argument),
        "source": "rulespec_defeasible_decision_model",
    }


def _topic_projection(argument: dict[str, Any]) -> dict[str, Any]:
    domain = str(argument["domain"])
    topics = tuple(argument.get("projection_topics", ())) or (domain,)
    return {
        "projection_id": f"projection.{argument['argument_id']}",
        "topic_domains": topics,
        "source_argument_id": argument["argument_id"],
        "source_rule_id": argument["rule_id"],
        "state": argument["state"],
        "score": argument["score"],
        "output_focus": _output_focus(domain),
        "boundary": argument["boundary"],
    }


def _mainline_candidates(arguments: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for argument in arguments:
        if not _should_emit_decision(argument):
            continue
        by_domain[str(argument["domain"])].append(argument)
    rows = []
    for domain, domain_arguments in by_domain.items():
        ranked = sorted(domain_arguments, key=lambda row: (row["score"], _priority(row)), reverse=True)
        primary = ranked[0]
        related = tuple(row["argument_id"] for row in ranked[1:4])
        rows.append(
            {
                "mainline_key": f"mainline.rulespec.{domain}",
                "title": _decision_label(primary),
                "domain": domain,
                "status": primary["state"],
                "score": primary["score"],
                "priority": MAINLINE_DOMAIN_PRIORITY.get(domain, 50),
                "summary": _mainline_summary(primary, ranked[1:4]),
                "source_argument_ids": (primary["argument_id"], *related),
                "source_rule_ids": tuple(row["rule_id"] for row in ranked[:4]),
                "support": primary["support"][:5],
                "question_seed": _question_seed(primary),
            }
        )
    return tuple(sorted(rows, key=lambda row: (row["priority"], row["score"]), reverse=True))


def _structural_state(rule: dict[str, Any]) -> str:
    match_status = str(rule.get("match_status", ""))
    base = STATE_FROM_MATCH.get(match_status, "out_of_scope")
    decision_state = str(rule.get("decision_state", ""))
    if base in {"blocked", "out_of_scope"}:
        return base
    if decision_state in {"mixed", "volatile", "requires_review", "countered"}:
        return decision_state
    return base


def _argument_score(
    rule: dict[str, Any],
    state: str,
    support_ids: tuple[str, ...],
    counters: tuple[dict[str, Any], ...],
    projections: tuple[dict[str, Any], ...],
) -> float:
    match_score = float(rule.get("match_score", 0.0) or 0.0)
    state_weight = {
        "confirmed": 0.16,
        "candidate": 0.12,
        "weak_candidate": 0.06,
        "mixed": 0.08,
        "volatile": 0.06,
        "requires_review": 0.04,
        "countered": -0.08,
        "blocked": -0.35,
        "out_of_scope": -0.18,
    }.get(state, 0.0)
    evidence_weight = min(0.14, len(support_ids) * 0.012)
    projection_weight = 0.04 if projections else 0.0
    counter_penalty = min(0.12, len(counters) * 0.035)
    blocked_penalty = 0.25 if str(rule.get("runtime_status", "")) == "blocked" else 0.0
    return round(max(0.0, min(0.96, match_score * 0.66 + state_weight + evidence_weight + projection_weight - counter_penalty - blocked_penalty)), 3)


def _support_text(rule: dict[str, Any], support_ids: tuple[str, ...]) -> tuple[str, ...]:
    rows = [f"{rule.get('title', '')}：{rule.get('matched_condition_count', 0)}/{rule.get('condition_count', 0)} 条件成立"]
    rows.extend(f"证据 {row}" for row in support_ids[:5])
    if rule.get("counter_evidence"):
        rows.append("存在反证或边界，需纳入裁决")
    return tuple(row for row in rows if row)


def _feature_ids(feature_layer: FeatureLayer, domain: str) -> tuple[str, ...]:
    direct = tuple(feature.feature_id for feature in feature_layer.features if feature.domain == domain)
    if direct:
        return direct[:6]
    return tuple(feature.feature_id for feature in feature_layer.features[:4])


def _certainty_label(rule: dict[str, Any], state: str) -> str:
    if state == "confirmed":
        return "high"
    if state in {"candidate", "mixed", "volatile"}:
        return "medium"
    if state in {"weak_candidate", "requires_review"}:
        return "low_review"
    if state in {"blocked", "countered"}:
        return "blocked_or_countered"
    return "out_of_scope"


def _boundary(rule: dict[str, Any], state: str) -> str:
    if state == "blocked":
        return "该规则用于阻断不合规输出，不进入用户命运结论。"
    if state == "out_of_scope":
        return "该规则仅归档或证据不足，不进入主线输出。"
    if state in {"mixed", "requires_review"}:
        return "该规则只能作为结构候选，需要结合反证与主线复核。"
    return "该规则只输出结构状态，不输出固定吉凶。"


def _should_emit_decision(argument: dict[str, Any]) -> bool:
    if argument["state"] in {"blocked", "out_of_scope"}:
        return False
    return argument["score"] >= 0.18


def _should_project(argument: dict[str, Any]) -> bool:
    return _should_emit_decision(argument) and str(argument.get("domain", "")) not in {"archive", "governance"}


def _priority(argument: dict[str, Any]) -> int:
    return MAINLINE_DOMAIN_PRIORITY.get(str(argument.get("domain", "")), 50)


def _decision_label(argument: dict[str, Any]) -> str:
    title = str(argument.get("title", "命理规则"))
    state = str(argument.get("state", "candidate"))
    suffix = {
        "confirmed": "明确成立",
        "candidate": "候选成立",
        "weak_candidate": "弱候选",
        "mixed": "成而不纯",
        "volatile": "岁运引动",
        "requires_review": "需复核",
        "countered": "有反证",
    }.get(state, "候选")
    return f"{title}：{suffix}"


def _portrait_label(argument: dict[str, Any]) -> str:
    return f"{domain_label(str(argument['domain']))}轴：{_decision_label(argument)}"


def _question_seed(argument: dict[str, Any]) -> str:
    domain = str(argument["domain"])
    label = _decision_label(argument)
    if domain in {"wealth", "career", "relationship", "romance", "health", "time"}:
        return f"{label}时，应该先复核哪条证据链？"
    return f"{domain_label(domain)}里，{label}需要哪些证据继续裁决？"


def _control_keys(argument: dict[str, Any]) -> tuple[str, ...]:
    domain = str(argument["domain"])
    if domain == "strength":
        return ("control.day_master_strength",)
    if domain == "wealth":
        return ("control.wealth_capacity",)
    if domain in {"career", "ten_god"}:
        return ("control.shang_guan_jian_guan",)
    if domain in {"pattern", "useful_god"}:
        return ("control.pattern_status",)
    return ()


def _output_focus(domain: str) -> tuple[str, ...]:
    return {
        "wealth": ("材料", "通道", "承接", "风险"),
        "career": ("规则", "表达", "平台", "缓冲"),
        "relationship": ("互动", "约束", "承接"),
        "romance": ("配偶星", "夫妻宫", "合冲", "边界"),
        "health": ("偏枯", "压力", "恢复", "禁断"),
        "time": ("原局", "大运", "流年", "引动"),
    }.get(domain, (measurement_stage(domain), domain_label(domain)))


def _mainline_summary(primary: dict[str, Any], related: list[dict[str, Any]]) -> str:
    support = "、".join(str(row) for row in primary.get("support", ())[:3])
    if related:
        labels = "、".join(_decision_label(row) for row in related[:3])
        return f"当前主线入口，RuleSpec 裁决主线，主规则为{_decision_label(primary)}，联动{labels}；证据：{support}。"
    return f"当前主线入口，RuleSpec 裁决主线，主规则为{_decision_label(primary)}；证据：{support}。"
