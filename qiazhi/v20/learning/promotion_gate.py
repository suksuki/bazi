from __future__ import annotations

from v20.learning.artifact_registry import ArtifactRecord


def promotion_gate(artifact: ArtifactRecord) -> dict[str, object]:
    ok = bool(artifact.decision_record_id and artifact.eval_report_id and artifact.production_eligible)
    return {
        "ok": ok,
        "artifact_id": artifact.artifact_id,
        "decision": "eligible_for_scoped_runtime_use" if ok else "blocked",
        "guardrails": ["PROMOTION_GATE_REQUIRED", "ROLLBACK_REQUIRED", "NO_CORE_TRUTH_MUTATION"],
    }
