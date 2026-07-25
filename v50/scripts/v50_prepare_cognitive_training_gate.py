from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data/validation/fixtures"
TAXONOMY_PATH = FIXTURE_DIR / "synthetic_chart_taxonomy_v2.json"
MATRIX_PATH = FIXTURE_DIR / "cognitive_benchmark_matrix_v2.json"
PATH_EVIDENCE_POLICY = "deepbazi.path_evidence_vector.ra3.v1"


def prepare_training_gate() -> tuple[dict[str, Any], dict[str, Any]]:
    taxonomy = _load(TAXONOMY_PATH)
    matrix = _load(MATRIX_PATH)
    cases = {item["case_id"]: item for item in taxonomy["cases"]}
    candidate_count = sum(item["contract_status"] == "candidate_pending_review" for item in taxonomy["cases"])
    expert_gold_count = sum(item["contract_status"] == "expert_reviewed_gold" for item in taxonomy["cases"])
    holdout_ids = list(matrix["holdout"]["case_ids"])
    queue = {
        "version": "deepbazi.cognitive_expert_review_queue.v2",
        "queue_id": _stable_id(
            "cognitive-expert-review-queue",
            _sha256(TAXONOMY_PATH),
            _sha256(MATRIX_PATH),
            *holdout_ids,
        ),
        "purpose": "Human expert labels for attention, hypothesis coverage, causal reasoning, and review calibration.",
        "source_snapshot": {
            "taxonomy_sha256": _sha256(TAXONOMY_PATH),
            "matrix_sha256": _sha256(MATRIX_PATH),
            "path_evidence_policy": PATH_EVIDENCE_POLICY,
        },
        "model_access_allowed": False,
        "expected_contract_included": False,
        "formal_authority_write_allowed": False,
        "training_use": "expert_review_candidate_only",
        "items": [
            {
                "case_id": case_id,
                "family_id": cases[case_id]["structure_archetype_id"],
                "chart": cases[case_id]["chart"],
                "source_mode": "synthetic",
                "epistemic_status": "candidate_pending_review",
                "formal_authority_write_allowed": False,
                "review_status": "unreviewed",
                "labels": {
                    "first_look_attention_refs": [],
                    "critical_omission_refs": [],
                    "minimum_hypothesis_set": [],
                    "strongest_alternative": "",
                    "selected_hypothesis": "",
                    "causal_path": {"source": [], "transformations": [], "target": []},
                    "counter_evidence": [],
                    "unresolved_questions": [],
                    "reviewer_confidence": "",
                    "reviewer_rationale": "",
                },
            }
            for case_id in holdout_ids
        ],
    }
    blockers = []
    if expert_gold_count < 30:
        blockers.append("expert_gold_below_minimum_30")
    if expert_gold_count == 0:
        blockers.append("no_expert_gold")
    blockers.append("permanent_blind_set_not_sealed")
    blockers.append("expert_inter_reviewer_agreement_not_measured")
    report = {
        "version": "deepbazi.cognitive_training_readiness_gate.v2",
        "status": "ready" if not blockers else "not_ready",
        "observed_data": {
            "synthetic_case_count": len(taxonomy["cases"]),
            "candidate_contract_count": candidate_count,
            "expert_gold_count": expert_gold_count,
            "expert_review_queue_count": len(queue["items"]),
            "permanent_blind_set_sealed": False,
            "blockers": blockers,
        },
        "training_decision": {
            "knowledge_curation_allowed": True,
            "retrieval_calibration_allowed": True,
            "attention_algorithm_calibration_allowed": True,
            "formal_candidate_promotion_allowed": False,
            "automatic_theory_promotion_allowed": False,
            "sft_allowed": False,
            "lora_allowed": False,
            "teacher_distillation_allowed": False,
            "weights_modified": False,
        },
        "required_before_weight_training": [
            "At least 30 expert-reviewed cases across isolated structure families.",
            "Pairwise attention labels and strongest-alternative labels.",
            "Inter-reviewer agreement and adjudication records.",
            "A sealed permanent blind set never used by prompts, retrieval, Teacher analysis, or tuning.",
            "A rollbackable model candidate with multidimensional quality and latency comparison.",
        ],
        "interpretation": "The training gate is functioning: current candidate contracts may guide research review but cannot serve as model gold.",
        "evidence_alignment": {
            "path_evidence_policy": PATH_EVIDENCE_POLICY,
            "synthetic_expected_contract_role": "research_candidate_not_gold",
            "legacy_numeric_path_metrics_role": "compatibility_observation_not_training_label",
            "life_case_write_allowed": False,
            "reasoner_policy_write_allowed": False,
        },
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "candidate_contract_promoted": False,
            "teacher_output_used_as_gold": False,
            "blind_set_exposed": False,
        },
    }
    return report, queue


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"training-review-queue-{digest}"


def _write(report: dict[str, Any], queue: dict[str, Any], output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cognitive_training_readiness_gate_v2.json"
    md_path = output_dir / "cognitive_training_readiness_gate_v2.md"
    queue_path = output_dir / "cognitive_expert_review_queue_v2.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    queue_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    observed = report["observed_data"]
    md_path.write_text(
        "\n".join(
            [
                "# Cognitive Training Readiness Gate v1",
                "",
                f"- Status: `{report['status']}`",
                f"- Candidate contracts: `{observed['candidate_contract_count']}`",
                f"- Expert gold: `{observed['expert_gold_count']}`",
                f"- Review queue: `{observed['expert_review_queue_count']}`",
                "",
                "## Blockers",
                "",
                *[f"- `{item}`" for item in observed["blockers"]],
                "",
                "## Training decision",
                "",
                "```json",
                json.dumps(report["training_decision"], ensure_ascii=False, indent=2),
                "```",
                "",
                "## Boundaries",
                "",
                "```json",
                json.dumps(report["boundary_status"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return json_path, md_path, queue_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare expert review data and enforce the cognitive weight-training gate.")
    parser.add_argument("--output-dir", default=str(ROOT / "reports/training-readiness/v2"))
    args = parser.parse_args()
    report, queue = prepare_training_gate()
    paths = _write(report, queue, Path(args.output_dir))
    print(json.dumps({"status": report["status"], "artifacts": [str(path) for path in paths]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
