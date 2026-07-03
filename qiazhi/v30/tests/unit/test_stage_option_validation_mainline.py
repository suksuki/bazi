from __future__ import annotations

from v30.validation.llm_prompt_profile_quality_audit import run_llm_prompt_profile_quality_audit
from v30.validation.stage_option_intelligence_replay import run_stage_option_intelligence_replay
from v30.validation.text_option_synthetic_validation import run_text_option_synthetic_validation


def test_text_option_synthetic_validation_covers_toi_spi_hidden_factor() -> None:
    result = run_text_option_synthetic_validation(reading_id="pytest-toi-synthetic-validation")

    assert result["version"] == "v30.text_option_synthetic_validation.v1"
    assert result["status"] == "completed"
    assert result["decision"]["text_option_synthetic_ready"] is True
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert {"SPI-7A", "TOI-7B", "TOI-7C", "HF-TOI-A", "VAL-518K-A"} <= {
        row["case_id"] for row in result["cases"]
    }


def test_stage_option_intelligence_replay_validation_is_ready() -> None:
    result = run_stage_option_intelligence_replay(reading_id="pytest-stage-option-replay")

    assert result["version"] == "v30.stage_option_intelligence_replay.v1"
    assert result["status"] == "completed"
    assert result["decision"]["admin_observability_ready"] is True
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["replay"]["summary"]["option_set_count"] >= 1


def test_llm_prompt_profile_quality_audit_is_offline_and_stage_bound() -> None:
    result = run_llm_prompt_profile_quality_audit(reading_id="pytest-prompt-profile-audit")

    assert result["version"] == "v30.llm_prompt_profile_quality_audit.v1"
    assert result["status"] == "completed"
    assert result["decision"]["prompt_profile_quality_ready"] is True
    assert result["live_smoke"]["llm_execution_performed"] is False
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert all(row["stage_local"] for row in result["stage_results"])
