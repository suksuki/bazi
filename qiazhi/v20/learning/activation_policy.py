from __future__ import annotations

from v20.learning.artifact_registry import ArtifactRecord


def activation_policy(artifact: ArtifactRecord) -> dict[str, object]:
    return {
        "ok": True,
        "artifact_id": artifact.artifact_id,
        "decision": "active",
        "guardrails": ["ACTIVE_POLICY_ITERATION", "ROLLBACK_RECORDED", "NO_CORE_TRUTH_MUTATION"],
    }
