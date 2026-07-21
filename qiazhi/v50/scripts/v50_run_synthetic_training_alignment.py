from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "packages", ROOT / "apps", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.graph.contracts import MingliPath
from scripts.v50_prepare_cognitive_training_gate import prepare_training_gate
from scripts.v50_run_synthetic_fixture_matrix import run_group as run_fixture_matrix
from scripts.v50_run_synthetic_work_system_fixtures import run_group as run_work_system
from scripts.v50_run_timing_synthetic_validation import run_group as run_timing_validation
from scripts.v50_validate_synthetic_chart_taxonomy import validate_taxonomy

MANIFEST_PATH = ROOT / "data/validation/synthetic_evidence_manifest_v1.json"
TAXONOMY_V2 = ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v2.json"
MATRIX_V2 = ROOT / "data/validation/fixtures/cognitive_benchmark_matrix_v2.json"


def run_alignment() -> dict[str, Any]:
    manifest = _load(MANIFEST_PATH)
    taxonomy_v2 = _load(TAXONOMY_V2)
    matrix_v2 = _load(MATRIX_V2)
    taxonomy_v1_result = validate_taxonomy()
    work_result = run_work_system()
    matrix_result = run_fixture_matrix("synthetic_fixture_matrix_v2")
    timing_result = run_timing_validation()
    training_report, training_queue = prepare_training_gate()
    _, repeated_queue = prepare_training_gate()
    path_schema = MingliPath.model_json_schema()["properties"]

    development = set(matrix_v2["development"]["case_ids"])
    holdout = set(matrix_v2["holdout"]["case_ids"])
    challenge = set(matrix_v2["challenge"]["case_ids"])
    suites = manifest["suites"]
    checks = [
        _check("manifest_assets_exist", all((ROOT / row["asset"]).is_file() for row in suites)),
        _check(
            "active_structure_regressions_pass",
            taxonomy_v1_result["passed"]
            and work_result["failed"] == 0
            and matrix_result["failed"] == 0,
        ),
        _check(
            "legacy_numeric_suites_cannot_promote",
            all(
                not row["formal_promotion_allowed"]
                for row in suites
                if row["classification"].startswith("legacy_unvalidated")
            ),
        ),
        _check(
            "timing_candidate_remains_runtime_isolated",
            timing_result["failed"] == 0
            and timing_result["runtime_timing_policy_activated"] is False,
        ),
        _check(
            "ra3_path_contract_has_no_public_score",
            "evidence_vector" in path_schema
            and "legacy_unvalidated_metrics" in path_schema
            and "path_score" not in path_schema,
        ),
        _check(
            "candidate_contracts_are_not_gold",
            all(
                row["contract_status"] == "candidate_pending_review"
                for row in taxonomy_v2["cases"]
            ),
        ),
        _check(
            "development_holdout_challenge_are_disjoint",
            not development.intersection(holdout)
            and not development.intersection(challenge)
            and not holdout.intersection(challenge),
        ),
        _check(
            "training_queue_is_deterministic_and_isolated",
            training_queue == repeated_queue
            and training_queue["model_access_allowed"] is False
            and training_queue["expected_contract_included"] is False
            and training_queue["formal_authority_write_allowed"] is False
            and all(
                row["formal_authority_write_allowed"] is False
                and row["epistemic_status"] == "candidate_pending_review"
                for row in training_queue["items"]
            ),
        ),
        _check(
            "weight_training_and_automatic_promotion_blocked",
            training_report["status"] == "not_ready"
            and training_report["training_decision"]["sft_allowed"] is False
            and training_report["training_decision"]["lora_allowed"] is False
            and training_report["training_decision"]["teacher_distillation_allowed"] is False
            and training_report["training_decision"]["formal_candidate_promotion_allowed"] is False
            and training_report["training_decision"]["automatic_theory_promotion_allowed"] is False,
        ),
    ]
    return {
        "schema_version": "deepbazi.synthetic_training_alignment.v1",
        "status": "PASS" if all(row["passed"] for row in checks) else "FAIL",
        "checks": checks,
        "counts": {
            "manifest_suites": len(suites),
            "active_work_cases": work_result["total"],
            "active_matrix_cases": matrix_result["total"],
            "candidate_contracts": len(taxonomy_v2["cases"]),
            "training_review_candidates": len(training_queue["items"]),
            "expert_gold": training_report["observed_data"]["expert_gold_count"],
            "legacy_observations": (
                work_result["legacy_observation_count"]
                + matrix_result["legacy_observation_count"]
            ),
        },
        "asset_hashes": {
            row["suite_id"]: _sha256(ROOT / row["asset"])
            for row in suites
        },
        "training_queue_id": training_queue["queue_id"],
        "formal_state_writes": 0,
        "weights_modified": False,
        "llm_used": False,
    }


def _check(name: str, passed: bool) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed)}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run synthetic evidence and training-candidate alignment")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_alignment()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
