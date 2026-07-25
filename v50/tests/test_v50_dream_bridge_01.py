from __future__ import annotations

from datetime import datetime, timezone
from copy import deepcopy
import json
from pathlib import Path

from fastapi.testclient import TestClient

from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.dream_feature import DreamFeaturePolicy
from product.dream_pilot import CANONICAL_NPC_IDS, DreamCanonicalNpcBootstrapService
from product.dream_store_memory import MemoryDreamStore
from product.product_api import PRODUCT_SESSION_COOKIE
from product.product_store import MemoryProductStore
from test_v50_mingli_structural_experiment import _case_payload


ROOT = Path(__file__).resolve().parents[1]
TEST_DREAM_CLIENT_ID = "dream-test-client-primary"
_DREAM_WORLD_REFS: dict[int, str] = {}


def _visit_request(home_case_id: str, *, client_instance_id: str = TEST_DREAM_CLIENT_ID) -> dict[str, object]:
    return {
        "home_case_id": home_case_id,
        "client_instance_id": client_instance_id,
    }


def _activate_dream_control(client: TestClient, payload: dict[str, object]) -> None:
    lease = payload["control_lease"]
    assert isinstance(lease, dict)
    client.headers.update({
        "x-dream-client-instance": str(lease["client_instance_id"]),
        "x-dream-lease-id": str(lease["lease_id"]),
        "x-dream-lease-epoch": str(lease["lease_epoch"]),
        "x-dream-fence-token": str(lease["fence_token"]),
    })
    _DREAM_WORLD_REFS[id(client)] = str(payload["world_projection_ref"])


def _navigation(
    client: TestClient,
    *,
    x: float = 50,
    y: float = 72,
    camera_heading: float = 0,
) -> dict[str, object]:
    return {
        "world_projection_ref": _DREAM_WORLD_REFS[id(client)],
        "position": {"x": x, "y": y},
        "camera_heading": camera_heading,
    }


def _dream_app(
    *,
    enabled: bool = True,
    consent: bool = True,
    npc_count: int = 2,
    legacy_human: bool = False,
):
    product_store = MemoryProductStore()
    account = product_store.register_account(
        email="dream-reader@example.com",
        password="safe-dream-pass",
        display_name="Dream Reader",
        role="member",
    )
    other_account = product_store.register_account(
        email="other-dream-reader@example.com",
        password="other-dream-pass",
        display_name="Other Reader",
        role="member",
    )
    user_id = str(account["user_id"])
    case_store = MemoryAgentCaseStore()
    home_case_id = "case-dream-home-owner"
    home_payload = _case_payload(home_case_id)
    if legacy_human:
        home_payload.pop("life_case", None)
    case_store.save(
        case_id=home_case_id,
        user_id=user_id,
        profile_id="profile-dream-home",
        payload=home_payload,
    )
    dream_store = MemoryDreamStore()
    bootstrapped = DreamCanonicalNpcBootstrapService(
        case_store=case_store,
        dream_store=dream_store,
    ).ensure()
    for item in bootstrapped[npc_count:]:
        grant = dream_store.get_grant(public_scene_ref=item.public_scene_ref)
        assert grant is not None
        now = datetime.now(timezone.utc)
        dream_store.save_grant(grant.model_copy(update={
            "status": "withdrawn",
            "withdrawn_at": now,
            "updated_at": now,
        }))

    policy = DreamFeaturePolicy(
        enabled=enabled,
        allowed_user_ids=frozenset({user_id}),
    )
    app = create_product_app(
        product_store=product_store,
        agent_case_store=case_store,
        dream_store=dream_store,
        dream_feature_policy=policy,
    )
    client = TestClient(app)
    client.cookies.set(
        PRODUCT_SESSION_COOKIE,
        product_store.create_session(user_id=user_id),
    )
    other_client = TestClient(app)
    other_client.cookies.set(
        PRODUCT_SESSION_COOKIE,
        product_store.create_session(user_id=str(other_account["user_id"])),
    )
    if consent and enabled:
        granted = client.post("/api/v50/dream/consent", json={
            "case_id": home_case_id,
            "accepted": True,
            "consent_version": "deepbazi.dream_pilot_consent.v1",
        })
        assert granted.status_code == 200, granted.text
    return client, other_client, dream_store, case_store, user_id, home_case_id


def _enter_three_tree_visit(client: TestClient, home_case_id: str) -> tuple[str, dict[str, object]]:
    created = client.post("/api/v50/dream/visits", json=_visit_request(home_case_id))
    assert created.status_code == 200, created.text
    created_payload = created.json()
    _activate_dream_control(client, created_payload)
    visit_id = created_payload["visit_id"]
    entered = client.post(f"/api/v50/dream/visits/{visit_id}/enter", json={})
    assert entered.status_code == 200, entered.text
    encounter = client.get(f"/api/v50/dream/visits/{visit_id}/encounter")
    assert encounter.status_code == 200, encounter.text
    return visit_id, encounter.json()


def _reveal_and_open_mirror(
    client: TestClient,
    *,
    visit_id: str,
    scene_ref: str,
) -> tuple[dict[str, object], dict[str, object]]:
    reveal = client.post(
        f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}/reveal",
        json={},
    )
    assert reveal.status_code == 200, reveal.text
    reveal_payload = reveal.json()
    view_ref = reveal_payload["onecanvas_view_ref"]
    opened = client.post(
        f"/api/v50/dream/visits/{visit_id}/mirror/open",
        json={
            "onecanvas_view_ref": view_ref,
            "navigation": _navigation(client),
        },
    )
    assert opened.status_code == 200, opened.text
    mirror = client.get(
        f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}/mirror",
        params={"view_ref": view_ref},
    )
    assert mirror.status_code == 200, mirror.text
    return reveal_payload, mirror.json()


def test_dream_bridge_is_server_disabled_by_default_and_client_cannot_bypass() -> None:
    client, _, _, _, _, home_case_id = _dream_app(enabled=False, consent=False)

    status = client.get("/api/v50/dream/status")
    bypass = client.post("/api/v50/dream/visits", json=_visit_request(home_case_id))

    assert status.status_code == 200
    assert status.json() == {
        "schema_version": "deepbazi.dream_feature_status.v1",
        "enabled": False,
        "available": False,
        "resumable": False,
        "eligible_scene_count": 0,
        "reason_code": "dream_feature_disabled",
        "consent_state": "not_granted",
        "human_scene_eligible": False,
        "canonical_npc_scene_count": 0,
        "composition_ready": False,
        "projection_version": "deepbazi.dream_projection.v1",
    }
    assert bypass.status_code == 404
    assert bypass.json()["detail"] == "dream_feature_disabled"


def test_dream_bridge_fails_closed_until_human_explicitly_consents() -> None:
    client, _, _, _, _, home_case_id = _dream_app(consent=False)

    status = client.get("/api/v50/dream/status", params={"case_id": home_case_id})
    created = client.post("/api/v50/dream/visits", json=_visit_request(home_case_id))

    assert status.status_code == 200
    assert status.json()["enabled"] is True
    assert status.json()["available"] is False
    assert status.json()["eligible_scene_count"] == 2
    assert status.json()["consent_state"] == "not_granted"
    assert status.json()["reason_code"] == "dream_human_consent_required"
    assert created.status_code == 409
    assert created.json()["detail"] == "DREAM_ENCOUNTER_UNAVAILABLE"


def test_human_consent_is_owner_initiated_revocable_and_immediately_disqualifies_tree() -> None:
    client, other_client, _, _, _, home_case_id = _dream_app(consent=False)

    foreign = other_client.post("/api/v50/dream/consent", json={
        "case_id": home_case_id,
        "accepted": True,
        "consent_version": "deepbazi.dream_pilot_consent.v1",
    })
    granted = client.post("/api/v50/dream/consent", json={
        "case_id": home_case_id,
        "accepted": True,
        "consent_version": "deepbazi.dream_pilot_consent.v1",
    })
    visit_id, _ = _enter_three_tree_visit(client, home_case_id)
    withdrawn = client.post("/api/v50/dream/consent/withdraw", json={
        "case_id": home_case_id,
        "confirmed": True,
    })
    status = client.get("/api/v50/dream/status", params={"case_id": home_case_id})
    stale_visit = client.get(f"/api/v50/dream/visits/{visit_id}/encounter")

    assert foreign.status_code == 404
    assert granted.status_code == 200
    assert granted.json()["state"] == "active"
    assert withdrawn.status_code == 200
    assert withdrawn.json()["state"] == "withdrawn"
    assert status.json()["available"] is False
    assert status.json()["human_scene_eligible"] is False
    assert stale_visit.status_code == 409
    assert stale_visit.json()["detail"] == "dream_scene_authorization_unavailable"


def test_reissued_human_consent_starts_new_visit_without_reusing_old_authorization() -> None:
    client, _, _, _, _, home_case_id = _dream_app()
    old_visit_id, _ = _enter_three_tree_visit(client, home_case_id)

    withdrawn = client.post("/api/v50/dream/consent/withdraw", json={
        "case_id": home_case_id,
        "confirmed": True,
    })
    reissued = client.post("/api/v50/dream/consent", json={
        "case_id": home_case_id,
        "accepted": True,
        "consent_version": "deepbazi.dream_pilot_consent.v1",
    })
    fresh = client.post("/api/v50/dream/visits", json=_visit_request(home_case_id))

    assert withdrawn.status_code == 200
    assert reissued.status_code == 200
    assert fresh.status_code == 200, fresh.text
    assert fresh.json()["visit_id"] != old_visit_id
    old_visit = client.get(f"/api/v50/dream/visits/{old_visit_id}/encounter")
    assert old_visit.status_code == 409
    assert old_visit.json()["detail"] == "dream_scene_source_version_changed"


def test_explicit_consent_materializes_only_chart_facts_for_legacy_human_case() -> None:
    client, _, _, case_store, _, home_case_id = _dream_app(
        consent=False,
        legacy_human=True,
    )
    before = case_store.get(case_id=home_case_id)
    assert before is not None and before.get("life_case") is None

    granted = client.post("/api/v50/dream/consent", json={
        "case_id": home_case_id,
        "accepted": True,
        "consent_version": "deepbazi.dream_pilot_consent.v1",
    })

    after = case_store.get(case_id=home_case_id)
    assert granted.status_code == 200, granted.text
    assert after is not None
    assert after["life_case"]["relation_assertions"] == []
    assert after["life_case"]["path_assertions"] == []
    assert after["life_case"]["baseline_insight"]["projection_payload"] == {
        "identity_class": "authorized_human",
        "professional_path_state": "unavailable_unconfirmed",
    }
    assert after["dream_projection_baseline"]["projection_boundary"] == "chart_facts_only"
    status = client.get("/api/v50/dream/status", params={"case_id": home_case_id})
    assert status.status_code == 200
    assert status.json()["composition_ready"] is True


def test_chart_only_consent_does_not_promote_a_blocked_cognitive_record() -> None:
    client, _, _, case_store, _, home_case_id = _dream_app(
        consent=False,
        legacy_human=True,
    )
    before = case_store.get(case_id=home_case_id)
    assert before is not None
    blocked = deepcopy(before)
    blocked["record"]["reliability_disposition"] = "blocked"
    blocked["record"]["review"]["disposition"] = "blocked"
    case_store.save(
        case_id=home_case_id,
        user_id=before["user_id"],
        profile_id=before["profile_id"],
        payload=blocked,
    )

    granted = client.post("/api/v50/dream/consent", json={
        "case_id": home_case_id,
        "accepted": True,
        "consent_version": "deepbazi.dream_pilot_consent.v1",
    })

    after = case_store.get(case_id=home_case_id)
    assert granted.status_code == 200, granted.text
    assert after is not None
    assert after["record"]["reliability_disposition"] == "blocked"
    assert after["record"]["review"]["disposition"] == "blocked"
    assert after["life_case"]["relation_assertions"] == []
    assert after["life_case"]["path_assertions"] == []
    assert after["life_case"]["baseline_insight"]["professional_release_status"] == "partially_blocked"
    assert after["life_case"]["baseline_insight"]["projection_payload"] == {
        "identity_class": "authorized_human",
        "professional_path_state": "unavailable_unconfirmed",
    }


def test_canonical_npc_bootstrap_is_unique_auditable_and_projection_only() -> None:
    _, _, dream_store, case_store, _, _ = _dream_app(consent=False)
    grants = [item for item in dream_store.list_grants() if item.subject_kind == "canonical_npc"]

    assert {item.subject_ref for item in grants} == CANONICAL_NPC_IDS
    assert len({item.case_id for item in grants}) == 2
    for grant in grants:
        row = case_store.get(case_id=grant.case_id)
        assert row is not None
        assert row["user_id"] is None
        assert row["canonical_npc"]["identity_class"] == "canonical_npc"
        assert row["canonical_npc"]["not_human"] is True
        assert row["canonical_npc"]["not_reality_evidence"] is True
        assert row["canonical_npc"]["disabled_capabilities"] == [
            "mind_wake", "free_dialogue", "autonomous_action"
        ]
        assert row["life_case"]["relation_assertions"] == []
        assert row["life_case"]["path_assertions"] == []


def test_three_tree_visit_is_exactly_three_deterministic_and_switchable_between_observations() -> None:
    client, _, _, _, _, home_case_id = _dream_app()
    visit_id, encounter = _enter_three_tree_visit(client, home_case_id)

    assert len(encounter["trees"]) == 3
    assert len({item["scene_ref"] for item in encounter["trees"]}) == 3
    assert all(set(item) >= {
        "scene_ref", "art_variant", "primary_element", "climate_token", "source_version",
        "source_kind", "source_label_key",
    } for item in encounter["trees"])
    assert [item["source_kind"] for item in encounter["trees"]].count("authorized_human") == 1
    assert [item["source_kind"] for item in encounter["trees"]].count("canonical_npc") == 2

    first = encounter["trees"][0]["scene_ref"]
    second = encounter["trees"][1]["scene_ref"]
    selected = client.post(
        f"/api/v50/dream/visits/{visit_id}/select-tree",
        json={"scene_ref": first},
    )
    selected_again = client.post(
        f"/api/v50/dream/visits/{visit_id}/select-tree",
        json={"scene_ref": first},
    )
    switched = client.post(
        f"/api/v50/dream/visits/{visit_id}/select-tree",
        json={"scene_ref": second},
    )

    assert selected.status_code == selected_again.status_code == 200
    assert selected.json()["state"] == "TREE_OBSERVING"
    assert selected.json()["selected_scene_ref"] == first
    assert switched.status_code == 200
    assert switched.json()["state"] == "TREE_OBSERVING"
    assert switched.json()["selected_scene_ref"] == second

    reveal = client.post(
        f"/api/v50/dream/visits/{visit_id}/trees/{second}/reveal",
        json={},
    )
    opened = client.post(
        f"/api/v50/dream/visits/{visit_id}/mirror/open",
        json={
            "onecanvas_view_ref": reveal.json()["onecanvas_view_ref"],
            "navigation": _navigation(client),
        },
    )
    locked_while_open = client.post(
        f"/api/v50/dream/visits/{visit_id}/select-tree",
        json={"scene_ref": first},
    )
    assert opened.status_code == 200
    assert locked_while_open.status_code == 409
    assert locked_while_open.json()["detail"] == "dream_tree_selection_locked"


def test_dream_visit_is_owner_scoped_and_resumable_without_duplicate_visit() -> None:
    client, other_client, _, _, _, home_case_id = _dream_app()
    visit_id, _ = _enter_three_tree_visit(client, home_case_id)

    resumed = client.post("/api/v50/dream/visits", json=_visit_request(home_case_id))
    assert resumed.status_code == 200, resumed.text
    _activate_dream_control(client, resumed.json())
    other_client.headers.update({
        key: value
        for key, value in client.headers.items()
        if key.startswith("x-dream-")
    })
    foreign = other_client.get(f"/api/v50/dream/visits/{visit_id}")

    assert resumed.status_code == 200
    assert resumed.json()["visit_id"] == visit_id
    assert foreign.status_code == 404


def test_dream_projection_omits_private_refs_and_non_committed_content() -> None:
    client, _, _, _, _, home_case_id = _dream_app()
    visit_id, encounter = _enter_three_tree_visit(client, home_case_id)
    scene_ref = encounter["trees"][0]["scene_ref"]
    selected = client.post(
        f"/api/v50/dream/visits/{visit_id}/select-tree",
        json={"scene_ref": scene_ref},
    )
    assert selected.status_code == 200

    tree = client.get(f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}")
    reveal = client.post(
        f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}/reveal",
        json={},
    )
    assert reveal.status_code == 200, reveal.text
    view_ref = reveal.json()["onecanvas_view_ref"]
    unopened = client.get(
        f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}/mirror",
        params={"view_ref": view_ref},
    )
    opened = client.post(
        f"/api/v50/dream/visits/{visit_id}/mirror/open",
        json={
            "onecanvas_view_ref": view_ref,
            "navigation": _navigation(client),
        },
    )
    mirror = client.get(
        f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}/mirror",
        params={"view_ref": view_ref},
    )

    assert tree.status_code == 200, tree.text
    assert tree.json()["work_path_state"] == "unavailable_unconfirmed"
    assert unopened.status_code == 409
    assert opened.status_code == 200
    assert mirror.status_code == 200, mirror.text

    payload = mirror.json()
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    assert "case-dream-home-owner" not in serialized
    assert "dream-human-grant" not in serialized
    assert "dream-reader" not in serialized
    assert '"potential"' not in serialized
    assert '"status": "legacy_unresolved"' not in serialized
    assert payload["verification"]["onecanvas_view_ref"] == view_ref
    assert payload["verification"]["binding"]["coordinate_version"] == (
        "canonical-six-pillar-twelve-node.v1"
    )
    assert payload["canvas"]["renderer_policy"]["available_visibility_layers"] == [
        "formal", "focus"
    ]
    for stage in payload["canvas"]["stages"].values():
        assert all(
            item["trace"]["epistemic_status"] == "committed"
            for item in stage["spec"]["paths"]
        )
        assert all(item["relation_state"] != "potential" for item in stage["spec"]["relations"])


def test_dream_mirror_reuses_six_pillar_canvas_and_opaque_context_refs() -> None:
    client, _, _, _, _, home_case_id = _dream_app()
    visit_id, encounter = _enter_three_tree_visit(client, home_case_id)
    scene_ref = encounter["trees"][0]["scene_ref"]
    client.post(
        f"/api/v50/dream/visits/{visit_id}/select-tree",
        json={"scene_ref": scene_ref},
    )
    _, mirror = _reveal_and_open_mirror(
        client,
        visit_id=visit_id,
        scene_ref=scene_ref,
    )
    canvas = mirror["canvas"]

    assert [item["slot_type"] for item in canvas["stages"]["year"]["scene_slots"]] == [
        "natal_year", "natal_month", "natal_day", "natal_hour", "luck", "year"
    ]
    assert [item["layer_id"] for item in canvas["stages"]["natal"]["layers"]] == [
        "overview", "five_element", "combination_conflict", "roots_reveal", "timing", "work_path"
    ]
    slot_refs = [item["slot_ref"] for item in canvas["stages"]["natal"]["scene_slots"]]
    assert slot_refs == [item["slot_ref"] for item in canvas["stages"]["luck"]["scene_slots"]]
    assert slot_refs == [item["slot_ref"] for item in canvas["stages"]["year"]["scene_slots"]]
    selected = canvas["stages"]["natal"]["spec"]["semantic_slots"][0]["slot_ref"]
    context = client.get(
        f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}/mirror/context",
        params={"stage": "natal", "selected": selected, "layer": "overview"},
    )
    assert context.status_code == 200, context.text
    serialized = json.dumps(context.json(), ensure_ascii=False)
    assert selected in serialized
    assert "case-dream-home-owner" not in serialized


def test_revoked_or_source_changed_grant_invalidates_existing_visit() -> None:
    client, _, dream_store, case_store, _, home_case_id = _dream_app()
    visit_id, encounter = _enter_three_tree_visit(client, home_case_id)
    scene_ref = next(
        item["scene_ref"]
        for item in encounter["trees"]
        if item["source_kind"] == "canonical_npc"
    )
    grant = dream_store.get_grant(public_scene_ref=scene_ref)
    assert grant is not None
    now = datetime.now(timezone.utc)
    dream_store.save_grant(grant.model_copy(update={
        "status": "withdrawn",
        "withdrawn_at": now,
        "updated_at": now,
    }))
    revoked = client.get(f"/api/v50/dream/visits/{visit_id}/encounter")
    assert revoked.status_code == 409
    assert revoked.json()["detail"] == "dream_scene_authorization_unavailable"

    # Restoring authorization does not bypass a changed Canonical source version.
    dream_store.save_grant(grant.model_copy(update={"status": "active", "withdrawn_at": None}))
    changed_payload = deepcopy(case_store.get(case_id=grant.case_id, user_id=None))
    assert changed_payload is not None
    changed_payload["world"]["timing_context"]["analysis_year"] = 2025
    changed_payload["world"]["timing_context"]["annual_pillar"] = "乙巳"
    case_store.save(
        case_id=grant.case_id,
        user_id=None,
        profile_id=None,
        payload=changed_payload,
    )
    changed = client.get(f"/api/v50/dream/visits/{visit_id}/encounter")
    assert changed.status_code == 409
    assert changed.json()["detail"] == "dream_scene_source_version_changed"


def test_tree_reveal_is_server_selected_opaque_and_required_for_mirror_open() -> None:
    client, _, _, _, _, home_case_id = _dream_app()
    visit_id, encounter = _enter_three_tree_visit(client, home_case_id)
    scene_ref = next(
        item["scene_ref"]
        for item in encounter["trees"]
        if item["source_kind"] == "canonical_npc"
    )
    client.post(
        f"/api/v50/dream/visits/{visit_id}/select-tree",
        json={"scene_ref": scene_ref},
    )

    reveal = client.post(
        f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}/reveal",
        json={},
    )
    repeated = client.post(
        f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}/reveal",
        json={},
    )
    invalid = client.post(
        f"/api/v50/dream/visits/{visit_id}/mirror/open",
        json={
            "onecanvas_view_ref": "dream-onecanvas-view-" + ("0" * 40),
            "navigation": _navigation(client),
        },
    )

    assert reveal.status_code == repeated.status_code == 200
    payload = reveal.json()
    assert repeated.json()["content_hash"] == payload["content_hash"]
    assert payload["onecanvas_view_ref"].startswith("dream-onecanvas-view-")
    assert payload["reveal_kind"] in {"path", "relation", "node", "none"}
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "dream-pilot-npc-case" not in serialized
    assert "npc-mist-lan" not in serialized
    assert invalid.status_code == 409
    assert invalid.json()["detail"] == "dream_mirror_reference_invalid"


def test_revocation_after_reveal_fails_open_closed_and_still_allows_safe_close() -> None:
    client, _, dream_store, _, _, home_case_id = _dream_app()
    visit_id, encounter = _enter_three_tree_visit(client, home_case_id)
    scene_ref = next(
        item["scene_ref"]
        for item in encounter["trees"]
        if item["source_kind"] == "canonical_npc"
    )
    client.post(
        f"/api/v50/dream/visits/{visit_id}/select-tree",
        json={"scene_ref": scene_ref},
    )
    reveal, _ = _reveal_and_open_mirror(
        client,
        visit_id=visit_id,
        scene_ref=scene_ref,
    )
    grant = dream_store.get_grant(public_scene_ref=scene_ref)
    assert grant is not None
    now = datetime.now(timezone.utc)
    dream_store.save_grant(grant.model_copy(update={
        "status": "withdrawn",
        "withdrawn_at": now,
        "updated_at": now,
    }))

    blocked = client.get(
        f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}/mirror",
        params={"view_ref": reveal["onecanvas_view_ref"]},
    )
    closed = client.post(f"/api/v50/dream/visits/{visit_id}/mirror/close", json={})

    assert blocked.status_code == 409
    assert blocked.json()["detail"] == "dream_scene_authorization_unavailable"
    assert closed.status_code == 200
    assert closed.json()["state"] == "TREE_OBSERVING"


def test_dream_routes_frontend_contracts_and_schema_are_present() -> None:
    client, _, _, _, _, _ = _dream_app(consent=False)
    direct = client.get("/experience/dream/visits/visit-opaque/trees/scene-opaque/mirror")
    source = (ROOT / "apps/product/experience_shell/src/dream_runtime.ts").read_text(encoding="utf-8")
    i18n = (ROOT / "apps/product/experience_shell/src/dream_i18n.ts").read_text(encoding="utf-8")
    styles = (ROOT / "apps/product/static/experience/styles.css").read_text(encoding="utf-8")
    schema = (ROOT / "deploy/postgres_v50_schema.sql").read_text(encoding="utf-8")

    assert direct.status_code == 200
    assert "renderDreamVerificationCanvas" in source
    assert "dream.path.none_confirmed" in i18n
    assert "data-dream-select" not in source
    assert '"fog_wait"' in source
    assert "prepareDreamReveal" in source
    assert "hitTreeAt" in source
    assert "getImageData" in source
    assert "sessionStorage" in source
    assert "localStorage" not in source
    assert "dream-root-mirror" in source
    assert "mirror_exit" in source
    assert "mirrorExitGeometry" in source
    assert "mirrorBoundaryClientY" in source
    assert 'closest<HTMLElement>(".dream-mirror-water")' not in source
    assert "startTapMotion" in source
    assert "treeApproachPoint" in source
    assert "advanceAbuFollower" in source
    assert "dream-tree-response-root" in styles
    assert "popstate" in source
    assert "data-dream-a11y=\"leave-mirror\"" in source
    assert "dream.source.canonical_npc" in i18n
    assert ".dream-first-visit" in styles
    assert ".dream-verification-canvas" in styles
    assert ".dream-root-mirror-reflection" in styles
    assert ".dream-mirror-layer.is-pulling-mirror" in styles
    assert "dream-own-root-catch" in styles
    assert "dream-touch-trunk-carry" in styles
    assert "@media (max-width: 720px)" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles
    assert "transition-property: opacity, filter !important" in styles
    assert "transition-duration: 900ms !important" in styles
    assert "CREATE TABLE IF NOT EXISTS v50_dream_scene_grants" in schema
    assert "CREATE TABLE IF NOT EXISTS v50_dream_visits" in schema
    assert "DreamCase" not in schema
    assert "DreamLedger" not in schema
