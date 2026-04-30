from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping

from v19.agent.income_stability import derive_income_stability
from v19.bazi_guided_questions import build_guided_question_answer, build_guided_question_context, guided_answer_to_plain_text
from v19.knowledge_store import retrieve_knowledge
from v19.rule_graph_runtime_context import build_rule_graph_runtime_context
from v19.structure_portrait import build_structure_portrait
from v19.synthetic_validation.framework_backfill import build_guided_case_framework_backfill, summarize_framework_backfill
from v19.synthetic_validation.guided_cases import GuidedSyntheticCase


GUIDED_SYNTHETIC_COLLISION_VERSION = "v19.guided_synthetic_collision.v1"


def _stable_hash(payload: Mapping[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _coerce_case(case: GuidedSyntheticCase | Mapping[str, Any]) -> GuidedSyntheticCase:
    if isinstance(case, GuidedSyntheticCase):
        return case
    return GuidedSyntheticCase.from_mapping(case)


def run_guided_synthetic_collision(cases: Iterable[GuidedSyntheticCase | Mapping[str, Any]]) -> Dict[str, Any]:
    normalized_cases = [_coerce_case(case) for case in cases]
    case_results = [_run_case(case) for case in normalized_cases]
    failures = [row for row in case_results if row["status"] == "fail"]
    payload = {"version": GUIDED_SYNTHETIC_COLLISION_VERSION, "case_ids": [case.case_id for case in normalized_cases]}
    return {
        "version": GUIDED_SYNTHETIC_COLLISION_VERSION,
        "validation_run": "guided_synthetic_run_" + _stable_hash(payload),
        "status": "fail" if failures else "pass",
        "summary": {
            "total": len(case_results),
            "passed": sum(1 for row in case_results if row["status"] == "pass"),
            "failed": len(failures),
        },
        "cases": case_results,
        "collision_review": _collision_review(case_results),
        "framework_backfill_review": summarize_framework_backfill(case_results),
        "evolution_report": _evolution_report(failures),
        "boundaries": [
            "SYNTHETIC_CASES_ONLY",
            "DOES_NOT_PROVE_REAL_WORLD_ACCURACY",
            "KNOWLEDGE_AND_RULE_PROPOSALS_ONLY",
            "ANALYST_REVIEW_REQUIRED_FOR_ACTIVATION",
            "NO_AUTO_RUNTIME_MUTATION",
            "P53_LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL",
        ],
    }


def _run_case(case: GuidedSyntheticCase) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    try:
        baseline_data = _agent_data_for_case(case, with_knowledge=False)
        baseline_context = dict(baseline_data.get("guided_question_context") or {})
        baseline_answer = build_guided_question_answer(baseline_data, case.question_key, case.message)
        baseline_text = guided_answer_to_plain_text(baseline_answer, "zh")

        agent_data = _agent_data_for_case(case, with_knowledge=True)
        guided_context = dict(agent_data.get("guided_question_context") or {})
        answer = build_guided_question_answer(agent_data, case.question_key, case.message)
        text = guided_answer_to_plain_text(answer, "zh")
    except Exception as exc:
        return {
            "case_id": case.case_id,
            "status": "fail",
            "tags": list(case.tags),
            "knowledge_tags": _standard_knowledge_tags(case),
            "framework_backfill": {},
            "failures": [{"failure_type": "exception", "message": str(exc)}],
            "observed": {},
        }

    recommended_keys = [str(row.get("key") or "") for row in guided_context.get("questions") or [] if isinstance(row, dict)]
    baseline_recommended_keys = [str(row.get("key") or "") for row in baseline_context.get("questions") or [] if isinstance(row, dict)]
    applied_ids = [str(row.get("knowledge_id") or "") for row in answer.get("applied_knowledge") or [] if isinstance(row, dict)]
    baseline_applied_ids = [str(row.get("knowledge_id") or "") for row in baseline_answer.get("applied_knowledge") or [] if isinstance(row, dict)]
    evidence_delta = [item for item in applied_ids if item not in set(baseline_applied_ids)]
    relation_types = sorted({str(row.get("type") or "") for row in (answer.get("retrieved_facts") or {}).get("relations") or [] if isinstance(row, dict)})
    baseline_relation_types = sorted({str(row.get("type") or "") for row in (baseline_answer.get("retrieved_facts") or {}).get("relations") or [] if isinstance(row, dict)})

    failures.extend(_missing_items("recommended_question_missing", case.expected_recommended_keys, recommended_keys))
    failures.extend(_missing_items("wealth_question_missing", case.expected_wealth_question_keys, recommended_keys))
    if case.expected_answer_kind and answer.get("answer_kind") != case.expected_answer_kind:
        failures.append({"failure_type": "answer_kind_mismatch", "expected": case.expected_answer_kind, "actual": answer.get("answer_kind")})
    if baseline_answer.get("answer_kind") != answer.get("answer_kind"):
        failures.append({"failure_type": "kb_mutated_answer_kind", "baseline": baseline_answer.get("answer_kind"), "augmented": answer.get("answer_kind")})
    if case.expected_source_signal_category and answer.get("source_signal_category") != case.expected_source_signal_category:
        failures.append(
            {
                "failure_type": "source_signal_category_mismatch",
                "expected": case.expected_source_signal_category,
                "actual": answer.get("source_signal_category"),
            }
        )
    if baseline_answer.get("source_signal_category") != answer.get("source_signal_category"):
        failures.append(
            {
                "failure_type": "kb_mutated_source_signal_category",
                "baseline": baseline_answer.get("source_signal_category"),
                "augmented": answer.get("source_signal_category"),
            }
        )
    failures.extend(_missing_items("knowledge_id_missing", case.expected_knowledge_ids, applied_ids))
    failures.extend(_missing_items("knowledge_delta_missing", case.expected_knowledge_ids, evidence_delta))
    failures.extend(_missing_items("relation_type_missing", case.expected_relation_types, relation_types))
    failures.extend(_missing_text(case.expected_text_contains, text))
    failures.extend(_forbidden_text(case.forbidden_text, text))
    framework_backfill = build_guided_case_framework_backfill(case, agent_data)
    failures.extend(framework_backfill.get("failures") or [])

    return {
        "case_id": case.case_id,
        "status": "fail" if failures else "pass",
        "structure_label": case.structure_label,
        "collision_focus": case.collision_focus,
        "tags": list(case.tags),
        "knowledge_tags": _standard_knowledge_tags(case),
        "framework_backfill": framework_backfill,
        "failures": failures,
        "observed": {
            "recommended_keys": recommended_keys,
            "wealth_question_keys": [key for key in recommended_keys if key in _wealth_question_keys()],
            "standardized_knowledge_tags": _standard_knowledge_tags(case),
            "framework_backfill_status": framework_backfill.get("status") or "",
            "framework_expected_topic_lanes": list((framework_backfill.get("expected") or {}).get("expected_topic_lanes") or []),
            "framework_expected_graph_features": list((framework_backfill.get("expected") or {}).get("expected_graph_features") or []),
            "answer_kind": answer.get("answer_kind") or "",
            "source_signal_category": answer.get("source_signal_category") or "",
            "applied_knowledge_ids": applied_ids,
            "relation_types": relation_types,
            "text_preview": " ".join(text.split())[:240],
        },
        "baseline_vs_kb_augmented": {
            "baseline": {
                "recommended_keys": baseline_recommended_keys,
                "answer_kind": baseline_answer.get("answer_kind") or "",
                "source_signal_category": baseline_answer.get("source_signal_category") or "",
                "applied_knowledge_ids": baseline_applied_ids,
                "relation_types": baseline_relation_types,
                "text_preview": " ".join(baseline_text.split())[:240],
            },
            "kb_augmented": {
                "recommended_keys": recommended_keys,
                "answer_kind": answer.get("answer_kind") or "",
                "source_signal_category": answer.get("source_signal_category") or "",
                "applied_knowledge_ids": applied_ids,
                "relation_types": relation_types,
                "text_preview": " ".join(text.split())[:240],
            },
            "evidence_delta": {
                "added_knowledge_ids": evidence_delta,
                "added_count": len(evidence_delta),
                "mutation_check": "routing_stable" if baseline_answer.get("answer_kind") == answer.get("answer_kind") and baseline_answer.get("source_signal_category") == answer.get("source_signal_category") else "routing_changed",
            },
        },
    }


def _agent_data_for_case(case: GuidedSyntheticCase, *, with_knowledge: bool = True) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "mode": "v19_synthetic_guided_collision",
        "boundary": "synthetic_explicit_pillars_no_birthdate",
        "chart": dict(case.chart),
        "time_context": dict(case.time_context or {"natal": case.chart, "luck_cycle": None, "flow_year": {"year": 2026, "pillar": {}, "relations_with_natal": {}}}),
    }
    data["inference_context"] = {
        "supported_theme": "income_stability",
        "income_stability": derive_income_stability(data["chart"]),
        "guardrails": ["SYNTHETIC_INFERENCE_CONTEXT"],
    }
    data["rule_graph_runtime_context"] = build_rule_graph_runtime_context(
        data,
        message=case.message,
        selected_question_key=case.question_key,
    )
    data["structure_portrait"] = build_structure_portrait(data)
    data["knowledge_context"] = retrieve_knowledge(data, case.message) if with_knowledge else {
        "version": "v19.synthetic.baseline.no_knowledge",
        "items": [],
        "count": 0,
        "runtime_scope": "baseline_without_kb_augmentation",
    }
    data["guided_question_context"] = build_guided_question_context(data)
    return data


def _missing_items(failure_type: str, expected: List[str], actual: List[str]) -> List[Dict[str, Any]]:
    actual_set = set(actual)
    return [
        {"failure_type": failure_type, "expected": item, "actual": actual}
        for item in expected
        if item not in actual_set
    ]


def _missing_text(expected: List[str], text: str) -> List[Dict[str, Any]]:
    return [
        {"failure_type": "answer_text_missing", "expected": item, "text_preview": " ".join(text.split())[:240]}
        for item in expected
        if item not in text
    ]


def _forbidden_text(forbidden: List[str], text: str) -> List[Dict[str, Any]]:
    return [
        {"failure_type": "forbidden_text_present", "forbidden": item, "text_preview": " ".join(text.split())[:240]}
        for item in forbidden
        if item and item in text
    ]


def _wealth_question_keys() -> set[str]:
    return {
        "q_income_stability",
        "q_income_factors",
        "q_income_path_structure",
        "q_income_continuity",
        "q_wealth_accessibility",
        "q_accessibility_signals",
        "q_signal_combination",
        "q_primary_auxiliary_signals",
        "q_volatility_factors",
        "kbq_income_path_route",
        "kbq_income_collision_route",
        "kbq_wealth_access_route",
        "kbq_wealth_feature_boundary",
        "kbq_wealth_metadata_boundary",
    }


def _standard_knowledge_tags(case: GuidedSyntheticCase) -> List[str]:
    if case.knowledge_tags:
        return sorted(set(case.knowledge_tags))
    tags = {f"case_tag:{item}" for item in case.tags if item}
    tags.update(f"knowledge_id:{item}" for item in case.expected_knowledge_ids if item)
    if case.expected_source_signal_category:
        tags.add(f"source_signal:{case.expected_source_signal_category}")
    if case.expected_answer_kind:
        tags.add(f"answer_kind:{case.expected_answer_kind}")
    return sorted(tags)


def _collision_review(case_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    stable = []
    misfires = []
    missing = []
    for result in case_results:
        label = result.get("structure_label") or result.get("case_id")
        if result.get("status") == "pass":
            stable.append({"case_id": result.get("case_id"), "structure_label": label, "collision_focus": result.get("collision_focus")})
            continue
        failures = result.get("failures") or []
        if any(str(item.get("failure_type") or "") in {"source_signal_category_mismatch", "kb_mutated_source_signal_category", "kb_mutated_answer_kind"} for item in failures):
            misfires.append({"case_id": result.get("case_id"), "structure_label": label, "failures": failures})
        if any("missing" in str(item.get("failure_type") or "") for item in failures):
            missing.append({"case_id": result.get("case_id"), "structure_label": label, "failures": failures})
    return {
        "stable_structures": stable,
        "misfire_structures": misfires,
        "missing_structures": missing,
    }


def _evolution_report(failures: List[Dict[str, Any]]) -> Dict[str, Any]:
    audit_records = []
    proposals = []
    for result in failures:
        failure_types = sorted({str(item.get("failure_type") or "") for item in result.get("failures") or []})
        target = _proposal_target(failure_types)
        attribution_layer = _failure_attribution_layer(failure_types)
        audit_id = "audit_" + _stable_hash({"case_id": result.get("case_id"), "failure_types": failure_types})
        audit_records.append(
            {
                "audit_id": audit_id,
                "case_id": result.get("case_id"),
                "structure_label": result.get("structure_label") or "",
                "collision_focus": result.get("collision_focus") or "",
                "knowledge_tags": list(result.get("knowledge_tags") or []),
                "failure_types": failure_types,
                "attribution": _failure_attribution(failure_types),
                "attribution_layer": attribution_layer,
                "review_status": "analyst_review_required",
                "guardrails": ["AUDIT_RECORD_ONLY", "NO_RUNTIME_MUTATION"],
            }
        )
        proposals.append(
            {
                "proposal_id": "draft_" + _stable_hash({"case_id": result.get("case_id"), "target": target, "failure_types": failure_types}),
                "case_id": result.get("case_id"),
                "target": target,
                "draft_type": _draft_type_for_target(target),
                "attribution_layer": attribution_layer,
                "knowledge_tags": list(result.get("knowledge_tags") or []),
                "failure_types": failure_types,
                "proposal_scope": "draft_only_requires_analyst_review",
                "suggested_action": _suggested_action(target),
            }
        )
    return {
        "audit_count": len(audit_records),
        "audit_records": audit_records,
        "proposal_count": len(proposals),
        "draft_suggestions": proposals,
        "items": proposals,
        "guardrails": ["NO_AUTO_LEARNING", "NO_AUTO_RULE_PROMOTION", "ANALYST_REVIEW_REQUIRED"],
    }


def _proposal_target(failure_types: List[str]) -> str:
    if any(item.startswith("framework_") for item in failure_types):
        return "framework_backfill_adapter_draft"
    if any(item in failure_types for item in {"answer_text_missing", "forbidden_text_present"}):
        return "answer_expression_seed_draft"
    if any(item in failure_types for item in {"knowledge_id_missing", "knowledge_delta_missing"}):
        return "knowledge_seed_draft"
    if any(item in failure_types for item in {"relation_type_missing", "source_signal_category_mismatch"}):
        return "rule_db_structured_fact_draft"
    if any(item in failure_types for item in {"recommended_question_missing", "wealth_question_missing"}):
        return "guided_question_ranking_draft"
    return "knowledge_or_rule_review_draft"


def _failure_attribution(failure_types: List[str]) -> str:
    if any(item.startswith("framework_") for item in failure_types):
        return "legacy_framework_backfill_layer"
    if any(item in failure_types for item in {"recommended_question_missing", "wealth_question_missing"}):
        return "question_recommendation_layer"
    if any(item in failure_types for item in {"knowledge_id_missing", "knowledge_delta_missing"}):
        return "knowledge_retrieval_layer"
    if any(item in failure_types for item in {"relation_type_missing", "source_signal_category_mismatch"}):
        return "rule_or_fact_retrieval_layer"
    if any(item in failure_types for item in {"answer_text_missing", "forbidden_text_present"}):
        return "answer_expression_layer"
    return "synthetic_collision_layer"


def _failure_attribution_layer(failure_types: List[str]) -> str:
    if any(item.startswith("framework_") for item in failure_types):
        return "framework"
    if any(item in failure_types for item in {"recommended_question_missing", "wealth_question_missing"}):
        return "recommendation"
    if any(item in failure_types for item in {"knowledge_id_missing", "knowledge_delta_missing"}):
        return "knowledge"
    if any(item in failure_types for item in {"relation_type_missing", "source_signal_category_mismatch", "kb_mutated_source_signal_category", "kb_mutated_answer_kind"}):
        return "rule"
    if any(item in failure_types for item in {"answer_text_missing", "forbidden_text_present", "answer_kind_mismatch"}):
        return "expression"
    return "synthetic"


def _draft_type_for_target(target: str) -> str:
    mapping = {
        "answer_expression_seed_draft": "answer_expression",
        "knowledge_seed_draft": "knowledge_seed",
        "rule_db_structured_fact_draft": "rule_draft",
        "guided_question_ranking_draft": "question_recommendation_draft",
        "framework_backfill_adapter_draft": "framework_adapter",
    }
    return mapping.get(target, "review_draft")


def _suggested_action(target: str) -> str:
    actions = {
        "answer_expression_seed_draft": "draft_or_update_answer_expression_seed_then_rerun_collision",
        "knowledge_seed_draft": "draft_or_reweight_knowledge_seed_then_rerun_collision",
        "rule_db_structured_fact_draft": "draft_structured_rule_or_relation_mapping_then_rerun_collision",
        "guided_question_ranking_draft": "review_question_score_or_signal_mapping_then_rerun_collision",
        "framework_backfill_adapter_draft": "update_legacy_case_framework_contract_then_rerun_collision",
    }
    return actions.get(target, "analyst_review_then_rerun_collision")
