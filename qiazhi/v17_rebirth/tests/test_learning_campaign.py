from __future__ import annotations

import pytest

from v17_rebirth.testing.learning_campaign import (
    LEARNING_CAMPAIGN_VERSION,
    LearningCampaignConfig,
    render_learning_campaign_markdown,
    run_learning_campaign,
)


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


def test_learning_campaign_runs_comprehensive_safe_cycle() -> None:
    report = run_learning_campaign(LearningCampaignConfig(max_duration_seconds=10_800))

    assert report["protocol"] == LEARNING_CAMPAIGN_VERSION
    assert report["primary_reviewer"] == "codex"
    assert report["secondary_reviewer"] == "analyst"
    assert report["can_auto_apply"] is False
    assert report["budget"]["within_budget"] is True
    assert report["budget"]["max_duration_seconds"] == 10_800
    assert report["plugin_governance_coverage"]["plugin_count"] > 0
    assert report["synthetic_batch"]["case_count"] >= 10
    assert report["extended_synthetic"]["case_count"] >= report["synthetic_batch"]["case_count"]
    assert report["practitioner_benchmarks"]["case_count"] >= 3
    insights = report["learning_insights"]
    assert insights["protocol"] == "v17.learning_insights.v1"
    assert insights["learning_value"] in {"actionable", "baseline_validated", "low_signal_green"}
    assert insights["validated_parameter_families"]
    algorithm = insights["algorithm_intelligence"]
    assert algorithm["protocol"] == "v17.learning_campaign.algorithm_intelligence.v1"
    assert algorithm["trace_case_count"] >= 1
    assert algorithm["average_trace_coverage"] > 0
    assert algorithm["validated_stages"]
    assert algorithm["critical_path_coverage_ratio"] > 0
    assert algorithm["gate_stage_coverage_ratio"] > 0
    assert algorithm["core_critical_path_coverage_ratio"] > 0
    assert algorithm["core_validated_steps"]
    assert "runtime_synced" not in algorithm["validated_stages"] or algorithm["authority_gate_coverage_ratio"] > 0
    assert insights["top_learning_signals"]
    assert insights["recommended_next_cases"]
    assert insights["freeze_rationale"]
    guidance = insights["parameter_optimization_guidance"]
    assert guidance["readiness"] in {"freeze_only", "review_candidates_ready"}
    assert guidance["freeze_families"]
    assert guidance["watch_families"]
    optimization_map = insights["parameter_optimization_map"]
    assert optimization_map
    assert all("parameter_family" in row for row in optimization_map)
    assert all("target" in row for row in optimization_map)
    assert all("required_commands" in row for row in optimization_map)
    assert all("safety_gates" in row for row in optimization_map)
    assert "do_not_write_real_config" in report["safety_gates"]


def test_learning_campaign_keeps_llm_review_as_explicit_package() -> None:
    report = run_learning_campaign(
        LearningCampaignConfig(
            max_duration_seconds=10_800,
            request_llm_review=True,
            max_extended_cases=2,
        )
    )

    llm_package = report["llm_review_package"]
    assert llm_package["protocol"] == "v17.learning_campaign.llm_review_package.v1"
    assert llm_package["requested"] is True
    assert "direct_config_patch" in llm_package["forbidden_output"]


def test_learning_campaign_markdown_report_is_codex_first() -> None:
    report = run_learning_campaign(
        LearningCampaignConfig(
            max_duration_seconds=10_800,
            max_extended_cases=2,
        )
    )
    rendered = render_learning_campaign_markdown(report)

    assert "# V17 Auto Learning Campaign Report" in rendered
    assert "主审：`codex`" in rendered
    assert "复核：`analyst`" in rendered
    assert "Learning Value" in rendered
    assert "Algorithm Intelligence" in rendered
    assert "关键路径覆盖率" in rendered
    assert "重点依赖边" in rendered
    assert "Core 关键路径覆盖率" in rendered
    assert "Freeze Rationale" in rendered
    assert "Parameter Optimization Guidance" in rendered
    assert "Parameter Optimization Map" in rendered
    assert "Learning Signals" in rendered
    assert "Next Hard Cases" in rendered
    assert "已验证参数族" in rendered
    assert "Safety Gates" in rendered
