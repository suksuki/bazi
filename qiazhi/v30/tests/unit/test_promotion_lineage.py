from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.learning import run_auto_apply_training
from v30.policy import RuntimePointerStore, build_promotion_lineage


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


def test_question_policy_lineage_links_pointer_artifact_validation_and_trace(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = RuntimePointerStore(settings)
    run_auto_apply_training(training_run_id="lineage-unit", store=store)
    lineage = build_promotion_lineage(family="question_policy", settings=settings, store=store)
    payload = lineage.model_dump(mode="json")

    assert lineage.version == "v30.promotion_lineage.v1"
    assert lineage.family == "question_policy"
    assert lineage.active_artifact_id == "question_policy.lineage-unit.question_policy"
    assert lineage.previous_artifact_id
    assert lineage.candidate_id == "lineage-unit.question_policy"
    assert lineage.validation_run_id.startswith("v30.synthetic.promotion.question_policy.all+v30.518k.sample.")
    assert payload["runtime_pointer"]["rollback_pointer"]["active_artifact_id"] == lineage.previous_artifact_id
    assert "corpus_518k_sample" in payload["policy_artifact_summary"]["validation_keys"]
    assert "question_policy_comparison" in payload["policy_artifact_summary"]["validation_keys"]
    assert any(row["family"] == "518k_validation" for row in payload["validation_artifacts"])
    assert any(row["family"] == "question_policy_comparison" for row in payload["validation_artifacts"])
    assert payload["active_runtime_trace_summary"]["family_consumed"] is True
    assert payload["active_runtime_trace_summary"]["active_policy_versions"]["question_policy"] == lineage.active_artifact_id
    assert "promotion_lineage_is_diagnostic_not_policy_mutation" in payload["boundaries"]


def test_structure_policy_lineage_works_without_comparison_artifact(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = RuntimePointerStore(settings)
    run_auto_apply_training(training_run_id="lineage-structure", store=store)
    lineage = build_promotion_lineage(family="structure_policy", settings=settings, store=store)

    assert lineage.active_artifact_id == "structure_policy.lineage-structure.structure_policy"
    assert lineage.active_runtime_trace_summary["family_consumed"] is True
    assert any(row["family"] == "518k_validation" for row in lineage.validation_artifacts)
    assert not any(row["family"] == "question_policy_comparison" for row in lineage.validation_artifacts)
