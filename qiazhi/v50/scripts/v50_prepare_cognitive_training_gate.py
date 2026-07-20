from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data/validation/fixtures"


def prepare_training_gate() -> tuple[dict[str, Any], dict[str, Any]]:
    taxonomy = _load(FIXTURE_DIR / "synthetic_chart_taxonomy_v2.json")
    matrix = _load(FIXTURE_DIR / "cognitive_benchmark_matrix_v2.json")
    cases = {item["case_id"]: item for item in taxonomy["cases"]}
    candidate_count = sum(item["contract_status"] == "candidate_pending_review" for item in taxonomy["cases"])
    expert_gold_count = sum(item["contract_status"] == "expert_reviewed_gold" for item in taxonomy["cases"])
    holdout_ids = list(matrix["holdout"]["case_ids"])
    queue = {
        "version": "deepbazi.cognitive_expert_review_queue.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Human expert labels for attention, hypothesis coverage, causal reasoning, and review calibration.",
        "model_access_allowed": False,
        "expected_contract_included": False,
        "items": [
            {
                "case_id": case_id,
                "family_id": cases[case_id]["structure_archetype_id"],
                "chart": cases[case_id]["chart"],
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
        "version": "deepbazi.cognitive_training_readiness_gate.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
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


def _write(report: dict[str, Any], queue: dict[str, Any], output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cognitive_training_readiness_gate_v1.json"
    md_path = output_dir / "cognitive_training_readiness_gate_v1.md"
    queue_path = ROOT / "data/training/cognitive_expert_review_queue_v1.json"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
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
    parser.add_argument("--output-dir", default=str(ROOT / "reports/training-readiness/v1"))
    args = parser.parse_args()
    report, queue = prepare_training_gate()
    paths = _write(report, queue, Path(args.output_dir))
    print(json.dumps({"status": report["status"], "artifacts": [str(path) for path in paths]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
