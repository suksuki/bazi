from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical, Topic
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.engines.bazi.temporal_service import CanonicalTemporalService
from core.engines.ziwei import build_ziwei_material_bundle_from_birth_input
from core.engines.ziwei.iztro_bridge import IztroZiweiUnavailable
from core.graph import (
    analyze_mingli_graph,
    build_mingli_graph_from_material_store,
    classify_node_roles,
    explore_mingli_paths,
)
from core.mingli_agent.contracts import ChartWorldInstance, KnowledgeExcerpt, WorldFact
from core.simulation import build_mingli_state_from_graph_analysis, run_ablation_simulation


ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_CARDS = ROOT / "data" / "knowledge" / "canon" / "knowledge_cards_v1.jsonl"
SYNTHETIC_TAXONOMY = ROOT / "data" / "validation" / "fixtures" / "synthetic_chart_taxonomy_v1.json"
_TEMPORAL_SERVICE = CanonicalTemporalService()

TEN_GOD_LABELS = {
    "bi_jian": "比肩",
    "jie_cai": "劫财",
    "shi_shen": "食神",
    "shang_guan": "伤官",
    "pian_cai": "偏财",
    "zheng_cai": "正财",
    "qi_sha": "七杀",
    "zheng_guan": "正官",
    "pian_yin": "偏印",
    "zheng_yin": "正印",
}

RELATION_LABELS = {
    "generates": "生",
    "controls": "克",
    "same_element_support": "同气",
    "stores": "藏",
    "roots": "通根",
    "forms_half_combination": "半合",
    "forms_triple_combination": "三合",
    "clashes": "冲",
    "harmonizes": "合",
    "position_link": "同柱",
}


def compile_chart_world(
    *,
    reading_id: str,
    birth_input: BirthInputCanonical,
    analysis_year: int | None = None,
    include_research_fixture_prior: bool = False,
) -> ChartWorldInstance:
    """Compile facts and tool observations without producing a Mingli verdict.

    Synthetic expectations are excluded by default.  Research callers may opt in
    when inspecting a fixture, but scored or production reasoning must keep the
    expected contract outside the model context.
    """

    calendar = normalize_birth_input(birth_input)
    store = build_bazi_material_store(reading_id=reading_id, birth_input=birth_input, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    paths = explore_mingli_paths(graph)
    roles = classify_node_roles(graph, paths)
    analysis = analyze_mingli_graph(graph, path_result=paths, role_result=roles)
    state = build_mingli_state_from_graph_analysis(analysis)
    ablation = run_ablation_simulation(state)
    timing = _timing_material(birth_input=birth_input, analysis_year=analysis_year or datetime.now().year)
    ziwei_profile, ziwei_facts = _compile_ziwei_world(
        reading_id=reading_id,
        birth_input=birth_input,
        analysis_year=analysis_year or datetime.now().year,
    )

    nodes = {node.node_id: node for node in graph.nodes}
    edges = {edge.edge_id: edge for edge in graph.edges}
    facts: list[WorldFact] = []
    facts.extend(_chart_material_facts(store))
    facts.extend(_graph_relation_facts(graph=graph, nodes=nodes))
    facts.extend(_path_observations(paths=paths, nodes=nodes, edges=edges))
    facts.extend(_role_observations(roles=roles))
    facts.extend(_ablation_observations(ablation=ablation))
    facts.extend(_importance_observations(analysis=analysis))
    facts.extend(_timing_observations(timing=timing))
    facts.extend(ziwei_facts)
    fixture_prior = _fixture_prior(birth_input) if include_research_fixture_prior else None
    if fixture_prior is not None:
        facts.append(fixture_prior)

    terms = _retrieval_terms(facts=facts, graph=graph)
    knowledge = retrieve_knowledge(terms=terms, limit=12)
    facts = [
        item.model_copy(update={"fact_id": f"{'F' if item.kind == 'fact' else 'O'}{index:03d}", "source_refs": [item.fact_id, *item.source_refs]})
        for index, item in enumerate(facts, start=1)
    ]
    knowledge = [
        item.model_copy(update={"knowledge_id": f"K{index:03d}", "source_refs": [item.knowledge_id, *item.source_refs]})
        for index, item in enumerate(knowledge, start=1)
    ]
    allowed_refs = _unique([
        *[fact.fact_id for fact in facts],
        *[ref for fact in facts for ref in fact.source_refs],
        *[item.knowledge_id for item in knowledge],
    ])
    return ChartWorldInstance(
        world_id=f"world:{reading_id}",
        reading_id=reading_id,
        pillars=[birth_input.year_pillar, birth_input.month_pillar, birth_input.day_pillar, birth_input.hour_pillar],
        birth_profile={
            "name": birth_input.name,
            "gender": birth_input.gender.value,
            "calendar_type": birth_input.calendar_type.value,
            "birth_date": birth_input.birth_date,
            "birth_time": birth_input.birth_time,
            "birth_location": birth_input.birth_location,
            "timezone": birth_input.timezone,
            "input_quality": birth_input.input_quality,
            "warnings": list(birth_input.warnings),
        },
        facts=facts,
        knowledge=knowledge,
        ziwei_profile=ziwei_profile,
        timing_context={
            **timing,
            "validation_status": "material_only",
            "publicly_supported": False,
        },
        allowed_evidence_refs=allowed_refs,
        boundaries=[
            "事实与工具观察不是最终命局判断。",
            "Graph、Path、Role 与 estimated sensitivity 当前均为 experimental_tool_observation。",
            "实验工具不得进入独立第一眼，也不得机械决定主假设、主做功或用神。",
            "Timing 当前为研究候选，只能输出条件性时机说明。",
            "现实职业和经历不得在第一轮先验推理中作为输入。",
            "紫微只使用已确认出生资料生成；来源不一致或时辰不确定时不得参与综合判断。",
            "八字与紫微不一致时必须保留差异并提出区分问题，不得机械平均。",
        ],
    )


def _compile_ziwei_world(
    *,
    reading_id: str,
    birth_input: BirthInputCanonical,
    analysis_year: int,
) -> tuple[dict[str, Any], list[WorldFact]]:
    try:
        bundle = build_ziwei_material_bundle_from_birth_input(
            reading_id=reading_id,
            birth_input=birth_input,
            topic=Topic.OVERVIEW,
            analysis_year=analysis_year,
        )
    except (IztroZiweiUnavailable, ValueError) as exc:
        profile = {
            "status": "unavailable",
            "reason": str(exc),
            "reasoning_ready": False,
            "warnings": [str(exc)],
        }
        return profile, [
            WorldFact(
                fact_id="fact:ziwei:source_quality",
                kind="fact",
                category="ziwei_source_quality",
                statement=f"紫微排盘暂不可用：{exc}",
                payload=profile,
                source_refs=["ziwei.source_quality"],
            )
        ]
    plate = bundle.plate_input
    profile = {
        "status": "ready" if plate.reasoning_ready else "blocked",
        "reasoning_ready": plate.reasoning_ready,
        "calculator": plate.calculator,
        "input_quality": plate.input_quality,
        "life_palace": plate.life_palace,
        "body_palace": plate.body_palace,
        "soul_star": plate.soul_star,
        "body_star": plate.body_star,
        "five_elements_class": plate.five_elements_class,
        "four_transformations": plate.four_transformations,
        "decade_palace": plate.decade_palace,
        "annual_palace": plate.annual_palace,
        "palaces": {name: palace.model_dump(mode="json") for name, palace in plate.palaces.items()},
        "horoscope": plate.horoscope,
        "warnings": plate.warnings,
    }
    source_fact = WorldFact(
        fact_id="fact:ziwei:source_quality",
        kind="fact",
        category="ziwei_source_quality",
        statement=(
            f"紫微排盘来源 {plate.calculator}；状态 {profile['status']}；"
            f"命宫 {plate.life_palace or '未知'}；身宫 {plate.body_palace or '未知'}"
        ),
        payload=profile,
        source_refs=[plate.plate_input_id, plate.calculator or "ziwei.calculator"],
    )
    if not plate.reasoning_ready:
        return profile, [source_fact]
    facts = [source_fact]
    for material in bundle.material_store.materials:
        category = material.material_type.value.replace(".", "_")
        facts.append(
            WorldFact(
                fact_id=f"fact:{material.material_id}",
                kind="fact",
                category=category,
                statement=f"{material.material_type.value}: {material.normalized_value}",
                payload=dict(material.raw_value),
                source_refs=[material.material_id, *material.evidence_refs, *material.knowledge_refs],
            )
        )
    return profile, facts


def retrieve_knowledge(*, terms: set[str], limit: int) -> list[KnowledgeExcerpt]:
    if not KNOWLEDGE_CARDS.exists():
        return []
    ranked: list[tuple[int, dict[str, Any]]] = []
    for line in KNOWLEDGE_CARDS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        card = json.loads(line)
        searchable = " ".join(
            str(card.get(key) or "")
            for key in ("id", "name_zh", "category", "summary", "definition", "related_concepts", "topic_mapping")
        ).lower()
        score = sum(4 if term.lower() in searchable else 0 for term in terms if len(term) > 1)
        if card.get("recommended_runtime_priority") == "P0":
            score += 2
        if card.get("category") in {"foundation", "pattern", "useful_god", "career", "wealth"}:
            score += 1
        if score:
            ranked.append((score, card))
    ranked.sort(key=lambda row: (-row[0], str(row[1].get("id"))))
    return [
        KnowledgeExcerpt(
            knowledge_id=str(card["id"]),
            title=str(card.get("name_zh") or card["id"]),
            summary=str(card.get("definition") or card.get("summary") or ""),
            conditions=[str(item) for item in card.get("conditions", [])][:6],
            counter_conditions=[str(item) for item in card.get("counter_conditions", [])][:6],
            controversy=str(card.get("controversy") or ""),
            source_refs=[str(item.get("title")) for item in card.get("sources", []) if item.get("title")][:4],
        )
        for _, card in ranked[:limit]
    ]


def _chart_material_facts(store) -> list[WorldFact]:
    facts: list[WorldFact] = []
    for material in store.materials:
        category = material.material_id.rsplit(":", 1)[-1]
        payload = material.raw_value if isinstance(material.raw_value, dict) else {"value": material.raw_value}
        facts.append(
            WorldFact(
                fact_id=f"fact:material:{len(facts) + 1}",
                kind="fact",
                category=category,
                statement=f"{category}: {json.dumps(payload, ensure_ascii=False, sort_keys=True)}",
                payload=payload,
                source_refs=[
                    material.material_id,
                    *material.evidence_refs,
                    *material.knowledge_refs,
                    *material.rule_refs,
                ],
            )
        )
    return facts


def _graph_relation_facts(*, graph, nodes: dict[str, Any]) -> list[WorldFact]:
    output: list[WorldFact] = []
    priority_edges = [
        edge
        for edge in graph.edges
        if edge.edge_type.value not in {"position_link", "stores"}
    ]
    priority_edges.sort(key=lambda edge: (edge.edge_type.value, edge.from_node_id, edge.to_node_id, edge.edge_id))
    for edge in priority_edges[:28]:
        source = nodes.get(edge.from_node_id)
        target = nodes.get(edge.to_node_id)
        if source is None or target is None:
            continue
        relation = RELATION_LABELS.get(edge.edge_type.value, edge.relation_label or edge.edge_type.value)
        output.append(
            WorldFact(
                fact_id=f"fact:edge:{edge.edge_id}",
                kind="fact",
                category="graph_relation",
                statement=f"{source.label}（{source.position}）{relation}{target.label}（{target.position}）",
                payload={
                    "from": source.label,
                    "from_position": source.position,
                    "to": target.label,
                    "to_position": target.position,
                    "relation": edge.edge_type.value,
                    "candidate_relation_key": edge.relation_key,
                    "directionality": edge.directionality.value,
                    "ontology_version": edge.ontology_version,
                    "participants": [
                        _graph_node_descriptor(nodes[node_id])
                        for node_id in edge.participant_node_ids
                        if node_id in nodes
                    ],
                },
                source_refs=[edge.edge_id, *edge.evidence_refs],
                authority="experimental_tool_observation",
            )
        )
    return output


def _path_observations(*, paths, nodes: dict[str, Any], edges: dict[str, Any]) -> list[WorldFact]:
    output: list[WorldFact] = []
    for path in paths.paths[:8]:
        labels = [nodes[node_id].label for node_id in path.node_ids if node_id in nodes]
        output.append(
            WorldFact(
                fact_id=f"observation:path:{path.path_id}",
                kind="derived_observation",
                category="candidate_path",
                statement=(
                    f"工具发现候选路径 {' → '.join(labels)}；"
                    f"关系 {' / '.join(path.relation_types)}；"
                    f"证据状态 {path.validation_state.value}"
                ),
                payload={
                    "labels": labels,
                    "relations": list(path.relation_types),
                    "mechanism_hints": list(path.mechanism_hints),
                    "validation_status": path.validation_state.value,
                    "evidence_vector": path.evidence_vector.model_dump(mode="json"),
                    "candidate_path_key": path.path_key,
                    "node_descriptors": [
                        _graph_node_descriptor(nodes[node_id])
                        for node_id in path.node_ids
                        if node_id in nodes
                    ],
                    "relation_descriptors": [
                        {
                            "relation_type": edges[edge_id].edge_type.value,
                            "candidate_relation_key": edges[edge_id].relation_key,
                            "directionality": edges[edge_id].directionality.value,
                            "ontology_version": edges[edge_id].ontology_version,
                            "participants": [
                                _graph_node_descriptor(nodes[node_id])
                                for node_id in edges[edge_id].participant_node_ids
                                if node_id in nodes
                            ],
                        }
                        for edge_id in path.edge_ids
                        if edge_id in edges
                    ],
                },
                source_refs=[path.path_id, *path.evidence_refs],
                authority="experimental_tool_observation",
            )
        )
    return output


def _graph_node_descriptor(node: Any) -> dict[str, str]:
    return {
        "candidate_node_key": str(node.node_key),
        "node_id": str(node.node_id),
        "position": str(node.position),
        "node_type": str(node.node_type.value),
        "label": str(node.label),
    }


def _role_observations(*, roles) -> list[WorldFact]:
    return [
        WorldFact(
            fact_id=f"observation:role:{item.assignment_id}",
            kind="derived_observation",
            category="candidate_node_role",
            statement=f"工具把 {item.label}（{item.position}）标记为 {item.role.value} 候选，置信 {item.confidence:.2f}",
            payload={
                "label": item.label,
                "position": item.position,
                "role": item.role.value,
                "confidence": item.confidence,
                "reason_codes": list(item.reason_codes),
                "validation_status": "experimental",
            },
            source_refs=[item.assignment_id, *item.evidence_refs],
            authority="experimental_tool_observation",
        )
        for item in roles.assignments[:10]
    ]


def _ablation_observations(*, ablation) -> list[WorldFact]:
    ranked = sorted(ablation.ablation_results, key=lambda item: -item.state_delta)
    return [
        WorldFact(
            fact_id=f"observation:ablation:{item.ablation_id}",
            kind="derived_observation",
            category="estimated_sensitivity",
            statement=f"实验工具估计 {item.target_label}（{item.target_position}）的结构敏感度为 {item.state_delta:.3f}；尚未执行真实重算消融",
            payload={
                "target": item.target_label,
                "position": item.target_position,
                "state_delta": item.state_delta,
                "affected_flows": list(item.affected_flows),
                "explanation_codes": list(item.explanation_codes),
                "validation_status": "experimental",
                "true_ablation_performed": False,
            },
            source_refs=[item.ablation_id, *item.evidence_refs],
            authority="experimental_tool_observation",
        )
        for item in ranked[:8]
    ]


def _importance_observations(*, analysis) -> list[WorldFact]:
    return [
        WorldFact(
            fact_id=f"observation:importance:{item.metric_id}",
            kind="derived_observation",
            category="tool_salience",
            statement=f"当前工具视角下 {item.label}（{item.position}）显著性 {item.final_importance:.3f}",
            payload={
                "label": item.label,
                "position": item.position,
                "tool_score": item.final_importance,
                "bridge": item.bridge_score,
                "criticality": item.criticality_score,
                "season": item.season_score,
                "explanation_codes": list(item.explanation_codes),
                "validation_status": "experimental",
            },
            source_refs=[item.metric_id, *item.evidence_refs],
            authority="experimental_tool_observation",
        )
        for item in analysis.node_metrics[:8]
    ]


def _timing_observations(*, timing: dict[str, Any]) -> list[WorldFact]:
    return [
        WorldFact(
            fact_id="fact:timing:material",
            kind="fact",
            category="timing_material",
            statement=f"分析年 {timing['analysis_year']} 为 {timing['annual_pillar']}；当前大运 {timing['luck_pillar'] or '资料不足'}",
            payload=timing,
            source_refs=["calendar.sexagenary_year", *timing.get("calculation_refs", [])],
        )
    ]


def _timing_material(*, birth_input: BirthInputCanonical, analysis_year: int) -> dict[str, Any]:
    return _TEMPORAL_SERVICE.resolve_world_timing(
        birth_input=birth_input,
        analysis_year=analysis_year,
    )


def _retrieval_terms(*, facts: list[WorldFact], graph) -> set[str]:
    terms = {"旺衰", "格局", "做功", "体用", "用神", "事业", "财富", "合冲刑害", "大运流年"}
    for node in graph.nodes:
        if node.ten_god:
            terms.add(node.ten_god)
            terms.add(TEN_GOD_LABELS.get(node.ten_god, node.ten_god))
        if node.element:
            terms.add(node.element)
    for fact in facts:
        if fact.category == "graph_relation":
            terms.add(str(fact.payload.get("relation") or ""))
    return {item for item in terms if item}


def _fixture_prior(birth_input: BirthInputCanonical) -> WorldFact | None:
    if not SYNTHETIC_TAXONOMY.exists():
        return None
    chart = " ".join([birth_input.year_pillar, birth_input.month_pillar, birth_input.day_pillar, birth_input.hour_pillar])
    data = json.loads(SYNTHETIC_TAXONOMY.read_text(encoding="utf-8"))
    row = next((item for item in data.get("cases", []) if item.get("chart") == chart), None)
    if row is None:
        return None
    return WorldFact(
        fact_id=f"observation:fixture:{row['case_id']}",
        kind="derived_observation",
        category="research_fixture_prior",
        statement=(
            f"结构研究 fixture 将此盘归为 {row['case_type']}；预期结构 {row.get('expected_structure', [])}；"
            f"预期路径 {row.get('expected_path', [])}；禁止机械结论 {row.get('must_not', [])}。"
        ),
        payload={
            "case_type": row.get("case_type"),
            "expected_structure": row.get("expected_structure", []),
            "expected_top_node": row.get("expected_top_node", []),
            "expected_path": row.get("expected_path", []),
            "expected_ablation": row.get("expected_ablation", []),
            "must_not": row.get("must_not", []),
        },
        source_refs=[f"synthetic_taxonomy:{row['case_id']}"],
    )


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
