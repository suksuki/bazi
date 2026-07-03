from __future__ import annotations

from v30.admin.contracts import AdminPermissionGrant, AdminRole


ADMIN_ROLE_ORDER: tuple[AdminRole, ...] = (
    "viewer",
    "analyst",
    "practitioner",
    "trainer",
    "validator",
    "publisher",
    "owner",
)

ROLE_PERMISSIONS: dict[AdminRole, tuple[str, ...]] = {
    "viewer": (
        "admin.manifest.read",
        "runtime_trace.read",
        "module_audit.read",
    ),
    "analyst": (
        "admin.manifest.read",
        "runtime_trace.read",
        "module_audit.read",
        "signal_registry.read",
        "evaluation.read",
        "validation.read",
    ),
    "practitioner": (
        "admin.manifest.read",
        "runtime_trace.read",
        "module_audit.read",
        "signal_registry.read",
        "evaluation.read",
        "golden_case.label",
        "practitioner_feedback.write_overlay",
    ),
    "trainer": (
        "admin.manifest.read",
        "runtime_trace.read",
        "module_audit.read",
        "signal_registry.read",
        "evaluation.read",
        "training.read",
        "training.job.run",
        "training.impact.read",
    ),
    "validator": (
        "admin.manifest.read",
        "runtime_trace.read",
        "module_audit.read",
        "signal_registry.read",
        "evaluation.read",
        "validation.read",
        "validation.job.run",
        "validation.gate.read",
        "corpus_518k.job.run",
    ),
    "publisher": (
        "admin.manifest.read",
        "runtime_trace.read",
        "module_audit.read",
        "signal_registry.read",
        "evaluation.read",
        "training.read",
        "training.impact.read",
        "validation.read",
        "validation.gate.read",
        "config.draft.write",
        "config.approve",
        "release.publish",
        "release.rollback",
    ),
    "owner": (
        "admin.manifest.read",
        "runtime_trace.read",
        "module_audit.read",
        "signal_registry.read",
        "evaluation.read",
        "evaluation.job.run",
        "golden_case.label",
        "training.read",
        "training.job.run",
        "training.impact.read",
        "validation.read",
        "validation.job.run",
        "validation.gate.read",
        "corpus_518k.job.run",
        "config.draft.write",
        "config.approve",
        "release.publish",
        "release.rollback",
        "admin.audit.read",
    ),
}


def normalize_admin_role(role: str | None) -> AdminRole:
    value = str(role or "viewer").strip()
    if value in ROLE_PERMISSIONS:
        return value  # type: ignore[return-value]
    return "viewer"


def build_admin_permission_grant(role: str | None) -> AdminPermissionGrant:
    normalized = normalize_admin_role(role)
    permissions = sorted(set(ROLE_PERMISSIONS[normalized]))
    return AdminPermissionGrant(
        role=normalized,
        permissions=permissions,
        can_publish="release.publish" in permissions,
        can_run_heavy_jobs=bool({"corpus_518k.job.run", "validation.job.run", "training.job.run"} & set(permissions)),
        can_mutate_runtime_policy="release.publish" in permissions or "release.rollback" in permissions,
        chart_fact_mutation_allowed=False,
    )


def admin_can(role: str | None, permission: str) -> bool:
    return permission in set(ROLE_PERMISSIONS[normalize_admin_role(role)])
