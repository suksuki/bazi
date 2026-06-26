from __future__ import annotations

from v30.llm import build_bazi_llm_prompt_request, compose_bazi_llm_answer_draft
from v30.llm.provider import V30LLMProviderConfig
from v30.runtime import create_smoke_runtime


BAZI_LLM_ROLE_LOCALE_PRODUCTION_SMOKE_VERSION = "v30.bazi_llm_role_locale_production_smoke.v1"
ROLES = ("guest", "user", "practitioner")
LOCALES = ("zh", "en", "ko")


def run_bazi_llm_role_locale_production_smoke(
    reading_id: str = "bl7-bazi-llm-role-locale-smoke",
) -> dict[str, object]:
    runtime = create_smoke_runtime(reading_id=reading_id)
    observations: list[dict[str, object]] = []
    for role_key in ROLES:
        for locale in LOCALES:
            task_type = "practitioner_analysis" if role_key == "practitioner" else "customer_initial_reading"
            assert runtime.answer_context is not None
            assert runtime.answer_result is not None
            answer = compose_bazi_llm_answer_draft(
                runtime,
                runtime.answer_context,
                runtime.answer_result,
                task_type=task_type,
                role_key=role_key,
                locale=locale,
                config=_disabled_config(),
            )
            observations.append(_answer_observation(role_key=role_key, locale=locale, answer=answer))
    locale_rewrite_observations = [
        _locale_rewrite_observation(runtime, locale=locale)
        for locale in LOCALES
    ]
    return build_bazi_llm_role_locale_production_smoke(
        answer_observations=observations,
        locale_rewrite_observations=locale_rewrite_observations,
    )


def build_bazi_llm_role_locale_production_smoke(
    *,
    answer_observations: list[dict[str, object]],
    locale_rewrite_observations: list[dict[str, object]],
) -> dict[str, object]:
    checks = [
        {
            "check_id": "role_locale_matrix_is_covered",
            "passed": {
                (row.get("role_key"), row.get("locale")) for row in answer_observations
            } == {(role, locale) for role in ROLES for locale in LOCALES},
            "observed": {"rows": answer_observations},
        },
        {
            "check_id": "customer_roles_hide_diagnostics_and_internal_sections",
            "passed": all(
                _customer_visibility_ok(row)
                for row in answer_observations
                if row.get("role_key") in {"guest", "user"}
            ),
            "observed": [
                row for row in answer_observations
                if row.get("role_key") in {"guest", "user"}
            ],
        },
        {
            "check_id": "practitioner_role_allows_dense_context_without_pointer_write",
            "passed": all(
                row.get("diagnostics_visible") is True
                and "structure_dynamics" in set(row.get("context_section_ids", []))
                and "policy_pointer_write" in set(row.get("excluded_modules", []))
                for row in answer_observations
                if row.get("role_key") == "practitioner"
            ),
            "observed": [
                row for row in answer_observations
                if row.get("role_key") == "practitioner"
            ],
        },
        {
            "check_id": "locale_metadata_and_terminology_boundaries_are_present",
            "passed": all(row.get("locale_section_present") is True for row in locale_rewrite_observations)
            and {row.get("locale") for row in locale_rewrite_observations} == set(LOCALES),
            "observed": locale_rewrite_observations,
        },
        {
            "check_id": "disabled_provider_fallback_preserves_non_mutation",
            "passed": all(
                row.get("source") == "rule_bound_fallback"
                and row.get("executed") is False
                and row.get("raw_runtime_payload_included") is False
                and row.get("chart_fact_mutation_allowed") is False
                for row in answer_observations
            ),
            "observed": answer_observations,
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": BAZI_LLM_ROLE_LOCALE_PRODUCTION_SMOKE_VERSION,
        "task": {
            "task_id": "BL7",
            "title": "Bazi LLM Role And Locale Production Smoke",
            "scope": "guest_user_practitioner_and_zh_en_ko_prompt_metadata_without_live_provider",
        },
        "answer_observations": answer_observations,
        "locale_rewrite_observations": locale_rewrite_observations,
        "completion_summary": {
            "bazi_llm_role_contract_completion": 82 if ready else 75,
            "bazi_llm_locale_contract_completion": 80 if ready else 70,
            "bazi_llm_production_smoke_completion": 78 if ready else 60,
            "bazi_llm_mainline_completion": 80 if ready else 75,
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "readiness_ready": ready,
            "decision_status": "bl7_bazi_llm_role_locale_smoke_ready"
            if ready
            else "bl7_bazi_llm_role_locale_smoke_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "live_llm_required": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "BL8" if ready else "BL7-FIX",
            "title": "Bazi LLM Closeout And Optional Live Smoke Boundary"
            if ready
            else "Fix Bazi LLM Role Locale Smoke",
            "reason": "role_locale_smoke_ready_without_live_provider"
            if ready
            else "role_locale_smoke_checks_failed",
        },
        "boundary": "bl7_smoke_validates_role_locale_llm_metadata_not_chart_facts",
    }


def _answer_observation(*, role_key: str, locale: str, answer) -> dict[str, object]:
    metadata = answer.llm_metadata if isinstance(answer.llm_metadata, dict) else {}
    prompt = metadata.get("prompt_request", {})
    prompt = prompt if isinstance(prompt, dict) else {}
    return {
        "role_key": role_key,
        "locale": locale,
        "source": answer.source,
        "status": metadata.get("status", ""),
        "fallback_reason": metadata.get("fallback_reason", ""),
        "executed": metadata.get("executed", None),
        "task_type": metadata.get("task_type", ""),
        "context_pack": prompt.get("context_pack", ""),
        "role_contract_id": prompt.get("role_contract_id", ""),
        "diagnostics_visible": prompt.get("diagnostics_visible", False),
        "context_section_ids": prompt.get("context_section_ids", []),
        "excluded_modules": prompt.get("excluded_modules", []),
        "raw_runtime_payload_included": prompt.get("raw_runtime_payload_included", True),
        "chart_fact_mutation_allowed": prompt.get("chart_fact_mutation_allowed", True),
    }


def _locale_rewrite_observation(runtime, *, locale: str) -> dict[str, object]:
    request = build_bazi_llm_prompt_request(
        runtime,
        task_type="locale_rewrite",
        role_key="user",
        locale=locale,
    )
    context = request.get("context_pack", {})
    sections = context.get("sections", []) if isinstance(context, dict) else []
    locale_sections = [
        section for section in sections
        if isinstance(section, dict) and section.get("section_id") == "locale_terminology"
    ]
    content = locale_sections[0].get("content", {}) if locale_sections else {}
    content = content if isinstance(content, dict) else {}
    return {
        "locale": locale,
        "context_pack": context.get("context_pack") if isinstance(context, dict) else "",
        "locale_section_present": bool(locale_sections),
        "section_locale": content.get("locale", ""),
        "fallback_allowed": content.get("fallback_allowed"),
        "raw_runtime_payload_included": request.get("raw_runtime_payload_included", True),
        "chart_fact_mutation_allowed": request.get("chart_fact_mutation_allowed", True),
    }


def _customer_visibility_ok(row: dict[str, object]) -> bool:
    sections = set(row.get("context_section_ids", []))
    return (
        row.get("diagnostics_visible") is False
        and "diagnostics_summary" not in sections
        and row.get("raw_runtime_payload_included") is False
        and row.get("chart_fact_mutation_allowed") is False
    )


def _disabled_config() -> V30LLMProviderConfig:
    return V30LLMProviderConfig(
        enabled=True,
        execute_llm=False,
        provider="ollama_native",
        host="127.0.0.1",
        port=11434,
        base_url="http://127.0.0.1:11434/v1",
        model="qwen-test",
        api_key_env="V30_LLM_API_KEY",
        http_timeout_sec=0.1,
        temperature=0.2,
        max_tokens=120,
        config_source="test",
    )
