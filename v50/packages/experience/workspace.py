from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, cast
from uuid import uuid4

from pydantic import Field, model_validator

from experience.canonical_scene import CanonicalProjectionEnvelope
from experience.contracts import ExperienceModel


WorkspaceSurface = Literal["overview", "onecanvas", "xiangfa", "theater", "mingli_lab"]
WorkspaceRole = Literal["guest", "member", "practitioner", "research"]


class CaseWorkspaceState(ExperienceModel):
    """Shared product selection state; it never owns Mingli cognition."""

    schema_version: Literal["deepbazi.case_workspace_state.v2"] = (
        "deepbazi.case_workspace_state.v2"
    )
    workspace_id: str
    case_id: str
    chart_version_id: str = ""
    life_case_version: str = ""
    scene_id: str = ""
    scene_source_hash: str = ""
    selected_period: str
    system_period: str
    active_domain: str = "whole_chart"
    active_mode: WorkspaceRole = "member"
    current_surface: WorkspaceSurface = "overview"
    selected_semantic_refs: list[str] = Field(default_factory=list)
    focused_path_ref: str = ""
    temporal_stage: Literal["natal", "luck", "annual"] = "natal"
    theater_timecode_ms: int = Field(default=0, ge=0)
    lab_session_id: str = ""
    lab_dirty: bool = False
    language: str = "zh"
    expanded_sections: list[str] = Field(default_factory=list)
    conversation_focus: str = "overview"
    draft_input: str = ""
    updated_at: str

    @model_validator(mode="before")
    @classmethod
    def upgrade_legacy_workspace_state(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        upgraded = dict(value)
        legacy_version = upgraded.pop("version", "")
        if legacy_version and legacy_version != "deepbazi.workspace_state.v1":
            raise ValueError("unsupported_legacy_workspace_state")
        return upgraded


class CaseWorkspaceEnvelope(ExperienceModel):
    """One product state bound to one role-filtered canonical scene."""

    schema_version: Literal["deepbazi.case_workspace_envelope.v1"] = (
        "deepbazi.case_workspace_envelope.v1"
    )
    state: CaseWorkspaceState
    projection: CanonicalProjectionEnvelope
    allowed_surfaces: list[WorkspaceSurface] = Field(min_length=1)
    creates_mingli_facts: Literal[False] = False
    creates_mingli_claims: Literal[False] = False
    writes_chart: Literal[False] = False
    writes_life_case: Literal[False] = False

    @model_validator(mode="after")
    def validate_scene_binding(self) -> "CaseWorkspaceEnvelope":
        if self.projection.projection_kind != "workspace":
            raise ValueError("case_workspace_requires_workspace_projection")
        identity = self.projection.scene_identity
        if (
            self.state.case_id != identity.case_ref
            or self.state.chart_version_id != identity.chart_version_id
            or self.state.life_case_version != identity.life_case_version
            or self.state.scene_id != identity.scene_id
            or self.state.scene_source_hash != identity.source_hash
        ):
            raise ValueError("case_workspace_scene_identity_mismatch")
        if self.state.current_surface not in self.allowed_surfaces:
            raise ValueError("case_workspace_surface_not_allowed")
        if not set(self.state.selected_semantic_refs).issubset(self.projection.semantic_refs):
            raise ValueError("case_workspace_selection_not_disclosed")
        return self


def build_case_workspace_state(
    *,
    case_id: str,
    selected_period: str | None = None,
    active_mode: WorkspaceRole = "member",
    active_domain: str = "whole_chart",
) -> CaseWorkspaceState:
    now = datetime.now(timezone.utc)
    system_period = now.strftime("%Y-%m")
    return CaseWorkspaceState(
        workspace_id=f"workspace-{uuid4().hex[:18]}",
        case_id=case_id,
        selected_period=_normalize_period_key(selected_period or system_period),
        system_period=system_period,
        active_mode=active_mode,
        active_domain=active_domain,
        updated_at=now.isoformat(),
    )


def select_case_workspace_period(
    *,
    workspace: CaseWorkspaceState,
    period_key: str,
) -> CaseWorkspaceState:
    return workspace.model_copy(update={
        "selected_period": _normalize_period_key(period_key),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


def compile_case_workspace(
    *,
    state: CaseWorkspaceState,
    projection: CanonicalProjectionEnvelope,
) -> CaseWorkspaceEnvelope:
    if projection.projection_kind != "workspace":
        raise ValueError("case_workspace_requires_workspace_projection")
    catalog: list[WorkspaceSurface] = [
        cast(WorkspaceSurface, item)
        for item in projection.payload.get("mode_catalog", [])
        if item in {"overview", "onecanvas", "xiangfa", "theater", "mingli_lab"}
    ]
    role = projection.role_disclosure.role
    if role not in {"practitioner", "research", "admin"}:
        catalog = [item for item in catalog if item != "mingli_lab"]
    if not catalog:
        catalog = ["overview"]
    selected = [ref for ref in state.selected_semantic_refs if ref in projection.semantic_refs]
    surface = state.current_surface if state.current_surface in catalog else "overview"
    identity = projection.scene_identity
    bound = state.model_copy(update={
        "case_id": identity.case_ref,
        "chart_version_id": identity.chart_version_id,
        "life_case_version": identity.life_case_version,
        "scene_id": identity.scene_id,
        "scene_source_hash": identity.source_hash,
        "active_mode": role if role != "admin" else "research",
        "current_surface": surface,
        "selected_semantic_refs": selected,
        "lab_session_id": state.lab_session_id if surface == "mingli_lab" else "",
        "lab_dirty": state.lab_dirty if surface == "mingli_lab" else False,
    })
    return CaseWorkspaceEnvelope(
        state=bound,
        projection=projection,
        allowed_surfaces=catalog,
    )


def _normalize_period_key(value: str) -> str:
    normalized = str(value).strip()
    try:
        datetime.strptime(normalized, "%Y-%m")
    except ValueError as exc:
        raise ValueError("invalid_period_key") from exc
    return normalized
