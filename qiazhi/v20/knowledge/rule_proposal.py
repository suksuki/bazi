from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.review_queue import CORE_DOMAIN_PRIORITY
from v20.knowledge.schema import KnowledgeUnit


@dataclass(frozen=True)
class KnowledgeRuleProposal:
    proposal_id: str
    proposal_type: str
    domain: str
    source_knowledge_id: str
    title: str
    summary: str
    required_chart_facts: tuple[str, ...]
    condition_model: dict[str, object]
    emits_feature_hooks: tuple[str, ...]
    supports_question_hooks: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    boundary: str
    validation_requirements: tuple[str, ...]
    activation_scope: str = "shadow_training_and_candidate_rule_graph"
    status: str = "released_to_shadow_training"
    risk: str = "medium"
    forbidden_outputs: tuple[str, ...] = (
        "direct_rule_truth",
        "fortune_verdict",
        "domain_event_prediction",
        "user_visible_runtime_activation_without_promotion",
    )
    guardrails: tuple[str, ...] = (
        "KNOWLEDGE_TO_RULE_IS_PROPOSAL_ONLY",
        "REVIEWED_KNOWLEDGE_REQUIRED",
        "SHADOW_TRAINING_ALLOWED_BY_DEFAULT",
        "PROMOTION_GATE_ONLY_FOR_USER_VISIBLE_RUNTIME",
        "NO_USER_VISIBLE_RULE_ACTIVATION",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_knowledge_rule_proposals(
    domain: str = "",
    *,
    limit: int = 12,
    units: tuple[KnowledgeUnit, ...] | None = None,
) -> dict[str, object]:
    selected = _selected_reviewed_units(domain, limit=limit, units=units or default_knowledge_units())
    proposals = tuple(_proposal_from_unit(unit) for unit in selected)
    return {
        "version": "v20.knowledge_rule_proposals.v1",
        "status": "ready" if proposals else "empty",
        "domain": domain.strip(),
        "proposal_count": len(proposals),
        "proposals": [row.to_dict() for row in proposals],
        "runtime_mutation": False,
        "guardrails": [
            "RULE_PROPOSALS_ARE_DRAFTS",
            "NO_RULE_GRAPH_WRITE",
            "NO_RUNTIME_ACTIVATION",
            "VALIDATION_AND_DECISION_REQUIRED",
        ],
    }


def build_first_wave_rule_proposals(*, limit_per_domain: int = 3) -> dict[str, object]:
    reports = [
        build_knowledge_rule_proposals(domain, limit=limit_per_domain)
        for domain in CORE_DOMAIN_PRIORITY
    ]
    reports = [row for row in reports if row["status"] != "empty"]
    return {
        "version": "v20.knowledge_first_wave_rule_proposals.v1",
        "status": "ready" if reports else "empty",
        "domain_count": len(reports),
        "proposal_count": sum(int(row["proposal_count"]) for row in reports),
        "core_domain_priority": CORE_DOMAIN_PRIORITY,
        "reports": reports,
        "runtime_mutation": False,
        "guardrails": [
            "FIRST_WAVE_RULE_PROPOSALS_ONLY",
            "CORE_BAZI_DOMAINS_FIRST",
            "NO_AUTOMATIC_ACTIVATION",
        ],
    }


def build_rule_proposal_preflight(domain: str = "", *, limit: int = 12) -> dict[str, object]:
    report = build_knowledge_rule_proposals(domain, limit=limit)
    failures = []
    promotion_requirements = []
    for proposal in report["proposals"]:
        if not isinstance(proposal, dict):
            continue
        proposal_id = str(proposal.get("proposal_id", ""))
        if not proposal.get("source_knowledge_id"):
            failures.append(f"missing_source_knowledge_id:{proposal_id}")
        if not proposal.get("boundary"):
            failures.append(f"missing_boundary:{proposal_id}")
        if not proposal.get("evidence_refs"):
            failures.append(f"missing_evidence_refs:{proposal_id}")
        if not proposal.get("emits_feature_hooks"):
            failures.append(f"missing_feature_hooks:{proposal_id}")
        if not proposal.get("supports_question_hooks"):
            failures.append(f"missing_question_hooks:{proposal_id}")
        promotion_requirements.append(f"synthetic_validation_before_user_visible_runtime:{proposal_id}")
        promotion_requirements.append(f"decision_record_before_user_visible_runtime:{proposal_id}")
    return {
        "version": "v20.knowledge_rule_proposal_preflight.v1",
        "domain": domain.strip(),
        "status": "blocked_static_contract" if failures else "ready_for_shadow_training",
        "ok": not failures,
        "proposal_count": report["proposal_count"],
        "failure_count": len(failures),
        "failures": failures,
        "promotion_requirements": promotion_requirements,
        "runtime_mutation": False,
        "guardrails": [
            "PREFLIGHT_ONLY",
            "SHADOW_TRAINING_ALLOWED_BY_DEFAULT",
            "NO_USER_VISIBLE_RUNTIME_ACTIVATION",
            "PROMOTION_GATE_ONLY_FOR_PRODUCTION",
        ],
    }


def build_first_wave_rule_proposal_preflight(*, limit_per_domain: int = 3) -> dict[str, object]:
    first_wave = build_first_wave_rule_proposals(limit_per_domain=limit_per_domain)
    reports = [
        build_rule_proposal_preflight(str(row["domain"]), limit=limit_per_domain)
        for row in first_wave["reports"]
        if isinstance(row, dict)
    ]
    return {
        "version": "v20.knowledge_first_wave_rule_proposal_preflight.v1",
        "status": "blocked_static_contract" if any(not row["ok"] for row in reports) else "ready_for_shadow_training",
        "ok": bool(reports) and all(row["ok"] for row in reports),
        "domain_count": len(reports),
        "proposal_count": sum(int(row["proposal_count"]) for row in reports),
        "blocked_domain_count": sum(1 for row in reports if not row["ok"]),
        "promotion_requirement_count": sum(len(row["promotion_requirements"]) for row in reports),
        "reports": reports,
        "runtime_mutation": False,
        "guardrails": [
            "FIRST_WAVE_PREFLIGHT_ONLY",
            "SHADOW_TRAINING_ALLOWED_BY_DEFAULT",
            "PROMOTION_GATE_ONLY_FOR_PRODUCTION",
        ],
    }


def _selected_reviewed_units(
    domain: str,
    *,
    limit: int,
    units: tuple[KnowledgeUnit, ...],
) -> tuple[KnowledgeUnit, ...]:
    normalized = domain.strip()
    rows = [
        unit
        for unit in units
        if unit.status == "reviewed" and (not normalized or unit.domain == normalized)
    ]
    rows = sorted(rows, key=lambda unit: (_domain_priority(unit.domain), unit.knowledge_id))
    return tuple(rows[:limit])


def _proposal_from_unit(unit: KnowledgeUnit) -> KnowledgeRuleProposal:
    return KnowledgeRuleProposal(
        proposal_id=f"v20.rule_proposal.{_safe_id(unit.knowledge_id)}",
        proposal_type="knowledge_to_rule_path_candidate",
        domain=unit.domain,
        source_knowledge_id=unit.knowledge_id,
        title=f"Rule proposal from {unit.title}",
        summary=unit.summary,
        required_chart_facts=_required_chart_facts(unit.domain),
        condition_model={
            "type": "feature_hook_prefix_match",
            "all_of": [{"feature_hook_prefix": hook} for hook in unit.feature_hooks],
            "boundary": unit.boundary,
        },
        emits_feature_hooks=unit.feature_hooks,
        supports_question_hooks=unit.question_hooks,
        evidence_refs=unit.source_refs,
        boundary=unit.boundary,
        validation_requirements=(
            "static_contract_check",
            "synthetic_suite_pass",
            "shadow_runtime_diff_report",
            "no_forbidden_output_scan",
            "decision_registry_approval",
        ),
        risk=_risk_for_domain(unit.domain),
    )


def _required_chart_facts(domain: str) -> tuple[str, ...]:
    mapping = {
        "strength": ("day_master", "month_branch", "support_pressure_scores", "hidden_stem_sources"),
        "ten_god": ("day_master", "visible_ten_gods", "hidden_ten_gods"),
        "useful_god": ("day_master_capacity", "element_distribution", "support_pressure_scores"),
        "element": ("visible_stems", "hidden_stems", "element_distribution"),
        "branch": ("pillar_branches", "relation_hits", "relation_layers"),
        "wealth": ("wealth_ten_god_positions", "visible_ten_gods", "hidden_ten_gods", "relation_context"),
        "pattern": ("rule_paths", "feature_evidence", "arbitration_state"),
        "time": ("explicit_time_pillars", "time_ten_gods", "time_relation_hits"),
        "career": ("ten_god_features", "strength_features", "pattern_features"),
        "relationship": ("ten_god_features", "branch_relation_features", "strength_features"),
        "health": ("element_distribution", "strength_features", "branch_relation_features"),
    }
    return mapping.get(domain, ("compiled_bazi_features", "reviewed_knowledge_refs"))


def _risk_for_domain(domain: str) -> str:
    if domain in {"career", "relationship", "health", "wealth", "time"}:
        return "medium"
    return "low"


def _domain_priority(domain: str) -> tuple[int, str]:
    try:
        return (CORE_DOMAIN_PRIORITY.index(domain), domain)
    except ValueError:
        return (len(CORE_DOMAIN_PRIORITY), domain)


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)
