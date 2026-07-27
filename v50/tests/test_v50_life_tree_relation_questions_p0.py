from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
import pytest

from experience.life_tree_questions import select_life_tree_questions
from experience.relation_work_projection import (
    compile_shared_relation_work_projection,
    project_relation_work_for_consumer,
)
from product.app import create_product_app
from product.life_tree_question_blueprints import (
    load_relation_lab_question_blueprints,
)
from product.relation_work_p0_fixture import build_p0_relation_work_fixture
from product.relation_work_p0_service import (
    RelationWorkP0Conflict,
    RelationWorkP0FeaturePolicy,
    RelationWorkP0Service,
)


NOW = datetime(2026, 7, 27, tzinfo=timezone.utc)


def test_twenty_five_versioned_blueprints_cover_all_required_question_kinds() -> None:
    blueprints = load_relation_lab_question_blueprints()

    assert len(blueprints) == 25
    assert len({item.blueprint_id for item in blueprints}) == 25
    assert {item.category for item in blueprints} == {
        "factual_observation",
        "candidate_comparison",
        "discriminating",
        "temporal_change",
        "counterfactual",
    }
    assert all(len(item.options) in {2, 3, 4} for item in blueprints)
    assert all(item.relevance_reason for item in blueprints)
    assert all(item.distinguishes for item in blueprints)
    assert all(item.provenance_refs for item in blueprints)
    assert all(item.writes_life_case is False for item in blueprints)
    assert all(item.upgrades_relation_effect is False for item in blueprints)
    assert all(item.upgrades_work_path is False for item in blueprints)
    assert all(item.declares_main_work is False for item in blueprints)


def test_question_selection_is_bound_to_current_tree_evidence() -> None:
    fixture = build_p0_relation_work_fixture()
    blueprints = load_relation_lab_question_blueprints()
    full = project_relation_work_for_consumer(
        fixture.projection,
        audience="dream",
    )
    without_clash_projection = compile_shared_relation_work_projection(
        relation_facts=list(fixture.relation_facts[:-1]),
        work_path_candidates=list(fixture.work_path_candidates),
        effect_resolutions=[],
    )
    without_clash = project_relation_work_for_consumer(
        without_clash_projection,
        audience="dream",
    )

    full_questions = select_life_tree_questions(
        projection=full,
        blueprints=blueprints,
    )
    reduced_questions = select_life_tree_questions(
        projection=without_clash,
        blueprints=blueprints,
    )

    assert len(full_questions) == 25
    assert len(reduced_questions) < len(full_questions)
    reduced_ids = {item.blueprint_id for item in reduced_questions}
    assert {"LT-F03", "LT-D05", "LT-T02", "LT-X04"}.isdisjoint(reduced_ids)
    assert all(
        item.source_foundation_ref == full.foundation_ref
        for item in full_questions
    )
    assert all(
        item.relation_fact_revision_refs or item.work_path_candidate_refs
        for item in full_questions
    )


def test_client_question_projection_contains_no_answer_or_truth_upgrade_field() -> None:
    service = RelationWorkP0Service(
        feature_policy=RelationWorkP0FeaturePolicy(enabled=True)
    )
    payload = service.bootstrap(participant_run_id="run-safe-projection")
    encoded = str(payload)

    assert "correct_option" not in encoded
    assert "correctOption" not in encoded
    assert "answer_key" not in encoded
    assert payload["write_boundary"] == {
        "owner": "TopicExploration",
        "writes_life_case": False,
        "upgrades_relation_effect": False,
        "upgrades_work_path": False,
        "declares_main_work": False,
    }


def test_answer_is_idempotent_topic_exploration_and_conflict_is_rejected() -> None:
    service = RelationWorkP0Service(
        feature_policy=RelationWorkP0FeaturePolicy(enabled=True)
    )
    question = service.questions[0]
    selected = question.options[0].option_id
    before_hash = service.fixture.projection.content_hash

    first = service.answer(
        participant_run_id="run-exploration",
        question_instance_id=question.instance_id,
        selected_option_id=selected,
        now=NOW,
    )
    repeated = service.answer(
        participant_run_id="run-exploration",
        question_instance_id=question.instance_id,
        selected_option_id=selected,
        now=NOW,
    )

    assert first == repeated
    assert first.writes_life_case is False
    assert first.responses == {question.instance_id: selected}
    assert service.fixture.projection.content_hash == before_hash
    with pytest.raises(
        RelationWorkP0Conflict,
        match="life_tree_question_answer_already_recorded",
    ):
        service.answer(
            participant_run_id="run-exploration",
            question_instance_id=question.instance_id,
            selected_option_id=question.options[1].option_id,
            now=NOW,
        )


def test_local_vertical_slice_restores_exploration_from_server_store() -> None:
    service = RelationWorkP0Service(
        feature_policy=RelationWorkP0FeaturePolicy(enabled=True)
    )
    client = TestClient(create_product_app(relation_work_p0_service=service))
    page = client.get("/experience/relation-work-p0")
    before = client.get(
        "/api/v50/relation-work-p0/bootstrap",
        params={"participant_run_id": "run-http"},
    )
    question = before.json()["questions"][0]
    answer = client.post(
        f"/api/v50/relation-work-p0/questions/{question['instance_id']}/answer",
        json={
            "participant_run_id": "run-http",
            "selected_option_id": question["options"][0]["option_id"],
        },
    )
    restored = client.get(
        "/api/v50/relation-work-p0/bootstrap",
        params={"participant_run_id": "run-http"},
    )

    assert page.status_code == 200
    assert answer.status_code == 200
    assert answer.json()["exploration"]["writes_life_case"] is False
    assert len(restored.json()["explorations"]) == 1
    assert restored.json()["foundation_hash"] == before.json()["foundation_hash"]


def test_feature_flag_defaults_to_closed() -> None:
    service = RelationWorkP0Service(
        feature_policy=RelationWorkP0FeaturePolicy(enabled=False)
    )
    client = TestClient(create_product_app(relation_work_p0_service=service))

    assert client.get("/experience/relation-work-p0").status_code == 404
    assert client.get(
        "/api/v50/relation-work-p0/bootstrap",
        params={"participant_run_id": "run-disabled"},
    ).status_code == 404
