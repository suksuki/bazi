from __future__ import annotations

from typing import Any


BAZI_LLM_OUTPUT_ACCEPTANCE_VERSION = "v30.bazi_llm_output_acceptance.v1"


def bazi_llm_output_text(payload: dict[str, object], task_type: str) -> str:
    if not isinstance(payload, dict):
        return ""
    if task_type == "locale_rewrite":
        return str(payload.get("rewritten_text") or payload.get("text") or "").strip()
    if task_type == "practitioner_analysis":
        return str(payload.get("analysis_text") or payload.get("text") or "").strip()
    if task_type == "hidden_factor_dialogue":
        return str(payload.get("dialogue_text") or payload.get("text") or "").strip()
    return str(payload.get("answer_text") or payload.get("text") or "").strip()


def validate_bazi_llm_output_payload(
    payload: dict[str, object],
    *,
    prompt_request: dict[str, object],
    text: str,
    drift_check: dict[str, object],
) -> dict[str, object]:
    contract = _dict(prompt_request.get("prompt_contract"))
    context_pack = _dict(prompt_request.get("context_pack"))
    output_schema = _dict(contract.get("output_schema"))
    role_contract = _dict(context_pack.get("role_contract")) or _dict(contract.get("role_contract"))
    required_fields = [str(row) for row in _list(output_schema.get("required_fields"))]
    missing_fields = [
        field for field in required_fields
        if not _field_present(payload, field)
    ]
    role_failures = _role_visibility_failures(text, role_contract)
    content_failures = _content_quality_failures(text, str(contract.get("task_type") or ""))
    drift_failures = _list(drift_check.get("failures"))
    accepted = not missing_fields and not role_failures and not content_failures and drift_check.get("passed") is True
    return {
        "version": BAZI_LLM_OUTPUT_ACCEPTANCE_VERSION,
        "accepted": accepted,
        "schema_id": output_schema.get("schema_id", ""),
        "required_fields": required_fields,
        "missing_fields": missing_fields,
        "role_contract_id": role_contract.get("role_contract_id", ""),
        "role_visibility_passed": not role_failures,
        "role_failures": role_failures,
        "content_quality_passed": not content_failures,
        "content_failures": content_failures,
        "drift_passed": drift_check.get("passed") is True,
        "drift_failures": drift_failures,
        "chart_fact_mutation_allowed": False,
        "raw_runtime_payload_included": prompt_request.get("raw_runtime_payload_included", True),
        "boundary": "bazi_llm_output_acceptance_validates_schema_role_and_drift_before_text_replacement",
    }


def _field_present(payload: dict[str, object], field: str) -> bool:
    value = payload.get(field)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _role_visibility_failures(text: str, role_contract: dict[str, object]) -> list[str]:
    failures: list[str] = []
    normalized = text.lower()
    diagnostics_visible = role_contract.get("diagnostics_visible") is True
    if not diagnostics_visible:
        forbidden_terms = (
            "diagnostics",
            "policy",
            "training",
            "admin",
            "raw_runtime",
            "prompt_contract_id",
            "context_pack_id",
            "v30.",
            "基础判断：",
            "路径复核：",
            "特征画像：",
            "证据数=",
            "llm_bazi_answer_draft",
            "llm accepted",
        )
        for term in forbidden_terms:
            if term in normalized:
                failures.append(f"customer_role_leaks_{term}")
    return failures


def _content_quality_failures(text: str, task_type: str) -> list[str]:
    failures: list[str] = []
    if not text.strip():
        return ["empty_answer_text"]
    if task_type in {"customer_initial_reading", "domain_followup", "practitioner_analysis"}:
        if not _has_any(text, ("庚", "甲", "乙", "丙", "丁", "戊", "己", "辛", "壬", "癸", "日主", "命局", "命盘")):
            failures.append("missing_chart_or_day_master_language")
        if not _has_any(text, ("官印相生", "财官印", "食伤生财", "食伤制官杀", "官杀", "印星", "财星", "食伤", "比劫", "十神")):
            failures.append("missing_bazi_mechanism_language")
        if not _has_any(text, ("事业", "财", "关系", "健康", "时运", "大运", "流年", "结构", "路径", "画像", "特征")):
            failures.append("missing_domain_or_evidence_layer_language")
    if task_type == "domain_followup":
        if not _has_any(text, ("事业", "财", "关系", "健康", "时运", "大运", "流年")):
            failures.append("missing_selected_domain_language")
    if task_type == "hidden_factor_dialogue":
        if not _has_any(text, ("年份", "反复", "状态", "反馈", "选项", "确认")):
            failures.append("missing_constrained_feedback_language")
    if _has_any(text, ("套路", "综合参考", "后续我们可以", "需结合后续问答复核", "Current chart supports")):
        failures.append("generic_placeholder_language")
    return failures


def _has_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
