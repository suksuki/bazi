from __future__ import annotations

from copy import deepcopy
import json

from fastapi.testclient import TestClient

from experience.store import MemoryTheaterStore
from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.product_store import MemoryProductStore
from product.relation_work_p0_service import (
    RelationWorkP0FeaturePolicy,
    RelationWorkP0Service,
)
from test_v50_read_only_canvas_c1 import _typed_real_case


def _client_with_two_cases(*, p0_enabled: bool = True):
    product_store = MemoryProductStore()
    case_store = MemoryAgentCaseStore()
    theater_store = MemoryTheaterStore()
    service = RelationWorkP0Service(
        feature_policy=RelationWorkP0FeaturePolicy(
            enabled=p0_enabled,
            canonical_enabled=True,
        ),
        case_store=case_store,
        theater_store=theater_store,
    )
    client = TestClient(
        create_product_app(
            product_store=product_store,
            agent_case_store=case_store,
            relation_work_p0_service=service,
        )
    )
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "P1 Owner",
            "email": "relation-work-p1@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    user_id = registered.json()["account"]["user_id"]
    first, _ = _typed_real_case("case-real-p1-a")
    second, _ = _typed_real_case("case-real-p1-b")
    second = deepcopy(second)
    for key, value in {
        "year_pillar": "甲子",
        "month_pillar": "丙寅",
        "day_pillar": "戊午",
        "hour_pillar": "庚申",
    }.items():
        second["birth_input"][key] = value
    case_store.save(
        case_id="case-real-p1-a",
        user_id=user_id,
        profile_id="profile-real-p1-a",
        payload=first,
    )
    case_store.save(
        case_id="case-real-p1-b",
        user_id=user_id,
        profile_id="profile-real-p1-b",
        payload=second,
    )
    return client, theater_store


def test_canonical_experience_does_not_load_or_require_p0_fixture() -> None:
    client, _ = _client_with_two_cases(p0_enabled=False)

    assert client.app.state.relation_work_p0_service.fixture is None
    assert client.get("/experience/relation-work-p0").status_code == 404
    response = client.get(
        "/api/v50/experience/cases/case-real-p1-a/life-tree/questions"
    )
    assert response.status_code == 200
    assert response.json()["data_source"] == "CURRENT_REAL_LIFECASE"


def test_switching_real_cases_changes_tree_and_lab_from_same_source() -> None:
    client, _ = _client_with_two_cases()

    tree_a = client.get(
        "/api/v50/relation-work-p0/cases/case-real-p1-a/bootstrap"
    ).json()
    tree_b = client.get(
        "/api/v50/relation-work-p0/cases/case-real-p1-b/bootstrap"
    ).json()
    lab_a = client.get(
        "/api/v50/relation-work-p0/cases/case-real-p1-a/lab/bootstrap"
    ).json()
    lab_b = client.get(
        "/api/v50/relation-work-p0/cases/case-real-p1-b/lab/bootstrap"
    ).json()

    assert tree_a["data_source"] == "CURRENT_REAL_LIFECASE"
    assert tree_a["foundation_hash"] != tree_b["foundation_hash"]
    assert tree_a["source"] == lab_a["relation_work"]["source"]
    assert tree_b["source"] == lab_b["relation_work"]["source"]
    assert tree_a["foundation_hash"] == lab_a["relation_work"]["foundation_content_hash"]
    assert tree_b["foundation_hash"] == lab_b["relation_work"]["foundation_content_hash"]
    assert tree_a == client.get(
        "/api/v50/relation-work-p0/cases/case-real-p1-a/bootstrap"
    ).json()
    assert tree_a["canonical_timing"] == lab_a["canonical_timing"]
    assert tree_a["tree_visual_profile"]["source"] == (
        "SERVER_DERIVED_CURRENT_LIFECASE_GRAPH"
    )
    assert tree_a["tree_visual_profile"]["profile_id"] != (
        tree_b["tree_visual_profile"]["profile_id"]
    )
    assert tree_a["tree_visual_profile"]["form"] == "tall_tensed"
    assert tree_b["tree_visual_profile"]["form"] == "wide_balanced"
    assert tree_a["tree_visual_profile"]["material"] == "sun_warmed"
    assert tree_b["tree_visual_profile"]["material"] == "dew_fed"
    assert (
        tree_a["tree_visual_profile"]["render_tokens"]["hue_rotate_deg"]
        != tree_b["tree_visual_profile"]["render_tokens"]["hue_rotate_deg"]
    )


def test_canonical_experience_routes_own_tree_and_lab_integration() -> None:
    client, theater_store = _client_with_two_cases()
    tree_url = (
        "/api/v50/experience/cases/case-real-p1-a/life-tree/questions"
    )
    lab_url = (
        "/api/v50/experience/cases/case-real-p1-a/"
        "mingli-lab/relation-work"
    )
    tree = client.get(tree_url)
    lab = client.get(lab_url)

    assert tree.status_code == 200
    assert lab.status_code == 200
    assert tree.json()["data_source"] == "CURRENT_REAL_LIFECASE"
    assert lab.json()["data_source"] == "CURRENT_REAL_LIFECASE"
    assert tree.json()["source"] == lab.json()["relation_work"]["source"]
    assert tree.json()["question_count"] == 1
    assert tree.json()["questions"][0]["blueprint_id"] == (
        "LQ-REAL-OUTPUT-DESTINATION-01"
    )
    assert all(
        item["purpose"] == "life_observation"
        and item["reveal_policy"] == "REALITY_FEEDBACK"
        and item["baseline_credit_allowed"] is False
        for item in tree.json()["questions"]
    )
    assert all(
        item["purpose"] == "lab_learning"
        for item in lab.json()["learning_questions"]
    )
    assert {
        item["blueprint_id"] for item in tree.json()["questions"]
    }.isdisjoint(
        item["blueprint_id"] for item in lab.json()["learning_questions"]
    )

    question = tree.json()["questions"][0]
    answer = client.post(
        f"{tree_url}/{question['instance_id']}/answer",
        json={"selected_option_id": question["options"][0]["option_id"]},
    )
    assert answer.status_code == 200
    assert len(
        theater_store.list_explorations(
            tree.json()["participant_run_id"]
        )
    ) == 1
    assert client.get(tree_url).json()["tree_scene"]["nodes"]


def test_real_case_answer_is_server_bound_persistent_and_conflict_safe() -> None:
    client, theater_store = _client_with_two_cases()
    bootstrap = client.get(
        "/api/v50/relation-work-p0/cases/case-real-p1-a/bootstrap"
    ).json()
    question = bootstrap["questions"][0]
    selected = question["options"][0]["option_id"]

    answer = client.post(
        "/api/v50/relation-work-p0/cases/case-real-p1-a/"
        f"questions/{question['instance_id']}/answer",
        json={"selected_option_id": selected},
    )
    assert answer.status_code == 200
    assert answer.json()["write_boundary"]["writes_life_case"] is False
    assert len(
        theater_store.list_explorations(bootstrap["participant_run_id"])
    ) == 1

    reloaded = client.get(
        "/api/v50/relation-work-p0/cases/case-real-p1-a/bootstrap"
    ).json()
    assert reloaded["explorations"][0]["responses"] == {
        question["instance_id"]: selected
    }
    repeated = client.post(
        "/api/v50/relation-work-p0/cases/case-real-p1-a/"
        f"questions/{question['instance_id']}/answer",
        json={"selected_option_id": selected},
    )
    assert repeated.status_code == 200
    conflict = client.post(
        "/api/v50/relation-work-p0/cases/case-real-p1-a/"
        f"questions/{question['instance_id']}/answer",
        json={"selected_option_id": question["options"][1]["option_id"]},
    )
    assert conflict.status_code == 409


def test_real_case_projection_does_not_disclose_answer_or_upgrade_authority() -> None:
    client, _ = _client_with_two_cases()
    response = client.get(
        "/api/v50/relation-work-p0/cases/case-real-p1-a/bootstrap"
    )
    assert response.status_code == 200
    serialized = response.text.lower()
    for forbidden in (
        "correct_answer",
        "answer_key",
        "professional_rank\": 1",
        "main_work_declared\": true",
        "outcome_evidence",
    ):
        assert forbidden not in serialized
    payload = response.json()
    assert payload["write_boundary"] == {
        "owner": "TopicExploration",
        "writes_life_case": False,
        "upgrades_relation_effect": False,
        "upgrades_work_path": False,
        "declares_main_work": False,
    }
    assert payload["professional_state"]["fail_closed"] is True
    assert "fixture:rgm-wpm-p0" not in json.dumps(payload, ensure_ascii=False)


def test_real_tree_scene_progress_is_server_derived_and_never_invents_fruit() -> None:
    client, _ = _client_with_two_cases()
    url = "/api/v50/relation-work-p0/cases/case-real-p1-a"
    initial = client.get(f"{url}/bootstrap").json()
    initial_nodes = {
        item["category"]: item for item in initial["tree_scene"]["nodes"]
    }

    assert initial["tree_scene"]["persistent_source"] == "TopicExploration"
    assert initial["tree_scene"]["frontend_truth_inference_allowed"] is False
    assert initial["tree_scene"]["flower_unlocked"] is True
    assert set(initial_nodes) == {"life_observation"}
    assert initial_nodes["life_observation"]["status"] == "available"
    assert len(initial_nodes["life_observation"]["question_refs"]) == 1
    assert initial["tree_scene"]["fruit"] == {
        "visible": False,
        "reason": "blindround_not_bound",
    }

    for question in initial["questions"]:
        response = client.post(
            f"{url}/questions/{question['instance_id']}/answer",
            json={"selected_option_id": question["options"][0]["option_id"]},
        )
        assert response.status_code == 200

    reloaded = client.get(f"{url}/bootstrap").json()
    reloaded_nodes = {
        item["category"]: item for item in reloaded["tree_scene"]["nodes"]
    }
    assert reloaded["tree_scene"]["flower_unlocked"] is True
    assert reloaded_nodes["life_observation"]["status"] == "explored"
    assert reloaded["tree_scene"]["fruit"]["visible"] is False
    assert reloaded["tree_scene"] == client.get(f"{url}/bootstrap").json()[
        "tree_scene"
    ]


def test_abu_observation_loop_is_bounded_persistent_and_idempotent() -> None:
    client, theater_store = _client_with_two_cases()
    url = "/api/v50/relation-work-p0/cases/case-real-p1-a"
    bootstrap = client.get(f"{url}/bootstrap").json()
    question = next(
        item
        for item in bootstrap["questions"]
        if item["category"] == "life_observation"
    )
    turn_url = f"{url}/questions/{question['instance_id']}/abu-turn"

    premature = client.post(
        turn_url,
        json={"request_id": "turn-before-answer", "message": "凭什么这样比较？"},
    )
    assert premature.status_code == 409

    answer = client.post(
        f"{url}/questions/{question['instance_id']}/answer",
        json={"selected_option_id": question["options"][0]["option_id"]},
    )
    assert answer.status_code == 200
    turn = client.post(
        turn_url,
        json={"request_id": "turn-evidence-001", "message": "凭什么这样比较？"},
    )
    assert turn.status_code == 200
    payload = turn.json()
    assert payload["turn"]["classification"] == "bounded_evidence"
    assert payload["boundaries"] == {
        "facts_are_server_projection_only": True,
        "candidates_are_not_professional_effects": True,
        "user_statement_is_not_lifecase_truth": True,
        "llm_used": False,
        "writes_life_case": False,
    }
    assert payload["write_boundary"]["writes_life_case"] is False
    assert len(theater_store.list_explorations(bootstrap["participant_run_id"])) == 2

    repeated = client.post(
        turn_url,
        json={"request_id": "turn-evidence-001", "message": "凭什么这样比较？"},
    )
    assert repeated.status_code == 200
    assert repeated.json()["turn"] == payload["turn"]
    conflict = client.post(
        turn_url,
        json={"request_id": "turn-evidence-001", "message": "这就是主线吗？"},
    )
    assert conflict.status_code == 409

    reloaded = client.get(f"{url}/bootstrap").json()
    assert len(reloaded["explorations"]) == 1
    assert reloaded["abu_conversation"]["llm_used"] is False
    assert reloaded["abu_conversation"]["turns"] == payload["history"]
    serialized = json.dumps(reloaded["abu_conversation"], ensure_ascii=False)
    assert "correct_answer" not in serialized
    assert "professional_judgment_allowed" in serialized
