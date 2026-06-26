from __future__ import annotations

from pathlib import Path

from v20.api.runtime import run_runtime_from_pillars
from v20.learning.structure_dynamics_runtime_pointer import (
    build_structure_dynamics_runtime_pointer,
    write_structure_dynamics_runtime_pointer_activate_candidate,
)


def test_v20_structure_dynamics_runtime_pointer_can_activate_candidate(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))

    preview = build_structure_dynamics_runtime_pointer()

    assert preview["version"] == "v20.structure_dynamics_runtime_pointer.v1"
    assert preview["status"] == "candidate_ready"
    assert preview["policy_family"] == "structure_dynamics_policy"
    assert preview["runtime_mutation"] is False
    assert preview["runtime_applied"] is False
    assert preview["policy_payload"] == {}
    assert preview["candidate"]["eligible_for_runtime"] is True
    assert preview["candidate"]["dynamic_path_consistency"] == 1.0
    assert preview["candidate"]["semantic_candidate_precision"] == 1.0

    activated = write_structure_dynamics_runtime_pointer_activate_candidate(
        source_role="admin",
        reason="structure dynamics synthetic path replay passed",
    )

    assert activated["status"] == "candidate_active"
    assert activated["runtime_mutation"] is True
    assert activated["active_policy_version"] == preview["candidate_policy_version"]
    assert Path(str(activated["active_pointer_path"])).exists()

    active = build_structure_dynamics_runtime_pointer()

    assert active["status"] == "candidate_active"
    assert active["runtime_applied"] is True
    assert active["runtime_allowed"] is True
    assert active["policy_payload"]["dynamic_path_weight_policy"]["source"] == "structure_dynamics_synthetic_plus_corpus_distribution"
    assert active["policy_payload"]["semantic_match_policy"]["semantic_match_threshold"] >= 0.84


def test_v20_structure_dynamics_runtime_pointer_blocks_unsupported_corpus_label(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    artifact_dir = tmp_path / "training" / "structure_dynamics_corpus_distribution"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "latest.json").write_text(
        """
{
  "version": "v20.structure_dynamics_corpus_distribution.v1",
  "status": "completed_with_findings",
  "limit": 8,
  "unsupported_label_count": 1,
  "unsupported_labels": ["未知结构"],
  "runtime_mutation": false
}
""".strip(),
        encoding="utf-8",
    )

    preview = build_structure_dynamics_runtime_pointer()

    assert preview["status"] == "blocked"
    assert preview["candidate"]["eligible_for_runtime"] is False
    assert preview["candidate"]["blocking_gate"] == "structure_dynamics_corpus_distribution_has_unsupported_labels"


def test_v20_structure_dynamics_runtime_consumes_active_pointer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    activated = write_structure_dynamics_runtime_pointer_activate_candidate(source_role="system", reason="runtime scorer test")

    result = run_runtime_from_pillars("辛酉", "癸巳", "乙卯", "丁丑", input_id="v20.sde.pointer.consume")
    dynamics = result["structure_dynamics"]
    policy = dynamics["sde_v2"]["runtime_policy"]

    assert activated["status"] == "candidate_active"
    assert policy["status"] == "active_policy_applied"
    assert policy["active_policy_version"] == activated["active_policy_version"]
    assert policy["weights"]["semantic_match_threshold"] >= 0.84
    assert dynamics["dominant_chain_v2"]["pattern_label"] == "食神制杀"
    assert dynamics["semantic_candidates"][0]["runtime_semantic_threshold"] == policy["weights"]["semantic_match_threshold"]
