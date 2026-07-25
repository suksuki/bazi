from __future__ import annotations

from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient

from experience.canonical_scene import CANONICAL_PROJECTION_KINDS
from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.canonical_scene import CanonicalSceneOwner, CanonicalSceneUnavailable
from product.canvas_projection import ReadOnlySixPillarCanvasService
from product.product_store import MemoryProductStore
from product.theater_envelope import ProductExperienceEnvelopePort
from test_v50_mingli_structural_experiment import _case_payload


def _saved_case(
    *,
    case_id: str = "case-cag03",
    user_id: str = "user-cag03",
    professional_markers: bool = False,
) -> tuple[MemoryAgentCaseStore, dict[str, object]]:
    store = MemoryAgentCaseStore()
    payload = _case_payload(case_id)
    payload.pop("record", None)
    if professional_markers:
        life_case = payload["life_case"]
        assert isinstance(life_case, dict)
        baseline = life_case["baseline_insight"]
        assert isinstance(baseline, dict)
        uncertainty = baseline["uncertainty"]
        assert isinstance(uncertainty, dict)
        uncertainty["competing_hypotheses"] = ["CAG03-ONLY-PROFESSIONAL-HYPOTHESIS"]
        reasoning = baseline["reasoning_path"]
        assert isinstance(reasoning, list)
        reasoning[0]["premise"] = "CAG03-ONLY-PROFESSIONAL-REASONING"
        basis = baseline["basis"]
        assert isinstance(basis, dict)
        basis["holistic_belief_refs"] = ["CAG03-INTERNAL-BELIEF-REF"]
    store.save(case_id=case_id, user_id=user_id, profile_id=None, payload=payload)
    return store, payload


def _registered_client(
    *,
    role: str = "member",
) -> tuple[TestClient, MemoryAgentCaseStore, str]:
    product_store = MemoryProductStore()
    case_store = MemoryAgentCaseStore()
    client = TestClient(
        create_product_app(product_store=product_store, agent_case_store=case_store)
    )
    response = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "CAG03",
            "email": f"cag03-{role}@example.com",
            "password": "secure-pass-123",
            "role": role,
        },
    )
    assert response.status_code == 200, response.text
    return client, case_store, str(response.json()["account"]["user_id"])


def test_canonical_scene_is_deterministic_and_does_not_need_legacy_record() -> None:
    store, _ = _saved_case()
    owner = CanonicalSceneOwner(case_store=store)
    before = deepcopy(store.get(case_id="case-cag03", user_id="user-cag03"))

    first = owner.issue(
        case_id="case-cag03",
        participant_id="user-cag03",
        account_role="member",
    )
    second = owner.issue(
        case_id="case-cag03",
        participant_id="user-cag03",
        account_role="member",
    )

    assert first == second
    assert first.scene.identity.scene_id.startswith("scene-")
    assert set(first.projections) == set(CANONICAL_PROJECTION_KINDS)
    assert all(
        item.scene_identity == first.scene.identity
        for item in first.projections.values()
    )
    assert all(not item.writes_life_case for item in first.projections.values())
    assert all(not item.creates_mingli_claims for item in first.projections.values())
    assert store.get(case_id="case-cag03", user_id="user-cag03") == before


def test_legacy_record_cannot_change_canonical_scene_identity_or_content() -> None:
    store, payload = _saved_case()
    owner = CanonicalSceneOwner(case_store=store)
    clean = owner.issue(
        case_id="case-cag03",
        participant_id="user-cag03",
        account_role="member",
    )
    modified = deepcopy(payload)
    modified["record"] = {
        "record_id": "malicious-legacy-record",
        "claim": "THIS MUST NEVER ENTER THE CANONICAL SCENE",
    }
    store.save(
        case_id="case-cag03",
        user_id="user-cag03",
        profile_id=None,
        payload=modified,
    )
    after = owner.issue(
        case_id="case-cag03",
        participant_id="user-cag03",
        account_role="member",
    )

    assert after == clean
    assert "THIS MUST NEVER" not in json.dumps(after.model_dump(mode="json"), ensure_ascii=False)


def test_member_disclosure_removes_professional_reasoning_before_serialization() -> None:
    store, _ = _saved_case(professional_markers=True)
    owner = CanonicalSceneOwner(case_store=store)
    member = owner.issue(
        case_id="case-cag03",
        participant_id="user-cag03",
        account_role="member",
    )
    practitioner = owner.issue(
        case_id="case-cag03",
        participant_id="user-cag03",
        account_role="practitioner",
    )
    member_json = json.dumps(member.model_dump(mode="json"), ensure_ascii=False)
    practitioner_json = json.dumps(practitioner.model_dump(mode="json"), ensure_ascii=False)

    assert member.scene.identity == practitioner.scene.identity
    assert member.scene.role_disclosure.disclosure_hash != practitioner.scene.role_disclosure.disclosure_hash
    assert member.scene.approved_reasoning_steps
    assert all(
        item.premise == "当前角色不披露专业推理前提。"
        for item in member.scene.approved_reasoning_steps
    )
    assert all(not item.source_refs for item in member.scene.approved_reasoning_steps)
    assert member.scene.competing_hypotheses == []
    assert member.scene.approved_claims[0].evidence_refs == []
    assert "CAG03-ONLY-PROFESSIONAL" not in member_json
    assert "CAG03-INTERNAL-BELIEF-REF" not in member_json
    assert "CAG03-ONLY-PROFESSIONAL-REASONING" in practitioner_json
    assert "CAG03-ONLY-PROFESSIONAL-HYPOTHESIS" in practitioner_json


def test_every_projection_uses_only_disclosed_scene_semantic_refs() -> None:
    store, _ = _saved_case(professional_markers=True)
    bundle = CanonicalSceneOwner(case_store=store).issue(
        case_id="case-cag03",
        participant_id="user-cag03",
        account_role="practitioner",
    )
    disclosed = set(bundle.scene.semantic_refs)

    for kind, envelope in bundle.projections.items():
        assert envelope.projection_kind == kind
        assert envelope.scene_identity.source_hash == bundle.scene.identity.source_hash
        assert envelope.role_disclosure == bundle.scene.role_disclosure
        assert set(envelope.semantic_refs).issubset(disclosed)
        assert envelope.adapter_id == f"canonical-scene-{kind}.cag03.v1"


def test_world_and_life_case_identity_mismatch_is_rejected() -> None:
    store, payload = _saved_case()
    mismatched = deepcopy(payload)
    world = mismatched["world"]
    assert isinstance(world, dict)
    world["world_id"] = "world:other-case"
    store.save(
        case_id="case-cag03",
        user_id="user-cag03",
        profile_id=None,
        payload=mismatched,
    )

    with pytest.raises(CanonicalSceneUnavailable, match="canonical_scene_world_version_mismatch"):
        CanonicalSceneOwner(case_store=store).issue(
            case_id="case-cag03",
            participant_id="user-cag03",
            account_role="member",
        )


def test_canonical_scene_api_ignores_client_fact_injection_and_has_no_write_route() -> None:
    client, store, user_id = _registered_client()
    payload = _case_payload("case-cag03-api")
    payload.pop("record", None)
    store.save(
        case_id="case-cag03-api",
        user_id=user_id,
        profile_id=None,
        payload=payload,
    )
    path = "/api/v50/scenes/cases/case-cag03-api"

    clean = client.get(path)
    injected = client.request(
        "GET",
        path,
        params={"year_pillar": "甲子", "life_case_version": "forged"},
        json={"world": {"pillars": ["甲子", "甲子", "甲子", "甲子"]}},
    )
    denied_write = client.post(path, json={"pillars": ["甲子"] * 4})

    assert clean.status_code == 200, clean.text
    assert injected.status_code == 200, injected.text
    assert clean.json() == injected.json()
    assert denied_write.status_code == 405
    assert clean.json()["scene"]["chart_facts"][0]["stem"] == "丁"
    assert clean.json()["compatibility_policy"]["client_formal_fact_input"] is False


def test_canonical_scene_api_enforces_case_ownership_and_projection_identity() -> None:
    client, store, user_id = _registered_client()
    payload = _case_payload("case-cag03-owned")
    payload.pop("record", None)
    store.save(
        case_id="case-cag03-owned",
        user_id="another-user",
        profile_id=None,
        payload=payload,
    )
    denied = client.get("/api/v50/scenes/cases/case-cag03-owned")
    assert denied.status_code == 404

    store.save(
        case_id="case-cag03-owned",
        user_id=user_id,
        profile_id=None,
        payload=payload,
    )
    bundle = client.get("/api/v50/scenes/cases/case-cag03-owned")
    projection = client.get(
        "/api/v50/scenes/cases/case-cag03-owned/projections/xiangfa"
    )
    assert bundle.status_code == 200, bundle.text
    assert projection.status_code == 200, projection.text
    assert (
        projection.json()["scene_identity"]
        == bundle.json()["scene"]["identity"]
    )
    assert projection.json()["projection_kind"] == "xiangfa"


def test_case_workspace_api_binds_role_filtered_scene_without_accepting_client_facts() -> None:
    client, store, user_id = _registered_client(role="member")
    payload = _case_payload("case-workspace-api")
    payload.pop("record", None)
    payload["workspace_state"] = {
        "schema_version": "deepbazi.case_workspace_state.v2",
        "workspace_id": "workspace-api",
        "case_id": "forged-case",
        "selected_period": "2026-07",
        "system_period": "2026-07",
        "active_domain": "whole_chart",
        "active_mode": "member",
        "current_surface": "mingli_lab",
        "selected_semantic_refs": ["hidden:research-only"],
        "updated_at": "2026-07-21T00:00:00+00:00",
    }
    store.save(
        case_id="case-workspace-api",
        user_id=user_id,
        profile_id=None,
        payload=payload,
    )
    path = "/api/v50/scenes/cases/case-workspace-api/workspace"

    clean = client.get(path)
    injected = client.request(
        "GET",
        path,
        params={"current_surface": "mingli_lab", "year_pillar": "甲子"},
        json={"state": {"current_surface": "mingli_lab"}},
    )
    denied_write = client.post(path, json={"state": {"current_surface": "onecanvas"}})

    assert clean.status_code == 200, clean.text
    assert clean.json() == injected.json()
    assert denied_write.status_code == 405
    assert clean.json()["state"]["case_id"] == "case-workspace-api"
    assert clean.json()["state"]["current_surface"] == "overview"
    assert clean.json()["state"]["selected_semantic_refs"] == []
    assert "mingli_lab" not in clean.json()["allowed_surfaces"]
    assert clean.json()["projection"]["projection_kind"] == "workspace"
    assert clean.json()["writes_life_case"] is False


def test_theater_compatibility_envelope_consumes_the_same_canonical_source() -> None:
    store, _ = _saved_case(professional_markers=True)
    owner = CanonicalSceneOwner(case_store=store)
    scene = owner.issue(
        case_id="case-cag03",
        participant_id="user-cag03",
        account_role="member",
    )
    envelope = ProductExperienceEnvelopePort(case_store=store).issue_envelope(
        participant_id="user-cag03",
        topic_id="whole-chart-baseline",
        topic_version="v1",
        disclosure_level="approved_insights",
        case_id="case-cag03",
    )

    assert envelope.mode == "personal_ready"
    assert envelope.source.source_hash == scene.scene.identity.source_hash
    assert envelope.source.chart_version == scene.scene.identity.chart_version_id
    assert [item.fact_ref for item in envelope.allowed_chart_facts] == [
        item.fact_ref for item in scene.scene.chart_facts
    ]
    assert [item.claim_ref for item in envelope.approved_claims] == [
        item.claim_ref for item in scene.scene.approved_claims
    ]
    assert "CAG03-ONLY-PROFESSIONAL" not in json.dumps(
        envelope.model_dump(mode="json"),
        ensure_ascii=False,
    )


def test_read_only_onecanvas_is_bound_to_the_canonical_scene_projection() -> None:
    store = MemoryAgentCaseStore()
    payload = _case_payload("case-cag03-canvas")
    store.save(
        case_id="case-cag03-canvas",
        user_id="user-cag03-canvas",
        profile_id=None,
        payload=payload,
    )
    canvas = ReadOnlySixPillarCanvasService(case_store=store).issue(
        case_id="case-cag03-canvas",
        participant_id="user-cag03-canvas",
        account_role="member",
    )

    assert canvas["canonical_scene"]["scene_id"] == canvas["projection_envelope"][
        "scene_identity"
    ]["scene_id"]
    assert canvas["projection_envelope"]["projection_kind"] == "onecanvas"
    assert canvas["projection_envelope"]["creates_mingli_facts"] is False
    assert canvas["projection_envelope"]["creates_mingli_claims"] is False
