from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from v30.config import V30Settings, load_settings
from v30.contracts import V30Model


PolicyFamily = Literal[
    "feature_policy",
    "rule_policy",
    "knowledge_policy",
    "structure_policy",
    "mainline_policy",
    "portrait_policy",
    "question_policy",
    "answer_policy",
    "presentation_policy",
    "hidden_factor_policy",
]

POINTER_VERSION = "v30.runtime_pointer.v1"
ARTIFACT_VERSION = "v30.policy_artifact.v1"
BASELINE_ARTIFACT_ID = "v30-baseline"


class PolicyArtifact(V30Model):
    artifact_id: str
    family: PolicyFamily
    version: str
    candidate_id: str
    payload: dict[str, Any]
    checksum: str = ""
    created_at: datetime
    metrics: dict[str, Any] = {}
    validation_summary: dict[str, Any] = {}
    compatible_runtime_version: str = "30.0.0a0"


class RuntimePointer(V30Model):
    version: str = POINTER_VERSION
    family: PolicyFamily
    active_artifact_id: str
    active_artifact_version: str
    previous_artifact_id: str = ""
    validation_run_id: str = ""
    promotion_reason: str = "baseline"
    env: str = "local"
    status: str = "active"
    updated_at: datetime
    updated_by: str = "system"
    rollback_pointer: dict[str, Any] = {}


class RuntimePointerStore:
    def __init__(self, settings: V30Settings | None = None):
        self._settings = settings or load_settings()
        self._root = self._settings.runtime_dir / "policies"

    def load_pointer(self, family: PolicyFamily) -> RuntimePointer:
        path = self._pointer_path(family)
        if not path.exists():
            pointer = baseline_pointer(family, env=self._settings.env)
            self.save_pointer(pointer)
            self.save_artifact(baseline_artifact(family))
            return pointer
        data = json.loads(path.read_text(encoding="utf-8"))
        return RuntimePointer.model_validate(data)

    def save_pointer(self, pointer: RuntimePointer) -> None:
        path = self._pointer_path(pointer.family)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(pointer.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    def save_artifact(self, artifact: PolicyArtifact) -> None:
        path = self._artifact_path(artifact.family, artifact.artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    def load_artifact(self, family: PolicyFamily, artifact_id: str) -> PolicyArtifact:
        path = self._artifact_path(family, artifact_id)
        if not path.exists():
            artifact = baseline_artifact(family)
            self.save_artifact(artifact)
            return artifact
        data = json.loads(path.read_text(encoding="utf-8"))
        return PolicyArtifact.model_validate(data)

    def load_active_artifact(self, family: PolicyFamily) -> PolicyArtifact:
        pointer = self.load_pointer(family)
        return self.load_artifact(family, pointer.active_artifact_id)

    def active_versions(self, families: tuple[PolicyFamily, ...]) -> dict[str, str]:
        return {family: self.load_pointer(family).active_artifact_id for family in families}

    def rollback_to_previous(self, family: PolicyFamily, *, updated_by: str = "v30.policy.rollback") -> RuntimePointer:
        current = self.load_pointer(family)
        target = current.rollback_pointer.get("active_artifact_id") if isinstance(current.rollback_pointer, dict) else ""
        if not target:
            raise ValueError(f"rollback pointer is not available for {family}")
        target_artifact = self.load_artifact(family, str(target))
        pointer = RuntimePointer(
            family=family,
            active_artifact_id=target_artifact.artifact_id,
            active_artifact_version=target_artifact.version,
            previous_artifact_id=current.active_artifact_id,
            validation_run_id=current.validation_run_id,
            promotion_reason="admin_policy_pointer_rollback_to_previous",
            env=current.env,
            status="active",
            updated_at=datetime.now(timezone.utc),
            updated_by=updated_by,
            rollback_pointer={
                "family": current.family,
                "active_artifact_id": current.active_artifact_id,
                "active_artifact_version": current.active_artifact_version,
            },
        )
        self.save_pointer(pointer)
        return pointer

    def _pointer_path(self, family: PolicyFamily) -> Path:
        return self._root / family / "active.json"

    def _artifact_path(self, family: PolicyFamily, artifact_id: str) -> Path:
        return self._settings.runtime_dir / "artifacts" / family / f"{artifact_id}.json"


def baseline_artifact(family: PolicyFamily) -> PolicyArtifact:
    return PolicyArtifact(
        artifact_id=f"{family}.{BASELINE_ARTIFACT_ID}",
        family=family,
        version=ARTIFACT_VERSION,
        candidate_id="baseline",
        payload=baseline_policy_payload(family),
        created_at=datetime.now(timezone.utc),
        validation_summary={"status": "baseline"},
    )


def baseline_policy_payload(family: PolicyFamily) -> dict[str, Any]:
    payload: dict[str, Any] = {"mode": "baseline", "family": family}
    if family == "structure_policy":
        payload["weights"] = {
            "mechanism.hidden_factor_dialogue_probe": 1.0,
            "mechanism.ten_god_visibility_context": 1.0,
            "mechanism.useful_god_candidate_gate": 1.0,
            "mechanism.branch_relation_dynamic_review": 1.0,
        }
    if family == "question_policy":
        payload["weights"] = {
            "topic_weights": {"*": 1.0},
            "intent_weights": {"*": 1.0},
            "stage_weights": {"*": 1.0},
            "question_weights": {"*": 1.0},
        }
    if family == "rule_policy":
        payload["weights"] = {
            "rule_weights": {"*": 1.0},
            "domain_weights": {"*": 1.0},
        }
    return payload


def baseline_pointer(family: PolicyFamily, *, env: str = "local") -> RuntimePointer:
    artifact = baseline_artifact(family)
    return RuntimePointer(
        family=family,
        active_artifact_id=artifact.artifact_id,
        active_artifact_version=artifact.version,
        env=env,
        updated_at=datetime.now(timezone.utc),
    )
