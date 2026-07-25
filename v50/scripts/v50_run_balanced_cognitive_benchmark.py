from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import MingliAgent, compile_chart_world


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data" / "validation" / "fixtures"
REPORT_ROOT = ROOT / "reports" / "mingli_agent" / "balanced-benchmark-v1"


def run_benchmark(*, live_case_types: list[str] | None = None, run_id: str = "offline") -> dict[str, Any]:
    taxonomy = _load(FIXTURE_DIR / "synthetic_chart_taxonomy_v1.json")
    matrix = _load(FIXTURE_DIR / "cognitive_benchmark_matrix_v1.json")
    cases = {item["case_id"]: item for item in taxonomy["cases"]}
    membership = {
        case_id: split
        for split in ("development", "holdout", "metamorphic")
        for case_id in matrix[split]
    }
    results = []
    for case_id in [*matrix["development"], *matrix["holdout"], *matrix["metamorphic"]]:
        case = cases[case_id]
        birth = _birth(case)
        world = compile_chart_world(
            reading_id=f"balanced-benchmark:{run_id}:{case_id}",
            birth_input=birth,
            include_research_fixture_prior=False,
        )
        categories = Counter(item.category for item in world.facts)
        results.append({
            "case_id": case_id,
            "case_type": case["case_type"],
            "split": membership[case_id],
            "pillars": world.pillars,
            "fact_count": len(world.facts),
            "fact_category_count": len(categories),
            "fact_categories": dict(categories),
            "candidate_path_count": categories.get("candidate_path", 0),
            "candidate_role_count": categories.get("candidate_node_role", 0),
            "knowledge_count": len(world.knowledge),
            "research_fixture_prior_count": categories.get("research_fixture_prior", 0),
            "world_fingerprint": _fingerprint(world.model_dump(mode="json")),
            "expected_path": case.get("expected_path", []),
        })

    metamorphic = _metamorphic_results(matrix=matrix, cases=cases, results=results)
    live_results = _run_live(cases=cases, case_types=live_case_types or [], run_id=run_id)
    ids = [item["case_id"] for item in results]
    prior_leaks = [item["case_id"] for item in results if item["research_fixture_prior_count"]]
    holdout_prior_leaks = [item["case_id"] for item in results if item["split"] == "holdout" and item["research_fixture_prior_count"]]
    failures = []
    if len(ids) != len(set(ids)):
        failures.append("duplicate_case_membership")
    if set(ids) != set(cases):
        failures.append("taxonomy_not_fully_covered")
    if holdout_prior_leaks:
        failures.append("holdout_prior_leak")
    if prior_leaks:
        failures.append("scored_fixture_prior_leak")
    failures.extend(item["failure"] for item in metamorphic if item.get("failure"))
    report = {
        "version": "deepbazi.balanced_cognitive_benchmark_report.v1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not failures and all(item.get("status") == "passed" for item in live_results) else "partial",
        "observed_data": {
            "case_count": len(results),
            "split_counts": dict(Counter(item["split"] for item in results)),
            "case_type_count": len({item["case_type"] for item in results}),
            "unique_world_fingerprints": len({item["world_fingerprint"] for item in results}),
            "holdout_prior_leaks": holdout_prior_leaks,
            "scored_prior_leaks": prior_leaks,
            "offline_failures": failures,
        },
        "offline_results": results,
        "metamorphic_results": metamorphic,
        "live_results": live_results,
        "interpretation": "该报告验证样本覆盖、holdout 先验隔离与受控变体一致性；它不把单个标签命中率当成命理认知质量。",
        "recommendation": "对 metamorphic failure 建立独立 Research Slice；不得为本报告修改引擎、Prompt 或理论。",
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "runtime_rules_modified": False,
            "brain_logic_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "prompt_modified": False,
            "holdout_fixture_prior_used": bool(holdout_prior_leaks),
        },
    }
    return report


def _metamorphic_results(*, matrix: dict[str, Any], cases: dict[str, dict[str, Any]], results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result_map = {item["case_id"]: item for item in results}
    output = []
    for pair in matrix["metamorphic_pairs"]:
        base_id = pair["base_case_id"]
        variant_id = pair["variant_case_id"]
        base_case, variant_case = cases[base_id], cases[variant_id]
        if pair["pair_id"] == "triple_combination_integrity":
            base_relations = _branch_relations(_birth(base_case), f"metamorphic:{base_id}")
            variant_relations = _branch_relations(_birth(variant_case), f"metamorphic:{variant_id}")
            complete_detected = any(item.get("type") in {"triple_combination", "three_harmony"} for item in base_relations)
            break_detected = bool(variant_relations)
            passed = complete_detected and break_detected and base_relations != variant_relations
            observation = {"base_relations": base_relations, "variant_relations": variant_relations}
            failure = "complete_triple_combination_not_represented_in_world_facts" if not passed else ""
        else:
            base_pillars = result_map[base_id]["pillars"]
            variant_pillars = result_map[variant_id]["pillars"]
            passed = base_pillars == base_case["chart"].split() and variant_pillars == variant_case["chart"].split()
            observation = {"base_pillars": base_pillars, "variant_pillars": variant_pillars}
            failure = "timing_fixture_mutated_natal_pillars" if not passed else ""
        output.append({
            "pair_id": pair["pair_id"],
            "status": "passed" if passed else "failed",
            "expectation": pair["expectation"],
            "observation": observation,
            "failure": failure,
        })
    return output


def _run_live(*, cases: dict[str, dict[str, Any]], case_types: list[str], run_id: str) -> list[dict[str, Any]]:
    if not case_types:
        return []
    agent = MingliAgent()
    output = []
    by_type = {item["case_type"]: item for item in cases.values()}
    for case_type in case_types:
        case = by_type[case_type]
        world = compile_chart_world(
            reading_id=f"balanced-live:{run_id}:{case_type}",
            birth_input=_birth(case),
            include_research_fixture_prior=False,
        )
        try:
            record = agent.first_reading(case_id=f"balanced-live:{case_type}", world=world)
            cognition = record.cognition
            output.append({
                "case_type": case_type,
                "status": "passed",
                "first_look": cognition.first_look,
                "selected_hypothesis": cognition.selected_hypothesis_id,
                "hypothesis_count": len(cognition.hypotheses),
                "work_path": cognition.work_path.path_statement,
                "domain_generation_policy": "on_demand",
                "stage_count": len(record.stage_receipts),
            })
        except Exception as exc:  # noqa: BLE001 - benchmark records failures and never repairs the model inline.
            output.append({"case_type": case_type, "status": "failed", "failure": f"{type(exc).__name__}:{exc}"})
    return output


def _branch_relations(birth: BirthInputCanonical, reading_id: str) -> list[dict[str, Any]]:
    world = compile_chart_world(reading_id=reading_id, birth_input=birth, include_research_fixture_prior=False)
    fact = next(item for item in world.facts if item.category == "branch_relations")
    return list(fact.payload.get("relations") or [])


def _birth(case: dict[str, Any]) -> BirthInputCanonical:
    payload = dict(case["birth_input"])
    payload["birth_time"] = "12:00"
    return BirthInputCanonical.model_validate(payload)


def _fingerprint(payload: dict[str, Any]) -> str:
    normalized = dict(payload)
    normalized.pop("world_id", None)
    normalized.pop("reading_id", None)
    return hashlib.sha256(json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(report: dict[str, Any], run_id: str) -> tuple[Path, Path]:
    target = REPORT_ROOT / run_id
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "balanced_cognitive_benchmark_v1.json"
    md_path = target / "balanced_cognitive_benchmark_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Balanced Cognitive Benchmark v1",
        "",
        f"- Status: `{report['status']}`",
        f"- Cases: `{report['observed_data']['case_count']}` / types `{report['observed_data']['case_type_count']}`",
        f"- Splits: `{report['observed_data']['split_counts']}`",
        f"- Unique world fingerprints: `{report['observed_data']['unique_world_fingerprints']}`",
        f"- Holdout prior leaks: `{report['observed_data']['holdout_prior_leaks']}`",
        "",
        "## Metamorphic",
        "",
    ]
    for item in report["metamorphic_results"]:
        lines.append(f"- `{item['pair_id']}`: **{item['status']}** {item.get('failure', '')}")
    lines.extend(["", "## Live cognition", ""])
    for item in report["live_results"]:
        lines.append(f"- `{item['case_type']}`: **{item['status']}** {item.get('first_look', item.get('failure', ''))}")
    lines.extend(["", "## Boundaries", "", "```json", json.dumps(report["boundary_status"], ensure_ascii=False, indent=2), "```", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="offline")
    parser.add_argument("--live-case-types", nargs="*", default=[])
    args = parser.parse_args()
    report = run_benchmark(live_case_types=args.live_case_types, run_id=args.run_id)
    json_path, md_path = _write(report, args.run_id)
    print(json.dumps({"status": report["status"], "json": str(json_path), "markdown": str(md_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
