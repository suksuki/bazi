from __future__ import annotations

from abu_v60.dream.first_slice import (
    FIRST_QUESTION_REF,
    first_episode_contract,
    first_tree_organs,
)
from abu_v60.dream.return_slice import (
    RETURN_QUESTION_REF,
    return_episode_contract,
    return_tree_organs,
)
from abu_v60.provenance import content_hash


def test_question_versions_have_disjoint_immutable_organ_projections() -> None:
    structure_ref = "v60-fact-test-structure"
    first = first_tree_organs(structure_ref)
    returning = return_tree_organs(structure_ref)

    first_refs = {organ["organ_ref"] for organ in first.values()}
    return_refs = {organ["organ_ref"] for organ in returning.values()}

    assert first_refs.isdisjoint(return_refs)
    assert content_hash(first) != content_hash(returning)
    assert first["question_flower"]["source_refs"] == [FIRST_QUESTION_REF]
    assert returning["question_flower"]["source_refs"] == [RETURN_QUESTION_REF]


def test_each_structure_branch_depends_on_both_evidence_leaves() -> None:
    for organs in (
        first_tree_organs("v60-fact-test-structure"),
        return_tree_organs("v60-fact-test-structure"),
    ):
        leaf_sources = {
            source_ref
            for key in ("evidence_leaf_world", "evidence_leaf_structure")
            for source_ref in organs[key]["source_refs"]
        }

        assert set(organs["structure_branch"]["source_refs"]) == leaf_sources


def test_canonical_tree_settlement_state_is_owned_by_episode_contract() -> None:
    assert (
        first_episode_contract().tree_state_after_settlement
        == "FIRST_FRUIT_MATURED"
    )
    assert (
        return_episode_contract().tree_state_after_settlement
        == "RETURN_FRUIT_MATURED"
    )
