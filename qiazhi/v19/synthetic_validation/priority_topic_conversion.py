from __future__ import annotations

from typing import Any, Dict, List

from v19.knowledge_base_audit import run_p31_all_knowledge_coverage_audit
from v19.synthetic_validation.ten_god_conflict_matrix import P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES


P31C_PRIORITY_TOPIC_CONVERSION_VERSION = "v19.p31c.priority_topic_conversion_registry.v1"
P31C_PRIORITY_TOPIC_EVAL_VERSION = "v19.p31c.priority_topic_eval_dataset.v1"
P31C_PRIORITY_TOPIC_REGRESSION_VERSION = "v19.p31c.priority_topic_regression.v1"
P31D_PRIORITY_TOPIC_SMART_GATE_VERSION = "v19.p31d.priority_topic_smart_gate.v1"
P31E_PRIORITY_TOPIC_RULE_PROPOSAL_VERSION = "v19.p31e.priority_topic_rule_proposal_generation.v1"
P31F_PRIORITY_TOPIC_REVIEW_PACKET_VERSION = "v19.p31f.priority_topic_review_packet.v1"
P31G_PRIORITY_TOPIC_DECISION_PREFLIGHT_VERSION = "v19.p31g.priority_topic_decision_preflight.v1"
P31H_PRIORITY_TOPIC_CONTROLLED_APPROVAL_VERSION = "v19.p31h.priority_topic_controlled_approval.v1"
P31I_PRIORITY_TOPIC_RULE_VERSION_VERSION = "v19.p31i.priority_topic_rule_version.v1"
P31J_PRIORITY_TOPIC_GOVERNANCE_RELEASE_VERSION = "v19.p31j.priority_topic_governance_release.v1"
P31K_PRIORITY_TOPIC_RULE_DB_CANDIDATES_VERSION = "v19.p31k.priority_topic_rule_db_candidates.v1"
P31L_PRIORITY_TOPIC_ADAPTER_READINESS_VERSION = "v19.p31l.priority_topic_adapter_readiness.v1"
P31M_PRIORITY_TOPIC_ADAPTER_FACTS_VERSION = "v19.p31m.priority_topic_adapter_facts.v1"

P31C_GUARDRAILS = [
    "TOPIC_CONVERSION_REGISTRY_ONLY",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_FORTUNE",
    "NO_DOMAIN_RESULT_PREDICTION",
    "CONDITION_MODEL_AND_EVAL_REQUIRED",
    "HIGH_RISK_ARCHIVE_FIRST",
]
P31D_GUARDRAILS = [
    "SMART_GATE_DRY_RUN_ONLY",
    "P31C_REGRESSION_REQUIRED",
    "LOW_RISK_SHADOW_PROPOSAL_ONLY",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_DOMAIN_RESULT_PREDICTION",
    "AUDITABLE_BLOCKERS_REQUIRED",
]
P31E_GUARDRAILS = [
    "RULE_PROPOSAL_GENERATION_ONLY",
    "P31D_SHADOW_GATE_REQUIRED",
    "VALIDATION_REQUIRED",
    "NO_APPROVAL_MUTATION",
    "NO_VERSION_RECORD",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_DOMAIN_RESULT_PREDICTION",
]
P31F_GUARDRAILS = [
    "REVIEW_PACKET_ONLY",
    "P31E_VALIDATION_READY_REQUIRED",
    "NO_APPROVAL_MUTATION",
    "NO_APPROVAL_PREFLIGHT",
    "NO_VERSION_RECORD",
    "NO_RUNTIME_RULE_ACTIVATION",
]
P31G_GUARDRAILS = [
    "DECISION_LEDGER_AND_PREFLIGHT_ONLY",
    "P31F_REVIEW_PACKET_REQUIRED",
    "ITEM_SCOPED_DECISIONS_REQUIRED",
    "NO_APPROVAL_EXECUTION",
    "NO_PROPOSAL_STATUS_MUTATION",
    "NO_VERSION_RECORD",
    "NO_RUNTIME_RULE_ACTIVATION",
]
P31H_GUARDRAILS = [
    "CONTROLLED_APPROVAL_ONLY",
    "P31G_PREFLIGHT_REQUIRED",
    "APPROVE_VALIDATION_READY_PROPOSALS_ONLY",
    "NO_VERSION_RECORD",
    "NO_RUNTIME_RULE_ACTIVATION",
]
P31I_GUARDRAILS = [
    "RULE_VERSION_RECORD_ONLY",
    "P31H_APPROVAL_REQUIRED",
    "P12_SYNTHETIC_REGRESSION_REQUIRED",
    "P31E_PROPOSALS_ONLY",
    "NO_RUNTIME_RULE_ACTIVATION",
]
P31J_GUARDRAILS = [
    "GOVERNANCE_RELEASE_RECORD_ONLY",
    "P31I_RULE_VERSION_REQUIRED",
    "P11_SYNTHETIC_REGRESSION_REQUIRED",
    "NO_RUNTIME_RULE_ACTIVATION",
]
P31K_GUARDRAILS = [
    "RULE_DB_CANDIDATE_INGESTION_ONLY",
    "P31J_GOVERNANCE_RELEASE_REQUIRED",
    "ENGINE_DISABLED_BY_DEFAULT",
    "NO_RUNTIME_RULE_ACTIVATION",
]
P31L_GUARDRAILS = [
    "ADAPTER_READINESS_REPORT_ONLY",
    "P31K_RULE_DB_CANDIDATES_REQUIRED",
    "NO_ENGINE_ACTIVATION",
    "NO_RUNTIME_RULE_ACTIVATION",
]
P31M_GUARDRAILS = [
    "ADAPTER_FACT_ENRICHMENT_ONLY",
    "P31K_RULE_DB_CANDIDATES_REQUIRED",
    "SYNTHETIC_GATE_MARKER_ONLY",
    "ENGINE_DISABLED",
    "NO_RUNTIME_RULE_ACTIVATION",
]


def build_p31c_priority_topic_conversion_registry() -> Dict[str, Any]:
    audit = run_p31_all_knowledge_coverage_audit()
    high_priority = [row for row in audit.get("gap_backlog") or [] if row.get("priority") in {"P0", "P1"}]
    existing_chain = _existing_ten_god_chain()
    models = [_model_from_spec(spec) for spec in _topic_model_specs()]
    samples = [sample for model in models for sample in _samples_for_model(model)]
    lanes = _lane_summary(models)
    return {
        "ok": True,
        "version": P31C_PRIORITY_TOPIC_CONVERSION_VERSION,
        "status": "priority_topic_conversion_ready_no_activation",
        "summary": {
            "high_priority_partial_count": len(high_priority),
            "existing_ten_god_chain_case_count": len(existing_chain),
            "new_condition_model_count": len(models),
            "eval_sample_requirement_count": len(samples),
            "activation_updated_count": 0,
            "by_lane": {row["lane"]: row["model_count"] for row in lanes},
            "by_priority": _count_by(models, "priority"),
        },
        "lanes": lanes,
        "existing_converted_chain": existing_chain,
        "models": models,
        "eval_dataset": {
            "version": P31C_PRIORITY_TOPIC_EVAL_VERSION,
            "sample_count": len(samples),
            "by_polarity": _count_by(samples, "polarity"),
            "samples": samples,
        },
        "conversion_policy": {
            "already_done": "Ten-god interaction mechanisms are already in the P28J-P30 condition/eval/shadow/scoring/arbitration chain.",
            "now": "Pattern, time activation, wealth/career bridges are promoted to condition models and eval requirements.",
            "later": "Archive/high-risk domains remain non-runtime until a dedicated safety model exists.",
        },
        "guardrails": P31C_GUARDRAILS,
    }


def run_p31c_priority_topic_regression() -> Dict[str, Any]:
    registry = build_p31c_priority_topic_conversion_registry()
    samples = [dict(row) for row in registry["eval_dataset"]["samples"]]
    sample_results = [_evaluate_sample(sample) for sample in samples]
    model_results = _model_results(samples)
    failures = [failure for row in sample_results for failure in row.get("failures") or []]
    failures.extend(failure for row in model_results for failure in row.get("failures") or [])
    false_positive_count = sum(1 for row in sample_results if row.get("false_positive"))
    forbidden_text_failure_count = sum(
        1
        for failure in failures
        if failure.get("failure_type") == "forbidden_text_contract_failed"
    )
    status = "pass" if not failures and false_positive_count == 0 and forbidden_text_failure_count == 0 else "fail"
    return {
        "ok": status == "pass",
        "version": P31C_PRIORITY_TOPIC_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "model_count": len(model_results),
            "sample_count": len(samples),
            "sample_passed": sum(1 for row in sample_results if row.get("status") == "pass"),
            "sample_failed": sum(1 for row in sample_results if row.get("status") == "fail"),
            "false_positive_count": false_positive_count,
            "forbidden_text_failure_count": forbidden_text_failure_count,
            "model_failed": sum(1 for row in model_results if row.get("status") == "fail"),
            "activation_updated_count": 0,
            "by_polarity": _count_by(samples, "polarity"),
        },
        "samples": sample_results,
        "models": model_results,
        "failures": failures,
        "activation_policy": {
            "p31c": "No topic rule activation. P31C validates the conversion registry and eval contracts only.",
            "next": "P31D may attach topic-specific interpreters or smart gates after this regression stays green.",
        },
        "guardrails": P31C_GUARDRAILS,
    }


def run_p31d_priority_topic_smart_gate(*, activate: bool = False) -> Dict[str, Any]:
    registry = build_p31c_priority_topic_conversion_registry()
    regression = run_p31c_priority_topic_regression()
    model_results = {str(row.get("model_id") or ""): dict(row) for row in regression.get("models") or []}
    gate_rows = [_p31d_gate_row(model, model_results.get(str(model.get("model_id") or "")), regression) for model in registry.get("models") or []]
    selected = [row for row in gate_rows if row["eligible"]]
    blocked = [row for row in gate_rows if not row["eligible"]]
    status = "dry_run_ready" if regression.get("status") == "pass" and selected and not activate else "blocked"
    if activate:
        status = "blocked"
    return {
        "ok": status == "dry_run_ready",
        "version": P31D_PRIORITY_TOPIC_SMART_GATE_VERSION,
        "status": status,
        "summary": {
            "model_count": len(gate_rows),
            "selected_shadow_proposal_count": len(selected),
            "blocked_count": len(blocked),
            "activation_updated_count": 0,
            "p31c_regression_status": regression.get("status"),
            "blocked_by_reason": _blocked_reason_counts(blocked),
            "selected_by_lane": _count_by(selected, "lane"),
        },
        "selected": selected,
        "blocked": blocked,
        "activation": {
            "requested": activate,
            "updated_count": 0,
            "status": "blocked_no_runtime_activation" if activate else "not_requested",
        },
        "gate_policy": {
            "eligible": "R1/R2 topic condition models with passing P31C regression may become shadow proposal-ready.",
            "blocked": "R3 or archive-first models remain blocked until a dedicated interpreter and safety review exists.",
            "activation": "P31D never activates runtime rules; it only prepares auditable proposal-ready candidates.",
        },
        "guardrails": P31D_GUARDRAILS,
    }


def run_p31e_priority_topic_rule_proposal_generation(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from v19 import lab_interfaces as lab

    registry = build_p31c_priority_topic_conversion_registry()
    gate = run_p31d_priority_topic_smart_gate()
    if gate.get("status") != "dry_run_ready":
        return {
            "ok": False,
            "version": P31E_PRIORITY_TOPIC_RULE_PROPOSAL_VERSION,
            "status": "blocked_by_p31d_gate",
            "summary": {
                "gate_selected_count": 0,
                "created_rule_proposal_count": 0,
                "validation_ready_count": 0,
                "validation_failed_count": 0,
                "activation_updated_count": 0,
            },
            "gate": gate,
            "items": [],
            "guardrails": P31E_GUARDRAILS,
        }
    models_by_id = {str(row.get("model_id") or ""): dict(row) for row in registry.get("models") or []}
    items: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    for selected in gate.get("selected") or []:
        model_id = str(selected.get("model_id") or "")
        model = models_by_id.get(model_id) or {}
        payload = _p31e_rule_proposal_payload(model, selected)
        created = lab.create_bazi_rule_proposal(payload, settings)
        if created.get("ok") is False:
            errors.append({"model_id": model_id, "stage": "create", "code": created.get("code"), "message": created.get("message")})
            continue
        proposal = dict(created.get("item") or {})
        validated = lab.validate_bazi_rule_proposal(str(proposal.get("proposal_id") or ""), settings)
        if validated.get("ok") is False or not validated.get("passed"):
            errors.append(
                {
                    "model_id": model_id,
                    "stage": "validate",
                    "proposal_id": proposal.get("proposal_id"),
                    "code": validated.get("code"),
                    "checks": validated.get("checks"),
                }
            )
        item = dict(validated.get("item") or proposal)
        items.append(
            {
                "model_id": model_id,
                "topic": model.get("topic") or selected.get("topic"),
                "lane": model.get("lane") or selected.get("lane"),
                "risk_level": model.get("risk_level") or selected.get("risk_level"),
                "proposal_id": item.get("proposal_id"),
                "rule_id": item.get("rule_id"),
                "domain": item.get("domain"),
                "status": item.get("status"),
                "validation_passed": bool((item.get("validation") or {}).get("passed")),
                "runtime_mutation": False,
            }
        )
    validation_ready = [row for row in items if row.get("status") == "validation_ready" and row.get("validation_passed")]
    validation_failed = [row for row in items if row.get("status") == "validation_failed" or not row.get("validation_passed")]
    status = "proposal_generation_ready" if len(validation_ready) == len(gate.get("selected") or []) and not errors else "proposal_generation_partial"
    return {
        "ok": status == "proposal_generation_ready",
        "version": P31E_PRIORITY_TOPIC_RULE_PROPOSAL_VERSION,
        "status": status,
        "summary": {
            "gate_selected_count": len(gate.get("selected") or []),
            "created_rule_proposal_count": len(items),
            "validation_ready_count": len(validation_ready),
            "validation_failed_count": len(validation_failed),
            "error_count": len(errors),
            "activation_updated_count": 0,
            "approval_mutation": False,
            "version_mutation": False,
            "runtime_mutation": False,
            "by_domain": _count_by(items, "domain"),
            "by_lane": _count_by(items, "lane"),
        },
        "items": items,
        "errors": errors,
        "gate": {
            "version": gate.get("version"),
            "status": gate.get("status"),
            "summary": gate.get("summary"),
        },
        "proposal_policy": {
            "current_stage": "Create and validate Bazi rule proposals from P31D shadow-ready models.",
            "approval": "No approval mutation in P31E.",
            "runtime": "No Rule DB engine activation or runtime inference mutation in P31E.",
        },
        "guardrails": P31E_GUARDRAILS,
    }


def run_p31f_priority_topic_review_packet(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from v19 import lab_interfaces as lab

    generated = run_p31e_priority_topic_rule_proposal_generation(settings)
    proposal_ids = [str(row.get("proposal_id") or "") for row in generated.get("items") or [] if row.get("proposal_id")]
    if generated.get("status") != "proposal_generation_ready" or not proposal_ids:
        return {
            "ok": False,
            "version": P31F_PRIORITY_TOPIC_REVIEW_PACKET_VERSION,
            "status": "blocked_by_p31e",
            "summary": {
                "proposal_count": len(proposal_ids),
                "validation_run_count": 0,
                "review_packet_count": 0,
                "approval_mutation": False,
                "approval_preflight_mutation": False,
                "version_mutation": False,
                "runtime_mutation": False,
            },
            "p31e": generated,
            "guardrails": P31F_GUARDRAILS,
        }
    validation = lab.create_proposal_validation_run(
        {
            "actor_role": "system",
            "proposal_ids": proposal_ids,
            "note": "P31F validation run for P31E priority topic rule proposals. Review packet only; no approval mutation.",
        },
        settings,
    )
    validation_item = dict(validation.get("item") or {})
    packet = lab.create_proposal_review_packet(
        {
            "actor_role": "system",
            "validation_run_id": validation_item.get("validation_run_id"),
            "note": "P31F review packet for priority topic rule proposals. No approval/preflight/version/runtime mutation.",
        },
        settings,
    )
    packet_item = dict(packet.get("item") or {})
    ok = bool(validation.get("ok")) and bool(packet.get("ok")) and validation_item.get("status") == "validation_ready" and packet_item.get("status") == "approval_review_ready"
    return {
        "ok": ok,
        "version": P31F_PRIORITY_TOPIC_REVIEW_PACKET_VERSION,
        "status": "review_packet_ready" if ok else "blocked",
        "summary": {
            "proposal_count": len(proposal_ids),
            "validation_run_count": 1 if validation.get("ok") else 0,
            "validation_passed": int((validation_item.get("summary") or {}).get("passed") or 0),
            "validation_failed": int((validation_item.get("summary") or {}).get("failed") or 0),
            "review_packet_count": 1 if packet.get("ok") else 0,
            "review_packet_item_count": int((packet_item.get("summary") or {}).get("total") or 0),
            "approval_mutation": False,
            "approval_preflight_mutation": False,
            "version_mutation": False,
            "runtime_mutation": False,
        },
        "validation_run": {
            "validation_run_id": validation_item.get("validation_run_id"),
            "status": validation_item.get("status"),
            "summary": validation_item.get("summary"),
        },
        "review_packet": {
            "packet_id": packet_item.get("packet_id"),
            "status": packet_item.get("status"),
            "summary": packet_item.get("summary"),
        },
        "p31e": {
            "version": generated.get("version"),
            "status": generated.get("status"),
            "summary": generated.get("summary"),
        },
        "packet_policy": {
            "current_stage": "Create a review packet for validation-ready P31E rule proposals.",
            "blocked_actions": ["approval", "approval_preflight", "version_record", "runtime_activation"],
        },
        "guardrails": P31F_GUARDRAILS,
    }


def run_p31g_priority_topic_decision_preflight(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from v19 import lab_interfaces as lab

    packetized = run_p31f_priority_topic_review_packet(settings)
    packet_id = str((packetized.get("review_packet") or {}).get("packet_id") or "")
    if packetized.get("status") != "review_packet_ready" or not packet_id:
        return {
            "ok": False,
            "version": P31G_PRIORITY_TOPIC_DECISION_PREFLIGHT_VERSION,
            "status": "blocked_by_p31f",
            "summary": {
                "proposal_count": int((packetized.get("summary") or {}).get("proposal_count") or 0),
                "decision_record_count": 0,
                "approval_preflight_record_count": 0,
                "approval_execution_mutation": False,
                "proposal_status_mutation": False,
                "version_mutation": False,
                "runtime_mutation": False,
            },
            "p31f": packetized,
            "guardrails": P31G_GUARDRAILS,
        }
    packets = lab.list_proposal_review_packets(settings)
    packet = next((dict(row) for row in packets.get("items") or [] if row.get("packet_id") == packet_id), {})
    items = [dict(row) for row in packet.get("items") or [] if isinstance(row, dict)]
    decisions = [
        {
            "proposal_id": row.get("proposal_id"),
            "decision": "approve_candidate",
            "note": "P31G item-scoped decision candidate for preflight only; no approval execution.",
        }
        for row in items
        if row.get("kind") == "bazi_rule_proposal" and row.get("validation_passed") is True and row.get("proposal_id")
    ]
    decision_result = lab.record_proposal_review_packet_decision(
        packet_id,
        {
            "actor_role": "system",
            "decisions": decisions,
            "note": "P31G batch decision ledger for priority topic rule proposals.",
        },
        settings,
    )
    preflight = lab.create_proposal_review_approval_preflight(
        packet_id,
        {
            "actor_role": "system",
            "note": "P31G approval preflight only; no approval execution, versioning, or runtime activation.",
        },
        settings,
    )
    decision_records = [dict(row) for row in decision_result.get("decision_records") or [] if isinstance(row, dict)]
    preflight_item = dict(preflight.get("item") or {})
    preflight_summary = dict(preflight_item.get("summary") or {})
    status = "decision_preflight_ready" if decision_result.get("ok") and preflight.get("ok") else "blocked"
    return {
        "ok": status == "decision_preflight_ready",
        "version": P31G_PRIORITY_TOPIC_DECISION_PREFLIGHT_VERSION,
        "status": status,
        "summary": {
            "proposal_count": len(items),
            "decision_record_count": len(decision_records),
            "approve_candidate_count": len([row for row in decision_records if row.get("decision") == "approve_candidate"]),
            "approval_preflight_record_count": 1 if preflight_item else 0,
            "preflight_status": preflight_item.get("status", ""),
            "preflight_ready_item_count": int(preflight_summary.get("ready_item_count") or 0),
            "preflight_failed_checks": int(preflight_summary.get("failed_checks") or 0),
            "approval_execution_mutation": False,
            "proposal_status_mutation": False,
            "version_mutation": False,
            "runtime_mutation": False,
        },
        "decision": {
            "ok": bool(decision_result.get("ok")),
            "decision_record_count": len(decision_records),
            "decision_summary": (decision_result.get("item") or {}).get("decision_summary"),
        },
        "approval_preflight": {
            "ok": bool(preflight.get("ok")),
            "approval_preflight_id": preflight_item.get("approval_preflight_id"),
            "status": preflight_item.get("status"),
            "summary": preflight_summary,
        },
        "review_packet": {
            "packet_id": packet_id,
            "status": (preflight.get("packet") or {}).get("status") or packet.get("status"),
            "decision_summary": (preflight.get("packet") or {}).get("decision_summary"),
            "approval_preflight_summary": (preflight.get("packet") or {}).get("approval_preflight_summary"),
        },
        "p31f": {
            "version": packetized.get("version"),
            "status": packetized.get("status"),
            "summary": packetized.get("summary"),
        },
        "preflight_policy": {
            "current_stage": "Record item-scoped decision candidates and run approval preflight for P31F packet.",
            "blocked_actions": ["approval_execution", "version_record", "runtime_activation"],
        },
        "guardrails": P31G_GUARDRAILS,
    }


def run_p31h_priority_topic_controlled_approval(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from v19 import lab_interfaces as lab

    preflighted = run_p31g_priority_topic_decision_preflight(settings)
    packet_id = str((preflighted.get("review_packet") or {}).get("packet_id") or "")
    if preflighted.get("status") != "decision_preflight_ready" or not packet_id:
        return {
            "ok": False,
            "version": P31H_PRIORITY_TOPIC_CONTROLLED_APPROVAL_VERSION,
            "status": "blocked_by_p31g",
            "summary": {
                "proposal_count": int((preflighted.get("summary") or {}).get("proposal_count") or 0),
                "approval_execution_count": 0,
                "approved_count": 0,
                "failed_count": 0,
                "version_mutation": False,
                "runtime_mutation": False,
            },
            "p31g": preflighted,
            "guardrails": P31H_GUARDRAILS,
        }
    approved = lab.execute_proposal_review_packet_approval(
        packet_id,
        {
            "actor_role": "admin",
            "note": "P31H controlled approval after P31G preflight. Proposal status only; no version or runtime activation.",
        },
        settings,
    )
    approval_item = dict(approved.get("item") or {})
    approval_summary = dict(approval_item.get("summary") or {})
    status = "controlled_approval_executed" if approved.get("ok") else "blocked"
    return {
        "ok": status == "controlled_approval_executed",
        "version": P31H_PRIORITY_TOPIC_CONTROLLED_APPROVAL_VERSION,
        "status": status,
        "summary": {
            "proposal_count": int((preflighted.get("summary") or {}).get("proposal_count") or 0),
            "approval_execution_count": 1 if approval_item else 0,
            "approved_count": int(approval_summary.get("approved_count") or 0),
            "failed_count": int(approval_summary.get("failed_count") or 0),
            "rule_approved_count": int(approval_summary.get("rule_approved_count") or 0),
            "question_approved_count": int(approval_summary.get("question_approved_count") or 0),
            "controlled_approval_mutation": bool(approval_item.get("controlled_approval_mutation")),
            "auto_approval": bool(approval_item.get("auto_approval")),
            "version_mutation": False,
            "runtime_mutation": False,
        },
        "approval_execution": {
            "ok": bool(approved.get("ok")),
            "approval_execution_id": approval_item.get("approval_execution_id"),
            "status": approval_item.get("status"),
            "summary": approval_summary,
        },
        "p31g": {
            "version": preflighted.get("version"),
            "status": preflighted.get("status"),
            "summary": preflighted.get("summary"),
        },
        "approval_policy": {
            "current_stage": "Controlled approval of P31E proposals after decision ledger and preflight.",
            "allowed_mutation": "proposal_status_to_approved",
            "blocked_actions": ["version_record", "runtime_activation"],
        },
        "guardrails": P31H_GUARDRAILS,
    }


def run_p31i_priority_topic_rule_version_record(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from v19 import bazi_rule_db as rule_db
    from v19 import lab_interfaces as lab
    from v19.bazi_source_archive import seed_current_knowledge_drafts

    approved = run_p31h_priority_topic_controlled_approval(settings)
    if approved.get("status") != "controlled_approval_executed":
        return {
            "ok": False,
            "version": P31I_PRIORITY_TOPIC_RULE_VERSION_VERSION,
            "status": "blocked_by_p31h",
            "summary": {
                "approved_count": int((approved.get("summary") or {}).get("approved_count") or 0),
                "version_record_count": 0,
                "included_proposal_count": 0,
                "runtime_mutation": False,
            },
            "p31h": approved,
            "guardrails": P31I_GUARDRAILS,
        }
    proposals = [dict(row) for row in lab.list_bazi_rule_proposals(settings).get("items") or [] if isinstance(row, dict)]
    approved_ids = [
        str(row.get("proposal_id") or "")
        for row in proposals
        if row.get("status") == "approved"
        and str(row.get("rule_id") or "").startswith("v19.p31e.")
        and (dict(row.get("evidence") or {}).get("source") == "p31e_priority_topic_rule_proposal_generation")
        and row.get("proposal_id")
    ]
    if not approved_ids:
        return {
            "ok": False,
            "version": P31I_PRIORITY_TOPIC_RULE_VERSION_VERSION,
            "status": "blocked_no_approved_p31e_proposals",
            "summary": {
                "approved_count": int((approved.get("summary") or {}).get("approved_count") or 0),
                "version_record_count": 0,
                "included_proposal_count": 0,
                "runtime_mutation": False,
            },
            "p31h": approved,
            "guardrails": P31I_GUARDRAILS,
        }
    seed_result = seed_current_knowledge_drafts()
    regression_baseline = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    recorded = lab.record_bazi_rule_version(
        {
            "included_proposals": approved_ids,
            "activated_by": "p31i_priority_topic_rule_version",
            "activated_by_role": "admin",
            "note": "P31I version record for P31E priority topic rule proposals. No runtime activation.",
        },
        settings,
    )
    version_item = dict(recorded.get("item") or {})
    status = "rule_version_recorded" if recorded.get("ok") else "blocked"
    return {
        "ok": status == "rule_version_recorded",
        "version": P31I_PRIORITY_TOPIC_RULE_VERSION_VERSION,
        "status": status,
        "summary": {
            "approved_count": int((approved.get("summary") or {}).get("approved_count") or 0),
            "version_record_count": 1 if version_item else 0,
            "included_proposal_count": len(version_item.get("included_proposals") or []),
            "rule_count": int(version_item.get("rule_count") or 0),
            "proposal_status_mutation": status == "rule_version_recorded",
            "version_mutation": status == "rule_version_recorded",
            "runtime_mutation": False,
        },
        "rule_version": {
            "ok": bool(recorded.get("ok")),
            "version_id": version_item.get("version_id"),
            "rule_count": version_item.get("rule_count"),
            "included_proposal_count": len(version_item.get("included_proposals") or []),
            "runtime_mutation": bool(version_item.get("runtime_mutation")),
            "p12_regression_gate": version_item.get("p12_regression_gate"),
        },
        "regression_baseline": {
            "seed_count": seed_result.get("count", 0),
            "rule_db_rule_count": regression_baseline.get("rule_count", 0),
            "runtime_mutation": False,
        },
        "p31h": {
            "version": approved.get("version"),
            "status": approved.get("status"),
            "summary": approved.get("summary"),
        },
        "version_policy": {
            "current_stage": "Record approved P31E rule proposals as a Bazi rule version.",
            "allowed_mutation": "proposal_status_to_active_record_and_version_record",
            "blocked_actions": ["runtime_activation"],
        },
        "guardrails": P31I_GUARDRAILS,
    }


def run_p31j_priority_topic_governance_release(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from v19 import lab_interfaces as lab

    versioned = run_p31i_priority_topic_rule_version_record(settings)
    version_id = str((versioned.get("rule_version") or {}).get("version_id") or "")
    if versioned.get("status") != "rule_version_recorded" or not version_id:
        return {
            "ok": False,
            "version": P31J_PRIORITY_TOPIC_GOVERNANCE_RELEASE_VERSION,
            "status": "blocked_by_p31i",
            "summary": {
                "rule_version_count": int((versioned.get("summary") or {}).get("version_record_count") or 0),
                "governance_release_count": 0,
                "runtime_mutation": False,
            },
            "p31i": versioned,
            "guardrails": P31J_GUARDRAILS,
        }
    release = lab.create_governance_release(
        {
            "actor_role": "admin",
            "release_type": "p31j_priority_topic_rule_release",
            "bazi_rule_version_ids": [version_id],
            "note": "P31J governance release record for P31I priority topic rule version. No runtime activation.",
        },
        settings,
    )
    release_item = dict(release.get("item") or {})
    release_summary = dict(release_item.get("summary") or {})
    status = "governance_release_recorded" if release.get("ok") else "blocked"
    return {
        "ok": status == "governance_release_recorded",
        "version": P31J_PRIORITY_TOPIC_GOVERNANCE_RELEASE_VERSION,
        "status": status,
        "summary": {
            "rule_version_count": 1 if version_id else 0,
            "governance_release_count": 1 if release_item else 0,
            "artifact_count": int(release_summary.get("artifact_count") or 0),
            "bazi_rule_version_artifact_count": int(((release_summary.get("by_artifact_type") or {}).get("bazi_rule_versions")) or 0),
            "version_mutation": bool((versioned.get("summary") or {}).get("version_mutation")),
            "release_mutation": status == "governance_release_recorded",
            "runtime_mutation": False,
        },
        "governance_release": {
            "ok": bool(release.get("ok")),
            "release_id": release_item.get("release_id"),
            "status": release_item.get("status"),
            "release_type": release_item.get("release_type"),
            "summary": release_summary,
            "runtime_mutation": bool(release_item.get("runtime_mutation")),
        },
        "p31i": {
            "version": versioned.get("version"),
            "status": versioned.get("status"),
            "summary": versioned.get("summary"),
        },
        "release_policy": {
            "current_stage": "Record P31I rule version as a governance release artifact.",
            "blocked_actions": ["runtime_activation"],
        },
        "guardrails": P31J_GUARDRAILS,
    }


def run_p31k_priority_topic_rule_db_candidates(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from v19 import lab_interfaces as lab
    from v19 import bazi_rule_db as rule_db

    released = run_p31j_priority_topic_governance_release(settings)
    if released.get("status") != "governance_release_recorded":
        return {
            "ok": False,
            "version": P31K_PRIORITY_TOPIC_RULE_DB_CANDIDATES_VERSION,
            "status": "blocked_by_p31j",
            "summary": {
                "governance_release_count": int((released.get("summary") or {}).get("governance_release_count") or 0),
                "rule_db_candidate_count": 0,
                "engine_enabled_count": 0,
                "runtime_mutation": False,
            },
            "p31j": released,
            "guardrails": P31K_GUARDRAILS,
        }
    versions = [dict(row) for row in lab.list_bazi_rule_versions(settings).get("items") or [] if isinstance(row, dict)]
    version_item = versions[0] if versions else {}
    proposals = [dict(row) for row in lab.list_bazi_rule_proposals(settings).get("items") or [] if isinstance(row, dict)]
    ingested = rule_db.ingest_rule_version_proposals_to_rule_db(
        version_item,
        proposals,
        enable_engine=False,
        source_stage="P31K_PRIORITY_TOPIC_RULE_DB_CANDIDATES",
    )
    p31_rules = [dict(row) for row in rule_db.list_bazi_rules(q="v19.p31e.").get("items") or [] if isinstance(row, dict)]
    engine_enabled_count = len([row for row in p31_rules if row.get("engine_enabled") is True])
    status = "rule_db_candidates_ingested" if ingested.get("ok") and len(p31_rules) == 22 and engine_enabled_count == 0 else "blocked"
    return {
        "ok": status == "rule_db_candidates_ingested",
        "version": P31K_PRIORITY_TOPIC_RULE_DB_CANDIDATES_VERSION,
        "status": status,
        "summary": {
            "governance_release_count": int((released.get("summary") or {}).get("governance_release_count") or 0),
            "rule_version_count": len(versions),
            "versioned_proposal_count": len(version_item.get("included_proposals") or []),
            "rule_db_candidate_count": len(p31_rules),
            "imported_count": int(ingested.get("imported_count") or 0),
            "updated_count": int(ingested.get("updated_count") or 0),
            "blocked_count": int(ingested.get("blocked_count") or 0),
            "engine_enabled_count": engine_enabled_count,
            "runtime_mutation": False,
        },
        "rule_db_ingestion": {
            "ok": bool(ingested.get("ok")),
            "status": ingested.get("status"),
            "version_id": ingested.get("version_id"),
            "proposal_count": ingested.get("proposal_count"),
            "imported_count": ingested.get("imported_count"),
            "updated_count": ingested.get("updated_count"),
            "blocked_count": ingested.get("blocked_count"),
            "engine_enabled_count": ingested.get("engine_enabled_count"),
            "runtime_mutation": bool(ingested.get("runtime_mutation")),
        },
        "p31j": {
            "version": released.get("version"),
            "status": released.get("status"),
            "summary": released.get("summary"),
        },
        "rule_db_policy": {
            "current_stage": "Ingest P31I versioned rule proposals into Rule DB as disabled adapter candidates.",
            "blocked_actions": ["engine_activation", "runtime_activation"],
        },
        "guardrails": P31K_GUARDRAILS,
    }


def run_p31l_priority_topic_adapter_readiness(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from v19 import bazi_rule_db as rule_db

    ingested = run_p31k_priority_topic_rule_db_candidates(settings)
    if ingested.get("status") != "rule_db_candidates_ingested":
        return {
            "ok": False,
            "version": P31L_PRIORITY_TOPIC_ADAPTER_READINESS_VERSION,
            "status": "blocked_by_p31k",
            "summary": {
                "rule_db_candidate_count": int((ingested.get("summary") or {}).get("rule_db_candidate_count") or 0),
                "ready_candidate_count": 0,
                "engine_enabled_count": 0,
                "runtime_mutation": False,
            },
            "p31k": ingested,
            "guardrails": P31L_GUARDRAILS,
        }
    gate = rule_db.smart_gate_bazi_rule_db_candidates(
        prefixes=["p31c."],
        max_risk_level="R2",
        min_confidence=0.0,
        limit=50,
        activate=False,
        actor_role="system",
        note="P31L adapter readiness dry run for P31K candidates. No activation.",
        regression_status="pass",
    )
    summary = dict(gate.get("summary") or {})
    status = "adapter_readiness_report_ready" if gate.get("ok") else "blocked"
    return {
        "ok": status == "adapter_readiness_report_ready",
        "version": P31L_PRIORITY_TOPIC_ADAPTER_READINESS_VERSION,
        "status": status,
        "summary": {
            "rule_db_candidate_count": int((ingested.get("summary") or {}).get("rule_db_candidate_count") or 0),
            "ready_candidate_count": int(summary.get("candidate_count") or 0),
            "selected_count": int(summary.get("selected_count") or 0),
            "blocked_count": int(summary.get("blocked_count") or 0),
            "already_active_count": int(summary.get("already_active_count") or 0),
            "engine_enabled_count": int(summary.get("activated_count") or 0),
            "blocked_by_reason": summary.get("blocked_by_reason") or {},
            "runtime_mutation": False,
        },
        "adapter_gate": {
            "status": gate.get("status"),
            "summary": summary,
            "selected": gate.get("selected") or [],
            "blocked_preview": (gate.get("blocked") or [])[:10],
            "runtime_mutation": False,
        },
        "p31k": {
            "version": ingested.get("version"),
            "status": ingested.get("status"),
            "summary": ingested.get("summary"),
        },
        "adapter_policy": {
            "current_stage": "Explain why P31K Rule DB candidates are not engine-ready.",
            "expected_blockers": ["missing_structured_facts", "missing_synthetic_gate_candidate"],
            "blocked_actions": ["engine_activation", "runtime_activation"],
        },
        "guardrails": P31L_GUARDRAILS,
    }


def run_p31m_priority_topic_adapter_fact_enrichment(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from v19 import bazi_rule_db as rule_db

    ingested = run_p31k_priority_topic_rule_db_candidates(settings)
    if ingested.get("status") != "rule_db_candidates_ingested":
        return {
            "ok": False,
            "version": P31M_PRIORITY_TOPIC_ADAPTER_FACTS_VERSION,
            "status": "blocked_by_p31k",
            "summary": {
                "rule_db_candidate_count": int((ingested.get("summary") or {}).get("rule_db_candidate_count") or 0),
                "adapter_fact_updated_count": 0,
                "eval_sample_count": 0,
                "engine_enabled_count": 0,
                "runtime_mutation": False,
            },
            "p31k": ingested,
            "guardrails": P31M_GUARDRAILS,
        }
    enriched = rule_db.enrich_rule_db_candidate_adapter_facts(
        prefixes=["p31c."],
        source_stage="P31M_PRIORITY_TOPIC_ADAPTER_FACTS",
    )
    rules = [dict(row) for row in rule_db.list_bazi_rules(q="v19.p31e.").get("items") or [] if isinstance(row, dict)]
    samples = [sample for rule in rules for sample in _p31m_adapter_eval_samples(rule)]
    failed_samples = [row for row in samples if row.get("status") != "pass"]
    gate = rule_db.smart_gate_bazi_rule_db_candidates(
        prefixes=["p31c."],
        max_risk_level="R2",
        min_confidence=0.0,
        limit=50,
        activate=False,
        actor_role="system",
        note="P31M synthetic gate dry-run after adapter fact enrichment. No activation.",
        regression_status="pass",
    )
    gate_summary = dict(gate.get("summary") or {})
    engine_enabled_count = len([row for row in rules if row.get("engine_enabled") is True])
    status = (
        "adapter_facts_regression_ready"
        if enriched.get("updated_count") == 22
        and not failed_samples
        and int(gate_summary.get("selected_count") or 0) == 22
        and engine_enabled_count == 0
        else "blocked"
    )
    return {
        "ok": status == "adapter_facts_regression_ready",
        "version": P31M_PRIORITY_TOPIC_ADAPTER_FACTS_VERSION,
        "status": status,
        "summary": {
            "rule_db_candidate_count": len(rules),
            "adapter_fact_updated_count": int(enriched.get("updated_count") or 0),
            "eval_sample_count": len(samples),
            "eval_failed_count": len(failed_samples),
            "gate_selected_count": int(gate_summary.get("selected_count") or 0),
            "gate_blocked_count": int(gate_summary.get("blocked_count") or 0),
            "engine_enabled_count": engine_enabled_count,
            "runtime_mutation": False,
            "by_eval_sample_type": _count_by(samples, "sample_type"),
            "by_category": enriched.get("by_category") or {},
        },
        "adapter_fact_enrichment": {
            "ok": bool(enriched.get("ok")),
            "status": enriched.get("status"),
            "updated_count": enriched.get("updated_count"),
            "skipped_count": enriched.get("skipped_count"),
            "engine_enabled_count": enriched.get("engine_enabled_count"),
            "runtime_mutation": bool(enriched.get("runtime_mutation")),
        },
        "adapter_eval": {
            "sample_count": len(samples),
            "failed_count": len(failed_samples),
            "failed_samples": failed_samples[:20],
        },
        "synthetic_gate_dry_run": {
            "status": gate.get("status"),
            "summary": gate_summary,
            "selected_count": len(gate.get("selected") or []),
            "blocked_count": len(gate.get("blocked") or []),
            "activated_count": len(gate.get("activated") or []),
            "runtime_mutation": False,
        },
        "p31k": {
            "version": ingested.get("version"),
            "status": ingested.get("status"),
            "summary": ingested.get("summary"),
        },
        "adapter_policy": {
            "current_stage": "Seed minimal adapter structured facts and synthetic gate markers for P31K candidates.",
            "blocked_actions": ["engine_activation", "runtime_activation"],
            "next": "P31N can run signal-level synthetic samples before any shadow engine activation.",
        },
        "guardrails": P31M_GUARDRAILS,
    }


def _existing_ten_god_chain() -> List[Dict[str, str]]:
    return [
        {
            "case_id": str(case.get("case_id") or ""),
            "topic": str(case.get("title") or ""),
            "lane": "ten_god_interaction_mechanism",
            "status": "converted_through_p28j_p30",
        }
        for case in P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES
    ]


def _topic_model_specs() -> List[Dict[str, Any]]:
    return _pattern_specs() + _time_activation_specs() + _domain_bridge_specs()


def _pattern_specs() -> List[Dict[str, Any]]:
    rows = [
        ("正官格", "P0", "regular_pattern", "p31c.pattern.regular.zhengguan"),
        ("七杀格", "P0", "regular_pattern", "p31c.pattern.regular.qisha"),
        ("正财格", "P0", "regular_pattern", "p31c.pattern.regular.zhengcai"),
        ("偏财格", "P0", "regular_pattern", "p31c.pattern.regular.piancai"),
        ("食神格", "P0", "regular_pattern", "p31c.pattern.regular.shishen"),
        ("伤官格", "P0", "regular_pattern", "p31c.pattern.regular.shangguan"),
        ("正印格", "P0", "regular_pattern", "p31c.pattern.regular.zhengyin"),
        ("偏印格", "P0", "regular_pattern", "p31c.pattern.regular.pianyin"),
        ("建禄格", "P0", "regular_pattern", "p31c.pattern.regular.jianlu"),
        ("羊刃格", "P0", "regular_pattern", "p31c.pattern.regular.yangren"),
        ("成格 / 破格", "P1", "pattern_quality", "p31c.pattern.quality.formation_break"),
        ("救应", "P1", "pattern_quality", "p31c.pattern.quality.rescue_path"),
        ("清浊 / 混杂", "P1", "pattern_quality", "p31c.pattern.quality.clarity_mixed"),
        ("相神", "P1", "pattern_quality", "p31c.pattern.quality.assistant_god"),
    ]
    return [
        _spec(
            topic=topic,
            priority=priority,
            lane=lane,
            model_id=model_id,
            source_refs=[
                "docs/bazi_knowledge/pattern/regular/regular_pattern_units_v1.md",
                "docs/bazi_knowledge/pattern/quality/pattern_quality_units_v1.md",
            ],
            risk_level="R2" if priority == "P0" else "R3",
            axes=_base_axes()
            + [
                _axis("month_command", "月令是否为格局入口。"),
                _axis("key_god_visibility", "关键十神是否透出、通根或只在藏干。"),
                _axis("clarity_mixed", "清浊、混杂和去留条件是否明确。"),
                _axis("rescue_path", "救应、相神或反制路径是否存在。"),
                _axis("pattern_answer_boundary", "只说明格局候选，不输出成格、贵贱、职业或财富结果。"),
            ],
        )
        for topic, priority, lane, model_id in rows
    ]


def _time_activation_specs() -> List[Dict[str, Any]]:
    rows = [
        ("大运引动本命", "P0", "p31c.time.luck_to_natal"),
        ("流年引动本命", "P0", "p31c.time.flow_to_natal"),
        ("流年引动大运", "P1", "p31c.time.flow_to_luck"),
        ("天干引动", "P1", "p31c.time.stem_activation"),
        ("地支引动", "P1", "p31c.time.branch_activation"),
        ("十神引动", "P1", "p31c.time.ten_god_activation"),
        ("墓库引动", "P1", "p31c.time.vault_activation"),
    ]
    return [
        _spec(
            topic=topic,
            priority=priority,
            lane="time_activation",
            model_id=model_id,
            source_refs=[
                "docs/bazi_knowledge/time_context/time_context_units_v1.md",
                "docs/bazi_knowledge/time_context/luck_flow_activation_units_v1.md",
            ],
            risk_level="R2",
            axes=_base_axes()
            + [
                _axis("time_layer", "区分本命、大运、流年和跨层关系。"),
                _axis("natal_not_rewritten", "时间层只能触发或看见结构，不改写本命结构。"),
                _axis("relation_type", "明确天干、地支、藏干、墓库或十神触发类型。"),
                _axis("trigger_target", "明确被触发的柱位、十神、宫位或结构对象。"),
                _axis("time_answer_boundary", "只说明触发层，不输出应期、事件或好坏。"),
            ],
        )
        for topic, priority, model_id in rows
    ]


def _domain_bridge_specs() -> List[Dict[str, Any]]:
    rows = [
        ("财富 / 收入结构", "P0", "wealth_domain_bridge", "p31c.domain.wealth_income_structure", "R2"),
        ("财星耗身", "P1", "wealth_domain_bridge", "p31c.domain.wealth_drain_capacity", "R2"),
        ("事业 / 职业结构", "P2", "career_domain_bridge", "p31c.domain.career_boundary", "R3"),
        ("官杀事业语境", "P2", "career_domain_bridge", "p31c.domain.career_official_kill", "R2"),
        ("食伤财事业路径", "P2", "career_domain_bridge", "p31c.domain.career_output_wealth", "R2"),
        ("格局事业承接", "P2", "career_domain_bridge", "p31c.domain.career_pattern_bridge", "R3"),
        ("宫位与十神组合", "P1", "palace_domain_bridge", "p31c.domain.palace_ten_god_bridge", "R2"),
    ]
    return [
        _spec(
            topic=topic,
            priority=priority,
            lane=lane,
            model_id=model_id,
            source_refs=[
                "docs/bazi_knowledge/wealth/wealth_units_v1.md",
                "docs/bazi_knowledge/career/career_units_v1.md",
                "docs/bazi_knowledge/palace/palace_units_v1.md",
            ],
            risk_level=risk_level,
            axes=_base_axes()
            + [
                _axis("upstream_signal", "必须承接十神、强弱、格局、宫位或时间层信号。"),
                _axis("domain_boundary", "领域只解释问题语境，不直接预测财富、职业或家庭结果。"),
                _axis("capacity_and_accessibility", "检查承载力、可达性、牵制和救应。"),
                _axis("question_scope", "必须确认用户问题域与回答边界。"),
                _axis("domain_answer_boundary", "不输出收入、职位、婚恋、健康、事件或应期断语。"),
            ],
        )
        for topic, priority, lane, model_id, risk_level in rows
    ]


def _model_from_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "model_id": spec["model_id"],
        "topic": spec["topic"],
        "lane": spec["lane"],
        "priority": spec["priority"],
        "risk_level": spec["risk_level"],
        "activation_allowed": False,
        "activation_status": "blocked_pending_topic_eval_and_interpreter",
        "condition_axes": spec["axes"],
        "eval_requirements": [
            "positive_core_path",
            "negative_missing_required_axis",
            "distractor_time_layer",
            "distractor_hidden_or_background",
        ],
        "source_refs": spec["source_refs"],
        "forbidden_outputs": [
            "fortune",
            "good_bad_verdict",
            "event_timing",
            "wealth_prediction",
            "career_prediction",
            "health_or_relationship_prediction",
        ],
        "audit_tags": ["p31c", spec["lane"], spec["priority"], "condition_model"],
    }


def _samples_for_model(model: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        _sample(model, "positive_core_path", "positive", "", "核心条件轴满足，可以识别为候选结构。"),
        _sample(model, "negative_missing_required_axis", "negative", "capacity_strength", "关键承载或可达条件缺失。"),
        _sample(model, "distractor_time_layer", "distractor_time", "source_layer", "只在时间层或背景层出现，不能改写本命。"),
        _sample(model, "distractor_hidden_or_background", "distractor_hidden", "source_layer", "只在藏干或背景信息中出现，不能作为主机制。"),
    ]


def _sample(model: Dict[str, Any], sample_type: str, polarity: str, failed_axis: str, scenario: str) -> Dict[str, Any]:
    expected_signal = model["model_id"] if polarity == "positive" else ""
    return {
        "case_id": f"syn.p31c.{model['model_id'].removeprefix('p31c.')}.{sample_type}",
        "source_model_id": model["model_id"],
        "topic": model["topic"],
        "lane": model["lane"],
        "polarity": polarity,
        "sample_type": sample_type,
        "scenario": scenario,
        "expected_signal": expected_signal,
        "forbidden_signals": [] if polarity == "positive" else [model["model_id"]],
        "condition_axes_expected": _axis_expectations(model, polarity, failed_axis),
        "expected_question_keys": ["q_read_structure_not_result", "q_condition_model_review"],
        "forbidden_text": ["发财", "破财", "升职", "离婚", "疾病", "官非", "必然", "应期"],
        "audit_tags": ["p31c", "eval_sample", f"polarity:{polarity}", f"lane:{model['lane']}"],
    }


def _axis_expectations(model: Dict[str, Any], polarity: str, failed_axis: str) -> List[Dict[str, str]]:
    rows = []
    for axis in model.get("condition_axes") or []:
        key = str(axis.get("key") or "")
        status = "satisfied"
        if polarity != "positive" and key in {failed_axis, "answer_boundary"}:
            status = "blocked"
        if polarity == "distractor_time" and key in {"source_layer", "time_layer", "natal_not_rewritten"}:
            status = "blocked"
        if polarity == "distractor_hidden" and key in {"source_layer", "key_god_visibility"}:
            status = "blocked"
        rows.append({"key": key, "expected": status})
    return rows


def _evaluate_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    required = [
        "case_id",
        "source_model_id",
        "polarity",
        "expected_signal",
        "forbidden_signals",
        "condition_axes_expected",
        "forbidden_text",
        "audit_tags",
    ]
    for key in required:
        if key not in sample:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "schema_field_missing", "field": key})
    polarity = str(sample.get("polarity") or "")
    source_id = str(sample.get("source_model_id") or "")
    expected_signal = str(sample.get("expected_signal") or "")
    axis_statuses = [str(row.get("expected") or "") for row in sample.get("condition_axes_expected") or [] if isinstance(row, dict)]
    if polarity == "positive":
        if expected_signal != source_id:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "positive_expected_signal_mismatch", "expected": source_id, "actual": expected_signal})
        if any(status == "blocked" for status in axis_statuses):
            failures.append({"case_id": sample.get("case_id"), "failure_type": "positive_axis_blocked"})
    else:
        if expected_signal:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "non_positive_expected_signal_should_be_empty", "actual": expected_signal})
        if source_id not in set(str(item) for item in sample.get("forbidden_signals") or []):
            failures.append({"case_id": sample.get("case_id"), "failure_type": "forbidden_signal_missing", "expected": source_id})
        if "blocked" not in axis_statuses:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "non_positive_has_no_blocked_axis"})
    forbidden_text = set(str(item) for item in sample.get("forbidden_text") or [])
    if not {"发财", "破财", "疾病", "应期"} <= forbidden_text:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "forbidden_text_contract_failed"})
    return {
        "case_id": sample.get("case_id"),
        "source_model_id": source_id,
        "polarity": polarity,
        "sample_type": sample.get("sample_type") or "",
        "false_positive": polarity != "positive" and bool(expected_signal),
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _model_results(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for sample in samples:
        grouped.setdefault(str(sample.get("source_model_id") or ""), []).append(sample)
    rows = []
    for model_id, model_samples in sorted(grouped.items()):
        failures = []
        by_polarity = _count_by(model_samples, "polarity")
        for polarity in ["positive", "negative", "distractor_time", "distractor_hidden"]:
            if int(by_polarity.get(polarity) or 0) < 1:
                failures.append({"model_id": model_id, "failure_type": "polarity_missing", "polarity": polarity})
        if len(model_samples) != 4:
            failures.append({"model_id": model_id, "failure_type": "sample_count_mismatch", "expected": 4, "actual": len(model_samples)})
        rows.append(
            {
                "model_id": model_id,
                "sample_count": len(model_samples),
                "by_polarity": by_polarity,
                "status": "fail" if failures else "pass",
                "failures": failures,
            }
        )
    return rows


def _p31d_gate_row(model: Dict[str, Any], result: Dict[str, Any] | None, regression: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(result or {})
    blockers: List[str] = []
    risk = str(model.get("risk_level") or "R4")
    lane = str(model.get("lane") or "")
    if regression.get("status") != "pass":
        blockers.append("p31c_regression_not_passed")
    if result.get("status") != "pass":
        blockers.append("model_eval_not_passed")
    if risk not in {"R1", "R2"}:
        blockers.append("risk_above_shadow_gate")
    if any(token in lane for token in ["relationship", "health"]):
        blockers.append("domain_safety_review_required")
    if model.get("activation_allowed") is not False:
        blockers.append("activation_contract_not_false")
    if "fortune" not in set(str(item) for item in model.get("forbidden_outputs") or []):
        blockers.append("fortune_forbidden_output_missing")
    return {
        "model_id": model.get("model_id"),
        "topic": model.get("topic"),
        "lane": lane,
        "priority": model.get("priority"),
        "risk_level": risk,
        "sample_count": result.get("sample_count", 0),
        "eligible": not blockers,
        "decision": "shadow_proposal_ready" if not blockers else "blocked",
        "blockers": blockers,
        "activation_allowed": False,
        "runtime_mutation": False,
    }


def _p31e_rule_proposal_payload(model: Dict[str, Any], selected: Dict[str, Any]) -> Dict[str, Any]:
    lane = str(model.get("lane") or selected.get("lane") or "")
    model_id = str(model.get("model_id") or selected.get("model_id") or "")
    domain = _p31e_rule_domain(lane)
    return {
        "actor_role": "system",
        "rule_id": "v19.p31e." + _proposal_slug(model_id),
        "domain": domain,
        "version": 1,
        "source_feedback_ids": [],
        "input_contract": {
            "required": ["chart", "time_context", "guided_question_context", "knowledge_context"],
            "source_model_id": model_id,
            "source_stage": "P31E_PRIORITY_TOPIC_RULE_PROPOSAL_GENERATION",
        },
        "condition": {
            "source": "p31e_priority_topic_shadow_proposal",
            "source_model_id": model_id,
            "topic": model.get("topic") or selected.get("topic"),
            "lane": lane,
            "priority": model.get("priority") or selected.get("priority"),
            "risk_level": model.get("risk_level") or selected.get("risk_level"),
            "condition_axes": model.get("condition_axes") or [],
            "eval_requirements": model.get("eval_requirements") or [],
            "p31d_decision": selected.get("decision"),
        },
        "output_contract": {
            "signal": _p31e_output_signal(lane, domain),
            "value_set": ["candidate_present", "not_present", "blocked", "unknown"],
            "is_prediction": False,
            "runtime_scope": "proposal_only_no_runtime_inference_mutation",
        },
        "reasoning_path": [
            "read P31C condition model",
            "require P31C eval regression pass",
            "require P31D low-risk shadow gate selection",
            "emit proposal-only structural signal contract",
            "block approval, versioning, and runtime activation in P31E",
        ],
        "evidence": {
            "source": "p31e_priority_topic_rule_proposal_generation",
            "source_model_id": model_id,
            "p31c_version": P31C_PRIORITY_TOPIC_CONVERSION_VERSION,
            "p31d_version": P31D_PRIORITY_TOPIC_SMART_GATE_VERSION,
            "source_refs": model.get("source_refs") or [],
            "sample_count": selected.get("sample_count", 0),
            "risk_level": model.get("risk_level") or selected.get("risk_level"),
            "activation_allowed": False,
            "runtime_mutation": False,
        },
        "confidence": _p31e_confidence(model.get("risk_level") or selected.get("risk_level"), lane),
        "rationale": f"P31E proposal-only rule candidate from shadow-ready topic model {model_id}.",
        "guardrails": [
            "FROM_P31D_SHADOW_GATE",
            "RULE_PROPOSAL_ONLY",
            "NO_RUNTIME_INFERENCE_MUTATION",
            "NO_PREDICTION",
            "STRUCTURE_ONLY",
            "NO_DOMAIN_RESULT_PREDICTION",
        ],
    }


def _p31e_rule_domain(lane: str) -> str:
    if lane == "time_activation":
        return "time_structure"
    if lane == "wealth_domain_bridge":
        return "income_stability"
    if lane == "palace_domain_bridge":
        return "structural_relation"
    if lane == "career_domain_bridge":
        return "structural_relation"
    if lane in {"regular_pattern", "pattern_quality"}:
        return "structural_relation"
    return "structural_relation"


def _p31e_output_signal(lane: str, domain: str) -> str:
    if domain == "time_structure":
        return "p31e_time_activation_candidate"
    if domain == "income_stability":
        return "p31e_income_structure_candidate"
    if lane == "regular_pattern":
        return "p31e_regular_pattern_candidate"
    if lane == "career_domain_bridge":
        return "p31e_career_context_candidate"
    if lane == "palace_domain_bridge":
        return "p31e_palace_context_candidate"
    return "p31e_structural_candidate"


def _p31e_confidence(risk_level: Any, lane: str) -> float:
    risk = str(risk_level or "R2")
    base = 0.72 if risk == "R1" else 0.62
    if lane == "time_activation":
        base += 0.02
    if lane == "career_domain_bridge":
        base -= 0.02
    return round(max(0.0, min(1.0, base)), 2)


def _p31m_adapter_eval_samples(rule: Dict[str, Any]) -> List[Dict[str, Any]]:
    rule_id = str(rule.get("rule_id") or "")
    condition = dict(rule.get("condition") or {})
    structured = dict(condition.get("structured_facts") or {})
    allowed = set(str(item) for item in rule.get("allowed_usage") or [])
    forbidden = set(str(item) for item in rule.get("forbidden_usage") or [])
    checks = [
        (
            "structured_facts_present",
            bool(structured)
            and structured.get("adapter_marker") == "p31m_priority_topic_candidate"
            and bool(structured.get("anchor")),
            "P31M structured facts must include marker and anchor.",
        ),
        (
            "synthetic_gate_candidate_present",
            {"rule_db", "engine_adapter_candidate", "synthetic_gate_candidate"} <= allowed,
            "Rule must be marked as a synthetic gate candidate before later activation gates.",
        ),
        (
            "engine_disabled_contract",
            rule.get("engine_enabled") is False
            and str(rule.get("engine_adapter_status") or "") == "adapter_facts_seeded_waiting_synthetic_gate",
            "P31M must keep the engine disabled after enrichment.",
        ),
        (
            "forbidden_runtime_outputs_present",
            {"direct_fortune_output", "domain_result_prediction", "runtime_activation_without_synthetic_gate"} <= forbidden,
            "P31M candidates must preserve forbidden runtime/result outputs.",
        ),
    ]
    return [
        {
            "case_id": f"syn.p31m.{rule_id}.{sample_type}",
            "rule_id": rule_id,
            "knowledge_id": rule.get("knowledge_id"),
            "sample_type": sample_type,
            "status": "pass" if passed else "fail",
            "message": message,
            "runtime_mutation": False,
        }
        for sample_type, passed, message in checks
    ]


def _proposal_slug(value: str) -> str:
    text = str(value or "").strip().removeprefix("p31c.")
    chars = []
    for char in text:
        chars.append(char if char.isalnum() or char in {"_", "-"} else "_")
    return "".join(chars).strip("_") or "unknown"


def _blocked_reason_counts(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        for blocker in row.get("blockers") or []:
            key = str(blocker or "unknown")
            counts[key] = counts.get(key, 0) + 1
    return counts


def _spec(
    *,
    topic: str,
    priority: str,
    lane: str,
    model_id: str,
    source_refs: List[str],
    risk_level: str,
    axes: List[Dict[str, str]],
) -> Dict[str, Any]:
    return {
        "topic": topic,
        "priority": priority,
        "lane": lane,
        "model_id": model_id,
        "source_refs": source_refs,
        "risk_level": risk_level,
        "axes": axes,
    }


def _base_axes() -> List[Dict[str, str]]:
    return [
        _axis("source_layer", "区分透干、藏干、本命、时间层和领域层。"),
        _axis("capacity_strength", "检查月令、根气、印比支持、克泄耗压力。"),
        _axis("same_layer_action", "确认作用对象是否在可作用层。"),
        _axis("answer_boundary", "只输出结构路径，不输出吉凶、应期、领域结果或传统断语。"),
    ]


def _axis(key: str, description: str) -> Dict[str, str]:
    return {"key": key, "description": description}


def _lane_summary(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lanes = sorted({str(row.get("lane") or "") for row in models})
    out = []
    for lane in lanes:
        lane_models = [row for row in models if row.get("lane") == lane]
        out.append(
            {
                "lane": lane,
                "model_count": len(lane_models),
                "topics": [str(row.get("topic") or "") for row in lane_models],
                "activation_allowed": False,
            }
        )
    return out


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
