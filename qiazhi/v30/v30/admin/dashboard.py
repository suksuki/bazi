from __future__ import annotations

from v30.admin.contracts import (
    ADMIN_API_PREFIX,
    LEGACY_ADMIN_API_PREFIX,
    AdminControlPlaneManifest,
    AdminRouteAlias,
    AdminWorkbench,
)
from v30.admin.permissions import build_admin_permission_grant


def build_admin_control_plane_manifest(*, role: str = "viewer") -> AdminControlPlaneManifest:
    permission_grant = build_admin_permission_grant(role)
    return AdminControlPlaneManifest(
        role=permission_grant.role,
        role_permissions=permission_grant,
        workbenches=_workbenches(),
        route_aliases=_route_aliases(),
        versioned_config_types=[
            "bazi_ruleset",
            "portrait_ruleset",
            "path_ruleset",
            "ziwei_standard",
            "ziwei_ruleset",
            "reality_probe_template",
            "hidden_attribute_schema",
            "advice_plan_template",
            "llm_prompt_profile",
            "llm_acceptance_rule",
            "policy_weight",
            "assertion_threshold",
        ],
        migration_phases=[
            {
                "phase": "phase1_logical_isolation",
                "status": "active",
                "scope": "same_repo_same_service_admin_namespace_and_contracts",
            },
            {
                "phase": "phase2_admin_frontend_isolation",
                "status": "started",
                "scope": "standalone admin frontend service on port 9031 proxies runtime and admin api",
            },
            {
                "phase": "phase3_admin_api_namespace_migration",
                "status": "started",
                "scope": "migrate legacy /api/v30/admin routes to /api/admin/v30 aliases",
            },
            {
                "phase": "phase4_worker_isolation",
                "status": "planned",
                "scope": "heavy training validation replay jobs run outside runtime request threads",
            },
            {
                "phase": "phase5_admin_service_isolation",
                "status": "planned",
                "scope": "admin api and worker can deploy independently",
            },
        ],
        job_policy={
            "version": "v30.admin_job_policy.v1",
            "heavy_tasks_must_use_job": True,
            "heavy_task_types": [
                "training",
                "validation",
                "replay",
                "corpus_518k",
                "before_after_diff",
                "llm_acceptance_batch",
                "golden_case_regression",
            ],
            "page_request_may_run_heavy_task": False,
            "artifact_store_required": True,
            "boundary": "admin_jobs_submit_and_poll_workers_without_blocking_user_runtime",
        },
        data_boundary={
            "version": "v30.admin_data_boundary.v1",
            "readonly_observation": ["signal_registry", "module_audit", "decision_trace", "llm_acceptance", "reading_replay"],
            "draft_config": ["ruleset", "weights", "ziwei_standard", "probe_template", "prompt_profile", "advice_template"],
            "published_config": ["active_ruleset_version", "active_weight_version", "active_prompt_version"],
            "publish_flow": ["draft", "validate", "review", "publish", "runtime"],
            "direct_runtime_mutation_allowed": False,
        },
        acceptance={
            "user_ui_shows_training_artifacts": False,
            "admin_namespace_started": True,
            "admin_manifest_available": True,
            "heavy_jobs_use_job_runner": True,
            "versioned_config_contract_defined": True,
            "publish_audit_required": True,
        },
    )


def _workbenches() -> list[AdminWorkbench]:
    return [
        AdminWorkbench(
            key="runtime_trace",
            label="Runtime Trace",
            purpose="查看单次测算的输入、ChartContext、Engine outputs、Decision trace、LLM acceptance 和 reading surface。",
            primary_resources=["reading_trace", "production_audit", "decision_workbench_quality"],
            default_permission="runtime_trace.read",
        ),
        AdminWorkbench(
            key="module_audit",
            label="Module Audit",
            purpose="查看模块产出责任、Signal Registry、下游消费者和用户侧影响。",
            primary_resources=["signal_registry", "module_audit", "production_sidecar"],
            default_permission="module_audit.read",
        ),
        AdminWorkbench(
            key="evaluation",
            label="Evaluation",
            purpose="管理 Golden Cases、ExpectedVerdict、ForbiddenAssertions、Advice/Probe 评测和回归评测。",
            primary_resources=["evaluation_case_spec", "evaluation_training_spine", "golden_cases"],
            default_permission="evaluation.read",
        ),
        AdminWorkbench(
            key="training",
            label="Training",
            purpose="运行训练任务、查看 Training Impact、before/after verdict diff、策略候选和回滚。",
            primary_resources=["training_orchestrator", "training_impact", "policy_lineage"],
            default_permission="training.read",
        ),
        AdminWorkbench(
            key="validation",
            label="Validation / Gate",
            purpose="运行 synthetic、518K、LLM boundary、Ziwei golden case 和 release gate。",
            primary_resources=["synthetic_validation", "corpus_518k", "readiness_matrix", "release_gate"],
            default_permission="validation.read",
        ),
        AdminWorkbench(
            key="config_release",
            label="Config / Release",
            purpose="管理规则、权重、prompt、紫微标准、probe 模板、advice 模板的版本发布和回滚。",
            primary_resources=["versioned_config", "release_gate", "audit_log"],
            default_permission="release.publish",
        ),
    ]


def _route_aliases() -> list[AdminRouteAlias]:
    return [
        AdminRouteAlias(
            method="GET",
            route=f"{ADMIN_API_PREFIX}/control-plane/manifest",
            workbench="config_release",
            permission="admin.manifest.read",
        ),
        AdminRouteAlias(
            method="GET",
            route=f"{ADMIN_API_PREFIX}/readings/{{reading_id}}/trace",
            legacy_route=f"{LEGACY_ADMIN_API_PREFIX}/runs/{{reading_id}}/trace",
            workbench="runtime_trace",
            permission="runtime_trace.read",
        ),
        AdminRouteAlias(
            method="GET",
            route=f"{ADMIN_API_PREFIX}/readings/{{reading_id}}/production-audit",
            legacy_route="/api/v30/readings/{reading_id}/production-audit",
            workbench="module_audit",
            permission="module_audit.read",
        ),
        AdminRouteAlias(
            method="GET",
            route=f"{ADMIN_API_PREFIX}/readings/{{reading_id}}/decision-workbench-quality",
            legacy_route=f"{LEGACY_ADMIN_API_PREFIX}/readings/{{reading_id}}/decision-workbench-quality",
            workbench="runtime_trace",
            permission="runtime_trace.read",
        ),
        AdminRouteAlias(
            method="GET",
            route=f"{ADMIN_API_PREFIX}/evaluation/training-spine",
            legacy_route=f"{LEGACY_ADMIN_API_PREFIX}/evaluation/training-spine",
            workbench="evaluation",
            permission="evaluation.read",
        ),
        AdminRouteAlias(
            method="GET",
            route=f"{ADMIN_API_PREFIX}/training/orchestrator/plans",
            legacy_route=f"{LEGACY_ADMIN_API_PREFIX}/training/orchestrator/plans",
            workbench="training",
            permission="training.read",
        ),
        AdminRouteAlias(
            method="POST",
            route=f"{ADMIN_API_PREFIX}/training/orchestrator/run",
            legacy_route=f"{LEGACY_ADMIN_API_PREFIX}/training/orchestrator/run",
            workbench="training",
            permission="training.job.run",
            risk="medium",
            job_required=True,
        ),
        AdminRouteAlias(
            method="GET",
            route=f"{ADMIN_API_PREFIX}/training/orchestrator/status",
            legacy_route=f"{LEGACY_ADMIN_API_PREFIX}/training/orchestrator/status",
            workbench="training",
            permission="training.read",
        ),
        AdminRouteAlias(
            method="GET",
            route=f"{ADMIN_API_PREFIX}/training/orchestrator/diff",
            legacy_route=f"{LEGACY_ADMIN_API_PREFIX}/training/orchestrator/diff",
            workbench="training",
            permission="training.impact.read",
        ),
        AdminRouteAlias(
            method="GET",
            route=f"{ADMIN_API_PREFIX}/validation/artifacts",
            legacy_route=f"{LEGACY_ADMIN_API_PREFIX}/validation/artifacts",
            workbench="validation",
            permission="validation.read",
        ),
    ]
