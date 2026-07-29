from __future__ import annotations

import inspect
from copy import deepcopy

import pytest
from abu_v60.dream.catalog import DreamEpisodeCatalog, EpisodeCatalogError
from abu_v60.dream.first_slice import (
    FIRST_QUESTION_REF,
    first_episode_contract,
    first_episode_definition,
)
from abu_v60.dream.outcomes import DreamOutcomeCoordinator
from abu_v60.dream.return_slice import (
    RETURN_QUESTION_REF,
    return_episode_contract,
    return_episode_definition,
)
from abu_v60.dream.service import DreamService
from abu_v60.game import (
    DreamEpisodeDefinition,
    DreamGameplayDirector,
    DreamPhase,
    EpisodeContractError,
    EpisodeNarrativeContract,
    life_tree_scene_registry,
    resolution_rule_for_persistence,
)
from abu_v60.provenance import content_hash
from abu_v60.story import (
    EpisodeAdmissionCompiler,
    EpisodeAuthoritySnapshot,
    episode_transition,
    qualification_episode_source_registry,
)
from abu_v60.story.service import LifeStoryEngine, StoryContractError
from pydantic import ValidationError


def _catalog_row(definition: DreamEpisodeDefinition) -> dict[str, object]:
    contract = definition.runtime
    admission = EpisodeAdmissionCompiler().compile(
        definition=definition,
        authority=EpisodeAuthoritySnapshot(
            life_case_revision_ref="v60-life-case-revision-test",
            life_case_revision_hash="a" * 64,
            world_event_ref=contract.world_event_ref,
            outcome_hash=content_hash(definition.sealed_outcome.model_dump(mode="json")),
        ),
    )
    return {
        "question_ref": contract.question_ref,
        "actor_ref": contract.actor_ref,
        "life_case_revision_ref": admission.life_case_revision_ref,
        "life_case_revision_hash": "a" * 64,
        "tree_ref": contract.tree_ref,
        "world_event_ref": contract.world_event_ref,
        "cutoff_tick": contract.cutoff_tick,
        "due_tick": contract.due_tick,
        "resolution_rule_json": admission.resolution_rule,
        "episode_ref": contract.episode_ref,
        "episode_version": contract.episode_version,
        "episode_contract_json": admission.episode_contract,
        "episode_contract_hash": admission.episode_contract_hash,
        "question_hash": admission.question_hash,
        "organ_set_hash": admission.organ_set_hash,
        "evidence_refs_json": list(admission.evidence_refs),
        "outcome_hash": admission.admission_manifest.outcome_hash,
        "admission_manifest_json": admission.admission_manifest.model_dump(mode="json"),
        "admission_manifest_hash": admission.admission_manifest_hash,
    }


def _catalog_rows() -> list[dict[str, object]]:
    return [
        _catalog_row(first_episode_definition("v60-fact-structure-test")),
        _catalog_row(return_episode_definition("v60-fact-structure-test")),
    ]


def _transition_row(
    source: str,
    target: str,
    label: str,
) -> dict[str, object]:
    transition = episode_transition(
        from_question_ref=source,
        to_question_ref=target,
        label=label,
    )
    payload = transition.model_dump(mode="json")
    return {
        **payload,
        "transition_json": payload,
        "transition_hash": content_hash(payload),
    }


def _catalog_transition_rows() -> list[dict[str, object]]:
    return [
        _transition_row(
            FIRST_QUESTION_REF,
            RETURN_QUESTION_REF,
            "过一段时间，再回到这棵树",
        )
    ]


def _refresh_admission_manifest(row: dict[str, object]) -> None:
    contract = dict(row["episode_contract_json"])
    manifest = dict(row["admission_manifest_json"])
    manifest.update(
        {
            "question_ref": row["question_ref"],
            "episode_ref": contract["episode_ref"],
            "episode_version": contract["episode_version"],
            "actor_ref": contract["actor_ref"],
            "tree_ref": contract["tree_ref"],
            "world_event_ref": contract["world_event_ref"],
            "question_hash": row["question_hash"],
            "organ_set_hash": row["organ_set_hash"],
            "resolution_rule_hash": contract["resolution_rule_hash"],
            "episode_contract_hash": row["episode_contract_hash"],
        }
    )
    row["admission_manifest_json"] = manifest
    row["admission_manifest_hash"] = content_hash(manifest)


def test_authored_episodes_are_complete_and_form_one_continuation_graph() -> None:
    first = first_episode_definition("v60-fact-structure-test")
    returning = return_episode_definition("v60-fact-structure-test")

    assert first.runtime.continuation_question_ref == RETURN_QUESTION_REF
    assert returning.runtime.continuation_question_ref is None
    assert first.runtime.question_ref == FIRST_QUESTION_REF
    assert first.runtime.entrypoint is True
    assert returning.runtime.entrypoint is False
    assert returning.runtime.entry_world_event is not None

    for episode in (first, returning):
        assert episode.runtime.episode_version == 3
        assert {moment.phase for moment in episode.runtime.narrative.moments} == set(DreamPhase)
        roles = [organ.role.value for organ in episode.organ_set.values()]
        assert roles.count("EVIDENCE_LEAF") == 2
        assert roles.count("STRUCTURE_BRANCH") == 1
        assert roles.count("QUESTION_FLOWER") == 1
        assert roles.count("OUTCOME_FRUIT") == 1


def test_episode_narratives_are_distinct_and_phase_disclosure_is_complete() -> None:
    first = first_episode_contract()
    returning = return_episode_contract()

    assert (
        first.narrative.for_phase(DreamPhase.OBSERVING).abu_line
        != returning.narrative.for_phase(DreamPhase.OBSERVING).abu_line
    )
    assert (
        first.narrative.for_phase(DreamPhase.REVEAL_READY).disclosure.value
        == "WORLD_COMMITTED_HIDDEN"
    )
    assert first.narrative.for_phase(DreamPhase.REVEALED).disclosure.value == "OUTCOME_REVEALED"


def test_episode_narrative_rejects_phase_disclosure_drift() -> None:
    payload = first_episode_contract().narrative.model_dump(mode="json")
    payload["moments"][0]["disclosure"] = "OUTCOME_REVEALED"

    with pytest.raises(ValidationError, match="phase_disclosure_mismatch"):
        EpisodeNarrativeContract.model_validate(payload)


def test_episode_package_rejects_authored_future_leak_before_reveal() -> None:
    payload = first_episode_definition("v60-fact-structure-test").model_dump(mode="json")
    payload["runtime"]["narrative"]["moments"][2]["theater_beat"] = payload["sealed_outcome"][
        "actual_event"
    ]

    with pytest.raises(ValidationError, match="narrative_leaks_future_outcome"):
        DreamEpisodeDefinition.model_validate(payload)


def test_episode_package_fails_when_one_evidence_leaf_is_deleted() -> None:
    payload = first_episode_definition("v60-fact-structure-test").model_dump(mode="json")
    payload["organ_set"].pop("evidence_leaf_structure")

    with pytest.raises(ValidationError, match="two_leaves"):
        DreamEpisodeDefinition.model_validate(payload)


def test_episode_package_rejects_future_evidence_in_decision_baseline() -> None:
    payload = first_episode_definition("v60-fact-structure-test").model_dump(mode="json")
    payload["baseline_evidence"][0]["atom"] = {"root_support": "limited"}

    with pytest.raises(ValidationError, match="baseline_evidence"):
        DreamEpisodeDefinition.model_validate(payload)


def test_director_rejects_tampered_persisted_contract() -> None:
    director = DreamGameplayDirector()
    contract = first_episode_contract()
    payload = contract.model_dump(mode="json")
    contract_hash = content_hash(payload)

    loaded = director.load_episode(
        payload=payload,
        expected_hash=contract_hash,
        question_ref=FIRST_QUESTION_REF,
    )
    assert loaded == contract

    payload["due_tick"] = 99
    with pytest.raises(EpisodeContractError, match="hash_mismatch"):
        director.load_episode(
            payload=payload,
            expected_hash=contract_hash,
            question_ref=FIRST_QUESTION_REF,
        )


def test_director_projects_commands_without_owning_content() -> None:
    definition = first_episode_definition("v60-fact-structure-test")
    director = DreamGameplayDirector()
    scene = director.scene(
        episode=definition.runtime,
        state={
            "observed_organs": [],
            "question_visible": False,
            "answer_sealed": False,
            "world_settled": False,
            "revealed": False,
            "reconciled": False,
        },
        organs=definition.model_dump(mode="json")["organ_set"],
        encounter_completed=False,
    )

    assert scene.episode_ref == definition.runtime.episode_ref
    assert scene.gameplay_id == "life_tree_question_v1"
    assert scene.scene_id == "v60.scene.life-tree.observing"
    assert scene.scene_version == 1
    assert scene.layout_key == "picture_book_fixed_tree"
    assert [command.value for command in scene.available_commands] == ["OBSERVE_EVIDENCE"]


def test_catalog_validates_the_complete_active_episode_graph() -> None:
    catalog = DreamEpisodeCatalog().from_rows(
        _catalog_rows(),
        transition_rows=_catalog_transition_rows(),
    )

    assert catalog.entry == first_episode_contract()
    assert catalog.for_question(RETURN_QUESTION_REF) == return_episode_contract()
    assert catalog.public_summary()["ordered_episode_refs"] == [
        first_episode_contract().episode_ref,
        return_episode_contract().episode_ref,
    ]
    assert len(catalog.graph_hash) == 64
    assert catalog.tree_entry_version(FIRST_QUESTION_REF) == 1
    assert catalog.tree_settlement_version(FIRST_QUESTION_REF) == 2
    assert catalog.tree_entry_version(RETURN_QUESTION_REF) == 3
    assert catalog.tree_settlement_version(RETURN_QUESTION_REF) == 4
    assert catalog.public_summary()["active_transition_count"] == 1


def test_catalog_accepts_three_independent_qualification_roots() -> None:
    registry = qualification_episode_source_registry()
    qualification_definitions = (
        registry.compile_definition(
            "v60.episode-package.wenxi-archive-trial.v1",
            bindings={
                "career_structure_fact_ref": "fact:career",
                "career_life_domain_vector_ref": "domain:career",
            },
        ),
        registry.compile_definition(
            "v60.episode-package.heyang-dyed-cloth.v1",
            bindings={
                "wealth_structure_fact_ref": "fact:wealth",
                "wealth_life_domain_vector_ref": "domain:wealth",
            },
        ),
        registry.compile_definition(
            "v60.episode-package.zhaoning-lantern-roster.v1",
            bindings={
                "relationship_structure_fact_ref": "fact:relationship",
                "relationship_life_domain_vector_ref": "domain:relationship",
            },
        ),
    )
    catalog = DreamEpisodeCatalog().from_rows(
        [
            *_catalog_rows(),
            *(_catalog_row(definition) for definition in qualification_definitions),
        ],
        transition_rows=_catalog_transition_rows(),
    )

    assert catalog.entry.question_ref == FIRST_QUESTION_REF
    assert len(catalog.entry_episode_refs) == 4
    for definition in qualification_definitions:
        assert catalog.tree_entry_version(definition.runtime.question_ref) == 1
        assert catalog.tree_settlement_version(definition.runtime.question_ref) == 2
        assert catalog.next_episode(definition.runtime.question_ref) is None


def test_catalog_can_append_a_third_episode_without_mutating_the_second() -> None:
    rows = _catalog_rows()
    third = deepcopy(rows[1])
    third_question_ref = "v60-question-yanzhou-third-v1"
    third_episode_ref = "v60-dream-episode-yanzhou-third-v1"
    third_baseline_ref = "v60-world-event-yanzhou-third-baseline-v1"
    third_outcome_ref = "v60-world-event-yanzhou-third-outcome-v1"
    contract = deepcopy(third["episode_contract_json"])
    assert contract["continuation_question_ref"] is None
    contract.update(
        {
            "episode_ref": third_episode_ref,
            "episode_version": 1,
            "content_key": "dream.yanzhou.third",
            "question_ref": third_question_ref,
            "baseline_event_ref": third_baseline_ref,
            "world_event_ref": third_outcome_ref,
            "cutoff_tick": 24,
            "due_tick": 36,
            "runtime_metadata": {
                **contract["runtime_metadata"],
                "baseline_event_ref": third_baseline_ref,
            },
            "entry_world_event": {
                **contract["entry_world_event"],
                "event_ref": third_baseline_ref,
                "caused_by_event_ref": rows[1]["world_event_ref"],
            },
            "tree_state_on_entry": "THIRD_BASELINE_COMMITTED",
            "tree_state_after_settlement": "THIRD_FRUIT_MATURED",
        }
    )
    for moment in contract["narrative"]["moments"]:
        moment["content_key"] = (
            f"dream.yanzhou.third.{str(moment['phase']).lower().replace('_', '-')}"
        )
    third.update(
        {
            "question_ref": third_question_ref,
            "world_event_ref": third_outcome_ref,
            "cutoff_tick": 24,
            "due_tick": 36,
            "episode_ref": third_episode_ref,
            "episode_version": 1,
            "episode_contract_json": contract,
            "episode_contract_hash": content_hash(contract),
            "question_hash": content_hash({"question_ref": third_question_ref}),
        }
    )
    _refresh_admission_manifest(third)
    rows.append(third)
    transitions = [
        *_catalog_transition_rows(),
        _transition_row(
            RETURN_QUESTION_REF,
            third_question_ref,
            "再回来看看新长出的枝路",
        ),
    ]

    catalog = DreamEpisodeCatalog().from_rows(
        rows,
        transition_rows=transitions,
    )

    assert rows[1]["episode_contract_json"]["continuation_question_ref"] is None
    assert catalog.next_episode(RETURN_QUESTION_REF) == (
        catalog.for_question(third_question_ref),
        "再回来看看新长出的枝路",
    )
    assert catalog.tree_entry_version(third_question_ref) == 5
    assert catalog.tree_settlement_version(third_question_ref) == 6


def test_dream_service_does_not_encode_authored_tree_state_names() -> None:
    source = inspect.getsource(DreamService) + inspect.getsource(DreamOutcomeCoordinator)

    for authored_state in (
        "DORMANT_QUESTION",
        "FIRST_FRUIT_MATURED",
        "RETURN_BASELINE_COMMITTED",
        "RETURN_FRUIT_MATURED",
    ):
        assert authored_state not in source
    assert "catalog.tree_entry_version" in source
    assert "catalog.tree_settlement_version" in source


def test_catalog_fails_closed_when_continuation_is_missing() -> None:
    rows = _catalog_rows()

    with pytest.raises(EpisodeCatalogError, match="transition_endpoint_inactive"):
        DreamEpisodeCatalog().from_rows(
            rows,
            transition_rows=[
                _transition_row(
                    FIRST_QUESTION_REF,
                    "v60-question-missing",
                    "找不到的下一章",
                )
            ],
        )


def test_catalog_fails_closed_when_active_episode_is_unreachable() -> None:
    rows = _catalog_rows()
    definition = return_episode_definition("v60-fact-structure-test")
    payload = definition.runtime.model_dump(mode="json")
    payload.update(
        {
            "episode_ref": "v60-dream-episode-unreachable-v1",
            "question_ref": "v60-question-unreachable-v1",
            "content_key": "dream.unreachable",
            "baseline_event_ref": "v60-world-event-unreachable-baseline-v1",
            "world_event_ref": "v60-world-event-unreachable-outcome-v1",
            "resolution_rule_hash": content_hash(
                resolution_rule_for_persistence(
                    {
                        **definition.resolution_rule.model_dump(mode="json"),
                        "baseline_event_ref": "v60-world-event-unreachable-baseline-v1",
                    }
                )
            ),
            "runtime_metadata": {
                **payload["runtime_metadata"],
                "baseline_event_ref": "v60-world-event-unreachable-baseline-v1",
            },
            "entry_world_event": {
                **payload["entry_world_event"],
                "event_ref": "v60-world-event-unreachable-baseline-v1",
            },
        }
    )
    row = _catalog_row(definition)
    row.update(
        {
            "question_ref": payload["question_ref"],
            "episode_ref": payload["episode_ref"],
            "world_event_ref": payload["world_event_ref"],
            "episode_contract_json": payload,
            "episode_contract_hash": content_hash(payload),
        }
    )
    _refresh_admission_manifest(row)
    rows.append(row)

    with pytest.raises(EpisodeCatalogError, match="parent_mismatch"):
        DreamEpisodeCatalog().from_rows(
            rows,
            transition_rows=_catalog_transition_rows(),
        )


def test_catalog_rejects_tampered_admission_manifest() -> None:
    rows = _catalog_rows()
    rows[0]["admission_manifest_hash"] = "0" * 64

    with pytest.raises(EpisodeCatalogError, match="admission_manifest_hash"):
        DreamEpisodeCatalog().from_rows(
            rows,
            transition_rows=_catalog_transition_rows(),
        )


def test_scene_registry_has_one_versioned_scene_for_every_phase() -> None:
    registry = life_tree_scene_registry()
    manifest = registry.public_manifest()

    assert {item["phase"] for item in manifest} == {phase.value for phase in DreamPhase}
    assert len({item["scene_id"] for item in manifest}) == len(DreamPhase)


def test_story_engine_does_not_import_dream_content() -> None:
    source = inspect.getsource(inspect.getmodule(LifeStoryEngine))
    assert "abu_v60.dream" not in source


def test_dream_service_has_no_authored_question_branching() -> None:
    source = inspect.getsource(inspect.getmodule(DreamService))
    assert "FIRST_QUESTION_REF" not in source
    assert "RETURN_QUESTION_REF" not in source
    assert "dream.first_slice" not in source
    assert "dream.return_slice" not in source


def test_story_metadata_fails_closed_without_persisted_contract() -> None:
    with pytest.raises(StoryContractError, match="metadata_incomplete"):
        LifeStoryEngine().episode_runtime_metadata(
            question_ref="v60-question-uncontracted",
            runtime_metadata=None,
        )
