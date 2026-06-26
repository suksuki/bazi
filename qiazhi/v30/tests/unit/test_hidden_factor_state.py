from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from v30.config import V30Settings
from v30.hidden_factor import (
    HiddenFactorCalibration,
    HiddenFactorState,
    build_hidden_factor_state,
    hidden_factor_feedback_from_payload,
    merge_hidden_factor_state,
)
from v30.runtime import create_smoke_runtime
from v30.runtime import attach_hidden_factor_state
from v30.storage.hidden_factor_state import LocalJsonHiddenFactorStateRepository


def _settings(tmp_path: Path) -> V30Settings:
    return V30Settings(
        database_url=None,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="local_json",
    )


def test_hidden_factor_state_promotes_calibrated_feedback_to_amplifier_candidate() -> None:
    runtime = create_smoke_runtime("v30-hidden-state", hidden_factor_user_calibrated=True)
    feedback = hidden_factor_feedback_from_payload(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        payload={
            "feedback_id": "feedback-001",
            "special_event_years": [2023],
            "repeated_states": ["career_pressure_repeat"],
        },
    )
    state = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=HiddenFactorCalibration.model_validate(
            runtime.question_plan.policy_effect["hidden_factor_calibration"]
        ),
        feedback=[feedback],
    )
    assert state.status == "amplifier_candidate"
    assert state.amplifier_candidate is True
    assert state.amplifier_strength > 0.8
    assert state.special_event_years == [2023]
    assert state.event_year_signal.year_count == 1
    assert state.repeated_state_signal.domains == ["career"]
    assert state.alignment_score > 0
    assert "repeated_state_pattern" not in state.next_feedback_needed


def test_hidden_factor_state_year_only_stays_dialogue_in_progress() -> None:
    runtime = create_smoke_runtime("v30-hidden-state-year-only")
    state = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=HiddenFactorCalibration.model_validate(
            runtime.question_plan.policy_effect["hidden_factor_calibration"]
        ),
        feedback=[
            hidden_factor_feedback_from_payload(
                reading_id=runtime.reading_id,
                context_id=runtime.chart_context.context_id,
                payload={"feedback_id": "feedback-year", "special_event_year": 2024},
            )
        ],
    )
    assert state.status == "dialogue_in_progress"
    assert state.amplifier_candidate is False
    assert state.alignment_score == 0.0


def test_hidden_factor_state_repeated_state_only_stays_dialogue_in_progress() -> None:
    runtime = create_smoke_runtime("v30-hidden-state-state-only")
    state = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=HiddenFactorCalibration.model_validate(
            runtime.question_plan.policy_effect["hidden_factor_calibration"]
        ),
        feedback=[
            hidden_factor_feedback_from_payload(
                reading_id=runtime.reading_id,
                context_id=runtime.chart_context.context_id,
                payload={"feedback_id": "feedback-state", "repeated_state": "relationship_repeat"},
            )
        ],
    )
    assert state.status == "dialogue_in_progress"
    assert state.amplifier_candidate is False
    assert state.repeated_state_signal.domains == ["relationship"]
    assert state.alignment_score == 0.0


def test_hidden_factor_state_multi_year_time_bound_alignment_is_stronger() -> None:
    runtime = create_smoke_runtime("v30-hidden-state-multi-year", luck_pillar="戊辰", flow_year_pillar="甲辰")
    calibration = HiddenFactorCalibration.model_validate(
        runtime.question_plan.policy_effect["hidden_factor_calibration"]
    )
    single = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=calibration,
        feedback=[
            hidden_factor_feedback_from_payload(
                reading_id=runtime.reading_id,
                context_id=runtime.chart_context.context_id,
                payload={"feedback_id": "single", "special_event_year": 2023, "repeated_state": "career_repeat"},
            )
        ],
    )
    multi = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=calibration,
        feedback=[
            hidden_factor_feedback_from_payload(
                reading_id=runtime.reading_id,
                context_id=runtime.chart_context.context_id,
                payload={
                    "feedback_id": "multi",
                    "special_event_years": [2021, 2023, 2024],
                    "repeated_states": ["career_repeat", "career_pressure_repeat"],
                    "luck_pillar": "戊辰",
                    "flow_year_pillar": "甲辰",
                },
            )
        ],
    )
    assert multi.status == "amplifier_candidate"
    assert multi.event_year_signal.is_multi_year is True
    assert multi.event_year_signal.bound_to_time_context is True
    assert multi.alignment_score > single.alignment_score
    assert multi.time_layer_alignment_score > single.time_layer_alignment_score
    assert multi.amplifier_strength > single.amplifier_strength
    assert multi.expires_at is not None


def test_hidden_factor_state_merges_dialogue_feedback() -> None:
    runtime = create_smoke_runtime("v30-hidden-state-merge", hidden_factor_user_calibrated=True)
    calibration = HiddenFactorCalibration.model_validate(
        runtime.question_plan.policy_effect["hidden_factor_calibration"]
    )
    first = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=calibration,
        feedback=[
            hidden_factor_feedback_from_payload(
                reading_id=runtime.reading_id,
                context_id=runtime.chart_context.context_id,
                payload={"feedback_id": "feedback-year", "special_event_year": 2021},
            )
        ],
    )
    second = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=calibration,
        feedback=[
            hidden_factor_feedback_from_payload(
                reading_id=runtime.reading_id,
                context_id=runtime.chart_context.context_id,
                payload={"feedback_id": "feedback-state", "repeated_state": "relationship_repeat"},
            )
        ],
    )
    merged = merge_hidden_factor_state(first, second)
    assert merged.status == "amplifier_candidate"
    assert merged.special_event_years == [2021]
    assert merged.repeated_states == ["relationship_repeat"]
    assert merged.feedback_ids == ["feedback-year", "feedback-state"]


def test_hidden_factor_state_denial_reduces_amplifier_claim() -> None:
    runtime = create_smoke_runtime("v30-hidden-state-denied")
    feedback = hidden_factor_feedback_from_payload(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        payload={"feedback_id": "feedback-denied", "confirmed": False},
    )
    state = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=HiddenFactorCalibration.model_validate(
            runtime.question_plan.policy_effect["hidden_factor_calibration"]
        ),
        feedback=[feedback],
    )
    assert state.status == "user_denied"
    assert state.amplifier_candidate is False
    assert state.denied_feedback_ids == ["feedback-denied"]
    assert state.amplifier_strength < 0.42


def test_hidden_factor_state_conflicts_when_denial_follows_candidate() -> None:
    runtime = create_smoke_runtime("v30-hidden-state-conflict")
    calibration = HiddenFactorCalibration.model_validate(
        runtime.question_plan.policy_effect["hidden_factor_calibration"]
    )
    candidate = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=calibration,
        feedback=[
            hidden_factor_feedback_from_payload(
                reading_id=runtime.reading_id,
                context_id=runtime.chart_context.context_id,
                payload={
                    "feedback_id": "feedback-affirmed",
                    "special_event_year": 2022,
                    "repeated_state": "career_pressure_repeat",
                },
            )
        ],
    )
    denial = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=calibration,
        feedback=[
            hidden_factor_feedback_from_payload(
                reading_id=runtime.reading_id,
                context_id=runtime.chart_context.context_id,
                payload={"feedback_id": "feedback-denied", "feedback_status": "denied"},
            )
        ],
    )
    merged = merge_hidden_factor_state(candidate, denial)
    assert merged.status == "conflicting"
    assert merged.amplifier_candidate is False
    assert merged.denied_feedback_ids == ["feedback-denied"]
    assert merged.amplifier_strength <= 0.52


def test_hidden_factor_state_local_json_repository_round_trip(tmp_path: Path) -> None:
    runtime = create_smoke_runtime("v30-hidden-state-store", hidden_factor_user_calibrated=True)
    state = build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=HiddenFactorCalibration.model_validate(
            runtime.question_plan.policy_effect["hidden_factor_calibration"]
        ),
    )
    repository = LocalJsonHiddenFactorStateRepository(_settings(tmp_path))
    repository.save_state(state)
    payload = repository.get_state_payload(state.state_id)
    assert payload is not None
    assert HiddenFactorState.model_validate(payload).state_id == state.state_id


def test_persisted_hidden_factor_state_rehydrates_runtime_question_and_answer() -> None:
    runtime = create_smoke_runtime(
        "v30-hidden-state-rehydrate",
        policy_payload_overrides={
            "question_policy": {
                "weights": {
                    "hidden_factor_event_policy": {
                        "mode": "feedback_conditioned_not_chart_fact",
                        "min_alignment_score": 0.45,
                        "candidate_alignment_multiplier": 1.04,
                        "time_layer_alignment_multiplier": 1.02,
                        "max_positive_multiplier": 1.06,
                        "expired_refresh_multiplier": 1.02,
                        "conflict_multiplier": 0.88,
                        "denial_multiplier": 0.82,
                    }
                }
            }
        },
    )
    state = HiddenFactorState(
        state_id="v30-hidden-state-rehydrate:hidden_factor_state",
        reading_id="v30-hidden-state-rehydrate",
        context_id=runtime.chart_context.context_id,
        status="amplifier_candidate",
        amplifier_strength=0.84,
        amplifier_candidate=True,
        special_event_years=[2024],
        repeated_states=["career_pressure_repeat"],
        alignment_score=0.69,
        feedback_ids=["feedback-001"],
    )
    rehydrated = attach_hidden_factor_state(runtime, state.model_dump(mode="json"))
    graph = rehydrated.question_plan.policy_effect["question_dialogue_graph"]
    hidden_question = next(
        row for row in rehydrated.question_plan.recommended_questions
        if row["topic"] == "hidden_factor"
    )
    assert rehydrated.question_plan.policy_effect["hidden_factor_state"]["status"] == "amplifier_candidate"
    assert "persisted_hidden_factor_state:amplifier_candidate" in hidden_question["reasons"]
    assert any(reason.startswith("hidden_factor_event_alignment:") for reason in hidden_question["reasons"])
    assert "hidden_factor_event_policy:aligned_candidate:0.69" in hidden_question["reasons"]
    assert hidden_question["policy_weight"] > 1.0
    assert "persisted_hidden_factor_state_can_condition_followups" in graph["policy_notes"]
    assert any(note.startswith("hidden_factor_event_alignment:") for note in graph["policy_notes"])
    assert rehydrated.answer_context is not None
    assert rehydrated.answer_context.role_answer_contract["hidden_factor_state"]["amplifier_candidate"] is True


def test_expired_hidden_factor_state_rehydrates_as_refresh_needed() -> None:
    runtime = create_smoke_runtime("v30-hidden-state-expired")
    state = HiddenFactorState(
        state_id="v30-hidden-state-expired:hidden_factor_state",
        reading_id="v30-hidden-state-expired",
        context_id=runtime.chart_context.context_id,
        status="amplifier_candidate",
        amplifier_strength=0.84,
        amplifier_candidate=True,
        special_event_years=[2021],
        repeated_states=["career_pressure_repeat"],
        alignment_score=0.69,
        time_layer_alignment_score=0.9,
        feedback_ids=["feedback-expired"],
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    rehydrated = attach_hidden_factor_state(runtime, state.model_dump(mode="json"))
    graph = rehydrated.question_plan.policy_effect["question_dialogue_graph"]
    hidden_question = next(
        row for row in rehydrated.question_plan.recommended_questions
        if row["topic"] == "hidden_factor"
    )
    payload = rehydrated.question_plan.policy_effect["hidden_factor_state"]
    assert payload["status"] == "expired"
    assert payload["amplifier_candidate"] is False
    assert "persisted_hidden_factor_state:expired_requires_refresh" in hidden_question["reasons"]
    assert "persisted_hidden_factor_state_expired_requires_refresh" in graph["policy_notes"]
    assert "refresh_hidden_factor_feedback" in payload["next_feedback_needed"]


def test_conflicting_hidden_factor_state_gets_policy_downweight() -> None:
    runtime = create_smoke_runtime(
        "v30-hidden-state-conflict-policy",
        policy_payload_overrides={
            "question_policy": {
                "weights": {
                    "hidden_factor_event_policy": {
                        "mode": "feedback_conditioned_not_chart_fact",
                        "min_alignment_score": 0.45,
                        "candidate_alignment_multiplier": 1.06,
                        "time_layer_alignment_multiplier": 1.03,
                        "max_positive_multiplier": 1.06,
                        "expired_refresh_multiplier": 1.02,
                        "conflict_multiplier": 0.86,
                        "denial_multiplier": 0.8,
                    }
                }
            }
        },
    )
    state = HiddenFactorState(
        state_id="v30-hidden-state-conflict-policy:hidden_factor_state",
        reading_id="v30-hidden-state-conflict-policy",
        context_id=runtime.chart_context.context_id,
        status="conflicting",
        amplifier_strength=0.42,
        amplifier_candidate=False,
        special_event_years=[2024],
        repeated_states=["career_pressure_repeat"],
        alignment_score=0.72,
        feedback_ids=["feedback-affirmed"],
        denied_feedback_ids=["feedback-denied"],
    )
    rehydrated = attach_hidden_factor_state(runtime, state.model_dump(mode="json"))
    hidden_question = next(
        row for row in rehydrated.question_plan.recommended_questions
        if row["topic"] == "hidden_factor"
    )
    assert "hidden_factor_event_policy:conflict_priority" in hidden_question["reasons"]
    assert hidden_question["policy_weight"] < 1.0
