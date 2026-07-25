from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import compile_chart_world


ROOT = Path(__file__).resolve().parents[1]


def run_cross_axis_suite() -> dict[str, Any]:
    base = _birth(name="原始档案", location="上海", hour_pillar="乙酉")
    identity_variant = _birth(name="匿名档案", location="首尔", hour_pillar="乙酉")
    break_variant = _birth(name="破组变体", location="上海", hour_pillar="丁亥")

    base_world = compile_chart_world(reading_id="metamorphic.base", birth_input=base, analysis_year=2026)
    identity_world = compile_chart_world(reading_id="metamorphic.identity", birth_input=identity_variant, analysis_year=2026)
    break_world = compile_chart_world(reading_id="metamorphic.break", birth_input=break_variant, analysis_year=2026)
    next_year_world = compile_chart_world(reading_id="metamorphic.next-year", birth_input=base, analysis_year=2027)

    tests = [
        _result(
            test_id="identity_fields_do_not_change_structure",
            passed=_structural_fingerprint(base_world) == _structural_fingerprint(identity_world),
            expectation="Changing name and public location text must not change Bazi structural facts.",
            observed={
                "base": _structural_fingerprint(base_world),
                "variant": _structural_fingerprint(identity_world),
            },
        ),
        _result(
            test_id="hour_branch_break_removes_triple_path",
            passed=_has_graph_relation(base_world, "forms_triple_combination")
            and not _has_graph_relation(break_world, "forms_triple_combination"),
            expectation="Replacing the 酉 hour branch with 亥 removes the 巳酉丑 triple-combination relation without relying on candidate-path ordering.",
            observed={
                "base_relations": _graph_relations(base_world),
                "variant_relations": _graph_relations(break_world),
            },
        ),
        _result(
            test_id="hour_branch_break_adds_observable_clash",
            passed=(
                not _ledger_relations(base_world, relation_type="clash")
                and len(_ledger_relations(break_world, relation_type="clash")) >= 2
            ),
            expectation="The controlled 亥 variant adds explicit 巳亥 clashes instead of silently collapsing to the base structure.",
            observed={
                "base": _ledger_relations(base_world, relation_type="clash"),
                "variant": _ledger_relations(break_world, relation_type="clash"),
            },
        ),
        _result(
            test_id="timing_only_change_preserves_natal_structure",
            passed=_structural_fingerprint(base_world) == _structural_fingerprint(next_year_world),
            expectation="Changing only analysis year must not rewrite natal Bazi facts, graph, paths, roles, or ablation observations.",
            observed={
                "base": _structural_fingerprint(base_world),
                "next_year": _structural_fingerprint(next_year_world),
            },
        ),
        _result(
            test_id="timing_only_change_updates_annual_material",
            passed=(
                base_world.timing_context["annual_pillar"] != next_year_world.timing_context["annual_pillar"]
                and base_world.pillars == next_year_world.pillars
            ),
            expectation="Analysis-year material changes while natal pillars remain fixed.",
            observed={
                "base_annual": base_world.timing_context["annual_pillar"],
                "next_annual": next_year_world.timing_context["annual_pillar"],
                "natal_pillars_equal": base_world.pillars == next_year_world.pillars,
            },
        ),
    ]
    failures = [item["test_id"] for item in tests if item["status"] == "failed"]
    return {
        "version": "deepbazi.cross_axis_metamorphic_suite.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not failures else "failed",
        "observed_data": {
            "test_count": len(tests),
            "pass_count": len(tests) - len(failures),
            "failures": failures,
            "variation_axes": ["identity_metadata", "hour_branch_relation", "analysis_year_timing"],
        },
        "test_results": tests,
        "interpretation": "The suite tests what must change and what must remain without using semantic expected labels as model hints.",
        "boundary_status": {
            "llm_used": False,
            "expected_contract_used": False,
            "mingli_algorithm_modified_during_run": False,
            "training_performed": False,
        },
    }


def _result(*, test_id: str, passed: bool, expectation: str, observed: dict[str, Any]) -> dict[str, Any]:
    return {
        "test_id": test_id,
        "status": "passed" if passed else "failed",
        "expectation": expectation,
        "observed": observed,
    }


def _birth(*, name: str, location: str, hour_pillar: str) -> BirthInputCanonical:
    return BirthInputCanonical.model_validate(
        {
            "birth_input_id": f"metamorphic-{name}-{hour_pillar}",
            "name": name,
            "gender": "male",
            "calendar_type": "solar",
            "birth_date": "1987-05-12",
            "birth_time": "18:00",
            "birth_location": location,
            "timezone": "Asia/Shanghai",
            "year_pillar": "丁巳",
            "month_pillar": "乙巳",
            "day_pillar": "乙丑",
            "hour_pillar": hour_pillar,
            "input_quality": "explicit_pillars",
        }
    )


def _structural_fingerprint(world: Any) -> str:
    payload = [
        {
            "kind": fact.kind,
            "category": fact.category,
            "statement": fact.statement,
            "payload": _without_identity_metadata(fact.payload),
        }
        for fact in world.facts
        if fact.category != "timing_material" and not fact.category.startswith("ziwei_")
    ]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def _without_identity_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_identity_metadata(item)
            for key, item in value.items()
            if key not in {
                "candidate_node_key",
                "candidate_relation_key",
                "candidate_path_key",
                "node_id",
                "relation_source_ref",
                "supporting_relation_refs",
                "blocking_relation_refs",
                "reason_refs",
            }
        }
    if isinstance(value, list):
        return [_without_identity_metadata(item) for item in value]
    return value


def _path_relations(world: Any) -> list[list[str]]:
    return [list(fact.payload.get("relations") or []) for fact in world.facts if fact.category == "candidate_path"]


def _has_path_relation(world: Any, relation: str) -> bool:
    return any(relation in relations for relations in _path_relations(world))


def _graph_relations(world: Any) -> list[str]:
    return [
        str(fact.payload.get("relation") or "")
        for fact in world.facts
        if fact.category == "graph_relation"
    ]


def _has_graph_relation(world: Any, relation: str) -> bool:
    return relation in _graph_relations(world)


def _ledger_relations(
    world: Any,
    *,
    relation_type: str | None = None,
) -> list[dict[str, Any]]:
    relations = list(
        next(fact.payload for fact in world.facts if fact.category == "branch_relations")
        .get("relations")
        or []
    )
    if relation_type is None:
        return relations
    return [item for item in relations if item.get("type") == relation_type]


def _write(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cross_axis_metamorphic_suite_v1.json"
    md_path = output_dir / "cross_axis_metamorphic_suite_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Cross-axis Metamorphic Suite v1", "", f"- Status: `{report['status']}`", ""]
    lines.extend(f"- `{item['test_id']}`: **{item['status']}** — {item['expectation']}" for item in report["test_results"])
    lines.extend(["", "## Boundaries", "", "```json", json.dumps(report["boundary_status"], ensure_ascii=False, indent=2), "```", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run controlled cross-axis metamorphic tests.")
    parser.add_argument("--output-dir", default=str(ROOT / "reports/cognitive-benchmark-v2/metamorphic-v1"))
    args = parser.parse_args()
    report = run_cross_axis_suite()
    paths = _write(report, Path(args.output_dir))
    print(json.dumps({"status": report["status"], "reports": [str(path) for path in paths]}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
