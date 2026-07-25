from __future__ import annotations

from scripts.v50_run_cognitive_benchmark_v2 import run_benchmark_v2


def test_cognitive_benchmark_v2_establishes_leak_free_structural_evidence() -> None:
    report = run_benchmark_v2(run_id="unit")

    assert report["status"] == "passed"
    assert report["observed_data"]["case_count"] == 75
    assert report["observed_data"]["family_count"] == 25
    assert report["observed_data"]["pillar_fact_pass_rate"] == 1.0
    assert report["observed_data"]["answer_isolation_pass_rate"] == 1.0
    assert report["observed_data"]["controlled_variant_family_pass_rate"] == 1.0
    assert report["observed_data"]["hard_failures"] == []
    assert report["effective_independent_evidence"]["structural"]["hard_pass"] == 75
    assert report["effective_independent_evidence"]["state"]["hard_pass"] == 0
    assert report["boundary_status"]["candidate_contract_treated_as_gold"] is False
