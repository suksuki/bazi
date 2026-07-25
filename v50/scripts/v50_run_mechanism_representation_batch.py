#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


V50_ROOT = Path(__file__).resolve().parents[1]
for path in (V50_ROOT / "packages", V50_ROOT / "apps"):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import analyze_mingli_graph, build_mingli_graph_from_material_store, classify_node_roles, explore_mingli_paths
from core.mechanism import build_mechanism_representation_from_flow_state
from core.simulation import build_mingli_state_from_graph_analysis, run_ablation_simulation
from core.state import build_bazi_flow_states


FIXTURE_PATH = V50_ROOT / "data" / "validation" / "fixtures" / "synthetic_chart_taxonomy_v1.json"
REPORT_DIR = V50_ROOT / "data" / "validation" / "reports"


def run_batch(*, limit: int | None = None, write_report: bool = False) -> dict[str, Any]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = payload["cases"][:limit] if limit else payload["cases"]
    results = [_run_case(case) for case in cases]
    summary = {
        "version": "v50.mechanism_representation_batch.v1",
        "fixture_file": str(FIXTURE_PATH),
        "case_count": len(cases),
        "total_representations": sum(len(result["representations"]) for result in results),
        "llm_used": False,
        "brain_used": False,
        "training_performed": False,
        "metrics": _metrics(results),
        "results": results,
    }
    if write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        json_path = REPORT_DIR / "mechanism_representation_batch_v1.json"
        md_path = REPORT_DIR / "mechanism_representation_batch_v1.md"
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        md_path.write_text(_markdown_report(summary), encoding="utf-8")
    return summary


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    reading_id = f"reading.mechanism_representation_batch.{case['case_id']}"
    birth_input = BirthInputCanonical(**case["birth_input"])
    calendar = normalize_birth_input(birth_input)
    store = build_bazi_material_store(reading_id=reading_id, birth_input=birth_input, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    paths = explore_mingli_paths(graph)
    roles = classify_node_roles(graph, paths)
    analysis = analyze_mingli_graph(graph, path_result=paths, role_result=roles)
    state = build_mingli_state_from_graph_analysis(analysis)
    simulation_report = run_ablation_simulation(state)
    flow_states = build_bazi_flow_states(
        analysis=analysis,
        path_result=paths,
        state=state,
        simulation_report=simulation_report,
        include_secondary_mechanisms=True,
    )
    representations = [
        build_mechanism_representation_from_flow_state(
            flow_state=flow_state,
            analysis=analysis,
            simulation_report=simulation_report,
        )
        for flow_state in flow_states
    ]
    return {
        "case_id": case["case_id"],
        "case_type": case["case_type"],
        "chart": case["chart"],
        "representation_count": len(representations),
        "representations": [
            {
                "representation_id": item.representation_id,
                "mechanism_code": item.mechanism_code,
                "mechanism_label_code": item.mechanism_label_code,
                "component_roles": sorted({component.role.value for component in item.components}),
                "component_count": len(item.components),
                "path_ref_count": len(item.path_refs),
                "state_delta_ref_count": len(item.state_delta_refs),
                "completeness": item.completeness.value,
                "missing_fields": list(item.missing_fields),
                "ast_shape": item.ast_shape,
                "state_delta_status": item.state_delta_status.value,
                "synthetic_filled_fields": list(item.synthetic_filled_fields),
                "hard_filled_fields": list(item.hard_filled_fields),
                "label_is_presentation_only": item.label_is_presentation_only,
                "confidence": item.confidence,
            }
            for item in representations
        ],
    }


def _metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    representations = [item for result in results for item in result["representations"]]
    mechanism_distribution = Counter(item["mechanism_code"] for item in representations)
    role_distribution = Counter(role for item in representations for role in item["component_roles"])
    completeness_distribution = Counter(item["completeness"] for item in representations)
    ast_shape_distribution = Counter(item["ast_shape"] for item in representations)
    total = len(representations)
    return {
        "mechanism_count": len(mechanism_distribution),
        "mechanism_distribution": dict(sorted(mechanism_distribution.items())),
        "role_count": len(role_distribution),
        "role_distribution": dict(sorted(role_distribution.items())),
        "completeness_distribution": dict(sorted(completeness_distribution.items())),
        "ast_shape_count": len(ast_shape_distribution),
        "ast_shape_distribution": dict(sorted(ast_shape_distribution.items())),
        "label_authority_violations": sum(1 for item in representations if item["label_is_presentation_only"] is not True),
        "synthetic_filled_count": sum(len(item["synthetic_filled_fields"]) for item in representations),
        "hard_filled_count": sum(len(item["hard_filled_fields"]) for item in representations),
        "avg_component_count": round(sum(int(item["component_count"]) for item in representations) / total, 3) if total else 0.0,
        "representations_without_state_delta": sum(1 for item in representations if int(item["state_delta_ref_count"]) == 0),
    }


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Mechanism Representation Batch v1",
        "",
        f"Cases: {summary['case_count']}",
        f"Total representations: {summary['total_representations']}",
        f"LLM used: {summary['llm_used']}",
        f"Brain used: {summary['brain_used']}",
        f"Training performed: {summary['training_performed']}",
        "",
        "## Metrics",
        "",
    ]
    for key, value in summary["metrics"].items():
        if key in {"mechanism_distribution", "role_distribution", "completeness_distribution", "ast_shape_distribution"}:
            continue
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Mechanism Distribution", ""])
    for code, count in summary["metrics"]["mechanism_distribution"].items():
        lines.append(f"- `{code}`: {count}")
    lines.extend(["", "## Role Distribution", ""])
    for role, count in summary["metrics"]["role_distribution"].items():
        lines.append(f"- `{role}`: {count}")
    lines.extend(["", "## Completeness Distribution", ""])
    for completeness, count in summary["metrics"]["completeness_distribution"].items():
        lines.append(f"- `{completeness}`: {count}")
    lines.extend(["", "## AST Shape Distribution", ""])
    for shape, count in summary["metrics"]["ast_shape_distribution"].items():
        lines.append(f"- `{shape}`: {count}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V50 mechanism representation batch report.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    summary = run_batch(limit=args.limit, write_report=args.write_report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
