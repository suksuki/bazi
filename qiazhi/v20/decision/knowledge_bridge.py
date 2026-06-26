from __future__ import annotations

from collections import Counter
import os
from time import monotonic
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
_POINTER_CACHE: dict[str, object] = {"expires_at": 0.0, "pointer": None, "error": ""}


def attach_knowledge_rule_bridge(
    decision_report: dict[str, object],
    *,
    limit_per_decision: int = 3,
    runtime_policy_pointer: dict[str, object] | None = None,
) -> dict[str, object]:
    """Attach reviewed-knowledge rule definitions to runtime decisions.

    This bridge explains which knowledge-authored definitions support an active
    runtime decision. V20 now treats reviewed knowledge rules as immediately
    usable structural rules, with continuous iteration handling later tuning.
    """
    decisions = [dict(row) for row in decision_report.get("decisions", ()) if isinstance(row, dict)]
    library = build_knowledge_rule_library()
    validation, activation = _runtime_lightweight_review_signals()
    pointer, pointer_error = _load_knowledge_runtime_pointer(runtime_policy_pointer)
    policy_index = _knowledge_policy_index(pointer)
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
            policy_index=policy_index,
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
        "policy_effect": {
            "knowledge_policy": _knowledge_policy_effect(pointer, pointer_error, policy_index, decisions),
        },
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_RULE_BRIDGE_FEEDS_ACTIVE_RUNTIME_CONTEXT",
            "KNOWLEDGE_RULE_DEFINITIONS_ARE_USABLE_STRUCTURAL_RULES",
            "CONTINUOUS_ITERATION_REFINES_RULE_CONTEXT",
            "KNOWLEDGE_BRIDGE_CONSUMES_ACTIVE_KNOWLEDGE_POINTER",
        ],
    }
    enriched = dict(decision_report)
    enriched["decisions"] = decisions
    enriched["knowledge_rule_bridge"] = bridge
    return enriched


def build_knowledge_rule_review_overlay(
    *,
    limit: int = 0,
    synthetic_case_limit: int = 0,
) -> dict[str, object]:
    validation, activation = _review_signal_reports(limit=limit, synthetic_case_limit=synthetic_case_limit)
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
    policy_index: dict[tuple[str, str], dict[str, object]],
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
        policy = _policy_for_definition(rule_key=rule_key, definition=definition, policy_index=policy_index)
        if policy:
            score += int(float(policy.get("mapping_weight_delta", 0.0) or 0.0) * 1000)
            score += int(float(policy.get("source_trust_delta", 0.0) or 0.0) * 500)
        scored.append((score, source_id, definition))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [
        _public_rule_ref(
            row[2],
            validation_by_rule.get(str(row[2].get("rule_key", "")), {}),
            gate_by_rule.get(str(row[2].get("rule_key", "")), {}),
            _policy_for_definition(rule_key=rule_key, definition=row[2], policy_index=policy_index),
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
    policy: dict[str, object] | None = None,
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
        "policy_applied": bool(policy),
        "policy_mapping_weight_delta": float(policy.get("mapping_weight_delta", 0.0) or 0.0) if policy else 0.0,
        "policy_answer_guidance_delta": float(policy.get("answer_guidance_delta", 0.0) or 0.0) if policy else 0.0,
        "policy_source_trust_delta": float(policy.get("source_trust_delta", 0.0) or 0.0) if policy else 0.0,
        "runtime_activation_candidate": True,
        "activation_status": definition.get("activation_status", ""),
        "runtime_allowed": True,
        "guardrails": [
            "RULE_REF_IS_ACTIVE_STRUCTURAL_EVIDENCE",
            "CONDITION_ATOMS_FEED_RUNTIME_CONTEXT",
            "VALIDATION_SIGNALS_REFINE_ACTIVE_RULES",
            "KNOWLEDGE_POLICY_REFINES_MAPPING_PRIORITY",
        ],
    }


def _load_knowledge_runtime_pointer(pointer: dict[str, object] | None) -> tuple[dict[str, object], str]:
    if pointer is not None:
        return pointer, ""
    baseline = _baseline_knowledge_pointer_if_no_active_policy()
    if baseline is not None:
        return baseline, ""
    now = monotonic()
    cached = _POINTER_CACHE.get("pointer")
    if isinstance(cached, dict) and now < float(_POINTER_CACHE.get("expires_at", 0.0) or 0.0):
        return cached, str(_POINTER_CACHE.get("error", ""))
    try:
        from v20.learning.knowledge_runtime_pointer import build_knowledge_runtime_pointer

        result = build_knowledge_runtime_pointer()
        _POINTER_CACHE.update({"pointer": result, "error": "", "expires_at": now + _runtime_pointer_cache_ttl()})
        return result, ""
    except Exception as exc:
        fallback = {
            "version": "v20.knowledge_runtime_pointer_unavailable.v1",
            "status": "error",
            "runtime_applied": False,
            "runtime_allowed": False,
            "blocking_gate": f"knowledge_runtime_pointer_failed:{exc}",
            "policy_payload": {},
            "runtime_mutation": False,
        }
        _POINTER_CACHE.update({"pointer": fallback, "error": str(exc), "expires_at": now + min(_runtime_pointer_cache_ttl(), 5.0)})
        return fallback, str(exc)


def _baseline_knowledge_pointer_if_no_active_policy() -> dict[str, object] | None:
    try:
        from v20.learning.knowledge_runtime_pointer import (
            KNOWLEDGE_BASELINE_VERSION,
            KNOWLEDGE_POINTER_RELATIVE_PATH,
        )
        from v20.storage.local_jsonl import local_jsonl_store_from_env

        path = local_jsonl_store_from_env().runtime_dir / KNOWLEDGE_POINTER_RELATIVE_PATH
        if not path.exists():
            active_version = KNOWLEDGE_BASELINE_VERSION
        else:
            import json

            payload = json.loads(path.read_text(encoding="utf-8"))
            active_version = str(payload.get("active_policy_version", "")) if isinstance(payload, dict) else ""
        if active_version and active_version != KNOWLEDGE_BASELINE_VERSION:
            return None
        return {
            "version": "v20.knowledge_runtime_pointer.v1",
            "status": "baseline",
            "policy_family": "knowledge_review",
            "active_policy_version": KNOWLEDGE_BASELINE_VERSION,
            "candidate_policy_version": "",
            "rollback_policy_version": KNOWLEDGE_BASELINE_VERSION,
            "active_pointer_source": "baseline",
            "candidate": {},
            "policy_payload": {},
            "runtime_applied": False,
            "runtime_allowed": False,
            "blocking_gate": "",
            "runtime_mutation": False,
            "guardrails": [
                "KNOWLEDGE_RUNTIME_POINTER_READ_ONLY",
                "BASELINE_POINTER_FAST_PATH",
                "NO_KNOWLEDGE_TRUTH_MUTATION",
            ],
        }
    except Exception:
        return None


def _runtime_pointer_cache_ttl() -> float:
    try:
        return max(0.0, float(os.getenv("V20_RUNTIME_POINTER_CACHE_TTL_SECONDS", "300")))
    except ValueError:
        return 300.0


def _knowledge_policy_index(pointer: dict[str, object]) -> dict[tuple[str, str], dict[str, object]]:
    if pointer.get("runtime_applied") is not True:
        return {}
    payload = pointer.get("policy_payload", {})
    if not isinstance(payload, dict):
        return {}
    rows = payload.get("knowledge_rule_mapping_policy", ())
    index: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows if isinstance(rows, list | tuple) else ():
        if not isinstance(row, dict):
            continue
        rule_key = str(row.get("rule_key", ""))
        source_knowledge_id = str(row.get("source_knowledge_id", ""))
        if rule_key and source_knowledge_id:
            index[(rule_key, source_knowledge_id)] = row
    return index


def _policy_for_definition(
    *,
    rule_key: str,
    definition: dict[str, object],
    policy_index: dict[tuple[str, str], dict[str, object]],
) -> dict[str, object] | None:
    source_id = str(definition.get("source_knowledge_id", ""))
    return policy_index.get((rule_key, source_id)) or policy_index.get((str(definition.get("rule_key", "")), source_id))


def _knowledge_policy_effect(
    pointer: dict[str, object],
    pointer_error: str,
    policy_index: dict[tuple[str, str], dict[str, object]],
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    applied_ref_count = sum(
        1
        for decision in decisions
        for ref in decision.get("knowledge_rule_refs", ())
        if isinstance(ref, dict) and ref.get("policy_applied") is True
    )
    if pointer_error:
        status = "pointer_error"
    elif pointer.get("runtime_applied") is not True:
        status = "not_applied"
    elif policy_index and not applied_ref_count:
        status = "active_no_matching_knowledge_ref"
    else:
        status = "applied" if applied_ref_count else "empty_payload"
    return {
        "version": "v20.knowledge_runtime_policy_effect.v1",
        "status": status,
        "active_policy_version": pointer.get("active_policy_version", ""),
        "candidate_policy_version": pointer.get("candidate_policy_version", ""),
        "policy_count": len(policy_index),
        "applied_ref_count": applied_ref_count,
        "target": "knowledge_rule_mapping_policy",
        "blocking_gate": str(pointer.get("blocking_gate", "")),
        "runtime_mutation": False,
        "guardrails": (
            "KNOWLEDGE_POLICY_IS_POINTER_DRIVEN",
            "KNOWLEDGE_POLICY_ADJUSTS_MAPPING_PRIORITY_ONLY",
            "KNOWLEDGE_POLICY_DOES_NOT_MUTATE_KNOWLEDGE_TRUTH",
        ),
    }


def _atom_ref(atom: dict[str, object]) -> dict[str, object]:
    return {
        "atom_id": atom.get("atom_id", ""),
        "atom_type": atom.get("atom_type", ""),
        "operator": atom.get("operator", ""),
        "evidence_role": atom.get("evidence_role", ""),
    }


def _review_signal_reports(
    *,
    limit: int = 0,
    synthetic_case_limit: int = 0,
) -> tuple[dict[str, object], dict[str, object]]:
    # Offline/admin helper only. Runtime must use _runtime_lightweight_review_signals:
    # full validation runs synthetic cases, and synthetic cases call runtime.
    from v20.learning.rule_activation import build_rule_activation_report
    from v20.validation.knowledge_rule_library import build_knowledge_rule_validation_report

    return (
        build_knowledge_rule_validation_report(limit=limit, synthetic_case_limit=synthetic_case_limit),
        build_rule_activation_report(limit=limit, synthetic_case_limit=synthetic_case_limit),
    )


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
