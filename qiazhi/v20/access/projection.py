from __future__ import annotations

from v20.access.roles import role_policy
from v20.role_view.projection import apply_role_answer_view, apply_role_question_view, build_role_view_model
from v20.role_view.runtime_pointer import build_role_view_runtime_pointer


def project_runtime_for_role(result: dict[str, object], role_key: str) -> dict[str, object]:
    policy = role_policy(role_key)
    payload = {key: result[key] for key in policy.allowed_runtime_fields if key in result}
    role_view_runtime_pointer = build_role_view_runtime_pointer()
    payload = apply_role_question_view(payload, role_key, runtime_pointer=role_view_runtime_pointer)
    role_view_model = build_role_view_model(result, role_key, runtime_pointer=role_view_runtime_pointer)
    payload["role_view_model"] = role_view_model
    if role_key in {"admin", "lab"}:
        payload["role_view_runtime_pointer"] = role_view_runtime_pointer
    payload = apply_role_answer_view(payload, role_key, role_view_model)
    if role_key in {"guest", "user"}:
        payload = _sanitize_user_payload(payload, role_key)
    elif role_key in {"admin", "lab"}:
        payload = _sanitize_observation_payload(payload)
    payload["version"] = "v20.role_runtime_view.v1"
    payload["role"] = policy.to_dict()
    payload["runtime_mutation"] = False
    payload["guardrails"] = list(payload.get("guardrails", ())) + [
        "ROLE_VIEW_PROJECTED_SERVER_SIDE",
        "BLOCKED_FIELDS_NOT_RENDERED",
    ]
    return payload


def _sanitize_observation_payload(payload: dict[str, object]) -> dict[str, object]:
    sanitized = dict(payload)
    if isinstance(sanitized.get("decision_report"), dict):
        sanitized["decision_report"] = _compact_decision_report(dict(sanitized["decision_report"]))
    if isinstance(sanitized.get("knowledge_refs"), list | tuple):
        sanitized["knowledge_refs"] = [_compact_knowledge_ref(row) for row in sanitized["knowledge_refs"][:8] if isinstance(row, dict)]
    if isinstance(sanitized.get("knowledge_report"), dict):
        sanitized["knowledge_report"] = _compact_status_report(dict(sanitized["knowledge_report"]))
    if isinstance(sanitized.get("knowledge_alignment"), dict):
        sanitized["knowledge_alignment"] = _compact_status_report(dict(sanitized["knowledge_alignment"]))
    if isinstance(sanitized.get("knowledge_semantic_model"), dict):
        sanitized["knowledge_semantic_model"] = _compact_status_report(dict(sanitized["knowledge_semantic_model"]))
    if isinstance(sanitized.get("feature_layer"), dict):
        layer = dict(sanitized["feature_layer"])
        layer["features"] = [_compact_feature(row) for row in layer.get("features", [])[:24] if isinstance(row, dict)]
        layer["macro_features"] = [_compact_feature(row) for row in layer.get("macro_features", [])[:12] if isinstance(row, dict)]
        layer["discovery_trace"] = _compact_status_report(dict(layer.get("discovery_trace", {}))) if isinstance(layer.get("discovery_trace"), dict) else {}
        sanitized["feature_layer"] = layer
    if isinstance(sanitized.get("feature_state_model"), dict):
        sanitized["feature_state_model"] = _compact_feature_state_model(dict(sanitized["feature_state_model"]))
    if isinstance(sanitized.get("structure_dynamics"), dict):
        sanitized["structure_dynamics"] = _compact_structure_dynamics(dict(sanitized["structure_dynamics"]))
    if isinstance(sanitized.get("question_intent_model"), dict):
        sanitized["question_intent_model"] = _compact_question_intent_model(dict(sanitized["question_intent_model"]))
    if isinstance(sanitized.get("llm_assist"), dict):
        sanitized["llm_assist"] = _compact_llm_assist(dict(sanitized["llm_assist"]))
    if isinstance(sanitized.get("orchestrator_evidence"), dict):
        evidence = dict(sanitized["orchestrator_evidence"])
        sanitized["orchestrator_evidence"] = {
            "version": evidence.get("version", ""),
            "status": evidence.get("status", ""),
            "evidence_count": evidence.get("evidence_count", len(evidence.get("evidence_items", ())) if isinstance(evidence.get("evidence_items", ()), list | tuple) else 0),
            "candidate_mainline_count": evidence.get("candidate_mainline_count", len(evidence.get("candidate_mainlines", ())) if isinstance(evidence.get("candidate_mainlines", ()), list | tuple) else 0),
            "policy_input_count": evidence.get("policy_input_count", len(evidence.get("policy_inputs", ())) if isinstance(evidence.get("policy_inputs", ()), list | tuple) else 0),
            "evidence_items": [_compact_evidence_item(row) for row in evidence.get("evidence_items", [])[:12] if isinstance(row, dict)],
            "runtime_mutation": False,
            "guardrails": evidence.get("guardrails", ()),
        }
    sanitized["observation_payload_policy"] = {
        "version": "v20.observation_payload_policy.v1",
        "mode": "compact_default",
        "runtime_mutation": False,
        "guardrails": [
            "ADMIN_OBSERVATION_DEFAULTS_TO_COMPACT_PAYLOAD",
            "FULL_RUNTIME_CAN_BE_EXPOSED_BY_DEDICATED_DEBUG_ENDPOINT",
            "COMPACTION_DOES_NOT_CHANGE_RUNTIME_DECISION",
        ],
    }
    return sanitized


def _compact_decision_report(report: dict[str, object]) -> dict[str, object]:
    return {
        "version": report.get("version", ""),
        "status": report.get("status", ""),
        "hit_count": report.get("hit_count", 0),
        "decision_count": report.get("decision_count", 0),
        "mainline_count": report.get("mainline_count", 0),
        "hits": [_compact_hit(row) for row in report.get("hits", [])[:24] if isinstance(row, dict)],
        "rule_runtime_hits": [_compact_hit(row) for row in report.get("rule_runtime_hits", [])[:80] if isinstance(row, dict)],
        "decisions": [_compact_decision(row) for row in report.get("decisions", [])[:48] if isinstance(row, dict)],
        "mainlines": list(report.get("mainlines", [])[:16]) if isinstance(report.get("mainlines", []), list | tuple) else [],
        "practitioner_controls": list(report.get("practitioner_controls", [])[:16]) if isinstance(report.get("practitioner_controls", []), list | tuple) else [],
        "portrait_projection": _compact_portrait_projection(report.get("portrait_projection", {})),
        "knowledge_rule_bridge": _compact_status_report(dict(report.get("knowledge_rule_bridge", {}))) if isinstance(report.get("knowledge_rule_bridge"), dict) else {},
        "rule_runtime_source": report.get("rule_runtime_source", ""),
        "core_seed_decision_status": report.get("core_seed_decision_status", ""),
        "runtime_mutation": False,
    }


def _compact_decision(row: dict[str, object]) -> dict[str, object]:
    return {
        "decision_key": row.get("decision_key", ""),
        "rule_key": row.get("rule_key", ""),
        "label": row.get("label", ""),
        "domain": row.get("domain", ""),
        "status": row.get("status", ""),
        "score": row.get("score", 0),
        "support": list(row.get("support", [])[:4]) if isinstance(row.get("support", []), list | tuple) else [],
        "missing_evidence": list(row.get("missing_evidence", [])[:3]) if isinstance(row.get("missing_evidence", []), list | tuple) else [],
        "portrait_tags": list(row.get("portrait_tags", [])[:4]) if isinstance(row.get("portrait_tags", []), list | tuple) else [],
        "knowledge_rule_refs": [_compact_knowledge_ref(ref) for ref in row.get("knowledge_rule_refs", [])[:2] if isinstance(ref, dict)],
    }


def _compact_hit(row: dict[str, object]) -> dict[str, object]:
    return {
        "rule_key": row.get("rule_key", ""),
        "title": row.get("title", row.get("label", "")),
        "label": row.get("label", row.get("title", "")),
        "domain": row.get("domain", ""),
        "status": row.get("status", row.get("match_status", "")),
        "match_status": row.get("match_status", row.get("status", "")),
        "score": row.get("score", row.get("match_score", 0)),
        "match_score": row.get("match_score", row.get("score", 0)),
        "condition_count": row.get("condition_count", 0),
        "matched_condition_count": row.get("matched_condition_count", 0),
    }


def _compact_feature(row: dict[str, object]) -> dict[str, object]:
    return {
        "feature_id": row.get("feature_id", row.get("macro_id", "")),
        "macro_id": row.get("macro_id", ""),
        "title": row.get("title", row.get("label", "")),
        "label": row.get("label", row.get("title", "")),
        "domain": row.get("domain", ""),
        "confidence": row.get("confidence", row.get("peak_confidence", 0)),
        "peak_confidence": row.get("peak_confidence", row.get("confidence", 0)),
        "readiness": row.get("readiness", ""),
        "state": row.get("state", ""),
        "question_hooks": list(row.get("question_hooks", [])[:3]) if isinstance(row.get("question_hooks", []), list | tuple) else [],
        "support": list(row.get("support", [])[:3]) if isinstance(row.get("support", []), list | tuple) else [],
    }


def _compact_feature_state_model(model: dict[str, object]) -> dict[str, object]:
    compact = {
        "version": model.get("version", ""),
        "status": model.get("status", ""),
        "algorithm": model.get("algorithm", ""),
        "feature_state_count": model.get("feature_state_count", model.get("state_count", 0)),
        "state_count": model.get("state_count", model.get("feature_state_count", 0)),
        "priority_count": model.get("priority_count", 0),
        "runtime_mutation": False,
        "guardrails": model.get("guardrails", ()),
    }
    for key in ("priority_features", "states"):
        if isinstance(model.get(key), list | tuple):
            compact[key] = [_compact_feature(row) for row in model[key][:16] if isinstance(row, dict)]
    return compact


def _compact_question_intent_model(model: dict[str, object]) -> dict[str, object]:
    return {
        "version": model.get("version", ""),
        "status": model.get("status", ""),
        "algorithm": model.get("algorithm", ""),
        "intent_count": model.get("intent_count", 0),
        "question_binding_count": model.get("question_binding_count", 0),
        "intent_type_counts": model.get("intent_type_counts", {}),
        "selected_question_intent": model.get("selected_question_intent", {}),
        "question_bindings": [
            {
                "question_key": row.get("question_key", ""),
                "title": row.get("title", ""),
                "domain": row.get("domain", ""),
                "primary_intent_type": row.get("primary_intent_type", ""),
                "intent_priority": row.get("intent_priority", 0),
            }
            for row in model.get("question_bindings", [])[:16]
            if isinstance(row, dict)
        ],
        "runtime_mutation": False,
        "guardrails": model.get("guardrails", ()),
    }


def _compact_structure_dynamics(dynamics: dict[str, object]) -> dict[str, object]:
    sde_v2 = dynamics.get("sde_v2", {}) if isinstance(dynamics.get("sde_v2"), dict) else {}
    return {
        "version": dynamics.get("version", ""),
        "status": dynamics.get("status", ""),
        "source": dynamics.get("source", ""),
        "dynamic_state": dynamics.get("dynamic_state", {}),
        "primary_dynamic_chain": dynamics.get("primary_dynamic_chain", {}),
        "primary_dynamic_chain_source": dynamics.get("primary_dynamic_chain_source", ""),
        "candidate_paths": dynamics.get("candidate_paths", [])[:8] if isinstance(dynamics.get("candidate_paths"), list) else [],
        "semantic_candidates": dynamics.get("semantic_candidates", [])[:8] if isinstance(dynamics.get("semantic_candidates"), list) else [],
        "sde_v2": {
            "version": sde_v2.get("version", ""),
            "algorithm": sde_v2.get("algorithm", ""),
            "runtime_policy": sde_v2.get("runtime_policy", {}),
            "path_diagnostics": sde_v2.get("path_diagnostics", {}),
            "path_count": sde_v2.get("path_count", 0),
            "node_count": sde_v2.get("node_count", 0),
            "edge_count": sde_v2.get("edge_count", 0),
        },
        "chain_state": dynamics.get("chain_state", ""),
        "energy_shift": dynamics.get("energy_shift", ""),
        "stability_shift": dynamics.get("stability_shift", ""),
        "volatility_score": dynamics.get("volatility_score", 0),
        "runtime_mutation": False,
        "guardrails": dynamics.get("guardrails", ()),
    }


def _compact_llm_assist(assist: dict[str, object]) -> dict[str, object]:
    context = assist.get("context_pack", {}) if isinstance(assist.get("context_pack"), dict) else {}
    safety = assist.get("answer_safety_review", {}) if isinstance(assist.get("answer_safety_review"), dict) else {}
    return {
        "version": assist.get("version", ""),
        "status": assist.get("status", ""),
        "routed_question_key": assist.get("routed_question_key", ""),
        "answer_rewrite": _compact_status_report(dict(assist.get("answer_rewrite", {}))) if isinstance(assist.get("answer_rewrite"), dict) else {},
        "practitioner_answer": _compact_status_report(dict(assist.get("practitioner_answer", {}))) if isinstance(assist.get("practitioner_answer"), dict) else {},
        "answer_safety_review": _compact_status_report(safety),
        "context_pack": {
            "version": context.get("version", ""),
            "publishable": context.get("publishable", False),
            "runtime_mutation": False,
            "task_context_count": len(context.get("task_contexts", {})) if isinstance(context.get("task_contexts"), dict) else 0,
            "knowledge_ref_count": context.get("knowledge_ref_count", 0),
            "user_text_present": context.get("user_text_present", False),
        },
        "runtime_mutation": False,
    }


def _compact_evidence_item(row: dict[str, object]) -> dict[str, object]:
    return {
        "evidence_id": row.get("evidence_id", ""),
        "source_type": row.get("source_type", ""),
        "domain": row.get("domain", ""),
        "label": row.get("label", ""),
        "summary": row.get("summary", ""),
        "confidence": row.get("confidence", 0),
        "boundary": row.get("boundary", ""),
    }


def _compact_knowledge_ref(row: dict[str, object]) -> dict[str, object]:
    return {
        "knowledge_id": row.get("knowledge_id", row.get("source_knowledge_id", "")),
        "source_knowledge_id": row.get("source_knowledge_id", row.get("knowledge_id", "")),
        "rule_key": row.get("rule_key", ""),
        "title": row.get("title", ""),
        "domain": row.get("domain", ""),
        "reviewed": row.get("reviewed", True),
        "evidence_template": row.get("evidence_template", ""),
        "runtime_allowed": row.get("runtime_allowed", True),
        "synthetic_state": row.get("synthetic_state", ""),
        "question_outputs": list(row.get("question_outputs", [])[:2]) if isinstance(row.get("question_outputs", []), list | tuple) else [],
    }


def _compact_portrait_projection(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    projection = dict(value)
    projection["axes"] = [
        {
            "axis_id": row.get("axis_id", ""),
            "label": row.get("label", ""),
            "domain": row.get("domain", ""),
            "confidence": row.get("confidence", 0),
            "evidence_boundaries": list(row.get("evidence_boundaries", [])[:3]) if isinstance(row.get("evidence_boundaries", []), list | tuple) else [],
        }
        for row in projection.get("axes", [])[:16]
        if isinstance(row, dict)
    ]
    return projection


def _compact_status_report(report: dict[str, object]) -> dict[str, object]:
    keys = (
        "version",
        "status",
        "ok",
        "count",
        "definition_count",
        "candidate_count",
        "mapped_decision_count",
        "library_definition_count",
        "validation_status",
        "activation_status",
        "runtime_mutation",
        "guardrails",
    )
    compact = {key: report[key] for key in keys if key in report}
    if "domains" in report:
        compact["domains"] = report["domains"]
    if "mapping_coverage" in report:
        compact["mapping_coverage"] = report["mapping_coverage"]
    return compact


def _sanitize_user_payload(payload: dict[str, object], role_key: str) -> dict[str, object]:
    sanitized = dict(payload)
    sanitized["questions"] = [_public_question(row, role_key) for row in sanitized.get("questions", []) if isinstance(row, dict)]
    if isinstance(sanitized.get("selected_question"), dict):
        sanitized["selected_question"] = _public_question(sanitized["selected_question"], role_key)
    if isinstance(sanitized.get("measurement_report"), dict):
        report = dict(sanitized["measurement_report"])
        report["topics"] = [
            {
                "topic_key": row.get("topic_key", ""),
                "label": row.get("label", ""),
                "stage": row.get("stage", ""),
                "status": row.get("status", ""),
                "confidence": row.get("confidence", 0),
                "question_keys": row.get("question_keys", ()),
                "boundary": row.get("boundary", ""),
                "role": row.get("role", ""),
            }
            for row in report.get("topics", [])
            if isinstance(row, dict)
        ]
        sanitized["measurement_report"] = report
    if isinstance(sanitized.get("decision_report"), dict):
        report = dict(sanitized["decision_report"])
        report = {
            "version": report.get("version", ""),
            "status": report.get("status", ""),
            "hit_count": report.get("hit_count", 0),
            "decision_count": report.get("decision_count", 0),
            "mainline_count": report.get("mainline_count", 0),
            "runtime_mutation": False,
        }
        sanitized["decision_report"] = report
    if isinstance(sanitized.get("feature_state_model"), dict):
        model = dict(sanitized["feature_state_model"])
        sanitized["feature_state_model"] = {
            "version": model.get("version", ""),
            "status": model.get("status", ""),
            "algorithm": model.get("algorithm", ""),
            "state_count": model.get("state_count", 0),
            "priority_count": model.get("priority_count", 0),
            "runtime_mutation": False,
        }
    if isinstance(sanitized.get("structure_dynamics"), dict):
        sanitized["structure_dynamics"] = _compact_structure_dynamics(dict(sanitized["structure_dynamics"]))
    if isinstance(sanitized.get("question_intent_model"), dict):
        model = dict(sanitized["question_intent_model"])
        model["intents"] = []
        model["question_bindings"] = [
            {
                "question_key": row.get("question_key", ""),
                "title": row.get("title", ""),
                "domain": row.get("domain", ""),
                "primary_intent_type": row.get("primary_intent_type", ""),
                "intent_priority": row.get("intent_priority", 0),
            }
            for row in model.get("question_bindings", [])
            if isinstance(row, dict)
        ]
        sanitized["question_intent_model"] = model
    if isinstance(sanitized.get("interaction_session"), dict):
        session = dict(sanitized["interaction_session"])
        session["signals"] = [
            {
                "signal_type": row.get("signal_type", ""),
                "domain": row.get("domain", ""),
                "strength": row.get("strength", 0),
                "effect": row.get("effect", ""),
                "primary_intent_type": row.get("primary_intent_type", ""),
            }
            for row in session.get("signals", [])
            if isinstance(row, dict)
        ]
        sanitized["interaction_session"] = session
    if isinstance(sanitized.get("mainline_arbitration"), dict):
        arbitration = dict(sanitized["mainline_arbitration"])
        arbitration["evidence_items"] = [
            {
                "evidence_id": row.get("evidence_id", ""),
                "source_type": row.get("source_type", ""),
                "domain": row.get("domain", ""),
                "label": row.get("label", ""),
                "summary": row.get("summary", ""),
                "confidence": row.get("confidence", 0),
                "boundary": row.get("boundary", ""),
            }
            for row in arbitration.get("evidence_items", [])
            if isinstance(row, dict) and "user" in row.get("role_visibility", [])
        ][:8]
        sanitized["mainline_arbitration"] = arbitration
    if isinstance(sanitized.get("brain_state"), dict):
        state = dict(sanitized["brain_state"])
        sanitized["brain_state"] = {
            "version": state.get("version", ""),
            "status": state.get("status", ""),
            "mode": state.get("mode", ""),
            "public_summary": state.get("public_summary", {}),
            "runtime_mutation": False,
            "guardrails": state.get("guardrails", ()),
        }
    return sanitized


def _public_question(row: dict[str, object], role_key: str) -> dict[str, object]:
    display_title = row.get("display_title", "") or row.get("title", "")
    public = {
        "question_key": row.get("question_key", ""),
        "question_id": row.get("question_id", ""),
        "title": display_title,
        "display_title": display_title,
        "domain": row.get("domain", ""),
        "question_strategy": row.get("question_strategy", ""),
        "role_view_level": row.get("role_view_level", ""),
        "role_view_source": row.get("role_view_source", ""),
        "measurement_topic": row.get("measurement_topic", ""),
        "measurement_stage": row.get("measurement_stage", ""),
        "seed_source_key": row.get("seed_source_key", ""),
        "next_question_atom_id": row.get("next_question_atom_id", ""),
        "next_question_topic": row.get("next_question_topic", ""),
        "next_question_stage": row.get("next_question_stage", ""),
        "next_question_score_reasons": list(row.get("next_question_score_reasons", ()))
        if isinstance(row.get("next_question_score_reasons", ()), list | tuple)
        else [],
        "role": row.get("role", ""),
        "question_narrative": row.get("question_narrative", {}),
        "question_anchor": _public_question_anchor(row.get("question_anchor", {}), role_key),
    }
    if role_key != "guest":
        public |= {
            "score": row.get("score", 0),
            "next_question_score": row.get("next_question_score", 0),
            "source_decision_key": row.get("source_decision_key", ""),
            "source_decision_status": row.get("source_decision_status", ""),
            "source_decision_label": row.get("source_decision_label", ""),
            "source_title": row.get("source_title", ""),
        }
    return public


def _public_question_anchor(anchor: object, role_key: str) -> dict[str, object]:
    if not isinstance(anchor, dict):
        return {}
    base = {
        "anchor_status": anchor.get("anchor_status", ""),
        "context_id": anchor.get("context_id", ""),
        "day_master": anchor.get("day_master", ""),
        "primary_dynamic_chain_label": anchor.get("primary_dynamic_chain_label", ""),
        "luck_pillar": anchor.get("luck_pillar", ""),
        "flow_year_pillar": anchor.get("flow_year_pillar", ""),
        "why_this_question": anchor.get("why_this_question", ""),
    }
    if role_key in {"admin", "lab", "analyst", "practitioner"}:
        base |= {
            "missing_requirements": list(anchor.get("missing_requirements", [])[:6])
            if isinstance(anchor.get("missing_requirements", []), list | tuple)
            else [],
            "evidence_refs": list(anchor.get("evidence_refs", [])[:6])
            if isinstance(anchor.get("evidence_refs", []), list | tuple)
            else [],
        }
    return base
