from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.policy.runtime_pointer import PolicyArtifact, RuntimePointerStore, baseline_artifact, baseline_pointer
from datetime import datetime, timezone


def _settings(tmp_path: Path) -> V30Settings:
    return V30Settings(
        database_url=None,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="memory",
    )


def test_baseline_pointer_is_v30_family_bound() -> None:
    pointer = baseline_pointer("structure_policy", env="test")
    assert pointer.family == "structure_policy"
    assert pointer.active_artifact_id == "structure_policy.v30-baseline"
    assert pointer.env == "test"
    assert pointer.status == "active"


def test_runtime_pointer_store_creates_v30_local_files(tmp_path: Path) -> None:
    store = RuntimePointerStore(_settings(tmp_path))
    pointer = store.load_pointer("structure_policy")
    pointer_path = tmp_path / ".runtime" / "policies" / "structure_policy" / "active.json"
    artifact_path = tmp_path / ".runtime" / "artifacts" / "structure_policy" / "structure_policy.v30-baseline.json"
    assert pointer.active_artifact_id == "structure_policy.v30-baseline"
    assert pointer_path.exists()
    assert artifact_path.exists()
    assert "v20" not in pointer_path.read_text(encoding="utf-8")


def test_runtime_pointer_store_reports_active_versions(tmp_path: Path) -> None:
    store = RuntimePointerStore(_settings(tmp_path))
    versions = store.active_versions(("structure_policy", "mainline_policy", "question_policy", "rule_policy"))
    assert versions == {
        "structure_policy": "structure_policy.v30-baseline",
        "mainline_policy": "mainline_policy.v30-baseline",
        "question_policy": "question_policy.v30-baseline",
        "rule_policy": "rule_policy.v30-baseline",
    }


def test_baseline_artifact_is_not_training_candidate() -> None:
    artifact = baseline_artifact("question_policy")
    assert artifact.candidate_id == "baseline"
    assert artifact.validation_summary["status"] == "baseline"
    assert artifact.payload["family"] == "question_policy"


def test_runtime_pointer_store_loads_active_artifact_payload(tmp_path: Path) -> None:
    store = RuntimePointerStore(_settings(tmp_path))
    store.load_pointer("structure_policy")
    artifact = PolicyArtifact(
        artifact_id="structure_policy.weighted",
        family="structure_policy",
        version="v30.policy_artifact.v1",
        candidate_id="weighted",
        payload={"weights": {"mechanism.hidden_factor_dialogue_probe": 1.2}},
        created_at=datetime.now(timezone.utc),
    )
    pointer = baseline_pointer("structure_policy", env="test").model_copy(
        update={
            "active_artifact_id": artifact.artifact_id,
            "previous_artifact_id": "structure_policy.v30-baseline",
            "updated_by": "test",
        }
    )
    store.save_artifact(artifact)
    store.save_pointer(pointer)
    active = store.load_active_artifact("structure_policy")
    assert active.artifact_id == "structure_policy.weighted"
    assert active.payload["weights"]["mechanism.hidden_factor_dialogue_probe"] == 1.2
