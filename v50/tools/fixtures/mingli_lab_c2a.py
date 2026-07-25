from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.engines.bazi.temporal_service import CanonicalTemporalService
from core.engines.bazi.knowledge import BRANCH_ELEMENTS, BRANCH_POLARITY, HIDDEN_STEMS, STEM_ELEMENTS, STEM_POLARITY
from core.engines.bazi.material_engine import resolve_ten_god
from core.engines.birth_calendar import resolve_birth_input_pillars
from core.graph import build_mingli_graph_from_material_store, explore_mingli_paths
from core.graph.contracts import MingliGraph, MingliGraphEdge, MingliGraphNode
from product.agent_case_store import PostgresAgentCaseStore
from product.canvas_projection import ReadOnlySixPillarCanvasService
from product.projection_refs import anonymous_ref as _anonymous_ref


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    ROOT
    / "archive"
    / "proofs"
    / "prototypes"
    / "mingli-lab-c2a"
    / "fixture.json"
)
DEFAULT_DATABASE_URL = "postgresql:///qiazhi_v50?host=/tmp"
HOUR_SAMPLES = tuple((hour, f"{hour:02d}:30") for hour in range(0, 24, 2))
RELATION_LABELS = {
    "generates": "相生",
    "controls": "相克",
    "same_element_support": "同气",
    "stores": "藏干",
    "roots": "通根",
    "forms_half_combination": "半合",
    "forms_triple_combination": "三合",
    "clashes": "相冲",
    "harmonizes": "相合",
    "position_link": "同柱",
}
_TEMPORAL_SERVICE = CanonicalTemporalService()


def build_fixture(*, database_url: str, case_id: str, user_id: str) -> dict[str, Any]:
    store = PostgresAgentCaseStore(database_url)
    row = store.get(case_id=case_id, user_id=user_id)
    if not row:
        raise ValueError("prototype_case_not_found")
    birth_payload = row.get("birth_input")
    if not isinstance(birth_payload, dict):
        raise ValueError("prototype_birth_input_missing")
    birth = BirthInputCanonical.model_validate(birth_payload)
    service = ReadOnlySixPillarCanvasService(case_store=store)
    formal = service.issue(case_id=case_id, participant_id=user_id, account_role="member")
    natal = formal["stages"]["natal"]["spec"]
    committed = [
        item for item in natal["paths"]
        if item["trace"]["epistemic_status"] == "committed"
    ]
    if len(committed) != 1:
        raise ValueError("prototype_requires_one_committed_path")
    formal_path = _formal_path(committed[0], natal)
    baseline_relations = _visible_relations_from_spec(natal)
    baseline_pillars = [
        f"{item['stem']}{item['branch']}"
        for item in natal["semantic_slots"]
    ]
    if len(baseline_pillars) != 4:
        raise ValueError("prototype_requires_four_natal_pillars")

    variants: list[dict[str, Any]] = []
    for index, (_, time_value) in enumerate(HOUR_SAMPLES):
        candidate_birth = resolve_birth_input_pillars(birth.model_copy(update={
            "birth_time": time_value,
            "year_pillar": "",
            "month_pillar": "",
            "day_pillar": "",
            "hour_pillar": "",
        }))
        graph = _graph(candidate_birth, f"c2a-{index:02d}")
        variant = _variant(
            index=index,
            time_value=time_value,
            birth=candidate_birth,
            graph=graph,
            baseline_pillars=baseline_pillars,
            baseline_relations=baseline_relations,
            formal_path=formal_path,
        )
        variants.append(variant)

    baseline_index = next(
        (
            index for index, item in enumerate(variants)
            if item["pillars"] == baseline_pillars
        ),
        None,
    )
    if baseline_index is None:
        raise ValueError("prototype_baseline_variant_missing")

    return {
        "schema_version": "deepbazi.mingli_lab_c2a_fixture.v1",
        "prototype": "Mingli Lab / 命局实验台",
        "source": {
            "case_ref": hashlib.sha256(case_id.encode("utf-8")).hexdigest()[:12],
            "source_mode": "real_formal_life_case_anonymized",
            "chart_version_id": _anonymous_ref(formal["source"]["chart_version_id"], "chart"),
            "life_case_version": formal["source"]["life_case_version"],
            "contains_personal_identity": False,
        },
        "formal": {
            "pillars": baseline_pillars,
            "luck_pillar": formal["source"]["luck_pillar"],
            "luck_year_range": formal["source"]["luck_year_range"],
            "annual_pillar": formal["source"]["annual_pillar"],
            "analysis_year": formal["source"]["analysis_year"],
            "path": formal_path,
        },
        "baseline_variant_index": baseline_index,
        "variants": variants,
        "year_dial": [
            {
                "year": year,
                "pillar": _TEMPORAL_SERVICE.derive_annual_pillar(year),
                "source_mode": "official" if year == formal["source"]["analysis_year"] else "hypothetical",
                "formal_temporal_effect_available": False,
            }
            for year in range(2024, 2029)
        ],
        "boundaries": [
            "实验副本不修改正式命盘或 LifeCase",
            "变体 Graph 是确定性结构证据，不是专业命理结论",
            "原正式主路径只作为比较基线，不自动转移到变体",
            "非正式流年只表示历法时间信号，不表示已验证的现实作用",
            "原型不调用 LLM，不保存出生资料或用户身份",
        ],
    }


def _graph(birth: BirthInputCanonical, reading_id: str) -> MingliGraph:
    calendar = normalize_birth_input(birth)
    materials = build_bazi_material_store(
        reading_id=reading_id,
        birth_input=birth,
        calendar=calendar,
    )
    return build_mingli_graph_from_material_store(materials)


def _formal_path(path: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    nodes = {item["node_ref"]: item for item in spec["nodes"]}
    relations = {item["relation_ref"]: item for item in spec["relations"]}
    segments = []
    for relation_ref in path["relation_refs"]:
        relation = relations[relation_ref]
        source = nodes[relation["from_node_ref"]]
        target = nodes[relation["to_node_ref"]]
        segments.append({
            "relation_ref": _anonymous_ref(relation_ref, "relation"),
            "relation_type": relation["relation_type"],
            "relation_label": relation["label"],
            "from_anchor": _spec_anchor(source),
            "to_anchor": _spec_anchor(target),
            "from_label": source["label"],
            "to_label": target["label"],
        })
    ordered_nodes = _ordered_path_nodes(segments)
    return {
        "path_ref": _anonymous_ref(path["path_ref"], "path"),
        "label": path["label"],
        "authority": "committed_life_case",
        "epistemic_status": "committed",
        "ordered_nodes": ordered_nodes,
        "segments": segments,
        "source_refs": [_anonymous_ref(item, "source") for item in path["trace"]["source_refs"]],
        "commitment_refs": [_anonymous_ref(item, "commitment") for item in path["trace"]["commitment_refs"]],
    }


def _variant(
    *,
    index: int,
    time_value: str,
    birth: BirthInputCanonical,
    graph: MingliGraph,
    baseline_pillars: list[str],
    baseline_relations: list[dict[str, Any]],
    formal_path: dict[str, Any],
) -> dict[str, Any]:
    pillars = [birth.year_pillar, birth.month_pillar, birth.day_pillar, birth.hour_pillar]
    nodes = _visible_nodes(graph, birth.day_pillar[0])
    relations = _visible_relations(graph)
    relation_index = {
        (item["from_anchor"], item["to_anchor"], item["relation_type"]): item
        for item in relations
    }
    continuity = []
    for segment in formal_path["segments"]:
        replacement = relation_index.get((
            segment["from_anchor"],
            segment["to_anchor"],
            segment["relation_type"],
        ))
        continuity.append({
            "baseline": segment,
            "status": "preserved" if replacement else "missing",
            "variant_relation": replacement,
        })
    preserved_count = sum(item["status"] == "preserved" for item in continuity)
    if preserved_count == len(continuity):
        continuity_status = "preserved"
    elif preserved_count:
        continuity_status = "partial"
    else:
        continuity_status = "broken"
    baseline_keys = {_relation_key(item) for item in baseline_relations}
    variant_keys = {_relation_key(item) for item in relations}
    added = [item for item in relations if _relation_key(item) not in baseline_keys]
    removed = [item for item in baseline_relations if _relation_key(item) not in variant_keys]
    candidate_path = _graph_candidate(graph)
    return {
        "variant_id": f"hour-variant-{index:02d}",
        "source_mode": "canonical" if pillars == baseline_pillars else "hypothetical",
        "time_value": time_value,
        "time_range": _time_range(time_value),
        "pillars": pillars,
        "calendar_compatible_with_locked_ymd": pillars[:3] == baseline_pillars[:3],
        "calendar_boundary_changes": [
            {"slot": slot, "before": baseline_pillars[i], "after": pillars[i]}
            for i, slot in enumerate(("year", "month", "day"))
            if pillars[i] != baseline_pillars[i]
        ],
        "nodes": nodes,
        "relations": relations,
        "formal_path_reference": {
            "continuity_status": continuity_status,
            "preserved_segments": preserved_count,
            "total_segments": len(continuity),
            "segments": continuity,
            "authority": "deterministic_structural_comparison",
        },
        "graph_candidate": candidate_path,
        "diff": {
            "changed_pillars": [
                {"slot": slot, "before": baseline_pillars[i], "after": pillars[i]}
                for i, slot in enumerate(("year", "month", "day", "hour"))
                if pillars[i] != baseline_pillars[i]
            ],
            "added_relation_count": len(added),
            "removed_relation_count": len(removed),
            "added_relations": added[:6],
            "removed_relations": removed[:6],
        },
    }


def _visible_nodes(graph: MingliGraph, day_stem: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for node in graph.nodes:
        if node.node_type.value not in {"stem", "branch"}:
            continue
        branch = node.label if node.node_type.value == "branch" else ""
        hidden = [
            {
                "stem": stem,
                "element": STEM_ELEMENTS.get(stem, ""),
                "polarity": STEM_POLARITY.get(stem, ""),
                "ten_god": resolve_ten_god(day_stem=day_stem, other_stem=stem),
            }
            for stem in HIDDEN_STEMS.get(branch, [])
        ]
        nodes.append({
            "node_key": node.position,
            "label": node.label,
            "node_type": node.node_type.value,
            "position": node.position,
            "element": node.element,
            "polarity": node.yin_yang or BRANCH_POLARITY.get(branch, ""),
            "ten_god": node.ten_god,
            "hidden_stems": hidden,
            "source_refs": [
                _anonymous_ref(item, "source")
                for item in [*node.material_refs, *node.evidence_refs]
            ],
        })
    return nodes


def _visible_relations(graph: MingliGraph) -> list[dict[str, Any]]:
    nodes = {item.node_id: item for item in graph.nodes}
    output = []
    for edge in graph.edges:
        source = nodes[edge.from_node_id]
        target = nodes[edge.to_node_id]
        if source.node_type.value not in {"stem", "branch"} or target.node_type.value not in {"stem", "branch"}:
            continue
        output.append(_relation(edge=edge, source=source, target=target))
    return output


def _visible_relations_from_spec(spec: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = {item["node_ref"]: item for item in spec["nodes"]}
    output = []
    for relation in spec["relations"]:
        source = nodes[relation["from_node_ref"]]
        target = nodes[relation["to_node_ref"]]
        if source["node_type"] not in {"stem", "branch"} or target["node_type"] not in {"stem", "branch"}:
            continue
        output.append({
            "relation_id": _anonymous_ref(relation["relation_ref"], "relation"),
            "from_key": _spec_anchor(source),
            "to_key": _spec_anchor(target),
            "from_anchor": _spec_anchor(source),
            "to_anchor": _spec_anchor(target),
            "from_label": source["label"],
            "to_label": target["label"],
            "relation_type": relation["relation_type"],
            "label": relation["label"],
            "source_refs": [
                _anonymous_ref(item, "source")
                for item in relation["trace"]["source_refs"]
            ],
        })
    return output


def _relation(*, edge: MingliGraphEdge, source: MingliGraphNode, target: MingliGraphNode) -> dict[str, Any]:
    relation_type = edge.edge_type.value
    return {
        "relation_id": _anonymous_ref(edge.edge_id, "relation"),
        "from_key": source.position,
        "to_key": target.position,
        "from_anchor": source.position,
        "to_anchor": target.position,
        "from_label": source.label,
        "to_label": target.label,
        "relation_type": relation_type,
        "label": f"{source.label}{RELATION_LABELS.get(relation_type, relation_type)}{target.label}",
        "source_refs": [
            _anonymous_ref(item, "source")
            for item in [*edge.material_refs, *edge.evidence_refs]
        ],
    }


def _graph_candidate(graph: MingliGraph) -> dict[str, Any] | None:
    visible = {
        node.node_id
        for node in graph.nodes
        if node.node_type.value in {"stem", "branch"}
    }
    nodes = {item.node_id: item for item in graph.nodes}
    edges = {item.edge_id: item for item in graph.edges}
    paths = explore_mingli_paths(graph, max_edges=3, limit=80).paths
    selected = next((
        item for item in paths
        if len(item.edge_ids) >= 2
        and set(item.node_ids).issubset(visible)
        and all(edges[edge_id].edge_type.value != "position_link" for edge_id in item.edge_ids)
    ), None)
    if selected is None:
        return None
    return {
        "path_ref": _anonymous_ref(selected.path_id, "path"),
        "authority": "experimental_graph_candidate",
        "epistemic_status": "candidate",
        "node_keys": [nodes[item].position for item in selected.node_ids],
        "node_labels": [nodes[item].label for item in selected.node_ids],
        "segments": [
            _relation(
                edge=edges[edge_id],
                source=nodes[edges[edge_id].from_node_id],
                target=nodes[edges[edge_id].to_node_id],
            )
            for edge_id in selected.edge_ids
        ],
        "source_refs": [
            _anonymous_ref(item, "source")
            for item in [selected.path_id, *selected.graph_refs, *selected.evidence_refs]
        ],
        "warning": "Graph 排名候选只用于结构实验，不是 LifeCase 正式主路径。",
    }


def _spec_anchor(node: dict[str, Any]) -> str:
    slot = str(node["semantic_slot_ref"]).removeprefix("slot-natal-")
    return f"{slot}_{node['node_type']}"


def _relation_key(item: dict[str, Any]) -> str:
    return "|".join((
        item["from_anchor"], item["from_label"], item["relation_type"],
        item["to_anchor"], item["to_label"],
    ))


def _ordered_path_nodes(segments: list[dict[str, Any]]) -> list[dict[str, str]]:
    targets = {item["to_anchor"] for item in segments}
    current = next((item for item in segments if item["from_anchor"] not in targets), segments[0])
    ordered = [{"anchor": current["from_anchor"], "label": current["from_label"]}]
    remaining = list(segments)
    while remaining:
        segment = next((item for item in remaining if item["from_anchor"] == ordered[-1]["anchor"]), None)
        if segment is None:
            segment = remaining[0]
            if segment["from_anchor"] != ordered[-1]["anchor"]:
                ordered.append({"anchor": segment["from_anchor"], "label": segment["from_label"]})
        ordered.append({"anchor": segment["to_anchor"], "label": segment["to_label"]})
        remaining.remove(segment)
    return ordered


def _time_range(time_value: str) -> str:
    hour = int(time_value[:2])
    branch = "子丑寅卯辰巳午未申酉戌亥"[hour // 2]
    start = (hour - 1) % 24
    end = (hour + 1) % 24
    return f"{branch}时 · {start:02d}:00–{end:02d}:00"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the anonymized Mingli Lab C2A prototype fixture.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    fixture = build_fixture(database_url=args.database_url, case_id=args.case_id, user_id=args.user_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "fixture_ready",
        "output": str(args.output),
        "case_ref": fixture["source"]["case_ref"],
        "variant_count": len(fixture["variants"]),
        "baseline_variant_index": fixture["baseline_variant_index"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
