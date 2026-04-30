from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Tuple

from v19.structure_portrait import FORBIDDEN_PORTRAIT_OUTPUTS
from v19.synthetic_validation.guided_cases import P11_GUIDED_SYNTHETIC_CASES
from v19.synthetic_validation.guided_runner import _agent_data_for_case


STRUCTURE_PORTRAIT_MATRIX_VERSION = "v19.mainline.structure_portrait_matrix.v1"
STRUCTURE_PORTRAIT_MATRIX_REGRESSION_VERSION = "v19.mainline.structure_portrait_matrix_regression.v1"

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


def _vector_signature(vectors: Dict[str, Any]) -> Tuple[float, ...]:
    keys = ["wealth_visibility", "branch_volatility", "time_trigger_activity", "pattern_index_strength", "useful_god_candidate_confidence"]
    return tuple(round(float(vectors.get(key) or 0), 2) for key in keys)


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
