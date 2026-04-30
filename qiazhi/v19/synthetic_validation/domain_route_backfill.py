from __future__ import annotations

from typing import Any, Dict, List

from v19.knowledge_base_audit import _load_all_knowledge_drafts


P61_DOMAIN_ROUTE_BACKFILL_VERSION = "v19.p61.domain_route_backfill.v1"
P61_DOMAIN_ROUTE_EVAL_VERSION = "v19.p61.domain_route_backfill_eval.v1"
P61_DOMAIN_ROUTE_REGRESSION_VERSION = "v19.p61.domain_route_backfill_regression.v1"

P61_SOURCE_IDS = {
    "p36.relationship.spouse_palace.existence",
    "p36.relationship.spouse_palace.boundary",
    "p36.relationship.ten_god_context.existence",
    "p36.relationship.ten_god_context.boundary",
    "p36.health.archive_boundary.existence",
    "p36.health.archive_boundary.boundary",
}

P61_FORBIDDEN_TEXT = ["发财", "破财", "升职", "离婚", "疾病", "寿命", "诊断", "治疗", "必然", "一定", "应期", "fortune"]

P61_GUARDRAILS = [
    "P61_DOMAIN_ROUTE_BACKFILL",
    "ROUTE_ONLY_SAFE_WRAPPER",
    "SOURCE_R3_R4_STAYS_ARCHIVE",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_RESULT_MUTATION",
    "NO_ANSWER_MUTATION",
    "NO_DOMAIN_RESULT_PREDICTION",
]


def build_p61_domain_route_backfill_candidates() -> Dict[str, Any]:
    drafts = {str(row.get("knowledge_id") or ""): dict(row) for row in _load_all_knowledge_drafts()}
    candidates = [_candidate_from_source(drafts[source_id]) for source_id in sorted(P61_SOURCE_IDS) if source_id in drafts]
    return {
        "ok": True,
        "version": P61_DOMAIN_ROUTE_BACKFILL_VERSION,
        "status": "domain_route_backfill_candidates_ready_no_activation",
        "runtime_scope": "relationship_health_route_candidate_backfill_only",
        "summary": {
            "source_candidate_count": len(P61_SOURCE_IDS),
            "candidate_count": len(candidates),
            "engine_enabled_count": 0,
            "activation_updated_count": 0,
            "by_domain": _count_by(candidates, "domain"),
            "by_source_risk": _count_by(candidates, "source_risk_level"),
        },
        "candidates": candidates,
        "policy": {
            "source": "P36 relationship and health archive knowledge.",
            "wrapper": "Create R2 route-only safety candidates while preserving original source risk.",
            "activation": "No production rule activation; candidates can guide Rule Graph routing only.",
        },
        "guardrails": P61_GUARDRAILS,
    }


def build_p61_domain_route_backfill_eval_dataset() -> Dict[str, Any]:
    registry = build_p61_domain_route_backfill_candidates()
    samples = [sample for candidate in registry.get("candidates") or [] for sample in _samples_for_candidate(candidate)]
    return {
        "ok": registry.get("ok") is True,
        "version": P61_DOMAIN_ROUTE_EVAL_VERSION,
        "status": "domain_route_backfill_eval_ready_no_activation",
        "runtime_scope": "route_only_candidate_eval_dataset",
        "summary": {
            "candidate_count": len(registry.get("candidates") or []),
            "sample_count": len(samples),
            "min_samples_per_candidate": 4 if registry.get("candidates") else 0,
            "engine_enabled_count": 0,
            "activation_updated_count": 0,
            "by_domain": _count_by(samples, "domain"),
            "by_polarity": _count_by(samples, "polarity"),
        },
        "samples": samples,
        "source_registry_summary": registry["summary"],
        "guardrails": P61_GUARDRAILS,
    }


def run_p61_domain_route_backfill_regression() -> Dict[str, Any]:
    registry = build_p61_domain_route_backfill_candidates()
    dataset = build_p61_domain_route_backfill_eval_dataset()
    candidate_results = [_evaluate_candidate(candidate) for candidate in registry.get("candidates") or []]
    sample_results = [_evaluate_sample(sample) for sample in dataset.get("samples") or []]
    failures = [failure for row in candidate_results + sample_results for failure in row.get("failures") or []]
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P61_DOMAIN_ROUTE_REGRESSION_VERSION,
        "status": status,
        "runtime_scope": "domain_route_backfill_regression_no_activation",
        "summary": {
            "candidate_count": len(candidate_results),
            "sample_count": len(sample_results),
            "candidate_failed": sum(1 for row in candidate_results if row.get("status") == "fail"),
            "sample_failed": sum(1 for row in sample_results if row.get("status") == "fail"),
            "forbidden_text_failure_count": sum(1 for failure in failures if failure.get("failure_type") == "forbidden_text_present"),
            "engine_enabled_count": 0,
            "activation_updated_count": 0,
            "runtime_mutation": False,
        },
        "candidates": candidate_results,
        "samples": sample_results,
        "failures": failures,
        "guardrails": P61_GUARDRAILS,
    }


def _candidate_from_source(draft: Dict[str, Any]) -> Dict[str, Any]:
    knowledge_id = str(draft.get("knowledge_id") or "")
    domain = str(draft.get("domain") or "")
    source_risk = str(draft.get("risk_level") or "")
    return {
        "candidate_rule_id": f"p61.route_candidate.{_slug(knowledge_id)}",
        "knowledge_id": knowledge_id,
        "title": str(draft.get("title") or knowledge_id),
        "domain": domain,
        "category": "domain_route_backfill",
        "risk_level": "R2",
        "source_risk_level": source_risk,
        "source_pack_id": str(draft.get("source_pack_id") or ""),
        "source_seed_file": str(draft.get("source_seed_file") or ""),
        "conversion_mode": "route_only_safe_wrapper",
        "framework_model": "domain_route_safe_wrapper_eval",
        "condition_axes_required": _condition_axes_for_domain(domain, draft),
        "expected_signal": f"signal:{_slug(knowledge_id)}",
        "expected_question_keys": _expected_question_keys(domain),
        "forbidden_outputs": _forbidden_outputs(draft),
        "forbidden_usage": sorted({str(item) for item in draft.get("forbidden_usage") or [] if str(item)}),
        "rule_action": "emit_domain_route_boundary_signal_only",
        "answer_boundary": "route_hint_only_no_domain_verdict",
        "engine_enabled": False,
        "activation_allowed": False,
        "validation_status": "p61_route_backfill_eval_required",
        "audit_tags": [
            "p61_domain_route_backfill",
            f"domain:{domain}",
            f"source_risk:{source_risk}",
            "route_only_safe_wrapper",
        ],
    }


def _samples_for_candidate(candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
    sample_types = [
        ("positive_route_boundary", "positive"),
        ("negative_domain_verdict_forbidden", "negative"),
        ("distractor_time_layer_only", "distractor_time"),
        ("distractor_missing_answer_boundary", "negative"),
    ]
    return [_sample_for_type(candidate, index, sample_type, polarity) for index, (sample_type, polarity) in enumerate(sample_types, start=1)]


def _sample_for_type(candidate: Dict[str, Any], index: int, sample_type: str, polarity: str) -> Dict[str, Any]:
    positive = polarity == "positive"
    signal = str(candidate.get("expected_signal") or "")
    return {
        "case_id": f"p61.domain_route.{_slug(str(candidate.get('knowledge_id') or 'unknown'))}.{index}.{sample_type}",
        "source_candidate_rule_id": str(candidate.get("candidate_rule_id") or ""),
        "knowledge_id": str(candidate.get("knowledge_id") or ""),
        "domain": str(candidate.get("domain") or ""),
        "polarity": polarity,
        "sample_type": sample_type,
        "expected_signal": signal if positive else "",
        "forbidden_signals": [] if positive else [signal],
        "expected_question_keys": list(candidate.get("expected_question_keys") or []),
        "forbidden_text": [] if positive else list(candidate.get("forbidden_outputs") or []),
        "condition_axes_expected": _condition_axes_expected(candidate, sample_type),
        "generated_answer_text": "",
        "engine_enabled": False,
        "activation_allowed": False,
        "runtime_mutation": False,
        "audit_tags": list(candidate.get("audit_tags") or []) + [sample_type],
    }


def _evaluate_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    if candidate.get("risk_level") != "R2":
        failures.append(_failure(candidate, "wrapper_risk_mismatch", "P61 wrappers must stay R2 route-only candidates."))
    if candidate.get("source_risk_level") not in {"R3", "R4"}:
        failures.append(_failure(candidate, "source_risk_not_preserved", "P61 is only for R3/R4 archive source wrappers."))
    if candidate.get("engine_enabled") is True or candidate.get("activation_allowed") is True:
        failures.append(_failure(candidate, "activation_not_allowed", "P61 cannot enable or activate candidates."))
    if not candidate.get("condition_axes_required"):
        failures.append(_failure(candidate, "condition_axes_missing", "P61 route candidates require condition axes."))
    return {
        "candidate_rule_id": candidate.get("candidate_rule_id"),
        "knowledge_id": candidate.get("knowledge_id"),
        "domain": candidate.get("domain"),
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _evaluate_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    positive = sample.get("polarity") == "positive"
    if sample.get("engine_enabled") is True or sample.get("activation_allowed") is True:
        failures.append(_sample_failure(sample, "activation_not_allowed", "P61 samples must stay non-runtime."))
    if positive and not sample.get("expected_signal"):
        failures.append(_sample_failure(sample, "positive_signal_missing", "Positive route sample requires a signal."))
    if not positive and sample.get("expected_signal"):
        failures.append(_sample_failure(sample, "false_positive_signal", "Non-positive samples cannot expect route signal."))
    if not positive and not sample.get("forbidden_signals"):
        failures.append(_sample_failure(sample, "forbidden_signal_missing", "Non-positive samples require forbidden signals."))
    answer_text = str(sample.get("generated_answer_text") or "")
    for token in sample.get("forbidden_text") or []:
        if token and str(token) in answer_text:
            failures.append(_sample_failure(sample, "forbidden_text_present", str(token)))
            break
    return {
        "case_id": sample.get("case_id"),
        "knowledge_id": sample.get("knowledge_id"),
        "domain": sample.get("domain"),
        "sample_type": sample.get("sample_type"),
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _condition_axes_for_domain(domain: str, draft: Dict[str, Any]) -> List[str]:
    facts = draft.get("structured_facts") if isinstance(draft.get("structured_facts"), dict) else {}
    axes = []
    axes.extend(_as_list(facts.get("minimum_facts")))
    axes.extend(_as_list(facts.get("required_context")))
    axes.extend(["source_layer", "domain_answer_boundary", "answer_downgrade", "no_domain_prediction", "route_only_boundary"])
    if domain == "relationship":
        axes.extend(["palace_position", "ten_god_object", "branch_relation"])
    if domain == "health":
        axes.extend(["medical_safety_policy", "no_diagnosis", "no_lifespan_claim"])
    return _dedupe(axes)


def _condition_axes_expected(candidate: Dict[str, Any], sample_type: str) -> List[Dict[str, str]]:
    if sample_type == "positive_route_boundary":
        return [{"axis": axis, "expected": "present"} for axis in candidate.get("condition_axes_required") or []]
    if sample_type == "distractor_time_layer_only":
        return [{"axis": "time_layer", "expected": "does_not_trigger_domain_route_without_domain_boundary"}]
    if sample_type == "distractor_missing_answer_boundary":
        return [{"axis": "domain_answer_boundary", "expected": "missing_blocks_signal"}]
    return [{"axis": "domain_verdict", "expected": "blocked"}]


def _expected_question_keys(domain: str) -> List[str]:
    return {
        "relationship": ["q_relationship_structure"],
        "health": ["q_health_structure"],
    }.get(domain, ["q_structure_overview"])


def _forbidden_outputs(draft: Dict[str, Any]) -> List[str]:
    values = list(P61_FORBIDDEN_TEXT)
    values.extend(str(item) for item in draft.get("forbidden_usage") or [])
    return _dedupe(values)


def _dedupe(values: List[Any]) -> List[str]:
    out = []
    for value in values:
        text = str(value).strip()
        if text and text not in out:
            out.append(text)
    return out


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item)]
    if value is None:
        return []
    return [str(value)] if str(value) else []


def _failure(candidate: Dict[str, Any], failure_type: str, detail: str) -> Dict[str, str]:
    return {
        "candidate_rule_id": str(candidate.get("candidate_rule_id") or ""),
        "knowledge_id": str(candidate.get("knowledge_id") or ""),
        "failure_type": failure_type,
        "detail": detail,
    }


def _sample_failure(sample: Dict[str, Any], failure_type: str, detail: str) -> Dict[str, str]:
    return {
        "case_id": str(sample.get("case_id") or ""),
        "knowledge_id": str(sample.get("knowledge_id") or ""),
        "failure_type": failure_type,
        "detail": detail,
    }


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
