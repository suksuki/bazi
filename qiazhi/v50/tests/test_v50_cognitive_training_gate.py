from __future__ import annotations

from scripts.v50_prepare_cognitive_training_gate import prepare_training_gate


def test_cognitive_weight_training_is_blocked_until_expert_gold_exists() -> None:
    report, queue = prepare_training_gate()

    assert report["status"] == "not_ready"
    assert report["observed_data"]["candidate_contract_count"] == 75
    assert report["observed_data"]["expert_gold_count"] == 0
    assert report["training_decision"]["sft_allowed"] is False
    assert report["training_decision"]["lora_allowed"] is False
    assert report["training_decision"]["weights_modified"] is False
    assert len(queue["items"]) == 24
    assert queue["expected_contract_included"] is False
    assert all("expected_contract" not in item for item in queue["items"])
