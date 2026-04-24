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
    assert insights["top_learning_signals"]
    assert insights["recommended_next_cases"]
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
    assert "Learning Signals" in rendered
    assert "Next Hard Cases" in rendered
    assert "已验证参数族" in rendered
    assert "Safety Gates" in rendered
