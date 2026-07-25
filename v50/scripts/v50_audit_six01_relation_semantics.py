from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations_with_replacement, product
from pathlib import Path
from typing import Any

from core.engines.bazi.knowledge import (
    BRANCH_ELEMENTS,
    HALF_TRIPLE_HARMONY,
    HIDDEN_STEMS,
    STEM_ELEMENTS,
    TRIPLE_HARMONY,
    TRIPLE_PUNISHMENT,
)
from core.engines.bazi.material_engine import (
    derive_branch_relations,
    derive_element_relations,
    resolve_ten_god,
)
from core.graph.contracts import MingliGraphEdgeType
from core.graph.path_qualification import qualify_relation_for_path
from core.graph.provenance import NodeRef, relation_directionality


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/v50_six01_relation_semantics_v1.json"
STEMS = tuple(STEM_ELEMENTS)
BRANCHES = tuple(BRANCH_ELEMENTS)
SIX_SLOTS = (
    {"slot_id": "natal_year", "scope": "natal", "slot": "year", "temporal": False},
    {"slot_id": "natal_month", "scope": "natal", "slot": "month", "temporal": False},
    {"slot_id": "natal_day", "scope": "natal", "slot": "day", "temporal": False},
    {"slot_id": "natal_hour", "scope": "natal", "slot": "hour", "temporal": False},
    {"slot_id": "luck", "scope": "luck", "slot": "luck", "temporal": True},
    {"slot_id": "annual", "scope": "year", "slot": "annual", "temporal": True},
)


def audit_six01_relation_semantics() -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    stem_matrix = [_stem_pair(source, target, fixture) for source, target in product(STEMS, repeat=2)]
    branch_matrix = [
        _branch_pair(left, right)
        for left, right in combinations_with_replacement(BRANCHES, 2)
    ]
    stem_branch_matrix = [
        _stem_branch(stem, branch) for stem, branch in product(STEMS, BRANCHES)
    ]
    scope_matrix = _scope_matrix()
    nary_matrix = _nary_matrix(fixture)
    fixture_results = [
        _run_fixture(category, item)
        for category in ("positive", "negative", "boundary")
        for item in fixture[category]
    ]
    ontology = [_ontology_row(edge_type) for edge_type in MingliGraphEdgeType]
    gaps = _open_gaps()
    result: dict[str, Any] = {
        "schema_version": "deepbazi.six01_relation_semantics_audit.v1",
        "status": "FOUNDATION_AUDIT_COMPLETE_WITH_OPEN_SEMANTICS",
        "authority_boundary": fixture["authority_boundary"],
        "counts": {
            "ordered_stem_pairs": len(stem_matrix),
            "unordered_branch_pairs_with_repeat": len(branch_matrix),
            "stem_branch_pairs": len(stem_branch_matrix),
            "ordered_six_slot_pairs": len(scope_matrix),
            "formal_nary_relations": sum(item["runtime_status"] == "implemented" for item in nary_matrix),
            "research_candidate_nary_relations": sum(item["runtime_status"] != "implemented" for item in nary_matrix),
            "runtime_relation_types": len(ontology),
            "positive_fixtures": len(fixture["positive"]),
            "negative_fixtures": len(fixture["negative"]),
            "boundary_fixtures": len(fixture["boundary"]),
            "open_semantic_gaps": len(gaps),
        },
        "matrices": {
            "stem_to_stem": stem_matrix,
            "branch_to_branch": branch_matrix,
            "stem_to_branch": stem_branch_matrix,
            "six_slot_identity_and_time": scope_matrix,
            "nary_relations": nary_matrix,
        },
        "runtime_ontology": ontology,
        "fixture_results": fixture_results,
        "open_semantic_gaps": gaps,
        "conclusions": {
            "structural_relation_is_activation": False,
            "combination_is_transformation": False,
            "fixed_strength_is_calibrated_measurement": False,
            "client_or_lab_may_promote_relation": False,
            "formal_algorithm_changed": False,
        },
        "formal_state_modified": False,
        "llm_used": False,
    }
    result["content_sha256"] = _hash(result)
    return result


def _stem_pair(source: str, target: str, fixture: dict[str, Any]) -> dict[str, Any]:
    relations = _element_relations(
        ("source", STEM_ELEMENTS[source]),
        ("target", STEM_ELEMENTS[target]),
    )
    candidates = fixture["reference_candidates"]["stem_five_combinations"]
    candidate = next(
        (
            item
            for item in candidates
            if set(item["participants"]) == {source, target} and source != target
        ),
        None,
    )
    return {
        "source": source,
        "target": target,
        "source_element": STEM_ELEMENTS[source],
        "target_element": STEM_ELEMENTS[target],
        "runtime_relations": relations,
        "ten_god_from_source": resolve_ten_god(day_stem=source, other_stem=target),
        "stem_combination_candidate": candidate,
        "stem_combination_runtime_status": "not_implemented" if candidate else "not_applicable",
        "activation_status": "not_evaluated",
        "priority_status": "not_defined",
    }


def _branch_pair(left: str, right: str) -> dict[str, Any]:
    relations = derive_branch_relations([("left", left), ("right", right)])
    return {
        "participants": [left, right],
        "runtime_branch_relations": sorted({str(item["type"]) for item in relations}),
        "runtime_element_relations": _element_relations(
            ("left", BRANCH_ELEMENTS[left]),
            ("right", BRANCH_ELEMENTS[right]),
        ),
        "multiple_structural_relations_preserved": len(relations) > 1,
        "activation_status": "not_evaluated",
        "transformation_status": "not_defined",
        "priority_status": "not_defined",
    }


def _stem_branch(stem: str, branch: str) -> dict[str, Any]:
    hidden = HIDDEN_STEMS[branch]
    root_candidates = [
        item for item in hidden if STEM_ELEMENTS[item] == STEM_ELEMENTS[stem]
    ]
    return {
        "stem": stem,
        "branch": branch,
        "stem_element": STEM_ELEMENTS[stem],
        "branch_dominant_element": BRANCH_ELEMENTS[branch],
        "hidden_stems": hidden,
        "runtime_dominant_element_relations": _element_relations(
            ("stem", STEM_ELEMENTS[stem]),
            ("branch", BRANCH_ELEMENTS[branch]),
        ),
        "day_master_root_candidate_hidden_stems": root_candidates,
        "position_link_requires_same_pillar": True,
        "explicit_cross_level_runtime_scope": (
            "day_master_root_only" if root_candidates else "position_link_only"
        ),
        "activation_status": "not_evaluated",
        "priority_status": "not_defined",
    }


def _scope_matrix() -> list[dict[str, Any]]:
    refs = {item["slot_id"]: _slot_node_ref(item) for item in SIX_SLOTS}
    rows: list[dict[str, Any]] = []
    for source, target in product(SIX_SLOTS, repeat=2):
        source_temporal = bool(source["temporal"])
        target_temporal = bool(target["temporal"])
        rows.append({
            "source_slot": source["slot_id"],
            "target_slot": target["slot_id"],
            "source_node_ref": refs[source["slot_id"]].node_ref,
            "target_node_ref": refs[target["slot_id"]].node_ref,
            "identity_distinct": (
                refs[source["slot_id"]].node_ref != refs[target["slot_id"]].node_ref
                if source["slot_id"] != target["slot_id"]
                else True
            ),
            "temporal_role": (
                "temporal_actor_on_natal"
                if source_temporal and not target_temporal
                else "natal_context_for_temporal"
                if not source_temporal and target_temporal
                else "same_layer_family"
            ),
            "relation_derivation": "same_level_only",
            "universal_priority_rule": "not_defined",
        })
    return rows


def _nary_matrix(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "relation_type": "triple_harmony",
            "participants": sorted(members),
            "relation_id": relation_id,
            "result_element": element,
            "bridge_branch": bridge,
            "arity": 3,
            "runtime_status": "implemented",
            "transformation_status": "not_defined",
        }
        for members, (relation_id, element, bridge) in TRIPLE_HARMONY.items()
    ]
    rows.extend(
        {
            "relation_type": "triple_punishment",
            "participants": list(required_order),
            "relation_id": relation_id,
            "result_element": "",
            "bridge_branch": "",
            "arity": 3,
            "runtime_status": "implemented",
            "transformation_status": "not_applicable",
        }
        for _, (relation_id, required_order) in TRIPLE_PUNISHMENT.items()
    )
    rows.extend(
        {
            "relation_type": "three_meeting",
            "participants": item["participants"],
            "relation_id": "research-candidate:" + "".join(item["participants"]),
            "result_element": item["candidate_element"],
            "bridge_branch": "",
            "arity": 3,
            "runtime_status": "research_candidate_not_implemented",
            "transformation_status": "conditions_unfrozen",
        }
        for item in fixture["reference_candidates"]["branch_three_meetings"]
    )
    return sorted(rows, key=lambda item: (item["runtime_status"], item["relation_type"], item["participants"]))


def _ontology_row(edge_type: MingliGraphEdgeType) -> dict[str, Any]:
    eligibility, reason_refs = qualify_relation_for_path(edge_type)
    levels = {
        "stores": ["branch", "hidden_stem"],
        "roots": ["branch", "stem"],
        "position_link": ["stem", "branch"],
        "forms_half_combination": ["branch", "branch"],
        "forms_triple_combination": ["branch", "branch", "branch"],
        "clashes": ["branch", "branch"],
        "harmonizes": ["branch", "branch"],
        "harms": ["branch", "branch"],
        "breaks": ["branch", "branch"],
        "punishes": ["branch", "branch_or_nary"],
    }.get(edge_type.value, ["same_level_visible_node", "same_level_visible_node"])
    return {
        "relation_type": edge_type.value,
        "directionality": relation_directionality(edge_type.value).value,
        "participant_levels": levels,
        "path_eligibility": eligibility.value,
        "eligibility_reason_refs": reason_refs,
        "epistemic_role": "candidate_structural_observation",
        "activation_role": "none_temporal_activation_is_a_separate_diff_state",
    }


def _open_gaps() -> list[dict[str, str]]:
    return [
        {"gap_id": "SIX-G01", "area": "stem_relation", "status": "open", "finding": "Five stem combinations are catalogued only as research candidates; runtime has no formal structural or transformation contract."},
        {"gap_id": "SIX-G02", "area": "stem_relation", "status": "open_school_dependent", "finding": "Stem-clash definitions differ by school and no formal profile is frozen."},
        {"gap_id": "SIX-G03", "area": "branch_relation", "status": "open", "finding": "Four three-meeting structures are not implemented in the formal relation engine."},
        {"gap_id": "SIX-G04", "area": "transformation", "status": "open", "finding": "Combination existence and successful transformation are not separated by a validated condition contract."},
        {"gap_id": "SIX-G05", "area": "cross_level", "status": "partial", "finding": "Stem-branch action is limited to dominant-element edges, same-pillar links and day-master roots; broader cross-level mechanisms are unqualified."},
        {"gap_id": "SIX-G06", "area": "position", "status": "open", "finding": "Month command, adjacency, distance and six-slot position priority are not encoded as relation qualifications."},
        {"gap_id": "SIX-G07", "area": "temporal_activation", "status": "partial", "finding": "Luck/year relations are derived, but structural presence, activation, reinforcement and blocking lack one general trigger contract."},
        {"gap_id": "SIX-G08", "area": "conflict_resolution", "status": "open", "finding": "Multiple simultaneous relations are preserved, but no approved priority or coexistence policy selects their practical effect."},
        {"gap_id": "SIX-G09", "area": "calibration", "status": "open", "finding": "Legacy edge strengths remain fixed compatibility values and are not calibrated evidence."},
    ]


def _run_fixture(category: str, item: dict[str, Any]) -> dict[str, Any]:
    observed = _fixture_observations(item)
    expected = set(item.get("expect", []))
    forbidden = set(item.get("forbid", []))
    return {
        "category": category,
        "fixture_id": item["fixture_id"],
        "observed": sorted(observed),
        "expected": sorted(expected),
        "forbidden": sorted(forbidden),
        "passed": expected.issubset(observed) and forbidden.isdisjoint(observed),
    }


def _fixture_observations(item: dict[str, Any]) -> set[str]:
    domain = item["domain"]
    participants = item["participants"]
    if domain == "stem_pair":
        rows = derive_element_relations([
            ("left", STEM_ELEMENTS[participants[0]]),
            ("right", STEM_ELEMENTS[participants[1]]),
        ])
        return {str(row["type"]) for row in rows}
    if domain in {"branch_pair", "branch_nary"}:
        rows = derive_branch_relations([
            (f"slot-{index}", branch) for index, branch in enumerate(participants)
        ])
        return {str(row["type"]) for row in rows}
    if domain == "stem_branch":
        stem, branch = participants
        observed = {
            str(row["type"])
            for row in derive_element_relations([
                ("stem", STEM_ELEMENTS[stem]),
                ("branch", BRANCH_ELEMENTS[branch]),
            ])
        }
        if any(STEM_ELEMENTS[item] == STEM_ELEMENTS[stem] for item in HIDDEN_STEMS[branch]):
            observed.add("day_master_root_candidate")
        return observed
    if domain == "scope_identity":
        refs = {item["slot_id"]: _slot_node_ref(item).node_ref for item in SIX_SLOTS}
        return {"distinct_node_identity"} if refs[participants[0]] != refs[participants[1]] else set()
    if domain == "catalog":
        return {"structural_not_activation"}
    raise ValueError(f"unknown_six01_fixture_domain:{domain}")


def _element_relations(left: tuple[str, str], right: tuple[str, str]) -> list[dict[str, str]]:
    rows = derive_element_relations([left, right])
    return [
        {
            "relation_type": str(item["type"]),
            "direction": (
                "source_to_target"
                if item["source_ref"] == left[0]
                else "target_to_source"
            ),
        }
        for item in rows
    ]


def _slot_node_ref(item: dict[str, Any]) -> NodeRef:
    return NodeRef(
        scene_ref="scene-scope:six01",
        life_case_id="life-case:six01",
        chart_version_id="chart:six01",
        world_id="world:six01",
        scope=item["scope"],
        slot=item["slot"],
        level="pillar",
        component="slot-identity",
        temporal_snapshot_ref=(
            f"snapshot:six01:{item['slot_id']}" if item["temporal"] else ""
        ),
    )


def _hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit six-pillar relation semantics")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_six01_relation_semantics()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(json.dumps({
            "status": result["status"],
            "output": str(args.output),
            "content_sha256": result["content_sha256"],
            "counts": result["counts"],
        }, ensure_ascii=False, sort_keys=True))
    else:
        print(rendered, end="")
    return 0 if all(item["passed"] for item in result["fixture_results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
