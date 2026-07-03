from __future__ import annotations

import pytest

from v30.admin import (
    ADMIN_API_PREFIX,
    AdminAuditEvent,
    AdminVersionedConfigRecord,
    admin_can,
    build_admin_control_plane_manifest,
    build_admin_permission_grant,
)
from v30.api.app import create_app


def test_admin_control_plane_manifest_defines_workbenches_and_boundaries() -> None:
    manifest = build_admin_control_plane_manifest(role="trainer")

    assert manifest.version == "v30.admin_control_plane.v1"
    assert manifest.api_prefix == "/api/admin/v30"
    assert manifest.legacy_api_prefix == "/api/v30/admin"
    assert manifest.role_permissions.role == "trainer"
    assert {row.key for row in manifest.workbenches} == {
        "runtime_trace",
        "module_audit",
        "evaluation",
        "training",
        "validation",
        "config_release",
    }
    assert manifest.job_policy["heavy_tasks_must_use_job"] is True
    assert manifest.acceptance["user_ui_shows_training_artifacts"] is False
    assert manifest.user_runtime_mutation_allowed is False
    assert manifest.chart_fact_mutation_allowed is False
    assert any(row.route == f"{ADMIN_API_PREFIX}/evaluation/training-spine" for row in manifest.route_aliases)
    assert any(row.route == f"{ADMIN_API_PREFIX}/training/orchestrator/run" and row.job_required for row in manifest.route_aliases)


def test_admin_rbac_separates_readers_trainers_validators_and_publishers() -> None:
    viewer = build_admin_permission_grant("viewer")
    trainer = build_admin_permission_grant("trainer")
    validator = build_admin_permission_grant("validator")
    publisher = build_admin_permission_grant("publisher")

    assert "runtime_trace.read" in viewer.permissions
    assert "training.job.run" not in viewer.permissions
    assert "training.job.run" in trainer.permissions
    assert "corpus_518k.job.run" in validator.permissions
    assert publisher.can_publish is True
    assert publisher.can_mutate_runtime_policy is True
    assert publisher.chart_fact_mutation_allowed is False
    assert admin_can("owner", "release.rollback") is True
    assert admin_can("analyst", "release.publish") is False


def test_versioned_config_requires_validation_before_active() -> None:
    active = AdminVersionedConfigRecord(
        config_type="policy_weight",
        version_id="policy-weight.v30.test",
        status="active",
        validation_run_ids=["eval-spine-run"],
        runtime_active=True,
    )

    assert active.runtime_active is True
    assert active.chart_fact_mutation_allowed is False
    with pytest.raises(ValueError):
        AdminVersionedConfigRecord(
            config_type="policy_weight",
            version_id="policy-weight.v30.bad",
            status="active",
            runtime_active=True,
        )


def test_admin_audit_policy_write_requires_reason_and_validation() -> None:
    event = AdminAuditEvent(
        event_id="audit-1",
        actor_id="admin",
        role="publisher",
        action="release.publish",
        risk="high",
        reason="passed evaluation spine",
        validation_run_id="eval-spine-run",
        production_policy_write=True,
    )

    assert event.production_policy_write is True
    with pytest.raises(ValueError):
        AdminAuditEvent(
            event_id="audit-2",
            actor_id="admin",
            role="publisher",
            action="release.publish",
            risk="high",
            production_policy_write=True,
        )


def test_admin_control_plane_routes_are_available_and_read_only() -> None:
    local_app = create_app()
    manifest_route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/admin/v30/control-plane/manifest"
    )
    evaluation_route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/admin/v30/evaluation/training-spine"
    )
    plans_route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/admin/v30/training/orchestrator/plans"
    )

    manifest = manifest_route.endpoint(role="validator")
    evaluation = evaluation_route.endpoint(include_phase2=False)
    plans = plans_route.endpoint()

    assert manifest["role"] == "validator"
    assert manifest["job_policy"]["page_request_may_run_heavy_task"] is False
    assert evaluation["status"] == "passed"
    assert evaluation["policy_boundary"]["production_policy_write_allowed"] is False
    assert any(row["plan_id"] == "evaluation_spine_quality_gate" for row in plans["plans"])
