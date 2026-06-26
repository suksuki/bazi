from __future__ import annotations

import subprocess
import sys

from v30.presentation.i18n import build_locale_terminology_contract, term_label
from v30.validation.locale_terminology_readiness import run_locale_terminology_readiness


def test_u3_locale_terminology_accepts_supported_locales() -> None:
    result = run_locale_terminology_readiness("unit-u3-locale")

    assert result["version"] == "v30.locale_terminology_readiness.v1"
    assert result["decision"]["decision_status"] == "u3_locale_terminology_ready"
    assert result["completion_summary"]["multi_locale_projection_completion"] == 88
    assert result["completion_summary"]["deep_locale_content_completion"] == 75
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["decision"]["llm_translation_required"] is False
    assert result["next_mainline_selection"]["task_id"] == "U4"
    assert all(row["passed"] for row in result["checks"])


def test_u3_term_contract_has_no_required_fallbacks() -> None:
    assert term_label("en", "day_master") == "Day Master"
    assert term_label("ko", "useful_god_candidate") == "용신 후보"
    for locale in ("zh", "en", "ko"):
        contract = build_locale_terminology_contract(locale)
        assert contract["ready"] is True
        assert contract["missing_term_keys"] == []
        assert contract["fallback_term_keys"] == []


def test_u3_locale_terminology_script_runs() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_locale_terminology_readiness.py",
            "--reading-id",
            "unit-u3-script",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "v30.locale_terminology_readiness.v1: passed" in result.stdout
    assert "u3_locale_terminology_ready" in result.stdout
