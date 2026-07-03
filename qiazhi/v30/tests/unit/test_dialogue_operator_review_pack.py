from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.training import DIALOGUE_OPERATOR_REVIEW_PACK_VERSION, run_dialogue_operator_review_pack
from v30.validation.dialogue_operator_review_pack import (
    DIALOGUE_OPERATOR_REVIEW_PACK_VALIDATION_VERSION,
    run_dialogue_operator_review_pack_validation,
)


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


def test_dialogue_operator_review_pack_summarizes_dtc_evidence(tmp_path: Path) -> None:
    pack = run_dialogue_operator_review_pack(
        run_id="dtc5-unit",
        sample_limit=8,
        persist_review=True,
        settings=_settings(tmp_path),
    )

    assert pack["version"] == DIALOGUE_OPERATOR_REVIEW_PACK_VERSION
    assert pack["status"] == "completed"
    assert pack["decision"]["decision_status"] == "dtc5_dialogue_operator_review_pack_ready"
    assert pack["decision"]["candidate_ready_for_heavy_validation_review"] is True
    assert pack["decision"]["promotion_allowed"] is False
    assert pack["decision"]["policy_pointer_write_allowed"] is False
    assert pack["evidence_summary"]["dtc1_sample_count"] >= 1
    assert pack["evidence_summary"]["dtc4_pass_ratio"] == 1.0
    assert all(row["status"] == "ready" for row in pack["review_items"])
    assert all(row["writes_policy_pointer"] is False for row in pack["operator_actions"])


def test_dialogue_operator_review_pack_validation_blocks_release(tmp_path: Path) -> None:
    validation = run_dialogue_operator_review_pack_validation(
        run_id="dtc5-validation",
        sample_limit=8,
        persist_review=True,
        settings=_settings(tmp_path),
    )

    assert validation["version"] == DIALOGUE_OPERATOR_REVIEW_PACK_VALIDATION_VERSION
    assert validation["status"] == "completed"
    assert validation["decision"]["operator_review_required"] is True
    assert validation["decision"]["candidate_ready_for_heavy_validation_review"] is True
    assert validation["decision"]["promotion_allowed"] is False
    assert validation["decision"]["policy_pointer_write_allowed"] is False
    assert validation["policy_boundary"]["policy_pointer_promotion_allowed"] is False
