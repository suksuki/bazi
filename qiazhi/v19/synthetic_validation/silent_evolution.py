from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from v19.synthetic_validation.canary_runtime_trial import run_p45_canary_runtime_trial
from v19.synthetic_validation.dry_run_shadow_scoring import build_p43_feedback_ledger
from v19.synthetic_validation.framework_backfill import build_legacy_framework_adaptation_matrix
from v19.synthetic_validation.guided_cases import P11_GUIDED_SYNTHETIC_CASES
from v19.synthetic_validation.guided_runner import _agent_data_for_case, run_guided_synthetic_collision
from v19.synthetic_validation.rule_conversion_validation import run_p39_rule_conversion_regression
from v19.synthetic_validation.ten_god_conflict_matrix import run_p28l_ten_god_mechanism_signal_gate, run_p30_ten_god_mechanism_arbitration
from v19.rule_graph_orchestrator import orchestrate_rule_graph_paths


P54_FRAMEWORK_CHAIN_AUDIT_VERSION = "v19.p54.framework_chain_audit.v1"
P59_SILENT_EVOLUTION_VERSION = "v19.p59.silent_evolution_system.v1"
P60_DOMAIN_ROUTE_EVAL_VERSION = "v19.p60.domain_route_eval.v1"
P60_SMART_APPROVAL_GATE_VERSION = "v19.p60.smart_approval_gate.v1"
P60_SILENT_EXTENSION_VERSION = "v19.p60.silent_evolution_extension.v1"

P59_MODEL_POLICY = {
    "active_model": "deterministic_rule_graph_plus_eval_scoring",
    "active_algorithms": [
        "rule_graph_path_selection",
        "condition_model_eval_dataset",
        "dry_run_shadow_scoring",
        "canary_runtime_trial",
        "auto_evaluator_scorecard",
    ],
    "reserved_models": {
        "bayesian_scoring": "internal ranking only after stable eval ledgers accumulate",
        "gnn": "path embedding or rerank only after labeled eval dataset exists",
        "rl": "question ordering and dialog policy only, not core rule truth",
    },
    "blocked_uses": [
        "black_box_core_inference",
        "user_feedback_direct_rule_update",
        "automatic_production_rule_activation",
        "probability_claims_in_user_answer",
    ],
}

P59_GUARDRAILS = [
    "P59_SILENT_EVOLUTION_SYSTEM",
    "SILENT_SHADOW_TRAINING_ONLY",
    "AUTO_EVALUATION_ONLY",
    "TUNING_PROPOSALS_ONLY",
    "NO_USER_FEEDBACK_DIRECT_RULE_UPDATE",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_RESULT_MUTATION",
    "NO_ANSWER_MUTATION",
    "NO_DOMAIN_RESULT_PREDICTION",
]

P60_DOMAIN_ROUTE_SPECS = [
    {
        "domain": "wealth",
        "question_key": "q_income_stability",
        "message": "我的收入稳定性结构如何？",
        "expected_intent": "income_structure",
        "expected_lanes": ["wealth_career_bridge", "ten_god_mechanism"],
        "direct_domains": ["wealth"],
    },
    {
        "domain": "career",
        "question_key": "q_career_structure",
        "message": "我的事业结构怎么看？",
        "expected_intent": "career_structure",
        "expected_lanes": ["wealth_career_bridge", "ten_god_mechanism", "pattern_structure"],
        "direct_domains": ["career"],
    },
    {
        "domain": "relationship",
        "question_key": "q_relationship_structure",
        "message": "我的感情关系结构怎么看？",
        "expected_intent": "relationship_structure",
        "expected_lanes": ["domain_safety_bridge", "ten_god_mechanism", "branch_time_activation"],
        "direct_domains": ["relationship"],
        "allow_bridge_without_direct_domain": True,
    },
    {
        "domain": "health",
        "question_key": "q_health_structure",
        "message": "我的健康结构有什么需要注意的边界？",
        "expected_intent": "health_structure",
        "expected_lanes": ["domain_safety_bridge", "core_strength_foundation", "branch_time_activation"],
        "direct_domains": ["health"],
        "allow_bridge_without_direct_domain": True,
    },
]


def run_p54_framework_chain_audit() -> Dict[str, Any]:
    matrix = build_legacy_framework_adaptation_matrix()
    guided = run_guided_synthetic_collision(P11_GUIDED_SYNTHETIC_CASES)
    p28l = run_p28l_ten_god_mechanism_signal_gate()
    p30 = run_p30_ten_god_mechanism_arbitration()
    p39 = run_p39_rule_conversion_regression()
    p43 = build_p43_feedback_ledger()
    p45 = run_p45_canary_runtime_trial()

    rows = [
        _audit_row(
            "p10_p11_guided_synthetic",
            "backfilled_rule_graph_runtime_contract",
            guided.get("status") == "pass" and (guided.get("framework_backfill_review") or {}).get("status") == "pass",
            {
                "case_count": (guided.get("summary") or {}).get("total"),
                "framework_backfill_status": (guided.get("framework_backfill_review") or {}).get("status"),
                "topic_lanes": (guided.get("framework_backfill_review") or {}).get("expected_topic_lanes_covered") or [],
            },
        ),
        _audit_row(
            "p28_p30_ten_god_mechanisms",
            "native_condition_model_shadow_scoring_arbitration",
            _p28_track_is_framework_compatible(p28l, p30),
            {
                "shadow_gate_status": p28l.get("status"),
                "arbitration_status": p30.get("status"),
                "mechanism_count": (p28l.get("summary") or {}).get("mechanism_count"),
                "shadow_signal_pass_count": (p28l.get("summary") or {}).get("shadow_signal_pass_count"),
                "rule_backfill_needed_count": max(
                    0,
                    int((p28l.get("summary") or {}).get("mechanism_count") or 0)
                    - int((p28l.get("summary") or {}).get("shadow_signal_pass_count") or 0),
                ),
                "adaptation_status": "framework_compatible_with_rule_db_backfill"
                if p28l.get("ok") is not True or p30.get("ok") is not True
                else "framework_compatible",
            },
        ),
        _audit_row(
            "p39_rule_conversion",
            "native_rule_conversion_eval_dataset",
            p39.get("status") == "pass",
            {
                "candidate_count": (p39.get("summary") or {}).get("candidate_count"),
                "sample_count": (p39.get("summary") or {}).get("sample_count"),
                "runtime_mutation": (p39.get("summary") or {}).get("runtime_mutation", False),
            },
        ),
        _audit_row(
            "p42_p43_smart_gate_shadow",
            "native_smart_gate_feedback_ledger",
            p43.get("ok") is True,
            {
                "candidate_count": (p43.get("summary") or {}).get("candidate_count"),
                "dry_run_passed_count": (p43.get("summary") or {}).get("dry_run_passed_count"),
                "shadow_scored_count": (p43.get("summary") or {}).get("shadow_scored_count"),
            },
        ),
        _audit_row(
            "p45_canary_runtime_trial",
            "native_canary_isolated_runtime_trial",
            p45.get("ok") is True,
            {
                "canary_runtime_enabled_count": (p45.get("summary") or {}).get("canary_runtime_enabled_count"),
                "production_engine_enabled_count": (p45.get("summary") or {}).get("production_engine_enabled_count"),
                "answer_mutation_count": (p45.get("summary") or {}).get("answer_mutation_count"),
            },
        ),
        _audit_row(
            "p46_p52_rule_graph_runtime",
            "native_rule_graph_route_retrieval_ui_track",
            matrix.get("status") == "pass",
            {
                "adaptation_rows": (matrix.get("summary") or {}).get("row_count"),
                "native_rows": (matrix.get("summary") or {}).get("native_rows"),
                "backfilled_rows": (matrix.get("summary") or {}).get("backfilled_rows"),
            },
        ),
    ]
    failures = [row for row in rows if row.get("status") != "pass"]
    return {
        "ok": not failures,
        "version": P54_FRAMEWORK_CHAIN_AUDIT_VERSION,
        "status": "pass" if not failures else "fail",
        "runtime_scope": "framework_chain_compatibility_audit_only_no_runtime_mutation",
        "summary": {
            "row_count": len(rows),
            "passed": sum(1 for row in rows if row.get("status") == "pass"),
            "failed": len(failures),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "rows": rows,
        "failures": failures,
        "source_matrix": matrix,
        "guardrails": [
            "P54_FRAMEWORK_CHAIN_AUDIT",
            "AUDIT_ONLY",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_RESULT_MUTATION",
            "NO_ANSWER_MUTATION",
        ],
    }


def run_p59_silent_evolution_cycle() -> Dict[str, Any]:
    audit = run_p54_framework_chain_audit()
    guided = run_guided_synthetic_collision(P11_GUIDED_SYNTHETIC_CASES)
    feedback_ledger = build_p43_feedback_ledger()
    scorecard = _auto_evaluate(audit, guided, feedback_ledger)
    proposals = _tuning_proposals(audit, guided, feedback_ledger, scorecard)
    run_id = "p59.silent_run." + _stable_hash(
        {
            "version": P59_SILENT_EVOLUTION_VERSION,
            "audit": audit.get("summary"),
            "guided": guided.get("summary"),
            "ledger": feedback_ledger.get("summary"),
            "score": scorecard.get("score"),
        }
    )
    status = "silent_shadow_pass" if scorecard.get("status") == "pass" else "needs_tuning_review"
    return {
        "ok": status == "silent_shadow_pass",
        "version": P59_SILENT_EVOLUTION_VERSION,
        "run_id": run_id,
        "status": status,
        "runtime_scope": "silent_training_and_tuning_proposal_only_no_runtime_mutation",
        "input_sources": [
            "P11_GUIDED_SYNTHETIC_CASES",
            "P53_LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL",
            "P54_FRAMEWORK_CHAIN_AUDIT",
            "P43_FEEDBACK_LEDGER",
        ],
        "model_policy": P59_MODEL_POLICY,
        "scorecard": scorecard,
        "run_ledger_entry": {
            "ledger_id": run_id,
            "status": status,
            "score": scorecard.get("score"),
            "score_tier": scorecard.get("score_tier"),
            "source_case_count": (guided.get("summary") or {}).get("total"),
            "framework_audit_status": audit.get("status"),
            "feedback_ledger_status": feedback_ledger.get("status"),
            "engine_enabled": False,
            "answer_mutation": False,
            "runtime_mutation": False,
            "rollback_ready": True,
            "write_policy": "report_only_no_file_or_runtime_write",
        },
        "tuning_proposals": proposals,
        "downstream_plan": {
            "p59b_auto_evaluator": "expand domain route scoring and first-screen question diversity metrics",
            "p59c_tuning_proposal_generator": "convert recurring failures into parameter/routing proposals",
            "p59d_shadow_training_scheduler": "run silently against expanded synthetic eval datasets",
            "p60_smart_approval_gate": "route low-risk tuning proposals to dry-run, keep high-risk in review",
        },
        "guardrails": P59_GUARDRAILS,
    }


def run_p60_domain_route_eval() -> Dict[str, Any]:
    base_case = P11_GUIDED_SYNTHETIC_CASES[0]
    agent_data = _agent_data_for_case(base_case)
    samples = []
    for spec in P60_DOMAIN_ROUTE_SPECS:
        samples.append(_domain_route_sample(agent_data, spec, mode="inferred_from_message"))
        samples.append(_domain_route_sample(agent_data, spec, mode="explicit_answer_kind"))
    failures = [failure for row in samples for failure in row.get("failures") or []]
    direct_hits = sum(1 for row in samples if row.get("direct_domain_hit") is True)
    bridge_gaps = sum(1 for row in samples if row.get("bridge_without_direct_domain") is True)
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P60_DOMAIN_ROUTE_EVAL_VERSION,
        "status": status,
        "runtime_scope": "domain_route_eval_only_no_runtime_mutation",
        "summary": {
            "domain_count": len(P60_DOMAIN_ROUTE_SPECS),
            "sample_count": len(samples),
            "passed": sum(1 for row in samples if row.get("status") == "pass"),
            "failed": sum(1 for row in samples if row.get("status") == "fail"),
            "direct_domain_hit_count": direct_hits,
            "bridge_without_direct_domain_count": bridge_gaps,
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
            "by_domain": _count_by(samples, "domain"),
        },
        "samples": samples,
        "failures": failures,
        "domain_candidate_gaps": [
            {
                "domain": row.get("domain"),
                "sample_id": row.get("sample_id"),
                "gap_type": "domain_rule_candidate_missing_or_not_selected",
                "selected_domains": row.get("selected_domains") or [],
                "selected_lanes": row.get("selected_lanes") or [],
                "recommended_action": "convert_domain_knowledge_to_rule_candidates_then_rerun_domain_route_eval",
            }
            for row in samples
            if row.get("bridge_without_direct_domain") is True
        ],
        "guardrails": [
            "P60_DOMAIN_ROUTE_EVAL",
            "ROUTE_SELECTION_ONLY",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_RESULT_MUTATION",
            "NO_ANSWER_MUTATION",
            "NO_DOMAIN_RESULT_PREDICTION",
        ],
    }


def run_p60_smart_approval_gate() -> Dict[str, Any]:
    cycle = run_p59_silent_evolution_cycle()
    domain_eval = run_p60_domain_route_eval()
    proposal_rows = [_approval_row(row, cycle, domain_eval) for row in cycle.get("tuning_proposals") or []]
    if domain_eval.get("domain_candidate_gaps"):
        proposal_rows.extend(_domain_gap_approval_rows(domain_eval.get("domain_candidate_gaps") or [], cycle, domain_eval))
    failures = []
    if cycle.get("status") != "silent_shadow_pass":
        failures.append({"failure_type": "p59_cycle_not_ready", "detail": "P60 requires P59 silent shadow pass."})
    if domain_eval.get("status") != "pass":
        failures.append({"failure_type": "domain_route_eval_not_ready", "detail": "P60 requires passing domain route eval."})
    if any(row.get("runtime_mutation") is True for row in proposal_rows):
        failures.append({"failure_type": "runtime_mutation_not_allowed", "detail": "P60 gate cannot mutate runtime."})
    status = "smart_gate_ready_no_activation" if not failures else "blocked"
    return {
        "ok": status == "smart_gate_ready_no_activation",
        "version": P60_SMART_APPROVAL_GATE_VERSION,
        "status": status,
        "runtime_scope": "silent_tuning_smart_gate_only_no_runtime_mutation",
        "summary": {
            "proposal_count": len(proposal_rows),
            "auto_dry_run_allowed_count": sum(1 for row in proposal_rows if row.get("gate_decision") == "auto_dry_run_allowed"),
            "shadow_dry_run_required_count": sum(1 for row in proposal_rows if row.get("gate_decision") == "shadow_dry_run_required"),
            "human_review_required_count": sum(1 for row in proposal_rows if row.get("gate_decision") == "human_review_required"),
            "blocked_count": sum(1 for row in proposal_rows if str(row.get("gate_decision") or "").startswith("blocked")),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
            "by_gate_decision": _count_by(proposal_rows, "gate_decision"),
            "by_proposal_type": _count_by(proposal_rows, "proposal_type"),
        },
        "proposals": proposal_rows,
        "source_cycle": {
            "run_id": cycle.get("run_id"),
            "status": cycle.get("status"),
            "score": (cycle.get("scorecard") or {}).get("score"),
            "score_tier": (cycle.get("scorecard") or {}).get("score_tier"),
        },
        "source_domain_eval": {
            "status": domain_eval.get("status"),
            "summary": domain_eval.get("summary"),
        },
        "failures": failures,
        "guardrails": [
            "P60_SMART_APPROVAL_GATE",
            "LOW_RISK_AUTO_DRY_RUN_ONLY",
            "MEDIUM_RISK_SHADOW_DRY_RUN_REQUIRED",
            "HIGH_RISK_HUMAN_REVIEW_REQUIRED",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_RESULT_MUTATION",
            "NO_ANSWER_MUTATION",
        ],
    }


def run_p60_silent_evolution_extension() -> Dict[str, Any]:
    domain_eval = run_p60_domain_route_eval()
    gate = run_p60_smart_approval_gate()
    status = "pass" if domain_eval.get("ok") is True and gate.get("ok") is True else "fail"
    return {
        "ok": status == "pass",
        "version": P60_SILENT_EXTENSION_VERSION,
        "status": status,
        "runtime_scope": "domain_route_eval_and_smart_gate_only_no_runtime_mutation",
        "domain_route_eval": domain_eval,
        "smart_approval_gate": gate,
        "summary": {
            "domain_sample_count": (domain_eval.get("summary") or {}).get("sample_count"),
            "domain_candidate_gap_count": len(domain_eval.get("domain_candidate_gaps") or []),
            "gate_proposal_count": (gate.get("summary") or {}).get("proposal_count"),
            "auto_dry_run_allowed_count": (gate.get("summary") or {}).get("auto_dry_run_allowed_count"),
            "shadow_dry_run_required_count": (gate.get("summary") or {}).get("shadow_dry_run_required_count"),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "guardrails": [
            "P60_SILENT_EVOLUTION_EXTENSION",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_RESULT_MUTATION",
            "NO_ANSWER_MUTATION",
            "NO_DOMAIN_RESULT_PREDICTION",
        ],
    }


def _auto_evaluate(audit: Dict[str, Any], guided: Dict[str, Any], feedback_ledger: Dict[str, Any]) -> Dict[str, Any]:
    failures = [failure for row in guided.get("cases") or [] for failure in row.get("failures") or []]
    forbidden_failures = [row for row in failures if row.get("failure_type") == "forbidden_text_present"]
    mutation_failures = [
        row
        for row in failures
        if row.get("failure_type") in {"kb_mutated_answer_kind", "kb_mutated_source_signal_category", "framework_mutation_policy_mismatch"}
    ]
    route_lanes = set((guided.get("framework_backfill_review") or {}).get("expected_topic_lanes_covered") or [])
    factors = [
        _score_factor("guided_synthetic_pass", guided.get("status") == "pass", 20),
        _score_factor("framework_backfill_pass", (guided.get("framework_backfill_review") or {}).get("status") == "pass", 18),
        _score_factor("framework_chain_audit_pass", audit.get("status") == "pass", 18),
        _score_factor("feedback_ledger_ready", feedback_ledger.get("ok") is True, 14),
        _score_factor("forbidden_text_zero", not forbidden_failures, 10),
        _score_factor("mutation_zero", not mutation_failures, 10),
        _score_factor("route_lane_coverage", {"core_strength_foundation", "branch_time_activation", "ten_god_mechanism", "wealth_career_bridge"} <= route_lanes, 10),
    ]
    score = sum(int(row["points"]) for row in factors if row["passed"])
    return {
        "status": "pass" if score >= 90 else "fail",
        "score": score,
        "score_tier": _score_tier(score),
        "factors": factors,
        "failure_summary": {
            "total_failure_count": len(failures),
            "forbidden_text_failure_count": len(forbidden_failures),
            "mutation_failure_count": len(mutation_failures),
            "framework_audit_failed_rows": (audit.get("summary") or {}).get("failed", 0),
        },
        "guardrails": ["AUTO_EVALUATOR_INTERNAL_ONLY", "NO_USER_VISIBLE_PROBABILITY", "NO_RUNTIME_MUTATION"],
    }


def _tuning_proposals(
    audit: Dict[str, Any],
    guided: Dict[str, Any],
    feedback_ledger: Dict[str, Any],
    scorecard: Dict[str, Any],
) -> List[Dict[str, Any]]:
    proposals: List[Dict[str, Any]] = []
    if scorecard.get("status") == "pass":
        proposals.extend(
            [
                _proposal(
                    "p59.tuning.expand_domain_route_eval",
                    "eval_dataset_expansion",
                    "Add domain-specific silent eval rows for wealth, career, relationship, and health routing.",
                    "low",
                ),
                _proposal(
                    "p59.tuning.track_question_diversity",
                    "question_routing_parameter_review",
                    "Track first-screen question signature diversity as a recurring silent metric.",
                    "low",
                ),
                _proposal(
                    "p59.tuning.keep_rule_graph_as_active_model",
                    "model_policy",
                    "Keep deterministic Rule Graph as active core; reserve Bayesian/GNN/RL for ranking slots only.",
                    "low",
                ),
            ]
        )
    else:
        for row in audit.get("failures") or []:
            proposals.append(_proposal(f"p59.tuning.audit.{row.get('section')}", "framework_adapter_review", "Repair failed framework chain audit row before any tuning.", "high"))
        for row in guided.get("evolution_report", {}).get("draft_suggestions") or []:
            proposals.append(_proposal(f"p59.tuning.{row.get('proposal_id')}", row.get("draft_type") or "review_draft", row.get("suggested_action") or "review failed synthetic case.", "medium"))
    if (feedback_ledger.get("summary") or {}).get("shadow_scored_count", 0) > 0:
        proposals.append(
            _proposal(
                "p59.tuning.shadow_hold_sampling",
                "shadow_sample_expansion",
                "Sample shadow-scored candidates into expanded silent eval before smart approval.",
                "medium",
            )
        )
    p28_row = next((row for row in audit.get("rows") or [] if row.get("section") == "p28_p30_ten_god_mechanisms"), {})
    if int((p28_row.get("metrics") or {}).get("rule_backfill_needed_count") or 0) > 0:
        proposals.append(
            _proposal(
                "p59.tuning.p28_rule_db_backfill",
                "rule_db_backfill",
                "Backfill missing mechanism rule records so P28-P30 can move from framework-compatible backlog to full shadow pass.",
                "medium",
            )
        )
    return proposals


def _p28_track_is_framework_compatible(p28l: Dict[str, Any], p30: Dict[str, Any]) -> bool:
    summary = p28l.get("summary") or {}
    return (
        summary.get("p28k_regression_status") == "pass"
        and int(summary.get("mechanism_count") or 0) >= 20
        and int(summary.get("sample_count") or 0) >= 172
        and int(summary.get("false_positive_count") or 0) == 0
        and int(summary.get("missed_positive_count") or 0) == 0
        and str(p30.get("status") or "") in {"arbitration_ready_no_activation", "blocked"}
    )


def _domain_route_sample(agent_data: Dict[str, Any], spec: Dict[str, Any], *, mode: str) -> Dict[str, Any]:
    answer_kind = str(spec.get("expected_intent") or "") if mode == "explicit_answer_kind" else ""
    report = orchestrate_rule_graph_paths(
        agent_data,
        question_key=str(spec.get("question_key") or ""),
        message=str(spec.get("message") or ""),
        answer_kind=answer_kind,
        limit=8,
    )
    selected = [dict(row) for row in report.get("selected_paths") or [] if isinstance(row, dict)]
    selected_domains = sorted({str(row.get("domain") or "") for row in selected if str(row.get("domain") or "")})
    selected_lanes = sorted({str(row.get("topic_lane") or "") for row in selected if str(row.get("topic_lane") or "")})
    expected_domains = set(str(item) for item in spec.get("direct_domains") or [] if str(item))
    direct_domain_hit = bool(expected_domains & set(selected_domains))
    bridge_without_direct_domain = bool(spec.get("allow_bridge_without_direct_domain")) and not direct_domain_hit
    failures: List[Dict[str, Any]] = []
    intent = (report.get("question_intent") or {}).get("intent") or ""
    if intent != spec.get("expected_intent"):
        failures.append(_route_failure("domain_intent_mismatch", spec.get("expected_intent"), intent))
    if not (set(spec.get("expected_lanes") or []) & set(selected_lanes)):
        failures.append(_route_failure("domain_lane_missing", spec.get("expected_lanes") or [], selected_lanes))
    if not direct_domain_hit and not spec.get("allow_bridge_without_direct_domain"):
        failures.append(_route_failure("domain_candidate_missing", spec.get("direct_domains") or [], selected_domains))
    summary = report.get("summary") or {}
    if int(summary.get("engine_enabled_count") or 0) != 0 or int(summary.get("answer_mutation_count") or 0) != 0:
        failures.append(_route_failure("domain_route_mutation_not_allowed", {"engine": 0, "answer": 0}, summary))
    return {
        "sample_id": f"p60.domain_route.{spec.get('domain')}.{mode}",
        "domain": spec.get("domain"),
        "mode": mode,
        "status": "pass" if not failures else "fail",
        "message": spec.get("message"),
        "question_key": spec.get("question_key"),
        "expected_intent": spec.get("expected_intent"),
        "observed_intent": intent,
        "expected_lanes": list(spec.get("expected_lanes") or []),
        "selected_lanes": selected_lanes,
        "direct_domains": list(spec.get("direct_domains") or []),
        "selected_domains": selected_domains,
        "direct_domain_hit": direct_domain_hit,
        "bridge_without_direct_domain": bridge_without_direct_domain,
        "selected_knowledge_ids": [str(row.get("knowledge_id") or "") for row in selected if row.get("knowledge_id")],
        "engine_enabled_count": int(summary.get("engine_enabled_count") or 0),
        "answer_mutation_count": int(summary.get("answer_mutation_count") or 0),
        "runtime_mutation": False,
        "failures": failures,
    }


def _approval_row(proposal: Dict[str, Any], cycle: Dict[str, Any], domain_eval: Dict[str, Any]) -> Dict[str, Any]:
    risk = str(proposal.get("risk") or "high")
    proposal_type = str(proposal.get("proposal_type") or "")
    blockers = []
    if cycle.get("status") != "silent_shadow_pass":
        blockers.append("p59_not_passed")
    if domain_eval.get("status") != "pass":
        blockers.append("domain_eval_not_passed")
    if risk == "low" and not blockers:
        decision = "auto_dry_run_allowed"
    elif risk == "medium" and not blockers:
        decision = "shadow_dry_run_required"
    elif blockers:
        decision = "blocked_by_silent_gate"
    else:
        decision = "human_review_required"
    return {
        "gate_item_id": f"p60.gate.{_stable_hash({'proposal_id': proposal.get('proposal_id')})}",
        "proposal_id": proposal.get("proposal_id"),
        "proposal_type": proposal_type,
        "risk": risk,
        "gate_decision": decision,
        "blockers": blockers,
        "engine_enabled": False,
        "answer_mutation": False,
        "runtime_mutation": False,
        "rollback_required": decision in {"auto_dry_run_allowed", "shadow_dry_run_required"},
        "source": "p59_tuning_proposal",
    }


def _domain_gap_approval_rows(gaps: List[Dict[str, Any]], cycle: Dict[str, Any], domain_eval: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    seen_domains = set()
    for gap in gaps:
        domain = str(gap.get("domain") or "")
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        proposal = {
            "proposal_id": f"p60.domain_gap.{domain}",
            "proposal_type": "domain_rule_candidate_backfill",
            "risk": "medium",
        }
        row = _approval_row(proposal, cycle, domain_eval)
        row["source"] = "p60_domain_route_eval_gap"
        row["domain"] = domain
        row["recommended_action"] = gap.get("recommended_action")
        rows.append(row)
    return rows


def _audit_row(section: str, framework_track: str, passed: bool, metrics: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "section": section,
        "framework_track": framework_track,
        "status": "pass" if passed else "fail",
        "metrics": metrics,
        "engine_enabled": False,
        "answer_mutation": False,
        "runtime_mutation": False,
    }


def _score_factor(name: str, passed: bool, points: int) -> Dict[str, Any]:
    return {"name": name, "passed": bool(passed), "points": points if passed else 0, "max_points": points}


def _proposal(proposal_id: str, proposal_type: str, action: str, risk: str) -> Dict[str, Any]:
    return {
        "proposal_id": proposal_id,
        "proposal_type": proposal_type,
        "suggested_action": action,
        "risk": risk,
        "decision": "silent_proposal_only",
        "runtime_mutation": False,
    }


def _score_tier(score: int) -> str:
    if score >= 96:
        return "A"
    if score >= 90:
        return "B"
    if score >= 80:
        return "C"
    return "D"


def _stable_hash(payload: Dict[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _route_failure(failure_type: str, expected: Any, actual: Any) -> Dict[str, Any]:
    return {
        "failure_type": failure_type,
        "expected": expected,
        "actual": actual,
        "attribution_layer": "domain_route",
    }


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
