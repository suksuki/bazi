from __future__ import annotations

from typing import Any, Dict, List, Sequence

from v19.knowledge_base_audit import _load_all_knowledge_drafts


P39_RULE_CONVERSION_VALIDATION_VERSION = "v19.p39.rule_conversion_validation.v1"
P39_RULE_CONVERSION_EVAL_VERSION = "v19.p39.rule_conversion_eval_dataset.v1"
P39_RULE_CONVERSION_REGRESSION_VERSION = "v19.p39.rule_conversion_regression.v1"

P39_ELIGIBLE_RISKS = {"R0", "R1", "R2"}
P39_BLOCKED_RISKS = {"R3", "R4"}
P39_GUARDRAILS = [
    "BATCH_RULE_CANDIDATE_CONVERSION",
    "R0_R2_ONLY",
    "R3_R4_BLOCKED_TO_ARCHIVE_REVIEW",
    "SYNTHETIC_EVAL_DATASET_REQUIRED",
    "ENGINE_DISABLED_BY_DEFAULT",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_DOMAIN_RESULT_PREDICTION",
]

P39_DEFAULT_FORBIDDEN_TEXT = [
    "发财",
    "破财",
    "官非",
    "灾祸",
    "疾病",
    "离婚",
    "应期",
    "改运",
    "必然",
    "一定",
    "fortune",
    "prediction",
]

P39_SAMPLE_TYPES = [
    "positive_contract",
    "negative_missing_condition_axis",
    "distractor_time_layer",
    "distractor_hidden_layer",
]


def build_p39_rule_conversion_candidates() -> Dict[str, Any]:
    drafts = sorted(_load_all_knowledge_drafts(), key=lambda row: str(row.get("knowledge_id") or ""))
    candidates = []
    blocked = []
    for draft in drafts:
        risk = str(draft.get("risk_level") or "unknown")
        if risk in P39_ELIGIBLE_RISKS:
            candidates.append(_candidate_from_draft(draft))
        else:
            blocked.append(_blocked_from_draft(draft))
    return {
        "ok": True,
        "version": P39_RULE_CONVERSION_VALIDATION_VERSION,
        "status": "rule_conversion_candidates_ready_no_activation",
        "summary": {
            "draft_count": len(drafts),
            "eligible_candidate_count": len(candidates),
            "blocked_count": len(blocked),
            "engine_enabled_count": sum(1 for row in candidates if row.get("engine_enabled") is True),
            "activation_updated_count": 0,
            "by_risk": _count_by(candidates, "risk_level"),
            "blocked_by_risk": _count_by(blocked, "risk_level"),
            "by_domain": _count_by(candidates, "domain"),
            "by_conversion_mode": _count_by(candidates, "conversion_mode"),
            "by_framework_model": _count_by(candidates, "framework_model"),
        },
        "candidates": candidates,
        "blocked": blocked,
        "conversion_policy": {
            "eligible": "R0/R1/R2 knowledge drafts become dry-run rule candidates with condition axes and synthetic samples.",
            "blocked": "R3/R4 drafts stay in archive or analyst-review lanes before rule candidate promotion.",
            "activation": "P39 never enables engine rules; it validates candidate contracts and sample coverage only.",
        },
        "guardrails": P39_GUARDRAILS,
    }


def build_p39_rule_conversion_eval_dataset() -> Dict[str, Any]:
    registry = build_p39_rule_conversion_candidates()
    candidates = list(registry.get("candidates") or [])
    samples = [sample for candidate in candidates for sample in _samples_for_candidate(candidate)]
    return {
        "ok": True,
        "version": P39_RULE_CONVERSION_EVAL_VERSION,
        "status": "eval_dataset_ready_no_rule_activation",
        "summary": {
            "candidate_count": len(candidates),
            "sample_count": len(samples),
            "min_samples_per_candidate": len(P39_SAMPLE_TYPES) if candidates else 0,
            "activation_updated_count": 0,
            "by_polarity": _count_by(samples, "polarity"),
            "by_sample_type": _count_by(samples, "sample_type"),
            "by_domain": _count_by(samples, "domain"),
        },
        "samples": samples,
        "source_registry_summary": registry["summary"],
        "guardrails": P39_GUARDRAILS,
    }


def run_p39_rule_conversion_regression() -> Dict[str, Any]:
    registry = build_p39_rule_conversion_candidates()
    dataset = build_p39_rule_conversion_eval_dataset()
    candidates = list(registry.get("candidates") or [])
    samples = list(dataset.get("samples") or [])
    candidate_results = [_evaluate_candidate(candidate) for candidate in candidates]
    sample_results = [_evaluate_sample(sample) for sample in samples]
    candidate_failures = [failure for row in candidate_results for failure in row.get("failures") or []]
    sample_failures = [failure for row in sample_results for failure in row.get("failures") or []]
    failures = candidate_failures + sample_failures
    false_positive_count = sum(1 for row in sample_results if row.get("false_positive"))
    forbidden_text_failure_count = sum(
        1
        for failure in failures
        if failure.get("failure_type") == "forbidden_text_contract_failed"
    )
    status = "pass" if not failures and false_positive_count == 0 and forbidden_text_failure_count == 0 else "fail"
    return {
        "ok": status == "pass",
        "version": P39_RULE_CONVERSION_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "candidate_count": len(candidates),
            "blocked_count": len(registry.get("blocked") or []),
            "sample_count": len(samples),
            "candidate_failed": sum(1 for row in candidate_results if row.get("status") == "fail"),
            "sample_passed": sum(1 for row in sample_results if row.get("status") == "pass"),
            "sample_failed": sum(1 for row in sample_results if row.get("status") == "fail"),
            "false_positive_count": false_positive_count,
            "forbidden_text_failure_count": forbidden_text_failure_count,
            "engine_enabled_count": registry["summary"]["engine_enabled_count"],
            "activation_updated_count": 0,
            "by_sample_type": dataset["summary"]["by_sample_type"],
        },
        "candidates": candidate_results,
        "samples": sample_results,
        "failures": failures,
        "activation_policy": {
            "p39": "Candidate conversion and synthetic validation only; runtime rule activation stays blocked.",
            "next": "Validated candidates can feed a later smart approval lane or deeper topic-specific condition models.",
        },
        "guardrails": P39_GUARDRAILS,
    }


def _candidate_from_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    knowledge_id = str(draft.get("knowledge_id") or "")
    conversion_mode = _conversion_mode(draft)
    axes = _condition_axes_required(draft, conversion_mode)
    forbidden = _forbidden_outputs(draft)
    domain = str(draft.get("domain") or "unknown")
    return {
        "candidate_rule_id": f"p39.rule_candidate.{_slug(knowledge_id)}",
        "knowledge_id": knowledge_id,
        "title": str(draft.get("title") or knowledge_id),
        "domain": domain,
        "category": str(draft.get("category") or "unknown"),
        "risk_level": str(draft.get("risk_level") or "unknown"),
        "source_pack_id": str(draft.get("source_pack_id") or ""),
        "source_seed_file": str(draft.get("source_seed_file") or ""),
        "conversion_mode": conversion_mode,
        "framework_model": _framework_model(draft, conversion_mode),
        "condition_axes_required": axes,
        "expected_signal": _expected_signal(knowledge_id),
        "expected_question_keys": _expected_question_keys(domain),
        "forbidden_outputs": forbidden,
        "forbidden_usage": sorted({str(item) for item in draft.get("forbidden_usage") or [] if str(item)}),
        "rule_action": _rule_action(conversion_mode),
        "answer_boundary": _answer_boundary(draft, conversion_mode),
        "engine_enabled": False,
        "activation_allowed": False,
        "validation_status": "synthetic_eval_required",
        "audit_tags": _audit_tags(draft, conversion_mode),
    }


def _blocked_from_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    risk = str(draft.get("risk_level") or "unknown")
    return {
        "knowledge_id": str(draft.get("knowledge_id") or ""),
        "title": str(draft.get("title") or draft.get("knowledge_id") or ""),
        "domain": str(draft.get("domain") or "unknown"),
        "category": str(draft.get("category") or "unknown"),
        "risk_level": risk,
        "source_pack_id": str(draft.get("source_pack_id") or ""),
        "blocked_reason": "risk_above_auto_candidate_gate" if risk in P39_BLOCKED_RISKS else "unknown_risk_level",
        "recommended_action": "archive_review_or_topic_specific_condition_model_before_rule_candidate",
        "engine_enabled": False,
        "activation_allowed": False,
    }


def _samples_for_candidate(candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [_sample_for_type(candidate, sample_type, index) for index, sample_type in enumerate(P39_SAMPLE_TYPES, start=1)]


def _sample_for_type(candidate: Dict[str, Any], sample_type: str, index: int) -> Dict[str, Any]:
    positive = sample_type == "positive_contract"
    signal = str(candidate.get("expected_signal") or "")
    axes = list(candidate.get("condition_axes_required") or [])
    sample = {
        "case_id": f"p39.eval.{_slug(str(candidate.get('knowledge_id') or 'unknown'))}.{index}.{sample_type}",
        "source_candidate_rule_id": str(candidate.get("candidate_rule_id") or ""),
        "source_mechanism_id": str(candidate.get("candidate_rule_id") or ""),
        "knowledge_id": str(candidate.get("knowledge_id") or ""),
        "source_pack_id": str(candidate.get("source_pack_id") or ""),
        "domain": str(candidate.get("domain") or "unknown"),
        "polarity": "positive" if positive else _polarity_for_sample_type(sample_type),
        "sample_type": sample_type,
        "expected_signal": signal if positive else "",
        "forbidden_signals": [] if positive else [signal],
        "expected_question_keys": list(candidate.get("expected_question_keys") or []),
        "forbidden_text": [] if positive else list(candidate.get("forbidden_outputs") or []),
        "condition_axes_expected": _sample_axes(sample_type, axes),
        "audit_tags": list(candidate.get("audit_tags") or []) + [f"p39_{sample_type}"],
        "generated_answer_text": "",
    }
    if sample_type == "distractor_time_layer":
        sample["distractor_context"] = {"time_layer": "present", "expected": "do_not_rewrite_natal_structure"}
    if sample_type == "distractor_hidden_layer":
        sample["distractor_context"] = {"hidden_stem_layer": "present", "expected": "do_not_trigger_visible_signal"}
    return sample


def _evaluate_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    if candidate.get("risk_level") not in P39_ELIGIBLE_RISKS:
        failures.append(_failure(candidate, "risk_gate_failed", "Only R0/R1/R2 candidates may enter P39 conversion."))
    if candidate.get("engine_enabled") is True or candidate.get("activation_allowed") is True:
        failures.append(_failure(candidate, "activation_contract_failed", "P39 candidates must stay engine-disabled and activation-blocked."))
    if not candidate.get("condition_axes_required"):
        failures.append(_failure(candidate, "condition_axes_missing", "Converted rule candidates require condition axes."))
    if not candidate.get("forbidden_outputs"):
        failures.append(_failure(candidate, "forbidden_outputs_missing", "Converted rule candidates require forbidden output contracts."))
    if not candidate.get("expected_question_keys"):
        failures.append(_failure(candidate, "question_keys_missing", "Converted rule candidates require question routing keys."))
    return {
        "candidate_rule_id": candidate.get("candidate_rule_id"),
        "knowledge_id": candidate.get("knowledge_id"),
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _evaluate_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    required = {
        "case_id",
        "source_candidate_rule_id",
        "knowledge_id",
        "polarity",
        "expected_signal",
        "forbidden_signals",
        "expected_question_keys",
        "forbidden_text",
        "condition_axes_expected",
        "audit_tags",
    }
    missing = sorted(key for key in required if key not in sample)
    if missing:
        failures.append(_sample_failure(sample, "sample_schema_missing_fields", ",".join(missing)))
    positive = sample.get("sample_type") == "positive_contract"
    if positive and not sample.get("expected_signal"):
        failures.append(_sample_failure(sample, "positive_signal_missing", "Positive samples require an expected signal."))
    if not positive and sample.get("expected_signal"):
        failures.append(_sample_failure(sample, "false_positive_signal", "Negative and distractor samples must not expect a positive signal."))
    if not positive and not sample.get("forbidden_signals"):
        failures.append(_sample_failure(sample, "forbidden_signal_missing", "Negative and distractor samples require a forbidden signal."))
    if not positive and not sample.get("forbidden_text"):
        failures.append(_sample_failure(sample, "forbidden_text_missing", "Negative and distractor samples require forbidden text contracts."))
    answer_text = str(sample.get("generated_answer_text") or "")
    for token in sample.get("forbidden_text") or []:
        if token and str(token) in answer_text:
            failures.append(_sample_failure(sample, "forbidden_text_contract_failed", str(token)))
            break
    return {
        "case_id": sample.get("case_id"),
        "knowledge_id": sample.get("knowledge_id"),
        "sample_type": sample.get("sample_type"),
        "status": "fail" if failures else "pass",
        "false_positive": (not positive and bool(sample.get("expected_signal"))),
        "failures": failures,
    }


def _conversion_mode(draft: Dict[str, Any]) -> str:
    domain = str(draft.get("domain") or "")
    category = str(draft.get("category") or "")
    text = f"{domain} {category} {draft.get('title') or ''} {draft.get('statement') or ''}"
    if domain == "answer_expression" or category.startswith("answer_"):
        return "answer_expression_contract"
    if domain in {"lab", "rule_db"} or category.startswith(("review_ui", "rule_db")):
        return "governance_gate_contract"
    if domain == "geo_context" or category.startswith("geo_"):
        return "metadata_boundary_rule"
    if any(token in text for token in ["mechanism", "关系", "格局", "强弱", "引动", "冲", "合", "刑", "害", "破", "财", "官", "杀", "印", "食", "伤", "比劫"]):
        return "condition_model_candidate"
    if domain in {"growth_phase", "nayin", "shensha", "auxiliary_pillars", "auxiliary_symbols", "calendar", "useful_god"}:
        return "archive_metadata_candidate"
    return "metadata_seed_rule_candidate"


def _framework_model(draft: Dict[str, Any], conversion_mode: str) -> str:
    if conversion_mode == "condition_model_candidate":
        return "condition_axes_plus_synthetic_samples"
    if conversion_mode in {"answer_expression_contract", "governance_gate_contract"}:
        return "answer_governance_guardrail_model"
    if conversion_mode == "metadata_boundary_rule":
        return "metadata_boundary_model"
    if conversion_mode == "archive_metadata_candidate":
        return "archive_neutral_tag_model"
    return "metadata_seed_model"


def _condition_axes_required(draft: Dict[str, Any], conversion_mode: str) -> List[str]:
    facts = draft.get("structured_facts") if isinstance(draft.get("structured_facts"), dict) else {}
    axes = []
    axes.extend(_as_list(facts.get("required_context")))
    axes.extend(_as_list(facts.get("minimum_facts")))
    if conversion_mode == "condition_model_candidate":
        axes.extend(["source_layer", "capacity_strength", "same_layer_action", "rescue_path", "answer_boundary"])
    elif conversion_mode == "metadata_boundary_rule":
        axes.extend(["metadata_source", "calculation_scope", "answer_boundary"])
    elif conversion_mode == "answer_expression_contract":
        axes.extend(["input_intent", "answer_boundary", "forbidden_text_filter"])
    elif conversion_mode == "governance_gate_contract":
        axes.extend(["review_source", "gate_state", "mutation_boundary"])
    elif conversion_mode == "archive_metadata_candidate":
        axes.extend(["archive_source", "neutral_tag", "answer_boundary"])
    else:
        axes.extend(["source_layer", "answer_boundary"])
    cleaned = []
    for axis in axes:
        value = str(axis).strip()
        if value and value not in cleaned:
            cleaned.append(value)
    return cleaned


def _forbidden_outputs(draft: Dict[str, Any]) -> List[str]:
    values = list(P39_DEFAULT_FORBIDDEN_TEXT)
    values.extend(str(item) for item in draft.get("forbidden_usage") or [])
    values.extend(_as_list((draft.get("structured_facts") or {}).get("forbidden_outputs")) if isinstance(draft.get("structured_facts"), dict) else [])
    out = []
    for value in values:
        text = str(value).strip()
        if text and text not in out:
            out.append(text)
    return out


def _expected_question_keys(domain: str) -> List[str]:
    by_domain = {
        "wealth": ["q_income_stability"],
        "career": ["q_career_structure"],
        "interaction": ["q_ten_god_metadata", "kbq_ten_god_interaction_boundary"],
        "pattern": ["q_structure_overview", "q_pattern_boundary"],
        "luck_flow": ["q_time_context_boundary"],
        "core_structure": ["q_structure_overview"],
        "strength": ["q_day_master_month_anchor"],
        "geo_context": ["q_chart_metadata_boundary"],
        "answer_expression": ["q_answer_boundary"],
        "lab": ["q_review_boundary"],
        "rule_db": ["q_rule_gate_boundary"],
    }
    return by_domain.get(domain, ["q_structure_overview"])


def _rule_action(conversion_mode: str) -> str:
    return {
        "condition_model_candidate": "emit_neutral_structure_signal_when_axes_match",
        "answer_expression_contract": "filter_or_rephrase_forbidden_answer_text",
        "governance_gate_contract": "emit_review_gate_state_only",
        "metadata_boundary_rule": "emit_metadata_boundary_signal_only",
        "archive_metadata_candidate": "emit_archive_neutral_tag_only",
    }.get(conversion_mode, "emit_neutral_metadata_signal_only")


def _answer_boundary(draft: Dict[str, Any], conversion_mode: str) -> str:
    if conversion_mode == "answer_expression_contract":
        return "answer_text_may_be_rewritten_but_must_not_add_prediction"
    if conversion_mode == "governance_gate_contract":
        return "review_state_only_no_rule_activation"
    if conversion_mode == "condition_model_candidate":
        return "structure_signal_only_no_domain_verdict"
    if conversion_mode == "metadata_boundary_rule":
        return "metadata_background_only_no_fortune_output"
    if str(draft.get("risk_level") or "") in {"R2"}:
        return "candidate_signal_only_requires_deeper_topic_eval_before_activation"
    return "neutral_rule_candidate_only"


def _audit_tags(draft: Dict[str, Any], conversion_mode: str) -> List[str]:
    tags = [
        "p39_rule_conversion",
        f"risk:{draft.get('risk_level') or 'unknown'}",
        f"domain:{draft.get('domain') or 'unknown'}",
        f"mode:{conversion_mode}",
    ]
    tags.extend(str(item) for item in draft.get("tags") or [] if str(item))
    return tags


def _sample_axes(sample_type: str, axes: Sequence[str]) -> List[Dict[str, str]]:
    if sample_type == "positive_contract":
        return [{"axis": axis, "expected": "present"} for axis in axes]
    if sample_type == "negative_missing_condition_axis":
        axis = axes[0] if axes else "source_layer"
        return [{"axis": str(axis), "expected": "missing_blocks_signal"}]
    if sample_type == "distractor_time_layer":
        return [{"axis": "time_layer", "expected": "does_not_rewrite_or_trigger_without_base_axes"}]
    return [{"axis": "hidden_stem_layer", "expected": "does_not_trigger_visible_signal_without_action_path"}]


def _polarity_for_sample_type(sample_type: str) -> str:
    if sample_type == "distractor_time_layer":
        return "distractor_time"
    if sample_type == "distractor_hidden_layer":
        return "distractor_hidden"
    return "negative"


def _expected_signal(knowledge_id: str) -> str:
    return f"signal:{_slug(knowledge_id)}"


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item)]
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


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
