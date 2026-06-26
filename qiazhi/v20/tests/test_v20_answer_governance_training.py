from __future__ import annotations

from v20.learning.answer_governance_training import build_answer_governance_training_report


def test_v20_answer_governance_training_turns_replay_answers_into_parameter_signal() -> None:
    replay = {
        "version": "v20.synthetic_bazi_replay_report.v1",
        "role_answer_governance_summary": {
            "version": "v20.role_answer_governance_replay_summary.v1",
            "role_view_count": 2,
            "average_quality_score": 1.0,
            "missing_profile_count": 0,
        },
        "stream_answer_governance_summary": {
            "version": "v20.stream_answer_governance_summary.v1",
            "source": "unit",
            "sample_count": 2,
            "average_quality_score": 1.0,
            "weak_or_thin_count": 0,
            "quality_band_counts": {"strong": 2},
        },
        "results": [
            {
                "case_id": "case.strong",
                "case_type": "negative_boundary_case",
                "actual": {
                    "answer_text": "当前命局可见：财星需要结合日主承载复核。边界：只说明证据支持的结构，下一步继续看时间层是否牵动。",
                },
            }
        ],
    }

    report = build_answer_governance_training_report(replay_report=replay)

    assert report["version"] == "v20.answer_governance_training_report.v1"
    assert report["status"] == "ready"
    assert report["case_count"] == 1
    assert report["average_quality_score"] >= 0.8
    assert report["parameter_targets"]["answer_guidance_weight"] > 0
    assert report["parameter_targets"]["role_answer_governance_weight"] > 0
    assert report["parameter_targets"]["prompt_context_budget_weight"] > 0
    assert report["parameter_targets"]["stream_answer_quality_weight"] > 0
    assert report["stream_answer_governance_summary"]["sample_count"] == 2
    assert report["role_answer_governance_summary"]["role_view_count"] == 2
    assert report["quality_findings"] == []
    assert "QUALITY_SCORE_FEEDS_RUNTIME_POINTER_WEIGHT_ONLY" in report["guardrails"]


def test_v20_answer_governance_training_blocks_weight_bonus_for_thin_answers() -> None:
    replay = {
        "version": "v20.synthetic_bazi_replay_report.v1",
        "role_answer_governance_summary": {
            "version": "v20.role_answer_governance_replay_summary.v1",
            "role_view_count": 1,
            "average_quality_score": 1.0,
            "missing_profile_count": 1,
        },
        "stream_answer_quality_samples": [
            {"quality_score": 0.2, "quality_band": "weak"},
        ],
        "results": [
            {
                "case_id": "case.thin",
                "case_type": "negative_boundary_case",
                "actual": {"answer_text": "财星可见，可以继续看。"},
            }
        ],
    }

    report = build_answer_governance_training_report(replay_report=replay)

    assert report["average_quality_score"] < 0.8
    assert report["parameter_targets"]["answer_guidance_weight"] == 0.0
    assert report["parameter_targets"]["role_answer_governance_weight"] == 0.0
    assert report["parameter_targets"]["prompt_context_budget_weight"] == 0.0
    assert report["weak_or_thin_case_count"] >= 1
    assert report["quality_findings"]
    assert "stream_answer_governance_weak_or_thin_count:1" in report["quality_findings"]
