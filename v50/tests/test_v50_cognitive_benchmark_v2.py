from __future__ import annotations

import json
from pathlib import Path

from scripts.v50_build_cognitive_benchmark_v2 import build_matrix


ROOT = Path(__file__).resolve().parents[1]


def test_v2_matrix_is_family_isolated_and_covers_all_cases() -> None:
    matrix = build_matrix()
    taxonomy = json.loads(
        (ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v2.json").read_text(encoding="utf-8")
    )
    family_to_split = {}
    case_ids = []
    for split in ("development", "holdout", "challenge"):
        payload = matrix[split]
        for family in payload["family_ids"]:
            assert family not in family_to_split
            family_to_split[family] = split
        case_ids.extend(payload["case_ids"])

    assert len(case_ids) == len(set(case_ids)) == 75
    assert set(case_ids) == {case["case_id"] for case in taxonomy["cases"]}
    assert len(family_to_split) == 25


def test_v2_matrix_forbids_weight_training_without_expert_gold() -> None:
    matrix = build_matrix()

    assert matrix["blind_gate"]["expected_contract_visible_to_model"] is False
    assert matrix["blind_gate"]["candidate_contract_counts_as_expert_gold"] is False
    assert matrix["blind_gate"]["expert_gold_count"] == 0
    assert matrix["blind_gate"]["ready_for_weight_training"] is False


def test_all_v2_expected_contracts_remain_candidate_evidence() -> None:
    taxonomy = json.loads(
        (ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v2.json").read_text(encoding="utf-8")
    )

    assert {case["contract_status"] for case in taxonomy["cases"]} == {"candidate_pending_review"}
