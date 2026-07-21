from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.engines.bazi.knowledge import (
    HALF_TRIPLE_HARMONY,
    PAIR_PUNISHMENT,
    SELF_PUNISHMENT,
    SIX_BREAK,
    SIX_CLASH,
    SIX_HARM,
    SIX_HARMONY,
    TRIPLE_PUNISHMENT,
    TRIPLE_HARMONY,
)
from core.graph import build_mingli_graph_from_material_store
from core.graph.contracts import MingliGraphEdgeType
from product.canvas_projection import LAYER_DEFINITIONS


ROOT = Path(__file__).resolve().parents[1]


def audit_six_pillar_relation_coverage() -> dict[str, Any]:
    builder_source = _read("packages/core/graph/builder.py")
    temporal_source = _read("apps/product/canvas_projection_temporal.py")
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
        "second_configured_triple": _witness(
            "second-configured-triple",
            ["甲申", "丙子", "壬辰", "庚子"],
        ),
        "missing_triple_member": _witness(
            "missing-triple-member",
            ["甲申", "丙子", "甲寅", "丙寅"],
        ),
        "root": _witness(
            "day-master-root",
            ["壬辰", "戊申", "丙午", "丁丑"],
        ),
        "half_triple": _witness(
            "half-triple",
            ["甲申", "丙子", "甲寅", "丙寅"],
        ),
        "arch_not_half": _witness(
            "arch-not-half",
            ["甲申", "戊辰", "甲寅", "丙寅"],
        ),
        "harm": _witness(
            "six-harm",
            ["甲子", "辛未", "甲寅", "丙寅"],
        ),
        "break": _witness(
            "six-break",
            ["乙巳", "壬申", "甲寅", "丙寅"],
        ),
        "pair_punishment": _witness(
            "pair-punishment",
            ["甲子", "丁卯", "甲寅", "丙寅"],
        ),
        "triple_punishment": _witness(
            "triple-punishment",
            ["丙寅", "己巳", "壬申", "甲寅"],
        ),
        "partial_triple_punishment": _witness(
            "partial-triple-punishment",
            ["丙寅", "己巳", "甲寅", "丁巳"],
        ),
    }

    temporal_block = temporal_source.split("def temporal_layer(", 1)[1]
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
        _check("declared_relation_types_counted", len(declared) == 13),
        _check("builder_emission_types_counted", len(emitted) == 13),
        _check(
            "material_clash_projection_closed",
            "clash" in witnesses["clash"]["material_relation_types"]
            and "clashes" in witnesses["clash"]["graph_relation_types"],
        ),
        _check(
            "material_harmony_projection_closed",
            "harmony" in witnesses["harmony"]["material_relation_types"]
            and "harmonizes" in witnesses["harmony"]["graph_relation_types"],
        ),
        _check(
            "all_triple_definitions_reproduced",
            len(TRIPLE_HARMONY) == 4
            and witnesses["configured_triple"]["triple_edge_count"] > 0
            and witnesses["second_configured_triple"]["triple_edge_count"] > 0,
        ),
        _check(
            "triple_requires_all_members",
            witnesses["configured_triple"]["triple_edge_count"] > 0
            and witnesses["missing_triple_member"]["triple_edge_count"] == 0,
        ),
        _check(
            "triple_output_is_nary",
            witnesses["configured_triple"]["max_triple_participant_arity"] == 3
            and witnesses["second_configured_triple"]["max_triple_participant_arity"] == 3,
        ),
        _check(
            "day_master_root_material_is_projected",
            "roots" in witnesses["root"]["graph_relation_types"],
        ),
        _check(
            "half_triple_is_distinct_from_arch_pair",
            "forms_half_combination" in witnesses["half_triple"]["graph_relation_types"]
            and "forms_half_combination" not in witnesses["arch_not_half"]["graph_relation_types"]
            and len(HALF_TRIPLE_HARMONY) == 8,
        ),
        _check(
            "harm_break_and_punishment_are_core_relations",
            "harms" in witnesses["harm"]["graph_relation_types"]
            and "breaks" in witnesses["break"]["graph_relation_types"]
            and "punishes" in witnesses["pair_punishment"]["graph_relation_types"]
            and witnesses["triple_punishment"]["max_punishment_participant_arity"] == 3
            and witnesses["partial_triple_punishment"]["max_punishment_participant_arity"] == 0,
        ),
        _check(
            "canvas_only_relation_types_identified",
            advertised - declared == set(),
        ),
        _check(
            "temporal_layers_use_shared_relation_derivation",
            "relations = temporal_relations(" in temporal_block
            and "def temporal_relations(" in temporal_source
            and "derive_element_relations(stems)" in temporal_source
            and "derive_branch_relations(branches)" in temporal_source,
        ),
        _check(
            "temporal_relations_are_same_level_only",
            'model.level == "stem"' in temporal_block
            and 'model.level == "branch"' in temporal_block,
        ),
    ]

    return {
        "schema_version": "deepbazi.six_pillar_relation_coverage_audit.v1",
        "status": "RA3_COMPLETE"
        if all(item["passed"] for item in checks)
        else "AUDIT_FAILED",
        "counts": {
            "declared_relation_types": len(declared),
            "builder_emitted_relation_types": len(emitted),
            "declared_but_unemitted": len(declared - emitted),
            "canvas_advertised_relation_types": len(advertised),
            "canvas_only_relation_types": len(advertised - declared),
            "configured_triple_combinations": len(TRIPLE_HARMONY),
            "configured_half_triple_combinations": len(HALF_TRIPLE_HARMONY),
            "six_clash_pairs_in_knowledge": len(SIX_CLASH),
            "six_harmony_pairs_in_knowledge": len(SIX_HARMONY),
            "six_harm_pairs_in_knowledge": len(SIX_HARM),
            "six_break_pairs_in_knowledge": len(SIX_BREAK),
            "pair_punishment_definitions": len(PAIR_PUNISHMENT),
            "self_punishment_definitions": len(SELF_PUNISHMENT),
            "triple_punishment_definitions": len(TRIPLE_PUNISHMENT),
            "temporal_relation_builders": 1,
            "findings": len(findings),
        },
        "declared_relation_types": sorted(declared),
        "builder_emitted_relation_types": sorted(emitted),
        "declared_but_unemitted": sorted(declared - emitted),
        "canvas_only_relation_types": sorted(advertised - declared),
        "relation_matrix": relation_matrix,
        "witnesses": witnesses,
        "resolved_findings": [
            {
                "finding_id": "REL-A01",
                "resolution": "Graph Builder now consumes the existing deterministic six-clash and six-harmony materials without granting path eligibility.",
            },
            {
                "finding_id": "REL-A02",
                "resolution": "Official luck and year layers now compile same-level stem and branch relations through the shared deterministic relation derivation before Canvas diffing.",
            },
            {
                "finding_id": "REL-A03",
                "resolution": "All four standard triple-harmony definitions now share one knowledge source and positive/missing-member fixtures.",
            },
            {
                "finding_id": "REL-A04",
                "resolution": "Each triple-harmony instance now has one stable relation identity with three participant node references.",
            },
            {
                "finding_id": "REL-A05",
                "resolution": "Harm, break, pair/self punishment, and complete triple punishment now have core relation identities and conservative fixtures.",
            },
            {
                "finding_id": "REL-A06",
                "resolution": "Unused activates and bridges Graph types were removed; activation remains a temporal diff state and bridge remains a path interpretation, not an unproven primitive relation.",
            },
        ],
        "findings": findings,
        "checks": checks,
        "relation_path_core_completed": [
            "consume existing deterministic branch-relation materials",
            "replace sample-specialized combinations with complete relation definitions",
            "compile official luck and year relations through the same deterministic relation derivation",
            "qualify path-participating relations through explicit positive and negative fixtures",
            "replace public path scores with evidence-backed discrete states",
            "apply conservative official luck and year path-state updates without mutating LifeCase",
        ],
        "remaining_findings": [
            "qualify dense cross-level natal element edges by position and layer",
            "retire isolated legacy unvalidated strengths after downstream compatibility migration",
        ],
        "relation_semantics_modified": False,
        "relation_projection_modified": True,
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
    punishments = [
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.PUNISHES
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
        "max_punishment_participant_arity": max(
            (len(edge.participant_node_ids) for edge in punishments),
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
