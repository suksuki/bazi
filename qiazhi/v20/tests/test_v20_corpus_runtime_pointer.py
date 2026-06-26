from __future__ import annotations

import json

from v20.corpus.artifacts import _similarity_score, build_corpus_artifacts
from v20.corpus.job_runner import FullPrecomputeJobConfig, run_full_precompute_job
from v20.learning.corpus_runtime_pointer import (
    CORPUS_ACTIVE_POINTER_VERSION,
    build_corpus_runtime_pointer,
    write_corpus_runtime_pointer_activate_candidate,
)
from v20.storage.local_jsonl import local_jsonl_store_from_env


def test_v20_corpus_runtime_pointer_blocks_without_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))

    pointer = build_corpus_runtime_pointer()

    assert pointer["status"] == "blocked"
    assert pointer["runtime_applied"] is False
    assert "corpus_artifact_status_not_completed" in pointer["blocking_gate"]


def test_v20_corpus_runtime_pointer_activates_completed_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    config = FullPrecomputeJobConfig(run_id="test_corpus_pointer", start=0, limit=6, status_every=2)
    run_full_precompute_job(config, runtime_dir=tmp_path)
    build_corpus_artifacts("test_corpus_pointer", runtime_dir=tmp_path, status_every=2)

    before_score = _similarity_score({"feature_id:a", "mainline_domains:wealth"}, {"feature_id:a", "mainline_domains:wealth"})
    result = write_corpus_runtime_pointer_activate_candidate(source_role="system", reason="test")
    pointer = build_corpus_runtime_pointer()
    after_score = _similarity_score({"feature_id:a", "mainline_domains:wealth"}, {"feature_id:a", "mainline_domains:wealth"})

    assert result["status"] == "candidate_active"
    assert result["runtime_mutation"] is True
    assert result["candidate"]["feature_threshold_policy_count"] >= 1
    assert result["candidate"]["similarity_tag_weight_policy_count"] >= 1
    assert pointer["status"] == "candidate_active"
    assert pointer["runtime_applied"] is True
    assert pointer["policy_payload"]["feature_threshold_policy"]
    assert after_score == before_score
    runtime = local_jsonl_store_from_env().runtime_dir
    active_path = runtime / "training" / "corpus_policy_versions" / "active_pointer.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    assert active["version"] == CORPUS_ACTIVE_POINTER_VERSION
    assert active["policy_payload"]["similarity_tag_weight_policy"]
