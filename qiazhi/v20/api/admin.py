from __future__ import annotations


def admin_api_scope() -> dict[str, object]:
    return {
        "version": "v20.admin_api_scope.v1",
        "allowed": ["knowledge_release", "artifact_registry", "promotion_gate"],
        "blocked": ["bypass_validation", "unreviewed_model_activation"],
    }
