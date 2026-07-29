from pathlib import Path

import pytest
from abu_v60.game import (
    DreamCommand,
    DreamCommandEnvelope,
    DreamGameEngine,
    DreamPhase,
    GameRuleError,
)
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _organs() -> dict[str, dict[str, str]]:
    return {
        "evidence_leaf_world": {"organ_ref": "leaf:world"},
        "evidence_leaf_structure": {"organ_ref": "leaf:structure"},
        "structure_branch": {"organ_ref": "branch:structure"},
        "question_flower": {"organ_ref": "flower:question"},
        "outcome_fruit": {"organ_ref": "fruit:outcome"},
    }


def _state(**updates: object) -> dict[str, object]:
    state: dict[str, object] = {
        "observed_organs": [],
        "question_visible": False,
        "answer_sealed": False,
        "world_settled": False,
        "revealed": False,
        "reconciled": False,
    }
    state.update(updates)
    return state


def test_game_engine_enforces_two_leaves_branch_and_flower_order() -> None:
    engine = DreamGameEngine()
    organs = _organs()
    with pytest.raises(GameRuleError, match="both_evidence_leaves_required"):
        engine.observe(state=_state(), organ_key="structure_branch", organs=organs)

    first = engine.observe(
        state=_state(),
        organ_key="evidence_leaf_world",
        organs=organs,
    )
    second = engine.observe(
        state=first.progress.as_state_json(),
        organ_key="evidence_leaf_structure",
        organs=organs,
    )
    branch = engine.observe(
        state=second.progress.as_state_json(),
        organ_key="structure_branch",
        organs=organs,
    )
    flower = engine.observe(
        state=branch.progress.as_state_json(),
        organ_key="question_flower",
        organs=organs,
    )
    assert flower.phase is DreamPhase.QUESTION_OPEN
    assert flower.progress.question_visible is True


def test_game_engine_exposes_only_current_legal_commands() -> None:
    engine = DreamGameEngine()
    organs = _organs()
    assert engine.available_commands(state=_state(), organs=organs) == (
        DreamCommand.OBSERVE_EVIDENCE,
    )
    assert engine.available_commands(
        state=_state(question_visible=True),
        organs=organs,
    ) == (DreamCommand.SEAL_ANSWER,)
    assert engine.available_commands(
        state=_state(answer_sealed=True),
        organs=organs,
    ) == ()
    assert engine.available_commands(
        state=_state(world_settled=True),
        organs=organs,
    ) == (DreamCommand.REVEAL,)


def test_public_organ_projection_is_derived_not_stored() -> None:
    engine = DreamGameEngine()
    organs = _organs()
    visible = engine.public_organs(organs=organs, state=_state())
    assert [item["key"] for item in visible if item["visible"]] == [
        "evidence_leaf_world",
        "evidence_leaf_structure",
    ]
    sealed = engine.public_organs(
        organs=organs,
        state=_state(
            observed_organs=["leaf:world", "leaf:structure", "branch:structure"],
            question_visible=True,
            answer_sealed=True,
        ),
    )
    assert next(item for item in sealed if item["key"] == "outcome_fruit")["status"] == "SEALED"


def test_command_envelope_requires_exact_payload_for_each_command() -> None:
    envelope = DreamCommandEnvelope(
        command=DreamCommand.OBSERVE_EVIDENCE,
        encounter_ref="encounter:1",
        expected_version=1,
        idempotency_key="encounter:1:v1:leaf:1",
        target_ref="leaf:1",
    )
    assert envelope.target_ref == "leaf:1"

    with pytest.raises(ValidationError, match="organ_command_requires_only_target_ref"):
        DreamCommandEnvelope(
            command=DreamCommand.OBSERVE_EVIDENCE,
            encounter_ref="encounter:1",
            expected_version=1,
            idempotency_key="invalid",
        )
    with pytest.raises(ValidationError, match="seal_answer_requires_only_choice_id"):
        DreamCommandEnvelope(
            command=DreamCommand.SEAL_ANSWER,
            encounter_ref="encounter:1",
            expected_version=1,
            idempotency_key="invalid",
            target_ref="leaf:1",
        )
    with pytest.raises(ValidationError, match="Input should be"):
        DreamCommandEnvelope(
            command="ADVANCE_WORLD",
            encounter_ref="encounter:1",
            expected_version=1,
            idempotency_key="invalid-world-control",
        )


def test_game_engine_rejects_command_target_mismatch_and_stale_phase() -> None:
    engine = DreamGameEngine()
    organs = _organs()

    with pytest.raises(GameRuleError, match="dream_command_target_mismatch"):
        engine.assert_command_available(
            command=DreamCommand.OBSERVE_EVIDENCE,
            state=_state(),
            organs=organs,
            organ_key="structure_branch",
        )
    with pytest.raises(GameRuleError, match="dream_command_not_available"):
        engine.assert_command_available(
            command=DreamCommand.REVEAL,
            state=_state(),
            organs=organs,
        )


def test_browser_audits_follow_world_owned_waiting_and_public_projection() -> None:
    tools = PROJECT_ROOT / "web" / "tools"
    first_slice = (tools / "first-slice-audit.mjs").read_text(encoding="utf-8")
    return_slice = (tools / "return-slice-audit.mjs").read_text(encoding="utf-8")

    assert "让世界继续" not in first_slice
    assert "ADVANCE_WORLD" not in first_slice
    assert "收下这次复盘" in first_slice
    assert 'locator(".candidate-path")' in first_slice
    assert ".tree.tree_version" not in return_slice
    assert ".tree.projection_version" in return_slice


def test_life_tree_scene_has_no_authored_episode_copy_branch() -> None:
    source = (PROJECT_ROOT / "web" / "src" / "LifeTreeScene.tsx").read_text(
        encoding="utf-8"
    )

    assert "returnVisit" not in source
    assert "FIRST_VISIT" not in source
    assert "RETURN_VISIT" not in source
    assert "湿岸的新细根" not in source
    assert "旧水渠" not in source
    assert "narrative.journey_title" in source
    assert "narrative.journey_status" in source
