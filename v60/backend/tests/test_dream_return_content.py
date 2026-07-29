from __future__ import annotations

from abu_v60.dream.first_slice import FIRST_QUESTION_REF, FIRST_TREE_REF
from abu_v60.dream.return_slice import (
    RETURN_HISTORICAL_EVIDENCE,
    RETURN_QUESTION_OPTIONS,
    RETURN_QUESTION_REF,
    RETURN_RESOLUTION_RULE,
    RETURN_SEALED_FUTURE_OUTCOME,
    RETURN_TREE_REF,
    return_episode_contract,
    return_tree_organs,
)
from abu_v60.experience import ExperienceProjectionComposer


def test_return_question_preserves_real_competition_before_outcome() -> None:
    atom_keys = set(RETURN_RESOLUTION_RULE["compare_atoms"])

    assert len(RETURN_QUESTION_OPTIONS) == 3
    assert all(set(option["proposition"]) == atom_keys for option in RETURN_QUESTION_OPTIONS)
    assert all(
        evidence["epistemic_role"] == "DECISION_BASELINE_NO_CREDIT"
        for evidence in RETURN_HISTORICAL_EVIDENCE
    )
    assert all("atom" not in evidence for evidence in RETURN_HISTORICAL_EVIDENCE)


def test_return_outcome_is_covered_by_committed_future_evidence() -> None:
    outcome = RETURN_SEALED_FUTURE_OUTCOME
    covered_atoms = {key for evidence in outcome["evidence"] for key in evidence["atom"]}

    assert covered_atoms == set(RETURN_RESOLUTION_RULE["compare_atoms"])
    assert set(outcome["resolved_proposition"]) == covered_atoms


def test_return_reuses_actor_tree_identity_with_new_semantic_organs() -> None:
    organs = return_tree_organs("v60-fact-test-structure")
    role_counts = {
        role: sum(organ["role"] == role for organ in organs.values())
        for role in (
            "EVIDENCE_LEAF",
            "STRUCTURE_BRANCH",
            "QUESTION_FLOWER",
            "OUTCOME_FRUIT",
        )
    }

    assert RETURN_TREE_REF == FIRST_TREE_REF
    assert RETURN_QUESTION_REF != FIRST_QUESTION_REF
    assert role_counts == {
        "EVIDENCE_LEAF": 2,
        "STRUCTURE_BRANCH": 1,
        "QUESTION_FLOWER": 1,
        "OUTCOME_FRUIT": 1,
    }
    assert all(organ["organ_ref"].endswith("-v2") for organ in organs.values())


def test_return_runtime_metadata_is_complete_and_has_no_third_visit() -> None:
    metadata = ExperienceProjectionComposer().question_metadata(
        question_ref=RETURN_QUESTION_REF,
        runtime_metadata=return_episode_contract().runtime_metadata.model_dump(mode="json"),
    )

    assert metadata["flower_name"] == "湿岸新芽花"
    assert metadata["fruit_name"] == "湿岸新芽果"
    assert metadata["npc_choice_id"] == "roots_retract"
    assert metadata["return_label"] is None
