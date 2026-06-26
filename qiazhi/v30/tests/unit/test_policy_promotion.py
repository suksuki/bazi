from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.policy import RuntimePointerStore, make_baseline_candidate, promote_candidate_if_valid


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


def test_promote_structure_policy_candidate_updates_pointer(tmp_path: Path) -> None:
    store = RuntimePointerStore(_settings(tmp_path))
    before = store.load_pointer("structure_policy")
    candidate = make_baseline_candidate(
        candidate_id="candidate-001",
        family="structure_policy",
        payload={"weights": {"evidence_coverage": 1.0}},
        change_summary="test candidate",
    )
    result = promote_candidate_if_valid(candidate, store=store)
    after = store.load_pointer("structure_policy")
    assert result.promoted
    assert result.previous_artifact_id == before.active_artifact_id
    assert result.artifact_id == "structure_policy.candidate-001"
    assert after.active_artifact_id == "structure_policy.candidate-001"
    assert after.previous_artifact_id == "structure_policy.v30-baseline"
    assert after.validation_run_id.startswith("v30.synthetic.promotion.structure_policy.all+v30.518k.sample.")
    assert after.rollback_pointer["active_artifact_id"] == "structure_policy.v30-baseline"


def test_promoted_artifact_records_synthetic_validation(tmp_path: Path) -> None:
    store = RuntimePointerStore(_settings(tmp_path))
    candidate = make_baseline_candidate(candidate_id="candidate-002", family="structure_policy")
    result = promote_candidate_if_valid(candidate, store=store)
    artifact_path = (
        tmp_path
        / ".runtime"
        / "artifacts"
        / "structure_policy"
        / "structure_policy.candidate-002.json"
    )
    text = artifact_path.read_text(encoding="utf-8")
    assert result.promoted
    assert "v30.synthetic.promotion.structure_policy.all" in text
    assert "corpus_518k_sample" in text
    assert "v20" not in text
