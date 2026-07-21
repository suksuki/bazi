from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.engines.bazi.knowledge import SIX_CLASH, SIX_HARMONY
from core.graph import build_mingli_graph_from_material_store
from core.graph.builder import TRIPLE_COMBINATIONS
from core.graph.contracts import MingliGraphEdgeType, MingliGraphNodeType
from product.canvas_projection import LAYER_DEFINITIONS


ROOT = Path(__file__).resolve().parents[1]


def audit_six_pillar_relation_coverage() -> dict[str, Any]:
    builder_source = _read("packages/core/graph/builder.py")
    temporal_source = _read("apps/product/canvas_projection.py")
    variant_source = _read("apps/product/structural_variant_compiler.py")
    declared = {item.value for item in MingliGraphEdgeType}
    emitted = {
        MingliGraphEdgeType[name].value
        for name in re.findall(r"MingliGraphEdgeType\.([A-Z_]+)", builder_source)
    }
    advertised = set().union(*(item[3] for item in LAYER_DEFINITIONS))
    test_references = _test_reference_counts(declared | advertised)

    witnesses = {
        "clash": _witness(
            "material-clash",
            ["甲子", "丙寅", "甲午", "甲子"],
        ),
        "harmony": _witness(
            "material-harmony",
            ["甲子", "丁卯", "乙丑", "丙子"],
        ),
        "configured_triple": _witness(
            "configured-triple",
            ["丁巳", "乙巳", "乙丑", "乙酉"],
        ),
        "unconfigured_triple": _witness(
            "unconfigured-triple",
            ["甲申", "丙子", "壬辰", "庚子"],
        ),
    }

    temporal_block = temporal_source.split("def _temporal_layer(", 1)[1].split(
        "def _layer_catalog(", 1
    )[0]
    relation_matrix = [
        {
            "relation_type": relation_type,
            "declared": relation_type in declared,
            "emitted_by_graph_builder": relation_type in emitted,
            "advertised_by_canvas": relation_type in advertised,
            "test_file_references": test_references.get(relation_type, 0),
        }
        for relation_type in sorted(declared | advertised)
    ]

    findings = [
        {
            "finding_id": "REL-A01",
            "severity": "critical",
            "finding": "Material Engine emits six-clash and six-harmony evidence, but Graph Builder does not consume BAZI_COMBINATION materials.",
        },
        {
            "finding_id": "REL-A02",
            "severity": "critical",
            "finding": "Luck and annual pillars are rendered as nodes without relation, cluster, path, or path-update computation.",
        },
        {
            "finding_id": "REL-A03",
            "severity": "high",
            "finding": "The only configured triple combination is Si-You-Chou; the builder is sample-specialized.",
        },
        {
            "finding_id": "REL-A04",
            "severity": "high",
            "finding": "Triple combination output uses binary edges even though stable relation identity supports n-ary participants.",
        },
        {
            "finding_id": "REL-A05",
            "severity": "high",
            "finding": "Canvas advertises punish, harm, and break relation layers that do not exist in the Graph relation enum.",
        },
        {
            "finding_id": "REL-A06",
            "severity": "high",
            "finding": "Six declared Graph relation types have no builder emission path.",
        },
        {
            "finding_id": "REL-A07",
            "severity": "medium",
            "finding": "Element edges connect every visible stem/branch pair without a position or layer qualification contract.",
        },
        {
            "finding_id": "REL-A08",
            "severity": "medium",
            "finding": "Relation strengths are fixed policy constants and are not calibrated measurements.",
        },
    ]

    checks = [
        _check("declared_relation_types_counted", len(declared) == 12),
        _check("builder_emission_types_counted", len(emitted) == 6),
        _check(
            "material_clash_gap_reproduced",
            "clash" in witnesses["clash"]["material_relation_types"]
            and "clashes" not in witnesses["clash"]["graph_relation_types"],
        ),
        _check(
            "material_harmony_gap_reproduced",
            "harmony" in witnesses["harmony"]["material_relation_types"]
            and "harmonizes" not in witnesses["harmony"]["graph_relation_types"],
        ),
        _check(
            "sample_specialized_triple_reproduced",
            witnesses["configured_triple"]["triple_edge_count"] > 0
            and witnesses["unconfigured_triple"]["triple_edge_count"] == 0,
        ),
        _check(
            "triple_output_is_not_nary",
            witnesses["configured_triple"]["max_triple_participant_arity"] == 2,
        ),
        _check(
            "canvas_only_relation_types_identified",
            advertised - declared == {"punishes", "harms", "breaks"},
        ),
        _check(
            "temporal_layer_has_no_relation_computation",
            all(token not in temporal_block for token in ("relations=", "paths=", "path_updates=")),
        ),
        _check(
            "structural_variant_appends_temporal_nodes_without_relations",
            'candidate["nodes"].extend' in variant_source
            and 'candidate["relations"].extend' not in variant_source,
        ),
        _check(
            "luck_and_year_node_types_declared_but_not_built",
            all(
                f"MingliGraphNodeType.{name}" not in builder_source
                for name in ("LUCK", "YEAR")
            ),
        ),
    ]

    return {
        "schema_version": "deepbazi.six_pillar_relation_coverage_audit.v1",
        "status": "AUDIT_COMPLETE_RA1_REQUIRED"
        if all(item["passed"] for item in checks)
        else "AUDIT_FAILED",
        "counts": {
            "declared_relation_types": len(declared),
            "builder_emitted_relation_types": len(emitted),
            "declared_but_unemitted": len(declared - emitted),
            "canvas_advertised_relation_types": len(advertised),
            "canvas_only_relation_types": len(advertised - declared),
            "configured_triple_combinations": len(TRIPLE_COMBINATIONS),
            "six_clash_pairs_in_knowledge": len(SIX_CLASH),
            "six_harmony_pairs_in_knowledge": len(SIX_HARMONY),
            "temporal_relation_builders": 0,
            "findings": len(findings),
        },
        "declared_relation_types": sorted(declared),
        "builder_emitted_relation_types": sorted(emitted),
        "declared_but_unemitted": sorted(declared - emitted),
        "canvas_only_relation_types": sorted(advertised - declared),
        "relation_matrix": relation_matrix,
        "witnesses": witnesses,
        "findings": findings,
        "checks": checks,
        "ra1_entry_order": [
            "consume existing deterministic branch-relation materials",
            "replace sample-specialized combinations with approved relation definitions",
            "emit true n-ary assertions for n-ary structures",
            "add explicit luck/year cross-layer relation compilation",
            "add minimal positive, negative, missing-member, and temporal fixtures",
            "only then admit relations to path qualification",
        ],
        "relation_semantics_modified": False,
        "formal_state_modified": False,
        "llm_used": False,
    }


def _witness(reading_id: str, pillars: list[str]) -> dict[str, Any]:
    birth = BirthInputCanonical(
        birth_input_id=f"birth:{reading_id}",
        gender="male",
        calendar_type="solar",
        birth_date="2000-01-01",
        birth_time="00:30",
        timezone="Asia/Shanghai",
        year_pillar=pillars[0],
        month_pillar=pillars[1],
        day_pillar=pillars[2],
        hour_pillar=pillars[3],
        input_quality="synthetic_structural_fixture",
    )
    store = build_bazi_material_store(
        reading_id=reading_id,
        birth_input=birth,
        calendar=normalize_birth_input(birth),
    )
    graph = build_mingli_graph_from_material_store(store)
    relation_material = next(
        item
        for item in store.materials
        if item.material_id.endswith(":bazi:branch_relations")
    )
    triples = [
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION
    ]
    return {
        "pillars": pillars,
        "material_relation_types": sorted(
            item["type"] for item in relation_material.raw_value["relations"]
        ),
        "graph_relation_types": sorted({edge.edge_type.value for edge in graph.edges}),
        "triple_edge_count": len(triples),
        "max_triple_participant_arity": max(
            (len(edge.participant_node_ids) for edge in triples),
            default=0,
        ),
    }


def _test_reference_counts(relation_types: set[str]) -> dict[str, int]:
    sources = {
        path: path.read_text(encoding="utf-8")
        for path in (ROOT / "tests").rglob("*.py")
    }
    return {
        relation_type: sum(relation_type in source for source in sources.values())
        for relation_type in sorted(relation_types)
    }


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _check(name: str, passed: bool) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit six-pillar relation coverage")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_six_pillar_relation_coverage()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] != "AUDIT_FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
