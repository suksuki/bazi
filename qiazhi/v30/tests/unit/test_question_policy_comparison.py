from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.policy.comparison import (
    build_question_policy_comparison,
    load_question_policy_comparison,
    persist_question_policy_comparison,
)
from v30.runtime import create_smoke_runtime
from v30.storage.artifacts import index_question_policy_comparison_artifact, search_validation_artifacts


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


def test_question_policy_comparison_reports_candidate_deltas(tmp_path: Path) -> None:
    runtime = create_smoke_runtime("question-policy-comparison")
    comparison = build_question_policy_comparison(
        runtime,
        candidate_id="comparison-unit",
        candidate_payload={
            "weights": {
                "topic_weights": {"hidden_factor": 1.25},
                "intent_weights": {"discover_hidden_factor_amplifier": 1.05},
                "stage_weights": {"dialogue_discovery": 1.03},
                "question_weights": {"*": 1.0},
            }
        },
        candidate_question_policy_id="question_policy.comparison-unit.question_policy",
    )

    assert comparison.version == "v30.question_policy_comparison.v1"
    assert comparison.candidate_id == "comparison-unit"
    assert comparison.active_top_question_id
    assert comparison.candidate_top_question_id
    assert comparison.weighted_delta_count > 0
    assert comparison.max_policy_weight_delta > 0
    assert comparison.summary["boundary"] == "question_policy_comparison_diagnostic_not_runtime_mutation"
    hidden_delta = next(row for row in comparison.decision_deltas if row.question_id == "q_v30_hidden_factor_boundary_discovery")
    assert hidden_delta.candidate_policy_weight > hidden_delta.active_policy_weight
    assert any(reason.startswith("question_policy_weight:") for reason in hidden_delta.added_reasons)

    persisted = persist_question_policy_comparison(comparison, settings=_settings(tmp_path))
    assert persisted.artifact_uri is not None
    assert persisted.artifact_record_id == "v30.question_policy_comparison.artifact.comparison-unit"
    assert persisted.artifact_search_backend == "json_fallback"
    assert Path(persisted.artifact_uri).exists()
    loaded = load_question_policy_comparison(candidate_id="comparison-unit", settings=_settings(tmp_path))
    latest = load_question_policy_comparison(settings=_settings(tmp_path))
    assert loaded["candidate_id"] == "comparison-unit"
    assert latest["candidate_id"] == "comparison-unit"
    search = search_validation_artifacts(
        settings=_settings(tmp_path),
        family="question_policy_comparison",
        candidate_id="comparison-unit",
    )
    assert search.backend == "json_fallback"
    assert search.count == 1
    assert search.artifacts[0].artifact_record_id == persisted.artifact_record_id
    assert search.artifacts[0].family == "question_policy_comparison"


def test_question_policy_comparison_can_index_to_v30_artifacts(tmp_path: Path) -> None:
    runtime = create_smoke_runtime("question-policy-comparison-db")
    comparison = build_question_policy_comparison(
        runtime,
        candidate_id="comparison-db",
        candidate_payload={"weights": {"topic_weights": {"hidden_factor": 1.25}}},
        candidate_question_policy_id="question_policy.comparison-db.question_policy",
    ).model_copy(update={"artifact_uri": str(tmp_path / "comparison-db.json")})
    from tests.unit.test_518k_validation import FakeConnection

    connection = FakeConnection()
    write = index_question_policy_comparison_artifact(
        comparison,
        settings=V30Settings(
            database_url="postgresql://user:pass@localhost:5432/qiazhi_v30",
            redis_url=None,
            redis_prefix="v30",
            runtime_dir=tmp_path / ".runtime",
            host="127.0.0.1",
            port=9030,
            env="test",
            repository="memory",
        ),
        connect=lambda _url: connection,
    )
    assert write.artifact_search_backend == "postgres"
    assert write.artifact_searchable is True
    assert write.artifact_record_id == "v30.question_policy_comparison.artifact.comparison-db"
    sql, params = connection.cursor_instance.executed[0]
    assert "v30_artifacts" in sql
    assert params[0] == write.artifact_record_id
    assert params[1] == "question_policy_comparison"
    assert params[2] == comparison.artifact_uri
