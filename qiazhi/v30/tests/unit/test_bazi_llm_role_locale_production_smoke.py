from __future__ import annotations

from v30.validation import run_bazi_llm_role_locale_production_smoke


def test_bazi_llm_role_locale_production_smoke_accepts_bl7() -> None:
    result = run_bazi_llm_role_locale_production_smoke(reading_id="pytest-bl7-smoke")

    assert result["version"] == "v30.bazi_llm_role_locale_production_smoke.v1"
    assert result["decision"]["decision_status"] == "bl7_bazi_llm_role_locale_smoke_ready"
    assert result["decision"]["readiness_ready"] is True
    assert result["decision"]["live_llm_required"] is False
    assert result["decision"]["policy_pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "BL8"


def test_bazi_llm_role_locale_smoke_covers_roles_and_locales() -> None:
    result = run_bazi_llm_role_locale_production_smoke(reading_id="pytest-bl7-matrix")
    rows = result["answer_observations"]

    assert {(row["role_key"], row["locale"]) for row in rows} == {
        (role, locale)
        for role in ("guest", "user", "practitioner")
        for locale in ("zh", "en", "ko")
    }
    customer_rows = [row for row in rows if row["role_key"] in {"guest", "user"}]
    assert customer_rows
    assert all(row["diagnostics_visible"] is False for row in customer_rows)
    assert all("diagnostics_summary" not in set(row["context_section_ids"]) for row in customer_rows)
    practitioner_rows = [row for row in rows if row["role_key"] == "practitioner"]
    assert practitioner_rows
    assert all(row["diagnostics_visible"] is True for row in practitioner_rows)
    assert all("structure_dynamics" in set(row["context_section_ids"]) for row in practitioner_rows)
    assert all("policy_pointer_write" in set(row["excluded_modules"]) for row in practitioner_rows)


def test_bazi_llm_locale_rewrite_context_has_terminology_boundary() -> None:
    result = run_bazi_llm_role_locale_production_smoke(reading_id="pytest-bl7-locale")
    rows = result["locale_rewrite_observations"]

    assert {row["locale"] for row in rows} == {"zh", "en", "ko"}
    assert all(row["context_pack"] == "BaziLocaleRewriteContext" for row in rows)
    assert all(row["locale_section_present"] is True for row in rows)
    assert all(row["fallback_allowed"] is False for row in rows)
    assert all(row["raw_runtime_payload_included"] is False for row in rows)
    assert all(row["chart_fact_mutation_allowed"] is False for row in rows)
