from __future__ import annotations

from datetime import datetime, timezone

from v30.core.chart_context import build_chart_context_from_birth_input, build_chart_context_from_displays
from v30.core.ten_god_energy import build_ten_god_energy_model
from v30.contracts import BirthInput
from v30.evidence import compile_feature_evidence
from v30.runtime import create_runtime_from_context
from v30.validation import extract_training_signals, run_synthetic_tier


def test_ten_god_energy_model_scores_natal_and_time_layers() -> None:
    context = build_chart_context_from_displays(
        reading_id="energy-explicit",
        year="甲子",
        month="乙丑",
        day="丙寅",
        hour="丁卯",
        luck_pillar="庚午",
        flow_year_pillar="辛未",
    )

    model = build_ten_god_energy_model(context)

    assert model.status == "ready"
    assert model.scores
    assert any(score.energy > 0 for score in model.scores.values())
    assert any("luck_" in source or "flow_year_" in source for score in model.scores.values() for source in score.sources)
    assert model.high_volatility_ten_gods
    assert model.boundary == "ten_god_energy_model_signal_not_chart_fact"


def test_ten_god_energy_evidence_enters_runtime_without_user_diagnostic_leak() -> None:
    result = build_chart_context_from_birth_input(
        reading_id="energy-birth",
        birth_input=BirthInput(
            birth_date="1990-02-04",
            birth_time="23:30",
            timezone="Asia/Shanghai",
            gender="female",
        ),
        created_at=datetime(2030, 6, 1, tzinfo=timezone.utc),
    )
    assert result.chart_context is not None

    runtime = create_runtime_from_context(result.chart_context)

    model = runtime.question_plan.policy_effect["ten_god_energy_model"]
    summary = runtime.question_plan.policy_effect["ten_god_energy_summary"]
    model_signal_summary = runtime.question_plan.policy_effect["model_signal_summary"]
    assert model["status"] == "ready"
    assert summary["top_energy"]
    assert model_signal_summary["version"] == "v30.model_signal_summary.v1"
    assert model_signal_summary["raw_score_visible"] is False
    assert model_signal_summary["energy_bands"]
    assert "energy" not in model_signal_summary["energy_bands"][0]
    assert "stability" not in model_signal_summary["energy_bands"][0]
    assert "volatility" not in model_signal_summary["energy_bands"][0]
    assert model_signal_summary["interface_contract"]["version"] == "v30.model_signal_interface_contract.v1"
    assert set(model_signal_summary["interface_contract"]["consumers"]) >= {
        "structure_selector",
        "ranked_decisions",
        "answer_context",
        "training_signals",
    }
    assert "raw_weight" in model_signal_summary["interface_contract"]["forbidden_fields"]
    assert model_signal_summary["calibration_profile"]["version"] == "v30.model_signal_calibration_profile.v1"
    assert model_signal_summary["calibration_profile"]["family_coverage"]
    assert set(model_signal_summary["ranked_decision_inputs"]) >= {
        "strength",
        "structure_pattern",
        "useful_god",
    }
    assert any(row.domain == "ten_god_energy" for row in runtime.feature_evidence)
    assert runtime.structure_state.path_scores["ten_god_energy_ready"] == 1.0
    assert runtime.structure_state.path_scores["model_signal_summary_ready"] == 1.0
    assert runtime.structure_state.path_scores["model_signal_energy_band_count"] > 0
    assert "top_dynamic_path_model_signal_adjusted_score" in runtime.structure_state.path_scores
    assert runtime.structure_state.path_scores["structure_policy_model_signal_fusion"] == 1.0
    assert runtime.answer_context is not None
    assert "ten_god_energy_summary" in runtime.answer_context.role_answer_contract["can_use"]
    assert "model_signal_summary" in runtime.answer_context.role_answer_contract["can_use"]
    assert runtime.answer_context.role_answer_contract["model_signal_summary"]["summary_id"] == model_signal_summary["summary_id"]


def test_model_signal_summary_feeds_ranked_decisions_without_fixed_verdict() -> None:
    result = build_chart_context_from_birth_input(
        reading_id="energy-fusion",
        birth_input=BirthInput(
            birth_date="1990-02-04",
            birth_time="23:30",
            timezone="Asia/Shanghai",
            gender="female",
        ),
        created_at=datetime(2030, 6, 1, tzinfo=timezone.utc),
    )
    assert result.chart_context is not None

    runtime = create_runtime_from_context(result.chart_context)
    summary_id = runtime.question_plan.policy_effect["model_signal_summary"]["summary_id"]
    decisions = runtime.question_plan.policy_effect["ranked_decisions"]

    for domain in ("strength", "structure_pattern", "useful_god"):
        decision = decisions[domain]
        model_signal = decision["model_signal_summary"]
        assert model_signal["summary_id"] == summary_id
        assert model_signal["boundary"] == "ranked_decision_consumes_model_signal_summary_not_raw_score"
        assert summary_id in decision["supporting_evidence"]
        assert decision["status"] == "ranked_candidate"
        assert decision["candidate_scores"]
        assert decision["primary_candidate"] in decision["candidate_scores"]
        assert decision["scoring_basis"]["ten_god_energy_bands"]
        assert "fixed_useful_god_verdict" not in decision["supporting_evidence"]


def test_ten_god_energy_compiler_evidence_is_boundary_tagged() -> None:
    context = build_chart_context_from_displays(
        reading_id="energy-evidence",
        year="甲子",
        month="乙丑",
        day="丙寅",
        hour="丁卯",
    )
    model = build_ten_god_energy_model(context)
    evidence = compile_feature_evidence(context, ten_god_energy_model=model)
    row = next(item for item in evidence if item.domain == "ten_god_energy")

    assert row.kind == "energy_vector"
    assert "ten_god_energy_model_ready" in row.supports
    assert row.boundary == "ten_god_energy_model_signal_not_chart_fact"


def test_ten_god_energy_calibration_tier_covers_core_families_and_bands() -> None:
    result = run_synthetic_tier("ten_god_energy_calibration")
    assert result.passed
    assert result.case_count == 5

    signal = next(
        row for row in extract_training_signals(result)
        if row.signal_id == "v30.training_signal.ten_god_energy_fusion"
    )
    assert set(signal.payload["calibration_family_coverage"]) >= {
        "self",
        "resource",
        "output",
        "wealth",
        "authority",
    }
    assert signal.payload["raw_score_hidden_count"] == signal.payload["observed_count"]
    assert signal.payload["energy_band_counts"]["high"] >= 1
    assert signal.payload["volatility_band_counts"]["high"] >= 1
    assert signal.payload["stability_band_counts"]["low"] >= 1
    assert signal.payload["calibration_flag_counts"]
    assert signal.payload["ranked_adjustment_count"] >= signal.payload["observed_count"]


def test_m4_ten_god_real_case_replay_tier_validates_interface_contract() -> None:
    result = run_synthetic_tier("m4_ten_god_real_case_replay")
    assert result.passed
    assert result.case_count == 5
    observations = [row.observed["m4_ten_god_real_case_replay"] for row in result.results]
    assert all(row["status"] == "ready" for row in observations)
    assert all(row["raw_score_visible"] is False for row in observations)
    assert all(row["forbidden_field_leaks"] == [] for row in observations)
    assert all(row["ranked_decision_domain_count"] >= 3 for row in observations)
    assert all(row["calibration_flags"] for row in observations)
    assert all(row["ranked_adjustment_version"] == "v30.model_signal_ranked_decision_adjustments.v1" for row in observations)
    assert all("dynamic_structure_bonus" in row["ranked_adjustment_score_bias_keys"] for row in observations)
    assert {family for row in observations for family in row["family_coverage"]} >= {
        "self",
        "resource",
        "output",
        "wealth",
        "authority",
    }

    signal = next(
        row for row in extract_training_signals(result)
        if row.signal_id == "v30.training_signal.ten_god_energy_fusion"
    )
    assert signal.payload["real_case_replay_count"] == 5
    assert signal.payload["real_case_replay_interface_ready_count"] == 5
    assert set(signal.payload["real_case_replay_family_coverage"]) >= {
        "self",
        "resource",
        "output",
        "wealth",
        "authority",
    }
