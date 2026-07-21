from __future__ import annotations

from datetime import datetime, timezone

from experience.canvas import create_temporal_sandbox
from experience.experiments import create_sandbox_state
from experience.lab import (
    MingliLabSession,
    exploration_from_lab_session,
    issue_lab_session,
    update_lab_session,
)
from experience.workspace import (
    CaseWorkspaceState,
    build_case_workspace_state,
    compile_case_workspace,
)
from product.agent_case_store import MemoryAgentCaseStore
from product.canonical_scene import CanonicalSceneOwner
from product.theater_experiment import _snapshot_from_case_row
from test_v50_mingli_structural_experiment import _case_payload


def _projection(*, role: str = "member"):
    case_id = "case-framework-lab"
    user_id = "user-framework-lab"
    store = MemoryAgentCaseStore()
    payload = _case_payload(case_id)
    store.save(case_id=case_id, user_id=user_id, profile_id=None, payload=payload)
    owner = CanonicalSceneOwner(case_store=store)
    return (
        owner.issue_projection(
            case_id=case_id,
            participant_id=user_id,
            account_role=role,
            projection_kind="workspace",
        ),
        owner.issue_scene(
            case_id=case_id,
            participant_id=user_id,
            account_role=role,
        ),
        payload,
    )


def test_case_workspace_binds_one_scene_and_drops_undisclosed_selection() -> None:
    projection, _, _ = _projection(role="member")
    state = build_case_workspace_state(case_id="case-framework-lab").model_copy(update={
        "current_surface": "mingli_lab",
        "selected_semantic_refs": [projection.semantic_refs[0], "hidden:research-only"],
        "lab_session_id": "must-clear",
        "lab_dirty": True,
    })

    workspace = compile_case_workspace(state=state, projection=projection)

    assert workspace.state.scene_id == projection.scene_identity.scene_id
    assert workspace.state.scene_source_hash == projection.scene_identity.source_hash
    assert workspace.state.current_surface == "overview"
    assert workspace.state.selected_semantic_refs == [projection.semantic_refs[0]]
    assert workspace.state.lab_session_id == ""
    assert workspace.state.lab_dirty is False
    assert "mingli_lab" not in workspace.allowed_surfaces
    assert workspace.writes_life_case is False


def test_legacy_workspace_state_upgrades_without_becoming_a_second_owner() -> None:
    legacy = {
        "version": "deepbazi.workspace_state.v1",
        "workspace_id": "workspace-legacy",
        "case_id": "case-framework-lab",
        "selected_period": "2026-07",
        "system_period": "2026-07",
        "active_domain": "whole_chart",
        "active_mode": "member",
        "language": "zh",
        "expanded_sections": ["baseline"],
        "conversation_focus": "overview",
        "draft_input": "",
        "updated_at": "2026-07-21T00:00:00+00:00",
    }

    state = CaseWorkspaceState.model_validate(legacy)

    assert state.schema_version == "deepbazi.case_workspace_state.v2"
    assert state.scene_id == ""
    assert state.current_surface == "overview"


def test_professional_workspace_and_lab_session_share_scene_identity() -> None:
    projection, _, _ = _projection(role="practitioner")
    workspace = compile_case_workspace(
        state=build_case_workspace_state(case_id="case-framework-lab").model_copy(
            update={"current_surface": "mingli_lab"}
        ),
        projection=projection,
    )
    session = issue_lab_session(
        projection=projection,
        session_id="lab-session-framework",
        participant_run_id="participant-framework",
        experiment_kind="temporal_hypothesis",
        base_snapshot_ref="snapshot-framework",
        now=datetime(2026, 7, 21, tzinfo=timezone.utc),
    )

    assert workspace.state.scene_id == session.scene_id
    assert workspace.state.scene_source_hash == session.scene_source_hash
    assert "mingli_lab" in workspace.allowed_surfaces
    assert session.writes_chart is False
    assert session.writes_life_case is False
    assert session.promotes_candidate is False


def test_temporal_and_mechanism_sandboxes_use_one_lab_session_contract() -> None:
    projection, scene, payload = _projection(role="member")
    temporal_session = issue_lab_session(
        projection=projection,
        session_id="lab-temporal",
        participant_run_id="participant-temporal",
        experiment_kind="temporal_hypothesis",
        base_snapshot_ref="snapshot-temporal",
        now=datetime(2026, 7, 21, tzinfo=timezone.utc),
    )
    temporal = create_temporal_sandbox(
        sandbox_session_id=temporal_session.session_id,
        base_snapshot_id=temporal_session.base_snapshot_ref,
        lab_session=temporal_session,
    )
    snapshot = _snapshot_from_case_row(
        case_id="case-framework-lab",
        row=payload,
        scene=scene,
    )
    mechanism = create_sandbox_state(
        participant_run_id="participant-mechanism",
        snapshot=snapshot,
    )

    assert isinstance(temporal.lab_session, MingliLabSession)
    assert isinstance(mechanism.lab_session, MingliLabSession)
    assert temporal.lab_session.scene_id == projection.scene_identity.scene_id
    assert mechanism.lab_session.scene_id == projection.scene_identity.scene_id
    assert temporal.writes_life_case is False
    assert mechanism.writes_life_case is False


def test_lab_evidence_preserves_snapshot_reference_and_deterministic_hash() -> None:
    projection, _, _ = _projection(role="practitioner")
    snapshot_ref = "snapshot:" + "long-reference-" * 12
    session = issue_lab_session(
        projection=projection,
        session_id="lab-evidence",
        participant_run_id="participant-evidence",
        experiment_kind="temporal_hypothesis",
        base_snapshot_ref=snapshot_ref,
        now=datetime(2026, 7, 21, tzinfo=timezone.utc),
    )
    restored = update_lab_session(session, status="restored", now=session.updated_at)

    exploration = exploration_from_lab_session(
        session=restored,
        topic_id="temporal-observation",
        selected_node_ids=[],
        result_refs=[],
        observations=["只记录实验观察"],
        restored_original=True,
    )

    assert exploration.base_snapshot_ref == snapshot_ref
    assert len(exploration.base_snapshot_hash) == 64
    assert exploration.base_snapshot_hash == exploration_from_lab_session(
        session=restored,
        topic_id="temporal-observation",
        selected_node_ids=[],
        result_refs=[],
        observations=["只记录实验观察"],
        restored_original=True,
    ).base_snapshot_hash


def test_theater_snapshot_uses_scene_not_legacy_cognitive_record() -> None:
    _, scene, payload = _projection(role="member")
    payload.pop("record", None)

    snapshot = _snapshot_from_case_row(
        case_id="case-framework-lab",
        row=payload,
        scene=scene,
    )

    assert snapshot.scene_id == scene.identity.scene_id
    assert snapshot.scene_source_hash == scene.identity.source_hash
    assert snapshot.disclosure_hash == scene.role_disclosure.disclosure_hash
    assert snapshot.approved_paths[0].path_ref == scene.path_assertions[0].path_ref
