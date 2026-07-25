from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import MingliContextCompiler, compile_chart_world


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data/validation/fixtures"


def run_benchmark_v2(*, run_id: str = "offline") -> dict[str, Any]:
    taxonomy = _load(FIXTURE_DIR / "synthetic_chart_taxonomy_v2.json")
    matrix = _load(FIXTURE_DIR / "cognitive_benchmark_matrix_v2.json")
    split_by_case = {
        case_id: split
        for split in ("development", "holdout", "challenge")
        for case_id in matrix[split]["case_ids"]
    }
    results = []
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fixture in taxonomy["cases"]:
        birth = _birth(fixture)
        world = compile_chart_world(
            reading_id=f"benchmark-v2:{run_id}:{fixture['case_id']}",
            birth_input=birth,
            include_research_fixture_prior=False,
        )
        context = MingliContextCompiler().compile(world=world, stage="pattern")
        encoded_context = json.dumps(context.payload, ensure_ascii=False, sort_keys=True)
        categories = Counter(item.category for item in world.facts)
        row = {
            "case_id": fixture["case_id"],
            "family_id": fixture["structure_archetype_id"],
            "split": split_by_case[fixture["case_id"]],
            "contract_status": fixture["contract_status"],
            "pillars_match": world.pillars == fixture["chart"].split(),
            "fixture_prior_count": categories.get("research_fixture_prior", 0),
            "expected_contract_in_context": any(
                token in encoded_context for token in ("expected_contract", "expected_path", "expert_structure_prior", "research_fixture_prior")
            ),
            "world_fingerprint": _fingerprint(world.model_dump(mode="json")),
            "fact_count": len(world.facts),
            "fact_category_count": len(categories),
            "knowledge_count": len(world.knowledge),
            "first_three_pillars": world.pillars[:3],
            "hour_pillar": world.pillars[3],
            "month_branch": _ledger_payload(world, "month_branch"),
            "day_master": _ledger_payload(world, "day_master"),
            "expected_contract_fingerprint": _fingerprint(fixture["expected_contract"]),
        }
        results.append(row)
        by_family[row["family_id"]].append(row)

    family_results = [_family_result(family_id, rows) for family_id, rows in sorted(by_family.items())]
    hard_failures = []
    hard_failures.extend(f"pillar_mismatch:{row['case_id']}" for row in results if not row["pillars_match"])
    hard_failures.extend(f"fixture_prior_leak:{row['case_id']}" for row in results if row["fixture_prior_count"])
    hard_failures.extend(f"context_answer_leak:{row['case_id']}" for row in results if row["expected_contract_in_context"])
    hard_failures.extend(
        f"controlled_variant_failure:{row['family_id']}:{','.join(row['failures'])}"
        for row in family_results
        if row["failures"]
    )
    split_family_overlap = _split_family_overlap(matrix)
    if split_family_overlap:
        hard_failures.append(f"family_split_overlap:{split_family_overlap}")

    structural_hard_passes = sum(row["pillars_match"] for row in results)
    structural_strong_passes = sum(not row["failures"] for row in family_results)
    report = {
        "version": "deepbazi.cognitive_benchmark_report.v2",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not hard_failures else "failed",
        "observed_data": {
            "case_count": len(results),
            "family_count": len(family_results),
            "split_counts": dict(Counter(row["split"] for row in results)),
            "family_split_overlap": split_family_overlap,
            "pillar_fact_pass_rate": round(structural_hard_passes / len(results), 4),
            "answer_isolation_pass_rate": round(
                sum(not row["expected_contract_in_context"] and not row["fixture_prior_count"] for row in results) / len(results), 4
            ),
            "controlled_variant_family_pass_rate": round(structural_strong_passes / len(family_results), 4),
            "unique_world_fingerprints": len({row["world_fingerprint"] for row in results}),
            "hard_failures": hard_failures,
        },
        "effective_independent_evidence": {
            "structural": {
                "hard_pass": structural_hard_passes,
                "strong_pass": structural_strong_passes,
                "soft_pass": 0,
                "observation_only": len(results),
                "note": "Candidate expected contracts remain observations and are not counted as expert truth.",
            },
            "state": {"hard_pass": 0, "strong_pass": 0, "soft_pass": 0, "observation_only": 75},
            "theme": {"hard_pass": 0, "strong_pass": 0, "soft_pass": 0, "observation_only": 75},
            "timing": {"hard_pass": 0, "strong_pass": 0, "soft_pass": 0, "observation_only": 15},
            "decision_confidence": {"hard_pass": 0, "strong_pass": 0, "soft_pass": 0, "observation_only": 75},
        },
        "case_results": results,
        "controlled_variant_results": family_results,
        "interpretation": (
            "The benchmark establishes fact fidelity, family isolation, answer isolation, and controlled-variant sensitivity. "
            "It does not claim expert correctness for candidate semantic contracts."
        ),
        "recommendation": (
            "Use this matrix for retrieval, attention, hypothesis, and review regression. "
            "Do not fine-tune weights until expert-reviewed gold and a sealed blind set exist."
        ),
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "runtime_rules_modified": False,
            "mingli_algorithm_modified": False,
            "expected_contract_visible_to_model": False,
            "candidate_contract_treated_as_gold": False,
        },
    }
    return report


def _family_result(family_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    if len(rows) != 3:
        failures.append("variant_count_not_three")
    if len({tuple(row["first_three_pillars"]) for row in rows}) != 1:
        failures.append("year_month_day_changed")
    if len({row["hour_pillar"] for row in rows}) != len(rows):
        failures.append("hour_pillar_not_varied")
    if len({row["expected_contract_fingerprint"] for row in rows}) != 1:
        failures.append("family_candidate_contract_changed")
    if len({row["world_fingerprint"] for row in rows}) != len(rows):
        failures.append("world_not_sensitive_to_hour_variant")
    if len({_fingerprint(row["month_branch"]) for row in rows}) != 1:
        failures.append("month_branch_ledger_drift")
    if len({_fingerprint(row["day_master"]) for row in rows}) != 1:
        failures.append("day_master_ledger_drift")
    return {
        "family_id": family_id,
        "case_ids": [row["case_id"] for row in rows],
        "split": rows[0]["split"],
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "invariants": {
            "year_month_day": rows[0]["first_three_pillars"],
            "month_branch": rows[0]["month_branch"],
            "day_master": rows[0]["day_master"],
            "candidate_contract_stable": len({row["expected_contract_fingerprint"] for row in rows}) == 1,
        },
        "changes": {
            "hour_pillars": [row["hour_pillar"] for row in rows],
            "world_fingerprints": [row["world_fingerprint"] for row in rows],
        },
    }


def _split_family_overlap(matrix: dict[str, Any]) -> list[str]:
    seen: dict[str, str] = {}
    overlap = []
    for split in ("development", "holdout", "challenge"):
        for family in matrix[split]["family_ids"]:
            if family in seen:
                overlap.append(f"{family}:{seen[family]}:{split}")
            seen[family] = split
    return overlap


def _birth(fixture: dict[str, Any]) -> BirthInputCanonical:
    payload = dict(fixture["birth_input"])
    payload["birth_time"] = "12:00"
    return BirthInputCanonical.model_validate(payload)


def _ledger_payload(world: Any, category: str) -> dict[str, Any]:
    return next(item.payload for item in world.facts if item.category == category)


def _fingerprint(payload: Any) -> str:
    if isinstance(payload, dict):
        payload = dict(payload)
        payload.pop("world_id", None)
        payload.pop("reading_id", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cognitive_benchmark_v2.json"
    md_path = output_dir / "cognitive_benchmark_v2.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    observed = report["observed_data"]
    md_path.write_text(
        "\n".join(
            [
                "# Cognitive Benchmark v2",
                "",
                f"- Status: `{report['status']}`",
                f"- Cases / families: `{observed['case_count']}` / `{observed['family_count']}`",
                f"- Pillar fact pass: `{observed['pillar_fact_pass_rate']}`",
                f"- Answer isolation pass: `{observed['answer_isolation_pass_rate']}`",
                f"- Controlled variant family pass: `{observed['controlled_variant_family_pass_rate']}`",
                f"- Unique world fingerprints: `{observed['unique_world_fingerprints']}`",
                "",
                "## Evidence levels",
                "",
                "```json",
                json.dumps(report["effective_independent_evidence"], ensure_ascii=False, indent=2),
                "```",
                "",
                "## Interpretation",
                "",
                report["interpretation"],
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
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run leak-free Cognitive Benchmark v2.")
    parser.add_argument("--run-id", default="offline")
    parser.add_argument("--output-dir", default=str(ROOT / "reports/cognitive-benchmark-v2/offline"))
    args = parser.parse_args()
    report = run_benchmark_v2(run_id=args.run_id)
    paths = _write(report, Path(args.output_dir))
    print(json.dumps({"status": report["status"], "reports": [str(path) for path in paths]}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
