from __future__ import annotations

import json
from pathlib import Path

from scripts.v50_run_balanced_cognitive_benchmark import run_benchmark


ROOT = Path(__file__).resolve().parents[1]


def test_balanced_matrix_covers_all_taxonomy_types_once_and_is_split_cleanly():
    matrix = json.loads((ROOT / "data/validation/fixtures/cognitive_benchmark_matrix_v1.json").read_text())
    taxonomy = json.loads((ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v1.json").read_text())
    grouped = [*matrix["development"], *matrix["holdout"], *matrix["metamorphic"]]
    assert len(grouped) == len(set(grouped)) == 17
    assert set(grouped) == {item["case_id"] for item in taxonomy["cases"]}


def test_offline_benchmark_blocks_holdout_fixture_prior_and_reports_metamorphic_gap():
    report = run_benchmark(run_id="unit")
    assert report["observed_data"]["case_count"] == 17
    assert report["observed_data"]["case_type_count"] == 17
    assert report["observed_data"]["holdout_prior_leaks"] == []
    assert report["observed_data"]["scored_prior_leaks"] == []
    assert all(item["research_fixture_prior_count"] == 0 for item in report["offline_results"])
    holdout = [item for item in report["offline_results"] if item["split"] == "holdout"]
    assert all(item["research_fixture_prior_count"] == 0 for item in holdout)
    relation_pair = next(item for item in report["metamorphic_results"] if item["pair_id"] == "triple_combination_integrity")
    assert relation_pair["status"] == "failed"
    assert relation_pair["failure"] == "complete_triple_combination_not_represented_in_world_facts"
    assert report["boundary_status"]["mingli_algorithm_modified"] is False
