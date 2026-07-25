from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from experience.canvas_contracts import (
    CanvasAction,
    CanvasCompileError,
    CanvasSandboxMutation,
    MingliCanvasCompileInput,
    TemporalSandboxState,
)
from experience.compiler import canonical_hash
from experience.lab import MingliLabSession, update_lab_session


def load_canvas_compile_input(path: str | Path) -> MingliCanvasCompileInput:
    return MingliCanvasCompileInput.model_validate_json(Path(path).read_text(encoding="utf-8"))


def create_temporal_sandbox(
    *,
    sandbox_session_id: str,
    base_snapshot_id: str,
    luck_layer_id: str = "",
    year_layer_id: str = "",
    lab_session: MingliLabSession | None = None,
) -> TemporalSandboxState:
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return TemporalSandboxState(
        lab_session=lab_session or MingliLabSession(
            session_id=sandbox_session_id,
            case_ref="synthetic-fixture",
            scene_id=f"scene-fixture-{canonical_hash({'base': base_snapshot_id})[:20]}",
            scene_source_hash=canonical_hash({"base_snapshot_id": base_snapshot_id}),
            disclosure_hash="0" * 64,
            experiment_kind="temporal_hypothesis",
            base_snapshot_ref=base_snapshot_id,
            source_mode="synthetic_fixture",
            synthetic_fixture_ref=base_snapshot_id,
            created_at=epoch,
            updated_at=epoch,
        ),
        base_luck_layer_id=luck_layer_id,
        base_year_layer_id=year_layer_id,
        selected_luck_layer_id=luck_layer_id,
        selected_year_layer_id=year_layer_id,
    )


def apply_canvas_action(
    *,
    source: MingliCanvasCompileInput,
    sandbox: TemporalSandboxState,
    action: CanvasAction,
) -> TemporalSandboxState:
    if action.action_type == "restore":
        return restore_temporal_sandbox(sandbox)
    if sandbox.status not in {"active", "modified"}:
        raise CanvasCompileError("sandbox_action_requires_active_state")
    layers = {item.layer_id: item for item in source.temporal_layers}
    target = layers.get(action.target_layer_id) if action.target_layer_id else None
    if action.action_type != "clear_year" and target is None:
        raise CanvasCompileError(f"sandbox_action_missing_layer:{action.target_layer_id}")
    if action.action_type == "set_luck" and target and target.layer_type != "luck":
        raise CanvasCompileError("sandbox_action_luck_requires_luck_layer")
    if action.action_type in {"set_year", "replace_year"} and target and target.layer_type != "year":
        raise CanvasCompileError("sandbox_action_year_requires_year_layer")

    before = sandbox.selected_luck_layer_id if action.action_type == "set_luck" else sandbox.selected_year_layer_id
    after = "" if action.action_type == "clear_year" else action.target_layer_id
    field_path = "temporal.luck" if action.action_type == "set_luck" else "temporal.year"
    source_mode: Literal["derived", "hypothetical"] = (
        "hypothetical" if target and target.layer_mode == "hypothetical" else "derived"
    )
    mutation = CanvasSandboxMutation(
        mutation_id=f"mutation-{canonical_hash({'session': sandbox.sandbox_session_id, 'revision': sandbox.revision + 1, 'action': action.model_dump(mode='json')})[:24]}",
        action_type=action.action_type,
        field_path=field_path,
        before_layer_id=before,
        after_layer_id=after,
        base_snapshot_id=sandbox.base_snapshot_id,
        source_mode=source_mode,
        source_refs=[action.source_ref, *(target.source_refs if target else [])],
    )
    updates: dict[str, Any] = {
        "lab_session": update_lab_session(
            sandbox.lab_session,
            status="modified",
            now=sandbox.lab_session.updated_at,
        ),
        "mutations": [*sandbox.mutations, mutation],
        "current_canvas_spec_id": "",
        "current_diff_spec_id": "",
    }
    if action.action_type == "set_luck":
        updates["selected_luck_layer_id"] = after
    else:
        updates["selected_year_layer_id"] = after
    return sandbox.model_copy(update=updates)


def restore_temporal_sandbox(sandbox: TemporalSandboxState) -> TemporalSandboxState:
    if sandbox.status not in {"active", "modified"}:
        raise CanvasCompileError("sandbox_restore_requires_active_state")
    return sandbox.model_copy(update={
        "lab_session": update_lab_session(
            sandbox.lab_session,
            status="restored",
            now=sandbox.lab_session.updated_at,
        ),
        "selected_luck_layer_id": sandbox.base_luck_layer_id,
        "selected_year_layer_id": sandbox.base_year_layer_id,
        "current_canvas_spec_id": "",
        "current_diff_spec_id": "",
    })



