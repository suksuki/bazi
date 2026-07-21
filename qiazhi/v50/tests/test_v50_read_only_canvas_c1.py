from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.canvas_projection import (
    ReadOnlyCanvasUnavailable,
    ReadOnlySixPillarCanvasService,
)
from product.product_store import MemoryProductStore
from test_v50_mingli_structural_experiment import _case_payload


ROOT = Path(__file__).resolve().parents[1]


def _typed_real_case(case_id: str) -> tuple[dict[str, object], str]:
    payload = _case_payload(case_id)
    world = payload["world"]
    record = payload["record"]
    assert isinstance(world, dict)
    assert isinstance(record, dict)
    path_facts = [
        item for item in world["facts"]
        if item["category"] == "candidate_path"
    ]
    committed_fact = path_facts[0]
    committed_ref = next(
        item for item in committed_fact["source_refs"] if item.startswith("path:")
    )
    work_path = record["cognition"]["work_path"]
    work_path["evidence_refs"] = [committed_fact["fact_id"]]
    work_path["candidate_path_refs"] = [committed_ref]
    work_path["path_statement"] = "结构化证据已经形成一条可定位的正式主路径。"

    payload["life_case"]["baseline_insight"]["basis"]["chart_fact_refs"] = [
        committed_fact["fact_id"]
    ]
    candidate_fact = next(
        item for item in path_facts if item["fact_id"] != committed_fact["fact_id"]
    )
    candidate_ref = next(item for item in candidate_fact["source_refs"] if item.startswith("path:"))
    work_path["competing_path_refs"] = [candidate_ref]
    return payload, candidate_ref


def _saved_case() -> tuple[MemoryAgentCaseStore, str, str, str]:
    store = MemoryAgentCaseStore()
    user_id = "user-canvas-c1"
    case_id = "case-canvas-c1-real"
    payload, candidate_ref = _typed_real_case(case_id)
    store.save(case_id=case_id, user_id=user_id, profile_id=None, payload=payload)
    return store, user_id, case_id, candidate_ref


def test_real_life_case_projects_read_only_four_five_six_pillar_stages() -> None:
    store, user_id, case_id, _ = _saved_case()
    before = deepcopy(store.get(case_id=case_id, user_id=user_id))
    service = ReadOnlySixPillarCanvasService(case_store=store)

    payload = service.issue(
        case_id=case_id,
        participant_id=user_id,
        account_role="member",
    )

    assert payload["status"] == "read_only_canvas_ready"
    assert payload["path_availability"]["status"] == "available"
    assert len(payload["stages"]["natal"]["spec"]["semantic_slots"]) == 4
    assert len(payload["stages"]["luck"]["spec"]["semantic_slots"]) == 5
    assert len(payload["stages"]["year"]["spec"]["semantic_slots"]) == 6
    assert len(payload["stages"]["natal"]["spec"]["paths"]) == 1
    assert payload["stages"]["natal"]["spec"]["paths"][0]["trace"]["epistemic_status"] == "committed"
    assert len(payload["stages"]["luck"]["diff"]["added_nodes"]) == 2
    assert len(payload["stages"]["year"]["diff"]["added_nodes"]) == 2
    assert not payload["stages"]["luck"]["diff"]["weakened_paths"]
    assert not payload["stages"]["year"]["diff"]["reinforced_paths"]
    assert payload["stages"]["luck"]["diff"]["unchanged_paths"][0]["change_type"] == "unchanged"
    assert payload["stages"]["year"]["diff"]["unchanged_paths"][0]["change_type"] == "unchanged"
    assert payload["llm_used"] is False
    assert payload["formal_state_writes"] is False
    assert payload["sandbox_mutations"] is False
    assert store.get(case_id=case_id, user_id=user_id) == before


def test_official_luck_and_year_update_committed_paths_without_promoting_candidates() -> None:
    store, user_id, case_id, _ = _saved_case()
    service = ReadOnlySixPillarCanvasService(case_store=store)

    first = service.issue(case_id=case_id, participant_id=user_id, account_role="member")
    second = service.issue(case_id=case_id, participant_id=user_id, account_role="member")

    assert first["stages"]["luck"]["spec"] == second["stages"]["luck"]["spec"]
    assert first["stages"]["year"]["spec"] == second["stages"]["year"]["spec"]
    expected_types = {
        "luck": {"position_link", "forms_half_combination", "forms_triple_combination"},
        "year": {"position_link", "harms"},
    }
    for stage in ("luck", "year"):
        spec = first["stages"][stage]["spec"]
        diff = first["stages"][stage]["diff"]
        nodes = {item["node_ref"]: item for item in spec["nodes"]}
        temporal_slot = spec["semantic_slots"][-1]["slot_ref"]
        temporal_refs = {
            item["node_ref"]
            for item in spec["nodes"]
            if item["semantic_slot_ref"] == temporal_slot
        }
        added_refs = {item["target_ref"] for item in diff["added_relations"]}
        added = [
            item for item in spec["relations"]
            if item["relation_ref"] in added_refs
        ]

        assert added
        assert expected_types[stage].issubset({item["relation_type"] for item in added})
        assert all(temporal_refs.intersection(item["participant_node_refs"]) for item in added)
        assert all(item["trace"]["epistemic_status"] == "derived" for item in added)
        assert not any(item["relation_state"] == "potential" for item in added)
        for relation in added:
            levels = {
                "stem" if nodes[ref]["node_type"].endswith("stem") else "branch"
                for ref in relation["participant_node_refs"]
            }
            if len(levels) > 1:
                assert relation["relation_type"] == "position_link"
                assert relation["relation_state"] == "structural"
                assert "不自动表示直接作用" in relation["trace"]["uncertainty"][0]
        assert not diff["introduced_paths"]
        assert not diff["activated_paths"]
        assert not diff["blocked_paths"]
        assert not diff["reinforced_paths"]
        assert not diff["weakened_paths"]
        assert len(diff["unchanged_paths"]) == 1
        assert diff["unchanged_paths"][0]["target_ref"].startswith("path:")


def test_member_projection_removes_practitioner_path_before_serialization() -> None:
    store, user_id, case_id, candidate_ref = _saved_case()
    service = ReadOnlySixPillarCanvasService(case_store=store)

    member = service.issue(case_id=case_id, participant_id=user_id, account_role="member")
    practitioner = service.issue(case_id=case_id, participant_id=user_id, account_role="practitioner")

    member_json = json.dumps(member, ensure_ascii=False)
    practitioner_json = json.dumps(practitioner, ensure_ascii=False)
    assert candidate_ref not in member_json
    assert candidate_ref in practitioner_json
    assert '"relation_state": "potential"' not in member_json
    assert '"relation_state": "potential"' in practitioner_json
    assert member["path_availability"]["candidate_path_count"] == 1
    assert len(member["stages"]["natal"]["spec"]["paths"]) == 1
    assert len(practitioner["stages"]["natal"]["spec"]["paths"]) == 2
    assert all(
        path["trace"]["epistemic_status"] != "candidate"
        for path in member["stages"]["natal"]["spec"]["paths"]
    )

    with pytest.raises(ReadOnlyCanvasUnavailable, match="canvas_object_not_disclosed"):
        service.issue_context(
            case_id=case_id,
            participant_id=user_id,
            account_role="member",
            stage="natal",
            selected_object_ref=candidate_ref,
            visible_layer="work_path",
        )


def test_context_pack_is_bound_to_disclosed_object_and_server_layer() -> None:
    store, user_id, case_id, _ = _saved_case()
    service = ReadOnlySixPillarCanvasService(case_store=store)
    projection = service.issue(case_id=case_id, participant_id=user_id, account_role="member")
    selected = projection["stages"]["year"]["spec"]["semantic_slots"][-1]["slot_ref"]

    context = service.issue_context(
        case_id=case_id,
        participant_id=user_id,
        account_role="member",
        stage="year",
        selected_object_ref=selected,
        visible_layer="work_path",
    )

    assert context.current_stage == "year"
    assert context.selected_object_refs == [selected]
    assert context.visible_layers == ["work_path"]
    assert selected in context.disclosed_object_refs
    assert context.hypothetical_mutations == []


def test_authenticated_canvas_api_returns_only_projected_read_only_payload() -> None:
    product_store = MemoryProductStore()
    case_store = MemoryAgentCaseStore()
    app = create_product_app(product_store=product_store, agent_case_store=case_store)
    client = TestClient(app)
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "画布测试",
            "email": "canvas-c1@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200
    user_id = registered.json()["account"]["user_id"]
    case_id = "case-canvas-c1-api"
    payload, candidate_ref = _typed_real_case(case_id)
    case_store.save(case_id=case_id, user_id=user_id, profile_id=None, payload=payload)

    response = client.get(f"/api/v50/experience/cases/{case_id}/canvas")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["renderer_policy"]["read_only"] is True
    assert candidate_ref not in response.text
    assert body["stages"]["year"]["spec"]["identity"]["audience_role"] == "member"
    assert body["formal_state_writes"] is False

    selected = body["stages"]["year"]["spec"]["semantic_slots"][-1]["slot_ref"]
    context = client.get(
        f"/api/v50/experience/cases/{case_id}/canvas/context",
        params={"stage": "year", "selected": selected, "layer": "work_path"},
    )
    assert context.status_code == 200, context.text
    assert context.json()["context"]["selected_object_refs"] == [selected]
    assert context.json()["llm_used"] is False


def test_renderer_consumes_server_layer_refs_without_relation_inference() -> None:
    source = (ROOT / "apps/product/experience_shell/src/components.ts").read_text(encoding="utf-8")
    api = (ROOT / "apps/product/experience_shell/src/api.ts").read_text(encoding="utf-8")

    assert "layer?.relation_refs" in source
    assert "relation.relation_type ===" not in source
    assert '<text x="${midX}"' in source
    assert 'role="button" data-canvas-object="${escapeAttr(relation.relation_ref)}"' in source
    assert "loadReadOnlyCanvas" in api
    assert "/canvas/context" in api
    assert "replace_year" not in source
    assert "sandbox" not in source.lower()
