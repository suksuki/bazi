from __future__ import annotations

from v20.validation import synthetic_replay
from v20.validation.synthetic_replay import normalize_synthetic_runtime_actual, run_synthetic_bazi_replay
from v20.validation.synthetic_schema import minimal_synthetic_bazi_cases
from v20.role_view.narrative_prompt_framework import question_narrative_for_question


def test_v20_synthetic_runtime_actual_normalizes_replay_material_without_private_text() -> None:
    runtime = _runtime_fixture()
    role_views = {
        "guest": _role_view_fixture("guest", "starter_questions", "public_entry", limit=1),
        "analyst": _role_view_fixture("analyst", "review_questions", "technical_review", limit=2),
    }

    actual = normalize_synthetic_runtime_actual(runtime, role_views=role_views)

    assert actual["feature_domains"] == ("strength", "wealth")
    assert actual["decision_domains"] == ("strength", "wealth")
    assert actual["portrait_labels"] == ("财星压力",)
    assert actual["question_keys"] == ("q_income_stability", "q_career_structure")
    assert actual["role_views"]["guest"]["question_count"] == 1
    assert actual["role_views"]["guest"]["visibility_level"] == "public_entry"
    assert actual["role_views"]["guest"]["voice_profile"] == "guest_soft_entry"
    assert actual["role_views"]["guest"]["question_narrative_quality"]["ready_ratio"] == 1.0
    assert actual["role_views"]["guest"]["answer_boundary_density"] == "plain_boundary"
    assert actual["role_views"]["guest"]["answer_style_policy"] == "compress_to_plain_boundary"
    assert actual["role_views"]["analyst"]["question_style"] == "review_questions"
    assert actual["role_views"]["analyst"]["answer_boundary_density"] == "technical_boundary_review"
    assert actual["runtime_mutation"] is False
    assert "NO_PRIVATE_TEXT_CAPTURED" in actual["guardrails"]


def test_v20_synthetic_bazi_replay_report_is_dry_run_and_uses_runtime_projection(monkeypatch) -> None:
    calls = []

    def fake_runtime(*pillars, **kwargs):
        calls.append({"pillars": pillars, "kwargs": kwargs})
        return _runtime_fixture()

    def fake_project(runtime, role_key):
        return _role_view_fixture(role_key, "starter_questions" if role_key == "guest" else "review_questions", role_key)

    monkeypatch.setattr(synthetic_replay, "run_runtime_from_pillars", fake_runtime)
    monkeypatch.setattr(synthetic_replay, "project_runtime_for_role", fake_project)

    report = run_synthetic_bazi_replay(minimal_synthetic_bazi_cases(), max_cases=1, role_keys=("guest", "analyst"))
    result = report["results"][0]

    assert report["version"] == "v20.synthetic_bazi_replay_report.v1"
    assert report["case_count"] == 1
    assert report["role_answer_governance_summary"]["version"] == "v20.role_answer_governance_replay_summary.v1"
    assert report["role_answer_governance_summary"]["role_view_count"] == 2
    assert report["role_answer_governance_summary"]["missing_profile_count"] == 0
    assert report["runtime_mutation"] is False
    assert result["actual"]["role_views"]["guest"]["question_count"] == 2
    assert result["actual"]["role_views"]["analyst"]["question_style"] == "review_questions"
    assert result["actual"]["role_views"]["analyst"]["voice_profile"] == "practitioner_evidence_review"
    assert result["actual"]["role_views"]["analyst"]["question_narrative_quality"]["ready_ratio"] == 1.0
    assert calls[0]["kwargs"]["llm_mode"] == "deterministic"
    assert calls[0]["kwargs"]["input_id"].startswith("v20.synthetic.bazi.")
    assert "NO_POLICY_POINTER_MUTATION" in result["guardrails"]


def test_v20_synthetic_bazi_replay_real_runtime_smoke_single_case() -> None:
    report = run_synthetic_bazi_replay(minimal_synthetic_bazi_cases()[:1], role_keys=("guest",))
    result = report["results"][0]
    actual = result["actual"]

    assert report["case_count"] == 1
    assert result["runtime_mutation"] is False
    assert actual["feature_domains"]
    assert actual["question_keys"]
    assert actual["answer_text"]
    assert actual["role_views"]["guest"]["question_count"] <= 3
    assert actual["role_views"]["guest"]["question_narrative_quality"]["ready_ratio"] == 1.0
    assert actual["role_views"]["guest"]["answer_boundary_density"] == "plain_boundary"


def _runtime_fixture() -> dict[str, object]:
    return {
        "version": "v20.runtime_result.v1",
        "input_id": "fixture",
        "locale": "zh",
        "chart_facts": {},
        "time_context": {},
        "core_inference": {},
        "feature_layer": {
            "features": [
                {"domain": "wealth", "feature_id": "feature.wealth.visible_material"},
                {"domain": "strength", "feature_id": "feature.strength.weak"},
            ]
        },
        "decision_report": {
            "decisions": [
                {"domain": "wealth", "rule_key": "rule.wealth.visible"},
                {"domain": "strength", "rule_key": "rule.strength.weak"},
            ],
            "portrait_projection": {
                "axes": [
                    {"axis_id": "wealth_pressure", "label": "财星压力", "domain": "wealth"},
                ]
            },
        },
        "questions": [
            {"question_key": "q_income_stability", "domain": "wealth", "measurement_stage": "focus"},
            {"question_key": "q_career_structure", "domain": "career", "measurement_stage": "structure"},
        ],
        "selected_question": {"question_key": "q_income_stability"},
        "answer_text": "fixture answer",
        "runtime_mutation": False,
        "guardrails": ["fixture"],
    }


def _role_view_fixture(role_key: str, question_style: str, visibility: str, *, limit: int = 2) -> dict[str, object]:
    questions = [
        dict(row) | {"question_narrative": question_narrative_for_question(dict(row), role_key)}
        for row in list(_runtime_fixture()["questions"])[:limit]
    ]
    return {
        "questions": questions,
        "role_view_model": {
            "question_profile": {
                "style": question_style,
                "voice_profile": question_narrative_for_question({}, role_key)["voice_profile"],
            },
            "visibility_profile": {"level": visibility},
        },
        "role_answer_profile": {
            "answer_governance_profile": {
                "quality_band": "strong",
                "quality_score": 1.0,
                "boundary_density": "plain_boundary" if role_key == "guest" else "technical_boundary_review",
                "style_policy": "compress_to_plain_boundary" if role_key == "guest" else "preserve_review_boundary",
            }
        },
        "role": {"role_key": role_key},
        "runtime_mutation": False,
    }
