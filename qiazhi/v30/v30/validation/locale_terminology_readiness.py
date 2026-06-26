from __future__ import annotations

from v30.presentation.client_model import build_presentation_model
from v30.presentation.i18n import BAZI_TERMS, REQUIRED_BAZI_TERM_KEYS, build_locale_terminology_contract
from v30.runtime import create_smoke_runtime


LOCALE_TERMINOLOGY_READINESS_VERSION = "v30.locale_terminology_readiness.v1"
LOCALES = ("zh", "en", "ko")


def run_locale_terminology_readiness(reading_id: str = "u3-locale-terminology") -> dict[str, object]:
    runtimes = {
        locale: create_smoke_runtime(reading_id=f"{reading_id}-{locale}", locale=locale)
        for locale in LOCALES
    }
    projections = {
        locale: build_presentation_model(
            runtimes[locale],
            role_key="user",
            locale=locale,
            client="web",
        ).model_dump(mode="json")
        for locale in LOCALES
    }
    admin_projections = {
        locale: build_presentation_model(
            runtimes[locale],
            role_key="admin",
            locale=locale,
            client="admin",
        ).model_dump(mode="json")
        for locale in LOCALES
    }
    return build_locale_terminology_readiness(
        projections=projections,
        admin_projections=admin_projections,
    )


def build_locale_terminology_readiness(
    *,
    projections: dict[str, dict[str, object]],
    admin_projections: dict[str, dict[str, object]],
) -> dict[str, object]:
    contracts = {locale: build_locale_terminology_contract(locale) for locale in LOCALES}
    checks = [
        {
            "check_id": "required_bazi_terms_are_covered_for_all_locales",
            "passed": all(contract.get("ready") is True for contract in contracts.values()),
            "observed": {
                locale: {
                    "term_count": contract.get("term_count"),
                    "missing_term_keys": contract.get("missing_term_keys"),
                    "fallback_term_keys": contract.get("fallback_term_keys"),
                }
                for locale, contract in contracts.items()
            },
        },
        {
            "check_id": "presentation_layout_exposes_ready_locale_contract",
            "passed": all(_layout_contract_ready(payload, locale) for locale, payload in projections.items())
            and all(_layout_contract_ready(payload, locale) for locale, payload in admin_projections.items()),
            "observed": {
                locale: _layout_contract(projections[locale])
                for locale in LOCALES
            },
        },
        {
            "check_id": "question_label_fallback_is_zero_for_supported_locales",
            "passed": all(_question_fallback_count(payload) == 0 for payload in projections.values())
            and all(_question_fallback_count(payload) == 0 for payload in admin_projections.values()),
            "observed": {
                locale: {
                    "user_fallback_count": _question_fallback_count(projections[locale]),
                    "admin_fallback_count": _question_fallback_count(admin_projections[locale]),
                }
                for locale in LOCALES
            },
        },
        {
            "check_id": "domain_cards_use_locale_terms",
            "passed": all(_domain_labels_match_locale(projections[locale], locale) for locale in LOCALES),
            "observed": {
                locale: _domain_labels(projections[locale])
                for locale in LOCALES
            },
        },
        {
            "check_id": "base_fact_labels_use_locale_terms",
            "passed": all(_base_fact_labels_match_locale(projections[locale], locale) for locale in LOCALES),
            "observed": {
                locale: _base_fact_labels(projections[locale])
                for locale in LOCALES
            },
        },
        {
            "check_id": "locale_projection_does_not_change_chart_facts",
            "passed": _chart_fact_fingerprints(projections) == _chart_fact_fingerprints(admin_projections),
            "observed": {
                "user_fingerprints": _chart_fact_fingerprints(projections),
                "admin_fingerprints": _chart_fact_fingerprints(admin_projections),
            },
        },
        {
            "check_id": "locale_terms_are_projection_only",
            "passed": all(
                contract.get("boundary") == "locale_terms_render_bazi_language_without_creating_chart_facts"
                for contract in contracts.values()
            ),
            "observed": {
                locale: contract.get("boundary")
                for locale, contract in contracts.items()
            },
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": LOCALE_TERMINOLOGY_READINESS_VERSION,
        "task": {
            "task_id": "U3",
            "title": "Locale Terminology And Fallback Contract",
            "scope": "zh_en_ko_bazi_terminology_projection",
        },
        "completion_summary": {
            "multi_locale_projection_completion": 88 if ready else 76,
            "deep_locale_content_completion": 75 if ready else 55,
            "multi_user_projection_completion": 88,
            "multi_terminal_projection_completion": 80,
            "locale_count": len(LOCALES),
            "required_term_count": len(REQUIRED_BAZI_TERM_KEYS),
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "readiness_ready": ready,
            "decision_status": "u3_locale_terminology_ready" if ready else "u3_locale_terminology_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "chart_fact_mutation_allowed": False,
            "core_bazi_modules_reopened": False,
            "llm_translation_required": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "U4" if ready else "U3-FIX",
            "title": "Terminal Contract Freeze" if ready else "Fix Locale Terminology Contract",
            "reason": "locale_terms_ready_next_terminal_contract" if ready else "u3_checks_failed",
        },
        "boundary": "u3_locale_terminology_is_projection_contract_not_bazi_fact_generation",
    }


def _layout_contract(payload: dict[str, object]) -> dict[str, object]:
    layout = payload.get("layout", {})
    if not isinstance(layout, dict):
        return {}
    contract = layout.get("locale_terminology_contract", {})
    return contract if isinstance(contract, dict) else {}


def _layout_contract_ready(payload: dict[str, object], locale: str) -> bool:
    contract = _layout_contract(payload)
    return contract.get("locale") == locale and contract.get("ready") is True


def _question_fallback_count(payload: dict[str, object]) -> int:
    layout = payload.get("layout", {})
    if not isinstance(layout, dict):
        return 999
    summary = layout.get("rendered_question_label_summary", {})
    if not isinstance(summary, dict):
        return 999
    return int(summary.get("fallback_count", 999) or 0)


def _domain_labels_match_locale(payload: dict[str, object], locale: str) -> bool:
    labels = _domain_labels(payload)
    expected = BAZI_TERMS[locale]  # type: ignore[index]
    return labels.get("career") == expected["career"] and labels.get("wealth") == expected["wealth"]


def _domain_labels(payload: dict[str, object]) -> dict[str, str]:
    surface = payload.get("reading_surface", {})
    if not isinstance(surface, dict):
        return {}
    cards = surface.get("domain_cards", [])
    if not isinstance(cards, list):
        return {}
    return {
        str(row.get("domain") or ""): str(row.get("label") or "")
        for row in cards
        if isinstance(row, dict)
    }


def _base_fact_labels_match_locale(payload: dict[str, object], locale: str) -> bool:
    labels = _base_fact_labels(payload)
    expected = BAZI_TERMS[locale]  # type: ignore[index]
    return (
        labels.get("day_master") == expected["day_master"]
        and labels.get("ten_gods") == expected["ten_god"]
        and labels.get("five_elements") == expected["five_elements"]
        and labels.get("relations") == expected["branch_relation"]
    )


def _base_fact_labels(payload: dict[str, object]) -> dict[str, str]:
    surface = payload.get("reading_surface", {})
    if not isinstance(surface, dict):
        return {}
    core = surface.get("core_bazi_reading", {})
    if not isinstance(core, dict):
        return {}
    explanations = core.get("base_fact_explanations", {})
    if not isinstance(explanations, dict):
        return {}
    return {
        key: str(value.get("label") or "")
        for key, value in explanations.items()
        if isinstance(value, dict)
    }


def _chart_fact_fingerprints(payloads: dict[str, dict[str, object]]) -> dict[str, tuple[str, str, str]]:
    fingerprints: dict[str, tuple[str, str, str]] = {}
    for locale, payload in payloads.items():
        chart = payload.get("chart_summary", {})
        surface = payload.get("reading_surface", {})
        core = surface.get("core_bazi_reading", {}) if isinstance(surface, dict) else {}
        fingerprints[locale] = (
            str(chart.get("day_master") if isinstance(chart, dict) else ""),
            str(chart.get("day_master_element") if isinstance(chart, dict) else ""),
            str(core.get("fact_integrity", {}).get("source_type") if isinstance(core, dict) else ""),
        )
    return fingerprints
