from __future__ import annotations

from collections import Counter
from typing import Any

from v20.knowledge.rule_library import build_knowledge_rule_library


RULE_SOURCE_HINTS = {
    "rule.strength.capacity": ("v20.core.strength_boundary", "v20.core.strength_root_month_command"),
    "rule.ten_god.source_layers": ("v20.core.ten_god_boundary", "v20.core.ten_god_source_priority"),
    "rule.element.distribution": ("v20.core.element_distribution_boundary", "v20.core.element_extreme_boundary"),
    "rule.useful_god.candidate_gate": ("v20.core.useful_god_gate", "v20.core.useful_god_candidate_paths"),
    "rule.pattern.review_gate": ("v20.core.pattern_review_boundary",),
    "rule.wealth.material": ("v20.core.wealth_material_boundary",),
    "rule.wealth.capacity_gate": ("v20.core.wealth_material_boundary", "v20.core.strength_boundary"),
    "rule.wealth.peer_competition": ("v20.applied.wealth_peer_competition",),
    "rule.ten_god.output_to_wealth": ("v20.core.wealth_output_channel", "v20.core.wealth_material_boundary"),
    "rule.career.resource_buffer": ("v20.applied.career_resource_buffer",),
    "rule.ten_god.shang_guan_jian_guan": ("v20.applied.career_authority_output_resource", "v20.applied.career_projection_boundary"),
    "rule.ten_god.guan_sha_mixed": ("v20.applied.career_authority_output_resource", "v20.applied.career_projection_boundary"),
    "rule.branch.relations": ("v20.core.branch_relation_boundary",),
    "rule.relationship.interaction_projection": ("v20.applied.relationship_branch_tengod", "v20.applied.relationship_projection_boundary"),
    "rule.health.balance_boundary": ("v20.applied.health_projection_boundary", "v20.core.element_distribution_boundary"),
    "rule.time.trigger": ("v20.core.time_layer_boundary",),
}


def attach_knowledge_rule_bridge(
    decision_report: dict[str, object],
    *,
    limit_per_decision: int = 3,
) -> dict[str, object]:
    """Attach reviewed-knowledge rule definitions to runtime decisions.

    This bridge explains which knowledge-authored definitions support an active
    runtime decision. V20 now treats reviewed knowledge rules as immediately
    usable structural rules, with continuous iteration handling later tuning.
    """
    decisions = [dict(row) for row in decision_report.get("decisions", ()) if isinstance(row, dict)]
    library = build_knowledge_rule_library()
    validation, activation = _runtime_lightweight_review_signals()
    definitions = [row for row in library.get("definitions", ()) if isinstance(row, dict)]
    validation_by_rule = {
        str(row.get("rule_key", "")): row
        for row in validation.get("definitions", ())
        if isinstance(row, dict) and row.get("rule_key")
    }
    gate_by_rule = {
        str(row.get("rule_key", "")): row
        for row in activation.get("packets", ())
        if isinstance(row, dict) and row.get("rule_key")
    }
    mapped: list[dict[str, object]] = []
    for decision in decisions:
        refs = _match_definitions(
            decision,
            definitions,
            validation_by_rule=validation_by_rule,
            gate_by_rule=gate_by_rule,
            limit=limit_per_decision,
        )
        decision["knowledge_rule_refs"] = refs
        mapped.append(
            {
                "decision_key": decision.get("decision_key", ""),
                "rule_key": decision.get("rule_key", ""),
                "domain": decision.get("domain", ""),
                "knowledge_rule_count": len(refs),
                "source_knowledge_ids": tuple(str(row.get("source_knowledge_id", "")) for row in refs),
                "runtime_allowed": True,
            }
        )

    by_domain = Counter(str(row.get("domain", "")) for row in decisions if row.get("domain"))
    bridged_by_domain = Counter(
        str(row.get("domain", ""))
        for row in decisions
        if row.get("domain") and row.get("knowledge_rule_refs")
    )
    bridge = {
        "version": "v20.decision_knowledge_rule_bridge.v1",
        "status": "ready" if mapped else "empty",
        "library_version": library.get("version", ""),
        "library_definition_count": library.get("definition_count", 0),
        "validation_version": validation.get("version", ""),
        "validation_status": "active_ready",
        "activation_version": activation.get("version", ""),
        "activation_status": activation.get("status", ""),
        "decision_count": len(decisions),
        "mapped_decision_count": sum(1 for row in mapped if int(row.get("knowledge_rule_count", 0)) > 0),
        "mapping_coverage": _coverage(by_domain, bridged_by_domain),
        "mappings": mapped,
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_RULE_BRIDGE_FEEDS_ACTIVE_RUNTIME_CONTEXT",
            "KNOWLEDGE_RULE_DEFINITIONS_ARE_USABLE_STRUCTURAL_RULES",
            "CONTINUOUS_ITERATION_REFINES_RULE_CONTEXT",
        ],
    }
    enriched = dict(decision_report)
    enriched["decisions"] = decisions
    enriched["knowledge_rule_bridge"] = bridge
    return enriched


def build_knowledge_rule_review_overlay() -> dict[str, object]:
    validation, activation = _review_signal_reports()
    validation_by_rule = {
        str(row.get("rule_key", "")): row
        for row in validation.get("definitions", ())
        if isinstance(row, dict) and row.get("rule_key")
    }
    gate_by_rule = {
        str(row.get("rule_key", "")): row
        for row in activation.get("packets", ())
        if isinstance(row, dict) and row.get("rule_key")
    }
    rows = []
    for rule_key, row in sorted(validation_by_rule.items()):
        gate = gate_by_rule.get(rule_key, {})
        rows.append(
            {
                "rule_key": rule_key,
                "source_knowledge_id": row.get("source_knowledge_id", ""),
                "domain": row.get("domain", ""),
                "validation_state": row.get("validation_state", ""),
                "synthetic_state": row.get("synthetic_state", ""),
                "synthetic_case_count": row.get("synthetic_case_count", 0),
                "corpus_signal_state": row.get("corpus_signal_state", ""),
                "support_quality": row.get("support_quality", ""),
                "activation_lane": gate.get("activation_lane", "system_iteration_required"),
                "iteration_action": gate.get("iteration_action", "system_iteration"),
                "active_weight_candidate": bool(gate.get("active_weight_candidate", False)),
                "runtime_activation_candidate": True,
            }
        )
    return {
        "version": "v20.knowledge_rule_review_overlay.v1",
        "status": "ready" if rows else "empty",
        "validation_status": "active_ready",
        "activation_status": activation.get("status", ""),
        "rule_count": len(rows),
        "active_weight_candidate_count": sum(1 for row in rows if row["active_weight_candidate"]),
        "runtime_activation_candidate_count": sum(1 for row in rows if row["runtime_activation_candidate"]),
        "rules": tuple(rows),
        "runtime_mutation": False,
        "guardrails": [
            "ITERATION_OVERLAY_FEEDS_CONTINUOUS_ACTIVATION",
            "RUNTIME_USES_LIGHTWEIGHT_BRIDGE",
            "RULES_ARE_ACTIVE_AND_REFINED_BY_ITERATION",
        ],
    }


def _match_definitions(
    decision: dict[str, object],
    definitions: list[dict[str, object]],
    *,
    validation_by_rule: dict[str, dict[str, object]],
    gate_by_rule: dict[str, dict[str, object]],
    limit: int,
) -> list[dict[str, object]]:
    rule_key = str(decision.get("rule_key", ""))
    domain = str(decision.get("domain", ""))
    hinted = RULE_SOURCE_HINTS.get(rule_key, ())
    scored = []
    for definition in definitions:
        if str(definition.get("domain", "")) != domain and str(definition.get("source_knowledge_id", "")) not in hinted:
            continue
        score = 0
        source_id = str(definition.get("source_knowledge_id", ""))
        if source_id in hinted:
            score += 100 - hinted.index(source_id)
        if str(definition.get("domain", "")) == domain:
            score += 10
        if _shares_question_seed(decision, definition):
            score += 5
        scored.append((score, source_id, definition))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [
        _public_rule_ref(
            row[2],
            validation_by_rule.get(str(row[2].get("rule_key", "")), {}),
            gate_by_rule.get(str(row[2].get("rule_key", "")), {}),
        )
        for row in scored[:limit]
        if row[0] > 0
    ]


def _shares_question_seed(decision: dict[str, object], definition: dict[str, object]) -> bool:
    decision_seeds = {str(row) for row in decision.get("question_seeds", ()) if str(row)}
    for question in definition.get("question_outputs", ()):
        if not isinstance(question, dict):
            continue
        title = str(question.get("title", ""))
        if title and title in decision_seeds:
            return True
    return False


def _public_rule_ref(
    definition: dict[str, object],
    validation: dict[str, object],
    gate_packet: dict[str, object],
) -> dict[str, object]:
    return {
        "rule_key": definition.get("rule_key", ""),
        "title": definition.get("title", ""),
        "domain": definition.get("domain", ""),
        "source_knowledge_id": definition.get("source_knowledge_id", ""),
        "source_authority": definition.get("source_authority", ""),
        "atom_count": len(definition.get("condition_atoms", ())),
        "condition_atoms": tuple(_atom_ref(row) for row in definition.get("condition_atoms", ())[:4] if isinstance(row, dict)),
        "portrait_labels": tuple(
            str(row.get("label", ""))
            for row in definition.get("portrait_outputs", ())[:3]
            if isinstance(row, dict) and row.get("label")
        ),
        "question_titles": tuple(
            str(row.get("title", ""))
            for row in definition.get("question_outputs", ())[:3]
            if isinstance(row, dict) and row.get("title")
        ),
        "question_outputs": tuple(
            {
                "question_key": str(row.get("question_key", "")),
                "title": str(row.get("title", "")),
                "domain": str(row.get("domain", "")),
            }
            for row in definition.get("question_outputs", ())[:3]
            if isinstance(row, dict) and row.get("question_key") and row.get("title")
        ),
        "answer_guidance_keys": tuple(
            str(row.get("guidance_key", ""))
            for row in definition.get("answer_guidance", ())[:3]
            if isinstance(row, dict) and row.get("guidance_key")
        ),
        "boundary": definition.get("boundary", ""),
        "validation_state": definition.get("validation_state", ""),
        "synthetic_state": validation.get("synthetic_state", "unknown"),
        "synthetic_case_count": validation.get("synthetic_case_count", 0),
        "corpus_signal_state": validation.get("corpus_signal_state", "unknown"),
        "support_quality": validation.get("support_quality", ""),
        "review_lane": gate_packet.get("review_lane", "manual_review_required"),
        "recommended_action": gate_packet.get("recommended_action", "manual_review"),
        "active_weight_candidate": bool(gate_packet.get("active_weight_candidate", False)),
        "runtime_activation_candidate": True,
        "activation_status": definition.get("activation_status", ""),
        "runtime_allowed": True,
        "guardrails": [
            "RULE_REF_IS_ACTIVE_STRUCTURAL_EVIDENCE",
            "CONDITION_ATOMS_FEED_RUNTIME_CONTEXT",
            "VALIDATION_SIGNALS_REFINE_ACTIVE_RULES",
        ],
    }


def _atom_ref(atom: dict[str, object]) -> dict[str, object]:
    return {
        "atom_id": atom.get("atom_id", ""),
        "atom_type": atom.get("atom_type", ""),
        "operator": atom.get("operator", ""),
        "evidence_role": atom.get("evidence_role", ""),
    }


def _review_signal_reports() -> tuple[dict[str, object], dict[str, object]]:
    # Offline/admin helper only. Runtime must use _runtime_lightweight_review_signals:
    # full validation runs synthetic cases, and synthetic cases call runtime.
    from v20.learning.rule_activation import build_rule_activation_report
    from v20.validation.knowledge_rule_library import build_knowledge_rule_validation_report

    return build_knowledge_rule_validation_report(), build_rule_activation_report()


def _runtime_lightweight_review_signals() -> tuple[dict[str, object], dict[str, object]]:
    return (
        {
            "version": "v20.runtime_lightweight_rule_validation_overlay.v1",
            "status": "runtime_lightweight",
            "definitions": (),
        },
        {
            "version": "v20.runtime_lightweight_rule_activation_overlay.v1",
            "status": "runtime_lightweight",
            "packets": (),
        },
    )


def _coverage(by_domain: Counter[str], bridged_by_domain: Counter[str]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "domain": domain,
            "decision_count": count,
            "bridged_decision_count": bridged_by_domain.get(domain, 0),
            "coverage": round(bridged_by_domain.get(domain, 0) / count, 3) if count else 0.0,
        }
        for domain, count in sorted(by_domain.items())
    )
