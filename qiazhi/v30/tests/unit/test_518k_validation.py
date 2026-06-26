from __future__ import annotations

import subprocess
import sys
import json
from pathlib import Path

import pytest

from v30.config import V30Settings
from v30.storage.artifacts import index_518k_validation_artifact, search_518k_validation_artifacts
from v30.validation import run_518k_validation, run_518k_readiness_matrix


class FakeCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql: str, params: tuple[object, ...]) -> None:
        self.executed.append((sql, params))


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.committed = True


def _settings(tmp_path: Path, database_url: str | None = None) -> V30Settings:
    return V30Settings(
        database_url=database_url,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="memory",
    )


def test_518k_sample_validation_replays_runtime_contract() -> None:
    result = run_518k_validation(mode="sample", limit=4)
    assert result.mode == "sample"
    assert result.target_case_count == 518_400
    assert result.case_count == 4
    assert result.promotion_signal == "eligible"
    assert result.coverage_metrics["hidden_factor_probe_coverage"] == 4
    assert result.coverage_metrics["krp_signal_coverage"] == 4
    assert result.coverage_metrics["question_recommendation_coverage"] == 4
    assert result.coverage_metrics["model_signal_summary_coverage"] == 4
    assert result.coverage_metrics["interaction_state_coverage"] == 4
    assert result.coverage_metrics["visible_internal_next_question_split_count"] == 4
    assert result.coverage_metrics["calibration_probe_user_visible_count"] == 0
    assert result.drift_metrics["unsupported_question_rate"] == 0.0
    assert result.drift_metrics["missing_model_signal_summary_rate"] == 0.0
    assert result.drift_metrics["missing_interaction_state_rate"] == 0.0
    assert result.drift_metrics["calibration_probe_user_visible_rate"] == 0.0


def test_518k_shard_validation_targets_selected_shard() -> None:
    result = run_518k_validation(mode="shard", shard_id=7, limit=3)
    assert result.shard_ids == [7]
    assert {row.shard_id for row in result.case_summaries} == {7}


def test_518k_validation_replays_candidate_policy_payload() -> None:
    result = run_518k_validation(
        mode="sample",
        limit=2,
        policy_payload_overrides={
            "question_policy": {"weights": {"topic_weights": {"hidden_factor": 1.25}}}
        },
        active_policy_version_overrides={"question_policy": "question_policy.518k-test"},
    )
    assert result.promotion_signal == "eligible"
    assert {row.top_question_id for row in result.case_summaries} == {
        "q_v30_hidden_factor_boundary_discovery"
    }


def test_518k_validation_reads_external_jsonl_source(tmp_path: Path) -> None:
    source_path = tmp_path / "cases.jsonl"
    source_path.write_text(
        "\n".join(
            [
                '{"case_id":"row-1","day_master":"庚","hidden_factor_user_calibrated":true}',
                '{"case_id":"row-2","day_master":"癸","useful_god_path_resolved":true}',
            ]
        ),
        encoding="utf-8",
    )
    result = run_518k_validation(mode="sample", limit=2, source_path=source_path)
    assert result.case_count == 2
    assert result.coverage_metrics["external_source_count"] == 2
    assert result.case_summaries[0].source == "external"
    assert result.case_summaries[0].source_row_id == "row-1"
    assert {row.day_master for row in result.case_summaries} == {"庚", "癸"}


def test_518k_validation_persists_v30_artifact(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    result = run_518k_validation(mode="sample", limit=1, artifact_dir=artifact_dir)
    assert result.artifact_uri is not None
    artifact_path = Path(result.artifact_uri)
    assert artifact_path.exists()
    assert artifact_path.parent == artifact_dir
    assert result.index_uri is not None
    assert result.index_entry_uri is not None
    assert result.artifact_record_id == f"v30.518k.artifact.{result.run_id}"
    assert result.artifact_search_backend in {"json_fallback", "postgres", "postgres_unavailable"}
    index_path = Path(result.index_uri)
    entry_path = Path(result.index_entry_uri)
    assert index_path == artifact_dir / "index.json"
    assert entry_path.exists()
    artifact_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    entry_payload = json.loads(entry_path.read_text(encoding="utf-8"))
    assert artifact_payload["run_id"] == result.run_id
    assert artifact_payload["index_uri"] == str(index_path)
    assert index_payload["index_id"] == "v30.518k.validation_index.v1"
    assert index_payload["latest_run_id_by_mode"]["sample"] == result.run_id
    assert entry_payload["artifact_uri"] == str(artifact_path)
    assert entry_payload["index_entry_uri"] == str(entry_path)
    assert entry_payload["artifact_record_id"] == result.artifact_record_id
    assert "v30.518k.sample" in artifact_path.read_text(encoding="utf-8")


def test_518k_validation_artifact_search_uses_json_fallback(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    first = run_518k_validation(mode="sample", limit=1, artifact_dir=artifact_dir)
    second = run_518k_validation(mode="shard", shard_id=7, limit=1, artifact_dir=artifact_dir)
    result = search_518k_validation_artifacts(
        settings=_settings(tmp_path),
        mode="sample",
        limit=5,
        artifact_dir=artifact_dir,
    )
    assert result.backend == "json_fallback"
    assert result.searchable is False
    assert result.count == 1
    assert result.artifacts[0].run_id == first.run_id
    assert result.artifacts[0].artifact_record_id == first.artifact_record_id
    assert result.artifacts[0].artifact_uri == first.artifact_uri
    assert second.run_id not in {row.run_id for row in result.artifacts}


def test_518k_validation_artifact_can_index_to_v30_artifacts(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    result = run_518k_validation(mode="sample", limit=1, artifact_dir=artifact_dir)
    connection = FakeConnection()
    write = index_518k_validation_artifact(
        result,
        settings=_settings(tmp_path, database_url="postgresql://user:pass@localhost:5432/qiazhi_v30"),
        connect=lambda _url: connection,
    )
    assert write.artifact_search_backend == "postgres"
    assert write.artifact_searchable is True
    assert write.artifact_record_id == result.artifact_record_id
    assert connection.committed is True
    sql, params = connection.cursor_instance.executed[0]
    assert "v30_artifacts" in sql
    assert params[0] == result.artifact_record_id
    assert params[1] == "518k_validation"
    assert params[2] == result.artifact_uri


def test_518k_full_requires_explicit_confirmation() -> None:
    with pytest.raises(ValueError, match="confirm_full"):
        run_518k_validation(mode="full", limit=1)


def test_518k_readiness_matrix_documents_sample_shard_and_full_boundary(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "matrix-artifacts"
    result = run_518k_readiness_matrix(
        sample_limit=3,
        shard_id=7,
        shard_limit=2,
        artifact_dir=artifact_dir,
        settings=_settings(tmp_path),
    )

    assert result["version"] == "v30.518k_readiness_matrix.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "bt9_518k_readiness_matrix_ready"
    assert result["decision"]["validation_518k_completion"] == 95
    assert result["decision"]["full_518k_required"] is False
    assert result["mode_readiness"]["sample"]["case_count"] == 3
    assert result["mode_readiness"]["sample"]["promotion_signal"] == "eligible"
    assert result["mode_readiness"]["shard"]["case_count"] == 2
    assert result["mode_readiness"]["shard"]["shard_ids"] == [7]
    assert result["mode_readiness"]["full"]["status"] == "explicit_confirmation_required"
    assert result["mode_readiness"]["full"]["run_executed"] is False
    assert result["corpus_mount_contract"]["generated_contract_available"] is True
    assert result["corpus_mount_contract"]["external_source_supported"] is True
    assert result["artifact_persistence"]["artifact_count"] == 2
    assert result["artifact_persistence"]["index_count"] == 2
    assert result["artifact_search"]["backend"] == "json_fallback"
    assert result["artifact_search"]["count"] >= 1
    assert result["coverage_summary"]["total_checked_case_count"] == 5
    assert result["coverage_summary"]["calibration_probe_user_visible_count"] == 0
    assert {row["family"] for row in result["candidate_family_coverage_matrix"]} == {
        "structure_policy",
        "mainline_policy",
        "question_policy",
        "rule_policy",
    }
    assert all(row["sample_ready"] and row["shard_ready"] for row in result["candidate_family_coverage_matrix"])
    assert all(not row["pointer_promotion_allowed_by_matrix"] for row in result["candidate_family_coverage_matrix"])
    assert result["policy_boundary"]["full_518k_run_allowed_by_default"] is False
    assert result["next_mainline_selection"]["task_id"] == "BT10"


def test_518k_validation_script_sample() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_518k_validation.py", "--mode", "sample", "--limit", "2"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "eligible mode=sample cases=2" in result.stdout
    assert "- artifact:" in result.stdout
    assert "- index:" in result.stdout


def test_518k_readiness_matrix_script() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_518k_readiness_matrix.py",
            "--sample-limit",
            "2",
            "--shard-limit",
            "2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "v30.518k_readiness_matrix.v1: passed" in result.stdout
    assert "bt9_518k_readiness_matrix_ready" in result.stdout
