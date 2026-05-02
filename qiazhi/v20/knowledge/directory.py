from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from v20.knowledge.directory_seeds import build_full_directory_seed_library


@dataclass(frozen=True)
class KnowledgeDirectoryNode:
    node_id: str
    title: str
    layer: str
    role: str
    priority: str
    content_status: str
    first_wave_topics: tuple[str, ...]
    maps_to_model_objects: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_knowledge_directory_manifest() -> dict[str, Any]:
    nodes = _directory_nodes()
    seed_library = build_full_directory_seed_library()
    first_wave = tuple(row for row in nodes if row.priority == "P0")
    return {
        "version": "v20.knowledge_directory_manifest.v1",
        "status": "directory_ready_full_seed_library_ready",
        "source_doc": "docs/bazi_knowledge/catalog/v20_knowledge_final_directory_zh_v1.md",
        "node_count": len(nodes),
        "p0_node_count": len(first_wave),
        "full_seed_library_status": seed_library["status"],
        "full_content_status": seed_library["full_content_status"],
        "full_content_doc": seed_library["full_content_doc"],
        "full_seed_count": seed_library["seed_count"],
        "full_seed_covered_node_count": seed_library["directory_node_count"],
        "nodes": [row.to_dict() for row in nodes],
        "p0_nodes": tuple(row.node_id for row in first_wave),
        "mainline_fill_order": (
            "L0",
            "L3",
            "L4",
            "L2",
            "L5",
            "L6",
            "L7",
            "L8",
            "L9",
            "L10",
            "L1",
            "L11",
            "L12",
        ),
        "runtime_mutation": False,
        "guardrails": (
            "DIRECTORY_IS_SOURCE_OF_KNOWLEDGE_FILL_NOT_RUNTIME_TRUTH",
            "P0_PRIORITIZES_FEATURE_DISCOVERY_OVER_APPLICATION_COPY",
            "APPLICATION_TOPICS_MUST_PROJECT_FROM_BAZI_FEATURES",
            "ARCHIVE_LAYERS_REQUIRE_EXTRA_REVIEW_BEFORE_RUNTIME_USE",
        ),
    }


def _directory_nodes() -> tuple[KnowledgeDirectoryNode, ...]:
    return (
        _node("L0", "排盘与基础符号", "foundation", "chart_fact_source", "P0", ("天干", "地支", "四柱", "历法与排盘元数据"), ("FactNode", "EvidenceAtom")),
        _node("L1", "五行与气候", "foundation", "climate_and_element_evidence", "P1", ("五行分布", "寒暖燥湿", "调候候选"), ("EvidenceAtom", "MechanismPath")),
        _node("L2", "强弱与承载", "core_mechanism", "capacity_arbitration", "P0", ("日主承载", "根气", "扶抑压力"), ("EvidenceAtom", "DecisionState")),
        _node("L3", "十神系统", "core_symbol", "ten_god_feature_source", "P0", ("十神本体", "十神来源层", "十神组合与机制"), ("EvidenceAtom", "RulePath", "MechanismPath")),
        _node("L4", "干支关系", "core_relation", "relation_feature_source", "P0", ("天干关系", "地支关系", "刑冲合害破墓库"), ("EvidenceAtom", "CounterEvidence", "TraceNode")),
        _node("L5", "格局系统", "core_mechanism", "pattern_candidate_source", "P0", ("正格", "特殊格", "格局清浊成败"), ("RulePath", "DecisionState")),
        _node("L6", "用神与取用路径", "core_arbitration", "useful_god_path_source", "P0", ("扶抑", "通关", "调候", "病药"), ("MechanismPath", "DecisionState")),
        _node("L7", "宫位与象法", "core_projection", "palace_symbol_source", "P0", ("年月日时宫位", "夫妻宫", "事业宫位象"), ("EvidenceAtom", "TopicProjection")),
        _node("L8", "盲派系统", "core_mechanism", "blind_lifa_feature_source", "P0", ("宾主体用", "做功", "位置象", "应期象"), ("MechanismPath", "CounterEvidence")),
        _node("L9", "岁运时间系统", "time", "activation_and_volatility_source", "P0", ("大运", "流年", "引动", "应期"), ("EvidenceAtom", "DecisionState", "TraceNode")),
        _node("L10", "领域应用", "application", "topic_projection_source", "P0", ("财富", "事业", "关系", "感情", "健康"), ("TopicProjection", "BaziFeature")),
        _node("L11", "辅助体系与归档", "archive", "high_risk_auxiliary_archive", "P2", ("神煞", "纳音", "胎元命宫身宫", "口诀技法"), ("EvidenceAtom", "CounterEvidence")),
        _node("L12", "回答表达与治理", "governance", "answer_boundary_source", "P1", ("禁止断语", "边界表达", "证据化回答"), ("EvidencePack", "AnswerPlan")),
    )


def _node(
    node_id: str,
    title: str,
    layer: str,
    role: str,
    priority: str,
    first_wave_topics: tuple[str, ...],
    maps_to_model_objects: tuple[str, ...],
) -> KnowledgeDirectoryNode:
    return KnowledgeDirectoryNode(
        node_id=node_id,
        title=title,
        layer=layer,
        role=role,
        priority=priority,
        content_status="directory_ready_full_seeded_needs_practitioner_review",
        first_wave_topics=first_wave_topics,
        maps_to_model_objects=maps_to_model_objects,
    )
