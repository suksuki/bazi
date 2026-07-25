from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from experience.dream_navigation import DreamDepartureAnchor, DreamWorldPosition
from product.product_api import PRODUCT_SESSION_COOKIE
from test_v50_dream_bridge_01 import (
    _activate_dream_control,
    _dream_app,
    _enter_three_tree_visit,
    _navigation,
    _visit_request,
)


def _same_account_client(client: TestClient) -> TestClient:
    other = TestClient(client.app)
    other.cookies.set(PRODUCT_SESSION_COOKIE, client.cookies.get(PRODUCT_SESSION_COOKIE))
    return other


def test_control_takeover_fences_old_tab_and_keeps_one_active_lease() -> None:
    client, _, _, _, _, case_id = _dream_app()
    visit_id, _ = _enter_three_tree_visit(client, case_id)
    old_headers = {
        key: value
        for key, value in client.headers.items()
        if key.startswith("x-dream-")
    }
    old_epoch = int(old_headers["x-dream-lease-epoch"])
    old_fence = int(old_headers["x-dream-fence-token"])
    second = _same_account_client(client)

    denied = second.post(
        "/api/v50/dream/visits",
        json=_visit_request(case_id, client_instance_id="dream-test-client-secondary"),
    )
    takeover = second.post(
        f"/api/v50/dream/visits/{visit_id}/control/takeover",
        json={"client_instance_id": "dream-test-client-secondary"},
    )
    assert denied.status_code == 409
    assert denied.json()["detail"] == "dream_control_takeover_required"
    assert takeover.status_code == 200, takeover.text
    takeover_payload = takeover.json()
    assert takeover_payload["visit_id"] == visit_id
    assert takeover_payload["control_lease"]["lease_epoch"] == old_epoch + 1
    assert takeover_payload["control_lease"]["fence_token"] == old_fence + 1
    _activate_dream_control(second, takeover_payload)

    stale = client.post(f"/api/v50/dream/visits/{visit_id}/control/heartbeat", json={})
    current = second.post(f"/api/v50/dream/visits/{visit_id}/control/heartbeat", json={})
    assert stale.status_code == 409
    assert stale.json()["detail"] == "dream_control_lease_superseded"
    assert current.status_code == 200


def test_suspend_recovery_clears_mirror_and_restores_only_safe_navigation() -> None:
    client, _, _, _, _, case_id = _dream_app()
    visit_id, encounter = _enter_three_tree_visit(client, case_id)
    scene_ref = encounter["trees"][0]["scene_ref"]
    assert client.post(
        f"/api/v50/dream/visits/{visit_id}/select-tree",
        json={"scene_ref": scene_ref},
    ).status_code == 200
    reveal = client.post(
        f"/api/v50/dream/visits/{visit_id}/trees/{scene_ref}/reveal",
        json={},
    ).json()
    opened = client.post(
        f"/api/v50/dream/visits/{visit_id}/mirror/open",
        json={
            "onecanvas_view_ref": reveal["onecanvas_view_ref"],
            "navigation": _navigation(client, x=54, y=73, camera_heading=18),
        },
    )
    assert opened.status_code == 200, opened.text

    suspended = client.post(
        f"/api/v50/dream/visits/{visit_id}/suspend",
        json={
            "navigation": _navigation(client, x=54, y=73, camera_heading=18),
            "recovery_sequence": 1,
        },
    )
    assert suspended.status_code == 200, suspended.text
    assert suspended.json()["runtime_state"] == "VISIT_SUSPENDED"
    assert suspended.json()["active_onecanvas_view_ref"] == ""

    recovered = client.post(f"/api/v50/dream/visits/{visit_id}/recover", json={})
    assert recovered.status_code == 200, recovered.text
    payload = recovered.json()
    assert payload["runtime_state"] == "LOCAL_MIST_REENTRY"
    assert payload["anchor_resolution"]["source"] == "recovery_checkpoint"
    assert payload["anchor_resolution"]["position"] == {"x": 54.0, "y": 73.0}
    assert payload["active_onecanvas_view_ref"] == ""


def test_departure_is_atomic_idempotent_and_next_visit_returns_from_anchor() -> None:
    client, _, store, _, user_id, case_id = _dream_app()
    visit_id, _ = _enter_three_tree_visit(client, case_id)
    checkpoint = client.post(
        f"/api/v50/dream/visits/{visit_id}/recovery/checkpoint",
        json={
            "navigation": _navigation(client, x=57, y=76, camera_heading=-12),
            "recovery_sequence": 1,
        },
    )
    assert checkpoint.status_code == 200, checkpoint.text
    intent = client.post(
        f"/api/v50/dream/visits/{visit_id}/departure/intent",
        json={"active": True},
    )
    assert intent.status_code == 200

    request = {
        "trigger": "SEMANTIC_EXIT",
        "navigation": _navigation(client, x=57, y=76, camera_heading=-12),
        "commit_sequence": 1,
    }
    first = client.post(f"/api/v50/dream/visits/{visit_id}/departure/commit", json=request)
    replay = client.post(f"/api/v50/dream/visits/{visit_id}/departure/commit", json=request)
    assert first.status_code == replay.status_code == 200
    assert first.json()["departure_commit_id"] == replay.json()["departure_commit_id"]
    assert replay.json()["idempotent_replay"] is True
    persisted = store.get_visit(visit_id=visit_id, owner_user_id=user_id)
    assert persisted is not None
    assert persisted.state.value == "COMPLETED"
    assert persisted.runtime_state.value == "DEPARTED"

    returned = client.post(
        "/api/v50/dream/visits",
        json=_visit_request(case_id, client_instance_id="dream-test-client-return"),
    )
    assert returned.status_code == 200, returned.text
    payload = returned.json()
    assert payload["visit_id"] != visit_id
    assert payload["is_return_visit"] is True
    assert payload["runtime_state"] == "LOCAL_MIST_REENTRY"
    assert payload["recovery_sequence"] == 1
    assert payload["anchor_resolution"]["source"] == "departure_anchor"
    assert payload["anchor_resolution"]["position"] == {"x": 57.0, "y": 76.0}


def test_spatial_departure_requires_real_boundary_crossing() -> None:
    client, _, _, _, _, case_id = _dream_app()
    visit_id, _ = _enter_three_tree_visit(client, case_id)
    assert client.post(
        f"/api/v50/dream/visits/{visit_id}/departure/intent",
        json={"active": True},
    ).status_code == 200
    base = {
        "trigger": "SPATIAL_BOUNDARY",
        "navigation": _navigation(client, x=92, y=84),
        "commit_sequence": 1,
    }
    blocked = client.post(
        f"/api/v50/dream/visits/{visit_id}/departure/commit",
        json={**base, "boundary_position": {"x": 94, "y": 85}},
    )
    committed = client.post(
        f"/api/v50/dream/visits/{visit_id}/departure/commit",
        json={**base, "boundary_position": {"x": 97, "y": 90}},
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"] == "dream_spatial_departure_boundary_not_crossed"
    assert committed.status_code == 200, committed.text
    assert committed.json()["trigger"] == "SPATIAL_BOUNDARY"

    returned = client.post(
        "/api/v50/dream/visits",
        json=_visit_request(case_id, client_instance_id="dream-test-spatial-return"),
    )
    assert returned.status_code == 200, returned.text
    resolution = returned.json()["anchor_resolution"]
    assert resolution["source"] == "departure_anchor"
    assert resolution["position"] == {"x": 87.5, "y": 84.0}
    assert resolution["fallback_reason"] == "anchor_mapped_to_nearest_safe_geometry"


def test_guest_anchor_moves_only_after_explicit_consent_and_is_one_time() -> None:
    client, _, store, _, _, case_id = _dream_app()
    capability = "guest-anchor-capability-that-is-long-and-unguessable"
    capability_hash = hashlib.sha256(capability.encode()).hexdigest()
    now = datetime.now(timezone.utc)
    source = DreamDepartureAnchor(
        anchor_id="dream-departure-anchor-guest-source",
        viewer_id="guest:browser-local-01",
        case_namespace="guest:dream-navigation",
        world_space_ref="dream-world:canonical-grove:v1",
        last_stable_forest_position=DreamWorldPosition(x=61, y=78),
        camera_heading=22,
        geometry_version="dream-grove-geometry.v1",
        source_visit_id="dream-guest-visit-01",
        visit_sequence=1,
        commit_sequence=1,
        anchor_version=1,
        departure_world_time=1,
        committed_at=now,
        departure_commit_id="dream-guest-departure-01",
        departure_trigger="SEMANTIC_EXIT",
        idempotency_key="guest-anchor-idempotency-source-01",
        migration_status="available",
        migration_capability_hash=capability_hash,
    )
    store.save_guest_departure_anchor(source)

    migrated = client.post(
        "/api/v50/dream/anchors/migrate-guest",
        json={
            "case_id": case_id,
            "guest_anchor_capability": capability,
            "accepted": True,
        },
    )
    repeated = client.post(
        "/api/v50/dream/anchors/migrate-guest",
        json={
            "case_id": case_id,
            "guest_anchor_capability": capability,
            "accepted": True,
        },
    )
    assert migrated.status_code == 200, migrated.text
    payload = migrated.json()
    assert payload["target_anchor"]["last_stable_forest_position"] == {"x": 61.0, "y": 78.0}
    assert payload["target_anchor"]["case_namespace"].startswith("life-case:")
    assert repeated.status_code == 409
    assert repeated.json()["detail"] == "dream_guest_anchor_unavailable"


def test_canonical_abu_projection_contains_only_public_world_state() -> None:
    client, _, _, _, _, case_id = _dream_app()
    created = client.post("/api/v50/dream/visits", json=_visit_request(case_id))
    assert created.status_code == 200
    abu = created.json()["canonical_abu"]
    assert abu == {
        "schema_version": "deepbazi.canonical_abu_public_projection.v1",
        "canonical_abu_ref": "canonical-being:abu",
        "identity_mode": "CANONICAL_UNIQUE_BEING",
        "world_space_ref": "dream-world:canonical-grove:v1",
        "public_position": {"x": 47.0, "y": 76.0},
        "public_action": "resting",
        "world_state_version": "canonical-abu-world-state.v1",
        "private_content_included": False,
    }


def test_canonical_abu_can_render_continuous_public_follow_motion() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root / "apps/product/experience_shell/src/dream_runtime.ts").read_text(
        encoding="utf-8"
    )
    styles = (root / "apps/product/static/experience/styles.css").read_text(
        encoding="utf-8"
    )

    assert "if (this.canonicalAbu) return false;" not in source
    assert 'main.dataset.abuMotion = this.abuFollowing ? "walking" : "resting";' in source
    assert 'this.abuFacing = dx < 0 ? "left" : "right"' in source
    assert "scaleX(var(--abu-facing))" in styles


def test_three_tree_desktop_layout_keeps_the_far_resident_inside_the_grove() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")

    assert "residents[0], x: 56, y: 48" in source
    assert "residents[1], x: 81, y: 27" in source


def test_client_retries_pending_departure_before_resuming_the_forest() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")

    pending_check = 'const pendingDeparture = this.readPendingDeparture();'
    retry = 'await this.resumePendingDeparture();'
    scene_entry = 'this.acceptVisit(await enterDreamVisit(this.visit.visit_id));'
    assert pending_check in source
    assert source.index(pending_check) < source.index(retry) < source.index(scene_entry)


def test_restored_visit_renews_control_before_waiting_for_interval() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")
    start_loops = source.split(
        "private startControlLoops",
        1,
    )[1].split(
        "private stopControlLoops",
        1,
    )[0]

    assert start_loops.index("void this.heartbeat();") < start_loops.index(
        "window.setInterval(() => void this.heartbeat()"
    )


def test_entry_takeover_resumes_the_authoritative_visit_without_an_empty_visit_id() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")

    takeover = source.split("private renderTakeover", 1)[1].split(
        "private applyServerNavigationState",
        1,
    )[0]
    assert "routeVisitId" in takeover
    assert "await takeoverDreamVisit(routeVisitId)" in takeover
    assert 'await createDreamVisit("", true)' in takeover


def test_visibility_recovery_replays_an_event_that_arrives_during_suspend() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")

    assert "private visibilityReconcilePending = false;" in source
    assert "this.visibilityReconcilePending = true;" in source
    assert "document.visibilityState !== requestedVisibility" in source
    assert "queueMicrotask(() => void this.handleVisibilityChange());" in source
