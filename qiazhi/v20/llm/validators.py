from __future__ import annotations

from v20.llm.contracts import LLMTaskContract
from v20.llm.enforcement import hard_enforce_text


def validate_llm_output(contract: LLMTaskContract, text: str) -> dict[str, object]:
    enforcement = hard_enforce_text(text)
    failures = list(enforcement["failures"])
    return {
        "ok": not failures,
        "task_name": contract.task_name,
        "failures": failures,
        "fallback": contract.fallback if failures else "",
        "guardrails": [
            "LLM_OUTPUT_VALIDATED",
            "HARD_TEXT_ENFORCEMENT_APPLIED",
            "DETERMINISTIC_FALLBACK_ON_FAILURE",
        ],
    }


def validate_llm_structured_output(contract: LLMTaskContract, payload: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    missing = [key for key in contract.required_outputs if key not in payload]
    if missing:
        failures.extend(f"missing:{key}" for key in missing)
    forbidden = [key for key in contract.forbidden_outputs if key in payload]
    if forbidden:
        failures.extend(f"forbidden_output_key:{key}" for key in forbidden)
    public_text = " ".join(
        str(value)
        for key, value in payload.items()
        if key in {"text", "summary", "normalized_question", "reason", "rationale", "risk_notes"}
    )
    enforcement = hard_enforce_text(public_text)
    failures.extend(failure for failure in enforcement["failures"] if failure != "empty_output")
    return {
        "ok": not failures,
        "task_name": contract.task_name,
        "failures": failures,
        "fallback": contract.fallback if failures else "",
        "guardrails": ["LLM_STRUCTURED_OUTPUT_VALIDATED", "CONTRACT_REQUIRED_OUTPUTS_CHECKED"],
    }
