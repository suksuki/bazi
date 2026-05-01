from __future__ import annotations

from v20.answer.measurement_policy import domain_label
from v20.knowledge.review_packet import build_first_wave_review_packets, build_knowledge_review_packet

DOMAIN_HOOKS = {
    "strength": (("feature.strength",), ("q_strength_assessment",)),
    "ten_god": (("feature.ten_god",), ("q_ten_god_focus", "q_ten_god_metadata")),
    "useful_god": (("feature.useful_god",), ("q_useful_god_candidates", "q_useful_god_evidence_gaps")),
    "element": (("feature.element",), ("q_element_balance", "q_element_support_pressure")),
    "branch": (("feature.branch",), ("q_branch_relation_detail", "q_structure_overview")),
    "wealth": (("feature.wealth", "feature.ten_god"), ("q_income_stability", "q_income_factors")),
    "pattern": (("feature.pattern",), ("q_pattern_structure",)),
    "time": (("feature.time",), ("q_time_layer_context", "q_time_relation_triggers")),
    "career": (("feature.ten_god", "feature.pattern", "feature.strength"), ("q_career_structure",)),
    "relationship": (("feature.ten_god", "feature.branch"), ("q_relationship_structure",)),
    "health": (("feature.element", "feature.strength", "feature.branch"), ("q_health_balance_boundary",)),
}


def build_knowledge_review_assist(domain: str, *, limit: int = 8) -> dict[str, object]:
    packet = build_knowledge_review_packet(domain, limit=limit)
    suggestions = [_suggestion(row, str(packet["domain"])) for row in packet["proposed_units"]]
    return {
        "version": "v20.knowledge_review_assist.v1",
        "domain": packet["domain"],
        "status": "ready" if suggestions else "empty",
        "packet_status": packet["status"],
        "suggestion_count": len(suggestions),
        "suggestions": suggestions,
        "runtime_mutation": False,
        "guardrails": [
            "REVIEW_ASSIST_ONLY",
            "SUGGESTIONS_REQUIRE_HUMAN_REVIEW",
            "NO_AUTOMATIC_FIELD_WRITE",
            "NO_RUNTIME_KNOWLEDGE_ACTIVATION",
        ],
    }


def build_first_wave_review_assist(*, limit_per_domain: int = 3) -> dict[str, object]:
    packets = build_first_wave_review_packets(limit_per_domain=limit_per_domain)
    assists = [build_knowledge_review_assist(str(packet["domain"]), limit=limit_per_domain) for packet in packets["packets"]]
    return {
        "version": "v20.knowledge_first_wave_review_assist.v1",
        "status": "ready" if assists else "empty",
        "domain_count": len(assists),
        "total_suggestion_count": sum(int(row["suggestion_count"]) for row in assists),
        "assists": assists,
        "runtime_mutation": False,
        "guardrails": [
            "FIRST_WAVE_REVIEW_ASSIST_ONLY",
            "NO_AUTOMATIC_APPROVAL",
            "NO_RUNTIME_RETRIEVAL_FROM_SUGGESTIONS",
        ],
    }


def _suggestion(row: dict[str, object], domain: str) -> dict[str, object]:
    feature_hooks, question_hooks = DOMAIN_HOOKS.get(domain, ((f"feature.{domain}",), ()))
    topic = domain_label(domain)
    summary = str(row.get("summary", "")).strip()
    return {
        "knowledge_id": row.get("knowledge_id", ""),
        "domain": domain,
        "title": row.get("title", ""),
        "summary_suggestion": summary,
        "evidence_template_suggestion": (
            f"Use reviewed {topic} source text, compiled feature evidence, and source refs before applying this unit."
        ),
        "boundary_suggestion": _boundary(domain, topic),
        "feature_hooks_suggestion": feature_hooks,
        "question_hooks_suggestion": question_hooks,
        "status_after_suggestion": "draft_review_required",
        "reviewer_must_confirm": (
            "source_refs",
            "evidence_template",
            "boundary",
            "feature_hooks",
            "question_hooks",
            "synthetic_validation",
        ),
        "guardrails": [
            "SUGGESTION_ONLY",
            "REVIEWER_CONFIRMATION_REQUIRED",
            "NO_STATUS_PROMOTION",
        ],
    }


def _boundary(domain: str, topic: str) -> str:
    if domain in {"career", "relationship", "health", "wealth"}:
        return f"{topic}知识只能作为 feature-backed 领域投影材料，不能直接生成事件、吉凶或保证性结论。"
    if domain == "useful_god":
        return "用神知识只能打开候选路径和证据缺口，不直接定死喜忌。"
    return f"{topic}知识只能解释结构证据和边界，不能作为直接断语或规则真值。"
