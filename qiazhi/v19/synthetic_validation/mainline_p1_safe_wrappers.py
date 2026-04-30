from __future__ import annotations

from typing import Any, Dict, List

from v19.synthetic_validation.domain_route_backfill import P61_SOURCE_IDS
from v19.synthetic_validation.rule_conversion_validation import build_p39_rule_conversion_candidates


P69_MAINLINE_P1_SAFE_WRAPPERS_VERSION = "v19.p69.mainline_p1_safe_wrappers.v1"
P69_MAINLINE_P1_REGRESSION_VERSION = "v19.p69.mainline_p1_regression.v1"

P69_FORBIDDEN_TEXT = [
    "发财",
    "破财",
    "升职",
    "离婚",
    "疾病",
    "寿命",
    "诊断",
    "治疗",
    "灾祸",
    "官非",
    "必然",
    "一定",
    "应期",
    "fortune",
]

P69_GUARDRAILS = [
    "P69_MAINLINE_P1_SAFE_WRAPPERS",
    "R3_R4_SOURCE_RISK_PRESERVED",
    "SAFE_WRAPPER_ONLY",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_RESULT_MUTATION",
    "NO_ANSWER_MUTATION",
    "NO_DOMAIN_RESULT_PREDICTION",
]

ROUTE_ONLY_DOMAINS = {"career", "relationship", "health", "family", "children", "personality"}
EVIDENCE_ONLY_DOMAINS = {"auxiliary_pillars", "auxiliary_symbols", "geo_context", "nayin", "shensha"}

P69_COVERAGE_SPECS = [
    {
        "coverage_id": "pattern_boundary",
        "message": "格局成格破格应该只看哪些结构边界？",
        "answer_kind": "pattern_structure",
        "expected_domains": ["pattern"],
        "expected_mode": "boundary_only_safe_wrapper",
    },
    {
        "coverage_id": "blind_lifa_boundary",
        "message": "盲派做功效率只能作为什么结构线索？",
        "answer_kind": "blind_lifa_boundary",
        "expected_domains": ["blind"],
        "expected_mode": "boundary_only_safe_wrapper",
    },
    {
        "coverage_id": "auxiliary_evidence",
        "message": "神煞、纳音、命宫身宫这些辅助象只能作为哪些证据标签？",
        "answer_kind": "auxiliary_evidence",
        "expected_domains": ["auxiliary_pillars", "auxiliary_symbols", "nayin", "shensha"],
        "expected_mode": "evidence_only_label",
    },
    {
        "coverage_id": "advanced_branch_time",
        "message": "暗合、地支穿和流月小运这些关系只能如何作为时间或关系背景？",
        "answer_kind": "branch_relation",
        "expected_domains": ["branch_advanced", "luck_flow"],
        "expected_mode": "boundary_only_safe_wrapper",
    },
]


def build_p69_mainline_p1_safe_wrappers() -> Dict[str, Any]:
    p39 = build_p39_rule_conversion_candidates()
    blocked = [dict(row) for row in p39.get("blocked") or [] if isinstance(row, dict)]
    candidates = [_candidate_from_blocked(row) for row in blocked if str(row.get("knowledge_id") or "") not in P61_SOURCE_IDS]
    all_wrapped_ids = {str(row.get("knowledge_id") or "") for row in candidates} | set(P61_SOURCE_IDS)
    blocked_ids = {str(row.get("knowledge_id") or "") for row in blocked}
    unwrapped = sorted(blocked_ids - all_wrapped_ids)
    return {
        "ok": True,
        "version": P69_MAINLINE_P1_SAFE_WRAPPERS_VERSION,
        "status": "mainline_p1_safe_wrappers_ready_no_activation",
        "runtime_scope": "r3_r4_archive_safe_wrapper_candidates_only",
        "summary": {
            "source_blocked_count": len(blocked),
            "existing_p61_wrapped_count": len([row for row in blocked if str(row.get("knowledge_id") or "") in P61_SOURCE_IDS]),
            "candidate_count": len(candidates),
            "total_safe_wrapper_coverage_count": len(blocked_ids & all_wrapped_ids),
            "unwrapped_source_count": len(unwrapped),
            "engine_enabled_count": 0,
            "activation_allowed_count": 0,
            "runtime_mutation": False,
            "by_source_risk": _count_by(candidates, "source_risk_level"),
            "by_wrapper_mode": _count_by(candidates, "conversion_mode"),
            "by_domain": _count_by(candidates, "domain"),
        },
        "candidates": candidates,
        "unwrapped_source_ids": unwrapped,
        "policy": {
            "source": "P39 R3/R4 blocked archive knowledge, excluding sources already covered by P61.",
            "wrapper_modes": ["route_only_safe_wrapper", "boundary_only_safe_wrapper", "evidence_only_label"],
            "activation": "No production rule activation; candidates can only support deterministic Rule Graph path selection.",
        },
        "guardrails": P69_GUARDRAILS,
    }


def run_p69_mainline_p1_regression() -> Dict[str, Any]:
    registry = build_p69_mainline_p1_safe_wrappers()
    coverage = build_p69_rule_graph_wrapper_coverage()
    candidate_results = [_evaluate_candidate(candidate) for candidate in registry.get("candidates") or []]
    failures = [failure for row in candidate_results for failure in row.get("failures") or []]
    failures.extend(coverage.get("failures") or [])
    if registry["summary"]["unwrapped_source_count"]:
        failures.append(
            {
                "failure_type": "unwrapped_r3_r4_source",
                "detail": ",".join(registry.get("unwrapped_source_ids") or []),
            }
        )
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P69_MAINLINE_P1_REGRESSION_VERSION,
        "status": status,
        "runtime_scope": "mainline_p1_safe_wrapper_regression_no_activation",
        "summary": {
            "candidate_count": len(candidate_results),
            "source_blocked_count": registry["summary"]["source_blocked_count"],
            "total_safe_wrapper_coverage_count": registry["summary"]["total_safe_wrapper_coverage_count"],
            "unwrapped_source_count": registry["summary"]["unwrapped_source_count"],
            "coverage_row_count": coverage["summary"]["row_count"],
            "coverage_failed": coverage["summary"]["failed"],
            "candidate_failed": sum(1 for row in candidate_results if row.get("status") == "fail"),
            "failure_count": len(failures),
            "engine_enabled_count": 0,
            "activation_allowed_count": 0,
            "runtime_mutation": False,
        },
        "candidates": candidate_results,
        "coverage": coverage,
        "failures": failures,
        "guardrails": P69_GUARDRAILS,
    }


def build_p69_rule_graph_wrapper_coverage() -> Dict[str, Any]:
    from v19.rule_graph_orchestrator import orchestrate_rule_graph_paths
    from v19.synthetic_validation.guided_cases import P11_GUIDED_SYNTHETIC_CASES
    from v19.synthetic_validation.guided_runner import _agent_data_for_case

    agent_data = _agent_data_for_case(P11_GUIDED_SYNTHETIC_CASES[0])
    rows = []
    failures = []
    for spec in P69_COVERAGE_SPECS:
        report = orchestrate_rule_graph_paths(
            agent_data,
            message=str(spec["message"]),
            answer_kind=str(spec["answer_kind"]),
            limit=8,
        )
        selected = [dict(row) for row in report.get("selected_paths") or [] if isinstance(row, dict)]
        expected_domains = set(str(item) for item in spec["expected_domains"])
        expected_mode = str(spec["expected_mode"])
        matching = [
            row
            for row in selected
            if str(row.get("domain") or "") in expected_domains
            and expected_mode in set(str(item) for item in row.get("audit_tags") or [])
        ]
        status = "pass" if matching else "fail"
        row = {
            "coverage_id": spec["coverage_id"],
            "message": spec["message"],
            "answer_kind": spec["answer_kind"],
            "status": status,
            "expected_domains": sorted(expected_domains),
            "expected_mode": expected_mode,
            "selected_count": len(selected),
            "matching_wrapper_count": len(matching),
            "matching_knowledge_ids": [str(item.get("knowledge_id") or "") for item in matching],
            "selected_preview": [
                {
                    "knowledge_id": row.get("knowledge_id"),
                    "domain": row.get("domain"),
                    "topic_lane": row.get("topic_lane"),
                    "score": row.get("score"),
                }
                for row in selected[:6]
            ],
            "engine_enabled_count": int((report.get("summary") or {}).get("engine_enabled_count") or 0),
            "answer_mutation_count": int((report.get("summary") or {}).get("answer_mutation_count") or 0),
        }
        if status == "fail":
            failures.append(
                {
                    "failure_type": "expected_wrapper_not_selected",
                    "coverage_id": str(spec["coverage_id"]),
                    "detail": f"Expected {expected_mode} for {sorted(expected_domains)}.",
                }
            )
        rows.append(row)
    return {
        "ok": not failures,
        "version": P69_MAINLINE_P1_SAFE_WRAPPERS_VERSION,
        "status": "pass" if not failures else "fail",
        "runtime_scope": "rule_graph_wrapper_coverage_no_activation",
        "summary": {
            "row_count": len(rows),
            "failed": len(failures),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "rows": rows,
        "failures": failures,
        "guardrails": P69_GUARDRAILS,
    }


def _candidate_from_blocked(blocked: Dict[str, Any]) -> Dict[str, Any]:
    knowledge_id = str(blocked.get("knowledge_id") or "")
    domain = str(blocked.get("domain") or "")
    category = str(blocked.get("category") or "")
    source_risk = str(blocked.get("risk_level") or "R4")
    mode = _wrapper_mode(domain, category)
    return {
        "candidate_rule_id": f"p69.safe_wrapper.{_slug(knowledge_id)}",
        "knowledge_id": knowledge_id,
        "title": str(blocked.get("title") or knowledge_id),
        "domain": domain,
        "category": category,
        "risk_level": "R2",
        "source_risk_level": source_risk,
        "source_pack_id": str(blocked.get("source_pack_id") or ""),
        "blocked_reason": str(blocked.get("blocked_reason") or ""),
        "source_recommended_action": str(blocked.get("recommended_action") or ""),
        "conversion_mode": mode,
        "framework_model": "mainline_p1_safe_wrapper_eval",
        "condition_axes_required": _condition_axes(domain, category, mode),
        "expected_signal": f"signal:p69:{_slug(knowledge_id)}",
        "expected_question_keys": _expected_question_keys(domain, category, mode),
        "forbidden_outputs": list(P69_FORBIDDEN_TEXT),
        "rule_action": _rule_action(mode),
        "answer_boundary": _answer_boundary(mode),
        "engine_enabled": False,
        "activation_allowed": False,
        "validation_status": "p69_mainline_p1_safe_wrapper_regression_required",
        "audit_tags": [
            "p69_mainline_p1_safe_wrapper",
            f"domain:{domain}",
            f"category:{category}",
            f"source_risk:{source_risk}",
            mode,
        ],
    }


def _evaluate_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    mode = str(candidate.get("conversion_mode") or "")
    if candidate.get("risk_level") != "R2":
        failures.append(_failure(candidate, "wrapper_risk_mismatch", "P69 wrappers must stay R2 candidates."))
    if candidate.get("source_risk_level") not in {"R3", "R4"}:
        failures.append(_failure(candidate, "source_risk_not_preserved", "P69 only wraps R3/R4 archive sources."))
    if mode not in {"route_only_safe_wrapper", "boundary_only_safe_wrapper", "evidence_only_label"}:
        failures.append(_failure(candidate, "wrapper_mode_invalid", mode))
    if candidate.get("engine_enabled") is True or candidate.get("activation_allowed") is True:
        failures.append(_failure(candidate, "activation_not_allowed", "P69 cannot activate candidates."))
    if not candidate.get("condition_axes_required"):
        failures.append(_failure(candidate, "condition_axes_missing", "P69 wrappers require condition axes."))
    if "no_prediction" not in set(candidate.get("condition_axes_required") or []):
        failures.append(_failure(candidate, "prediction_boundary_missing", "P69 wrappers must include no_prediction."))
    return {
        "candidate_rule_id": candidate.get("candidate_rule_id"),
        "knowledge_id": candidate.get("knowledge_id"),
        "domain": candidate.get("domain"),
        "conversion_mode": mode,
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _wrapper_mode(domain: str, category: str) -> str:
    if domain in ROUTE_ONLY_DOMAINS:
        return "route_only_safe_wrapper"
    if domain in EVIDENCE_ONLY_DOMAINS:
        return "evidence_only_label"
    if domain in {"pattern", "blind", "branch_advanced", "luck_flow", "timing", "strength", "core_structure", "growth_phase", "useful_god"}:
        return "boundary_only_safe_wrapper"
    if category.endswith("_archive") or "archive" in category:
        return "evidence_only_label"
    return "boundary_only_safe_wrapper"


def _condition_axes(domain: str, category: str, mode: str) -> List[str]:
    axes = [
        "source_layer",
        "source_risk_preserved",
        "answer_downgrade",
        "no_prediction",
        "no_domain_verdict",
        "safe_wrapper_boundary",
        f"domain:{domain}",
        f"category:{category}",
    ]
    if mode == "route_only_safe_wrapper":
        axes.extend(["route_intent_boundary", "domain_answer_boundary"])
    elif mode == "boundary_only_safe_wrapper":
        axes.extend(["condition_model_required", "boundary_only_interpretation"])
    else:
        axes.extend(["evidence_label_only", "no_inference_without_primary_structure"])
    if domain == "pattern":
        axes.extend(["pattern_condition_model", "formation_break_boundary", "rescue_path_required"])
    if domain == "blind":
        axes.extend(["blind_lifa_path_boundary", "source_target_layer", "work_efficiency_not_verdict"])
    if domain in {"luck_flow", "timing"}:
        axes.extend(["time_layer", "time_context_does_not_mutate_natal"])
    if domain == "branch_advanced":
        axes.extend(["branch_relation_feature", "relation_name_not_event"])
    if domain in {"geo_context", "auxiliary_pillars", "auxiliary_symbols", "nayin", "shensha"}:
        axes.extend(["auxiliary_context_only", "not_primary_structure"])
    return _dedupe(axes)


def _expected_question_keys(domain: str, category: str, mode: str) -> List[str]:
    if domain == "career" or domain == "pattern":
        return ["q_career_structure", "q_structure_overview"]
    if domain == "relationship":
        return ["q_relationship_structure", "q_structure_overview"]
    if domain == "health":
        return ["q_health_structure", "q_structure_overview"]
    if domain in {"luck_flow", "timing"}:
        return ["q_time_context_boundary", "q_luck_flow_layers"]
    if domain == "branch_advanced":
        return ["q_branch_relation_detail", "q_time_vs_natal_relation"]
    if domain in {"strength", "core_structure", "growth_phase", "useful_god"}:
        return ["q_day_master_month_anchor", "q_month_command_anchor", "q_structure_overview"]
    if domain == "blind":
        return ["q_structure_overview", "q_vault_structure"]
    if mode == "route_only_safe_wrapper":
        return ["q_structure_overview"]
    if "archive" in category:
        return ["q_read_result_not_fortune", "q_structure_overview"]
    return ["q_structure_overview"]


def _rule_action(mode: str) -> str:
    return {
        "route_only_safe_wrapper": "emit_route_boundary_signal_only",
        "boundary_only_safe_wrapper": "emit_boundary_condition_signal_only",
        "evidence_only_label": "emit_evidence_label_only",
    }.get(mode, "emit_boundary_condition_signal_only")


def _answer_boundary(mode: str) -> str:
    return {
        "route_only_safe_wrapper": "route_hint_only_no_domain_verdict",
        "boundary_only_safe_wrapper": "boundary_note_only_no_mechanism_verdict",
        "evidence_only_label": "evidence_label_only_no_inference",
    }.get(mode, "boundary_note_only_no_mechanism_verdict")


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def _dedupe(values: List[str]) -> List[str]:
    out = []
    seen = set()
    for value in values:
        clean = str(value or "").strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        out.append(clean)
    return out


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in str(value or "").lower()).strip("_")


def _failure(candidate: Dict[str, Any], failure_type: str, detail: str) -> Dict[str, str]:
    return {
        "knowledge_id": str(candidate.get("knowledge_id") or ""),
        "failure_type": failure_type,
        "detail": detail,
    }
