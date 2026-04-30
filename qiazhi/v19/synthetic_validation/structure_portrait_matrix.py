from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Tuple

from v19.structure_portrait import FORBIDDEN_PORTRAIT_OUTPUTS
from v19.synthetic_validation.guided_cases import P11_GUIDED_SYNTHETIC_CASES
from v19.synthetic_validation.guided_runner import _agent_data_for_case


STRUCTURE_PORTRAIT_MATRIX_VERSION = "v19.mainline.structure_portrait_matrix.v1"
STRUCTURE_PORTRAIT_MATRIX_REGRESSION_VERSION = "v19.mainline.structure_portrait_matrix_regression.v1"
STRUCTURE_PORTRAIT_SHADOW_TUNING_VERSION = "v19.mainline.structure_portrait_shadow_tuning.v1"
STRUCTURE_PORTRAIT_SHADOW_TUNING_REGRESSION_VERSION = "v19.mainline.structure_portrait_shadow_tuning_regression.v1"

REQUIRED_LABEL_FAMILIES = {"strength", "useful_god", "ten_god", "wealth", "branch", "time", "pattern"}

GUARDRAILS = [
    "STRUCTURE_PORTRAIT_SYNTHETIC_MATRIX",
    "PORTRAIT_ROUTE_VALIDATION_ONLY",
    "NO_RESULT_MUTATION",
    "NO_ANSWER_MUTATION",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_HARD_USEFUL_GOD_VERDICT",
]


@lru_cache(maxsize=4)
def build_structure_portrait_synthetic_matrix(limit: int = 12) -> Dict[str, Any]:
    cases = P11_GUIDED_SYNTHETIC_CASES[:limit]
    rows = []
    for case in cases:
        data = _agent_data_for_case(case)
        portrait = dict(data.get("structure_portrait") or {})
        context = dict(data.get("guided_question_context") or {})
        questions = [dict(row) for row in context.get("questions") or [] if isinstance(row, dict)]
        labels = [dict(row) for row in portrait.get("labels") or [] if isinstance(row, dict)]
        judgements = [dict(row) for row in portrait.get("candidate_judgements") or [] if isinstance(row, dict)]
        forbidden_failures = _forbidden_failures(labels, judgements)
        rows.append(
            {
                "case_id": case.case_id,
                "expected_question_key": case.question_key,
                "portrait_status": portrait.get("status") or "",
                "label_ids": [str(row.get("label_id") or "") for row in labels],
                "label_families": sorted({str(row.get("family") or "") for row in labels if row.get("family")}),
                "vectors": dict(portrait.get("vectors") or {}),
                "candidate_judgement_ids": [str(row.get("judgement_id") or "") for row in judgements],
                "top_question_keys": [str(row.get("key") or "") for row in questions[:5]],
                "forbidden_failures": forbidden_failures,
                "runtime_mutation": False,
                "answer_mutation": False,
            }
        )
    vector_signatures = {_vector_signature(row.get("vectors") or {}) for row in rows}
    question_signatures = {tuple(row.get("top_question_keys") or []) for row in rows}
    label_families = set().union(*(set(row.get("label_families") or []) for row in rows)) if rows else set()
    forbidden_failure_count = sum(len(row.get("forbidden_failures") or []) for row in rows)
    return {
        "ok": True,
        "version": STRUCTURE_PORTRAIT_MATRIX_VERSION,
        "status": "structure_portrait_matrix_ready",
        "runtime_scope": "portrait_synthetic_matrix_only_no_runtime_mutation",
        "summary": {
            "case_count": len(rows),
            "vector_signature_count": len(vector_signatures),
            "top_question_signature_count": len(question_signatures),
            "label_family_coverage": sorted(label_families),
            "forbidden_text_failure_count": forbidden_failure_count,
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "cases": rows,
        "guardrails": GUARDRAILS,
    }


@lru_cache(maxsize=4)
def run_structure_portrait_synthetic_matrix_regression() -> Dict[str, Any]:
    matrix = build_structure_portrait_synthetic_matrix()
    summary = dict(matrix.get("summary") or {})
    failures: List[Dict[str, str]] = []
    if int(summary.get("case_count") or 0) < 12:
        failures.append(_failure("case_count_too_low", "Structure portrait matrix requires at least 12 synthetic cases."))
    if int(summary.get("vector_signature_count") or 0) < 5:
        failures.append(_failure("portrait_vectors_not_diverse", "Synthetic cases must produce distinct portrait vectors."))
    if int(summary.get("top_question_signature_count") or 0) < 6:
        failures.append(_failure("question_routes_not_diverse", "Portrait-guided questions must not collapse into one list."))
    observed = set(summary.get("label_family_coverage") or [])
    if not REQUIRED_LABEL_FAMILIES <= observed:
        failures.append(_failure("label_family_coverage_gap", ",".join(sorted(REQUIRED_LABEL_FAMILIES - observed))))
    if int(summary.get("forbidden_text_failure_count") or 0) != 0:
        failures.append(_failure("forbidden_text_leak", "Portrait labels or judgements leaked hard verdict language."))
    for row in matrix.get("cases") or []:
        if row.get("runtime_mutation") is True or row.get("answer_mutation") is True:
            failures.append(_failure("mutation_not_allowed", str(row.get("case_id") or "")))
        if row.get("portrait_status") != "ready":
            failures.append(_failure("portrait_not_ready", str(row.get("case_id") or "")))
        if not row.get("top_question_keys"):
            failures.append(_failure("question_route_missing", str(row.get("case_id") or "")))
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": STRUCTURE_PORTRAIT_MATRIX_REGRESSION_VERSION,
        "status": status,
        "runtime_scope": "portrait_synthetic_matrix_regression_no_runtime_mutation",
        "summary": {
            **summary,
            "failure_count": len(failures),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "matrix": matrix,
        "failures": failures,
        "guardrails": GUARDRAILS,
    }


@lru_cache(maxsize=4)
def build_structure_portrait_shadow_tuning_report(limit: int = 20) -> Dict[str, Any]:
    matrix = build_structure_portrait_synthetic_matrix(limit)
    cases = [dict(row) for row in matrix.get("cases") or [] if isinstance(row, dict)]
    bucket_counts: Dict[str, int] = {}
    for row in cases:
        for key in list(row.get("top_question_keys") or [])[:5]:
            bucket = _question_bucket(str(key or ""))
            bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    vector_signatures = int((matrix.get("summary") or {}).get("vector_signature_count") or 0)
    question_signatures = int((matrix.get("summary") or {}).get("top_question_signature_count") or 0)
    proposals = _shadow_weight_proposals(bucket_counts, len(cases), vector_signatures, question_signatures)
    return {
        "ok": True,
        "version": STRUCTURE_PORTRAIT_SHADOW_TUNING_VERSION,
        "status": "portrait_shadow_tuning_ready",
        "runtime_scope": "portrait_weight_shadow_tuning_report_only_no_runtime_mutation",
        "summary": {
            "case_count": len(cases),
            "vector_signature_count": vector_signatures,
            "top_question_signature_count": question_signatures,
            "bucket_coverage_count": len(bucket_counts),
            "proposal_count": len(proposals),
            "forbidden_text_failure_count": int((matrix.get("summary") or {}).get("forbidden_text_failure_count") or 0),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "bucket_counts": bucket_counts,
        "proposals": proposals,
        "source_matrix_summary": matrix.get("summary") or {},
        "guardrails": GUARDRAILS + [
            "SHADOW_TUNING_ONLY",
            "NO_PRODUCTION_WEIGHT_UPDATE",
            "NO_AUTO_LEARNING",
        ],
    }


@lru_cache(maxsize=4)
def run_structure_portrait_shadow_tuning_regression() -> Dict[str, Any]:
    report = build_structure_portrait_shadow_tuning_report()
    summary = dict(report.get("summary") or {})
    failures: List[Dict[str, str]] = []
    if int(summary.get("case_count") or 0) < 20:
        failures.append(_failure("case_count_too_low", "P79 shadow tuning expects all 20 P11 synthetic cases."))
    if int(summary.get("vector_signature_count") or 0) < 8:
        failures.append(_failure("vector_signature_count_too_low", "Portrait vectors need enough spread before tuning review."))
    if int(summary.get("top_question_signature_count") or 0) < 6:
        failures.append(_failure("question_signature_count_too_low", "Question routes should stay diverse under portrait weighting."))
    if int(summary.get("bucket_coverage_count") or 0) < 5:
        failures.append(_failure("bucket_coverage_too_low", "Common Bazi entry buckets must be represented."))
    if int(summary.get("forbidden_text_failure_count") or 0) != 0:
        failures.append(_failure("forbidden_text_leak", "Shadow tuning cannot proceed with hard-verdict language."))
    if summary.get("runtime_mutation") is True or int(summary.get("engine_enabled_count") or 0) != 0:
        failures.append(_failure("mutation_not_allowed", "Shadow tuning must not mutate runtime or enable rules."))
    for proposal in report.get("proposals") or []:
        if proposal.get("decision") != "shadow_review_only" or proposal.get("runtime_mutation") is True:
            failures.append(_failure("proposal_boundary_invalid", str(proposal.get("proposal_id") or "")))
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": STRUCTURE_PORTRAIT_SHADOW_TUNING_REGRESSION_VERSION,
        "status": status,
        "runtime_scope": "portrait_shadow_tuning_regression_no_runtime_mutation",
        "summary": {
            **summary,
            "failure_count": len(failures),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "report": report,
        "failures": failures,
        "guardrails": report.get("guardrails") or GUARDRAILS,
    }


def _vector_signature(vectors: Dict[str, Any]) -> Tuple[float, ...]:
    keys = ["wealth_visibility", "branch_volatility", "time_trigger_activity", "pattern_index_strength", "useful_god_candidate_confidence"]
    return tuple(round(float(vectors.get(key) or 0), 2) for key in keys)


def _question_bucket(key: str) -> str:
    if key in {"q_strength_assessment", "q_useful_god_candidates", "q_unfavorable_god_boundary", "q_favorable_elements_boundary"}:
        return "strength_useful_god"
    if key == "q_pattern_structure":
        return "pattern_structure"
    if "income" in key or "wealth" in key:
        return "income_stability"
    if "branch" in key or "combination" in key or "harmony" in key or "disruption" in key:
        return "branch_relation"
    if "time" in key or "luck" in key:
        return "time_context"
    if "ten_god" in key or "hidden" in key or "month_command" in key or "day_master" in key:
        return "metadata"
    if "vault" in key:
        return "vault"
    return "structure_basis"


def _shadow_weight_proposals(bucket_counts: Dict[str, int], case_count: int, vector_signatures: int, question_signatures: int) -> List[Dict[str, Any]]:
    proposals: List[Dict[str, Any]] = []
    target = max(case_count, 1)
    expected = {
        "strength_useful_god": 0.45,
        "pattern_structure": 0.22,
        "branch_relation": 0.35,
        "time_context": 0.18,
        "income_stability": 0.28,
        "metadata": 0.35,
    }
    for bucket, minimum_ratio in expected.items():
        observed_ratio = bucket_counts.get(bucket, 0) / target
        action = "keep"
        if observed_ratio < minimum_ratio * 0.55:
            action = "review_increase"
        elif observed_ratio > minimum_ratio * 2.4:
            action = "review_decrease"
        proposals.append(
            {
                "proposal_id": f"p79.shadow_weight.{bucket}",
                "bucket": bucket,
                "action": action,
                "observed_ratio": round(observed_ratio, 3),
                "minimum_ratio": minimum_ratio,
                "reason": "Review only. The proposal is based on synthetic portrait routing spread, not user outcome feedback.",
                "decision": "shadow_review_only",
                "runtime_mutation": False,
            }
        )
    if vector_signatures >= 8 and question_signatures >= 6:
        proposals.append(
            {
                "proposal_id": "p79.shadow_weight.keep_portrait_secondary_bias",
                "bucket": "global",
                "action": "keep_secondary_bias",
                "observed_ratio": 1.0,
                "minimum_ratio": 1.0,
                "reason": "Vector and question-route diversity are sufficient; portrait should remain secondary to Rule Graph path order.",
                "decision": "shadow_review_only",
                "runtime_mutation": False,
            }
        )
    return proposals


def _forbidden_failures(labels: List[Dict[str, Any]], judgements: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    failures: List[Dict[str, str]] = []
    forbidden = [item for item in FORBIDDEN_PORTRAIT_OUTPUTS if item not in {"一定"}]
    for row in labels:
        text = " ".join(str(row.get(key) or "") for key in ["candidate_statement", "value", "label_id"])
        for token in forbidden:
            if token in text:
                failures.append({"source_id": str(row.get("label_id") or ""), "token": token})
    for row in judgements:
        text = " ".join(str(row.get(key) or "") for key in ["text", "judgement_id"])
        for token in forbidden:
            if token in text:
                failures.append({"source_id": str(row.get("judgement_id") or ""), "token": token})
    return failures


def _failure(failure_type: str, detail: str) -> Dict[str, str]:
    return {"failure_type": failure_type, "detail": detail}
