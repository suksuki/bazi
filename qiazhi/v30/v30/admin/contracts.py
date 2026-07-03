from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from v30.contracts import V30Model


ADMIN_CONTROL_PLANE_VERSION = "v30.admin_control_plane.v1"
ADMIN_API_PREFIX = "/api/admin/v30"
LEGACY_ADMIN_API_PREFIX = "/api/v30/admin"

AdminRole = Literal["viewer", "analyst", "practitioner", "trainer", "validator", "publisher", "owner"]
AdminWorkbenchKey = Literal[
    "runtime_trace",
    "module_audit",
    "evaluation",
    "training",
    "validation",
    "config_release",
]
AdminOperationRisk = Literal["low", "medium", "high", "critical"]
VersionedConfigStatus = Literal["draft", "validating", "approved", "active", "archived", "rolled_back"]


class AdminPermissionGrant(V30Model):
    version: str = "v30.admin_permission_grant.v1"
    role: AdminRole
    permissions: list[str] = Field(default_factory=list)
    can_publish: bool = False
    can_run_heavy_jobs: bool = False
    can_mutate_runtime_policy: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "admin_permission_grant_controls_control_plane_actions_not_chart_facts"

    @model_validator(mode="after")
    def _no_chart_fact_mutation(self) -> "AdminPermissionGrant":
        if self.chart_fact_mutation_allowed:
            raise ValueError("Admin permissions cannot mutate chart facts")
        return self


class AdminWorkbench(V30Model):
    version: str = "v30.admin_workbench.v1"
    key: AdminWorkbenchKey
    label: str
    purpose: str
    primary_resources: list[str] = Field(default_factory=list)
    default_permission: str
    job_required_for_heavy_actions: bool = True
    user_surface_visible: bool = False
    runtime_mutation_allowed: bool = False
    chart_fact_mutation_allowed: bool = False

    @model_validator(mode="after")
    def _workbench_is_control_plane_only(self) -> "AdminWorkbench":
        if self.user_surface_visible:
            raise ValueError("Admin workbench cannot be user-surface visible")
        if self.chart_fact_mutation_allowed:
            raise ValueError("Admin workbench cannot mutate chart facts")
        return self


class AdminRouteAlias(V30Model):
    version: str = "v30.admin_route_alias.v1"
    method: str
    route: str
    legacy_route: str = ""
    workbench: AdminWorkbenchKey
    permission: str
    risk: AdminOperationRisk = "low"
    job_required: bool = False
    runtime_mutation_allowed: bool = False
    production_policy_write_allowed: bool = False
    chart_fact_mutation_allowed: bool = False

    @model_validator(mode="after")
    def _route_boundary_is_safe(self) -> "AdminRouteAlias":
        if self.chart_fact_mutation_allowed:
            raise ValueError("Admin route aliases cannot mutate chart facts")
        if self.production_policy_write_allowed and self.risk not in {"high", "critical"}:
            raise ValueError("Production policy writes must be high or critical risk")
        return self


class AdminVersionedConfigRecord(V30Model):
    version: str = "v30.admin_versioned_config_record.v1"
    config_type: str
    version_id: str
    status: VersionedConfigStatus = "draft"
    created_by: str = ""
    approved_by: str = ""
    created_at: str = ""
    activated_at: str = ""
    validation_run_ids: list[str] = Field(default_factory=list)
    change_summary: str = ""
    rollback_target: str = ""
    runtime_active: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "versioned_config_moves_draft_validate_review_publish_without_mutating_chart_facts"

    @model_validator(mode="after")
    def _active_requires_approval(self) -> "AdminVersionedConfigRecord":
        if self.runtime_active and self.status != "active":
            raise ValueError("runtime_active requires active status")
        if self.status == "active" and not self.validation_run_ids:
            raise ValueError("active config requires validation_run_ids")
        if self.chart_fact_mutation_allowed:
            raise ValueError("versioned config cannot mutate chart facts")
        return self


class AdminAuditEvent(V30Model):
    version: str = "v30.admin_audit_event.v1"
    event_id: str
    actor_id: str
    role: AdminRole
    action: str
    risk: AdminOperationRisk = "low"
    before_ref: str = ""
    after_ref: str = ""
    reason: str = ""
    validation_run_id: str = ""
    created_at: str = ""
    production_policy_write: bool = False
    chart_fact_mutation_allowed: bool = False

    @model_validator(mode="after")
    def _dangerous_actions_need_reason_and_validation(self) -> "AdminAuditEvent":
        if self.chart_fact_mutation_allowed:
            raise ValueError("Admin audit event cannot allow chart fact mutation")
        if self.production_policy_write and (not self.reason or not self.validation_run_id):
            raise ValueError("Policy write audit requires reason and validation_run_id")
        return self


class AdminControlPlaneManifest(V30Model):
    version: str = ADMIN_CONTROL_PLANE_VERSION
    api_prefix: str = ADMIN_API_PREFIX
    legacy_api_prefix: str = LEGACY_ADMIN_API_PREFIX
    status: str = "phase1_logical_isolation"
    role: AdminRole = "viewer"
    role_permissions: AdminPermissionGrant
    workbenches: list[AdminWorkbench] = Field(default_factory=list)
    route_aliases: list[AdminRouteAlias] = Field(default_factory=list)
    versioned_config_types: list[str] = Field(default_factory=list)
    migration_phases: list[dict[str, object]] = Field(default_factory=list)
    job_policy: dict[str, object] = Field(default_factory=dict)
    data_boundary: dict[str, object] = Field(default_factory=dict)
    acceptance: dict[str, object] = Field(default_factory=dict)
    user_runtime_mutation_allowed: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "admin_control_plane_manifest_describes_admin_surface_without_mutating_runtime"

    @model_validator(mode="after")
    def _manifest_is_boundary_only(self) -> "AdminControlPlaneManifest":
        if self.user_runtime_mutation_allowed:
            raise ValueError("Admin manifest cannot mutate user runtime")
        if self.chart_fact_mutation_allowed:
            raise ValueError("Admin manifest cannot mutate chart facts")
        return self
