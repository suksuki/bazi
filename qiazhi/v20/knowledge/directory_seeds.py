from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DirectoryKnowledgeSeed:
    seed_id: str
    directory_node: str
    title: str
    layer: str
    measurement_role: str
    evidence_requirements: tuple[str, ...]
    feature_targets: tuple[str, ...]
    rule_path_candidate: str
    content_status: str = "seed_ready_needs_practitioner_review"
    runtime_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_full_directory_seed_library() -> dict[str, Any]:
    seeds = _all_seeds()
    node_ids = sorted({seed.directory_node for seed in seeds})
    p0_nodes = tuple(node_id for node_id in node_ids if node_id not in {"L1", "L11", "L12"})
    return {
        "version": "v20.full_directory_seed_library.v1",
        "status": "full_directory_seeded_for_review",
        "source_directory": "docs/bazi_knowledge/catalog/v20_knowledge_final_directory_zh_v1.md",
        "full_content_doc": "docs/bazi_knowledge/catalog/v20_knowledge_full_content_zh_v1.md",
        "full_content_status": "full_content_draft_ready",
        "seed_count": len(seeds),
        "directory_node_count": len(node_ids),
        "covered_directory_nodes": tuple(node_ids),
        "p0_covered_nodes": p0_nodes,
        "runtime_allowed_count": sum(1 for seed in seeds if seed.runtime_allowed),
        "seeds": [seed.to_dict() for seed in seeds],
        "coverage_by_node": {
            node_id: sum(1 for seed in seeds if seed.directory_node == node_id)
            for node_id in node_ids
        },
        "next_review_lanes": (
            "convert_p0_seed_to_KnowledgeUnit_batches",
            "split_large_topics_into_EvidenceAtom_and_RulePath",
            "add_counterexamples_for_runtime_iteration",
            "bind_topic_projection_to_BaziFeature_outputs",
        ),
        "runtime_mutation": False,
        "guardrails": (
            "FULL_DIRECTORY_SEEDS_ARE_KNOWLEDGE_BASE_CONTENT_NOT_RUNTIME_RULES",
            "RUNTIME_ALLOWED_FALSE_UNTIL_PRACTITIONER_REVIEW_AND_SYNTHETIC_CASES",
            "NO_DIRECT_FORTUNE_VERDICT_FROM_DIRECTORY_SEEDS",
            "PROMOTE_BY_DIRECTORY_NODE_BATCH_NOT_ONE_OFF_PATCHES",
        ),
    }


def _all_seeds() -> tuple[DirectoryKnowledgeSeed, ...]:
    rows: list[DirectoryKnowledgeSeed] = []
    for node_id, layer, role, topics in _seed_topics():
        for index, topic in enumerate(topics, start=1):
            rows.append(
                DirectoryKnowledgeSeed(
                    seed_id=f"v20.seed.{node_id.lower()}.{index:03d}",
                    directory_node=node_id,
                    title=topic,
                    layer=layer,
                    measurement_role=role,
                    evidence_requirements=_evidence_requirements(node_id),
                    feature_targets=_feature_targets(node_id),
                    rule_path_candidate=_rule_path_candidate(node_id),
                )
            )
    return tuple(rows)


def _seed_topics() -> tuple[tuple[str, str, str, tuple[str, ...]], ...]:
    return (
        ("L0", "foundation", "chart_fact_source", (
            "十天干阴阳五行", "天干生克合冲", "日主日元定位", "十二地支阴阳五行", "地支藏干主中余气",
            "地支季节方位时辰", "四柱年月日时远近内外", "天干外显地支内藏", "节气月令", "立春换年",
            "真太阳时与出生地", "时区夏令时历史时区", "经度校正", "排盘不确定性", "原局与外部时间层区分",
        )),
        ("L1", "foundation", "climate_and_element_evidence", (
            "五行生克泄耗助", "五行制化通关", "五行数量与权重", "五行透出与藏干", "五行集中偏枯",
            "五行流通阻滞", "寒暖燥湿基础", "月令气候", "地域气候背景", "调候候选", "气候与强弱分离",
            "气候与健康边界分离",
        )),
        ("L2", "core_mechanism", "capacity_arbitration", (
            "日主强弱", "得令失令", "得地失地", "得势失势", "得助失助", "承载力", "边界强弱",
            "中和状态", "通根", "本气根中气根余气根", "禄刃根", "墓库根虚根", "根被冲合",
            "印比扶身", "食伤泄身", "财星耗身", "官杀克身", "扶身泄秀制杀通关病药路径",
        )),
        ("L3", "core_symbol", "ten_god_feature_source", (
            "比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印枭神", "正印",
            "明透十神", "藏干十神", "重复十神", "月令十神", "年柱月柱日支时柱十神", "十神远近内外",
            "伤官见官", "枭神夺食", "食神制杀", "杀印相生", "官印相生", "伤官配印",
            "食伤生财", "财生官财官相生", "比劫夺财分财", "财破印财多坏印", "官杀混杂",
            "食伤混杂印枭混杂", "官杀攻身", "合杀留官合官留杀", "羊刃驾杀", "官星护财财制枭护食",
        )),
        ("L4", "core_relation", "relation_feature_source", (
            "天干五合", "合化", "合绊", "合动", "合而不化", "天干冲克", "天干制化通关",
            "地支六合", "地支六冲", "三合半合", "三会", "刑", "害", "破", "穿", "墓库",
            "伏吟反吟", "拱夹", "暗合", "遥合", "冲合并见", "刑冲合害破混杂", "关系方向与宫位落点",
        )),
        ("L5", "core_mechanism", "pattern_candidate_source", (
            "正格十类", "月令取格", "格局成格条件", "格局破格条件", "格局清浊", "格局高低边界",
            "财格", "官格", "杀格", "印格", "食神格", "伤官格", "建禄月劫", "专旺从格",
            "化气格", "特殊格局归档", "格局与用神分离", "格局与做功合参",
        )),
        ("L6", "core_arbitration", "useful_god_path_source", (
            "扶抑取用", "调候取用", "通关取用", "病药取用", "泄秀取用", "制杀取用",
            "候选用神", "忌神候选", "喜忌边界", "取用优先级", "多路径冲突", "用神反证",
            "岁运改变取用权重", "用神不等于事件结论",
        )),
        ("L7", "core_projection", "palace_symbol_source", (
            "年柱宫位", "月柱宫位", "日柱宫位", "时柱宫位", "夫妻宫日支", "父母长辈宫位",
            "事业平台宫位", "子女晚景宫位", "宫位远近内外", "宫位被冲合刑害", "宫位藏干取象",
            "宫位与十神合参", "宫位与岁运引动", "宫位象法边界",
        )),
        ("L8", "core_mechanism", "blind_lifa_feature_source", (
            "宾主体用", "主客关系", "体用转换", "做功主体", "做功对象", "做功媒介",
            "做功路径连续性", "做功阻断", "入主入库", "财来就我我去取财", "官杀作用路径",
            "食伤输出路径", "印星转化路径", "宫位象", "干支象", "十神象", "位置象", "应期象",
            "象法必须回证据", "盲派隐私边界",
        )),
        ("L9", "time", "activation_and_volatility_source", (
            "大运层", "流年层", "流月层", "原局大运流年三层栈", "大运改变背景", "流年触发",
            "岁运并临", "伏吟反吟时间层", "冲合刑害引动", "墓库开闭引动", "十神岁运透出",
            "应期候选", "时间层不直接断事件", "volatile 状态表达",
        )),
        ("L10", "application", "topic_projection_source", (
            "财富财星材料", "财富食伤生财", "财富财库开闭", "财富比劫分夺", "财富承载与现金流",
            "事业官杀规则", "事业伤官见官", "事业官印相生", "事业格局承接", "事业学业考试",
            "关系比劫合作竞争", "关系人际互动", "关系合作承接", "关系外部资源分配",
            "感情配偶星", "感情夫妻宫", "感情合冲引动", "感情承接边界",
            "健康五行偏枯", "健康寒暖燥湿", "健康压力恢复", "健康医疗禁断边界",
        )),
        ("L11", "archive", "high_risk_auxiliary_archive", (
            "神煞归档", "桃花红鸾天喜", "驿马华盖", "纳音归档", "胎元命宫身宫", "空亡",
            "十二长生", "口诀技法", "古籍异文", "门派差异", "高风险断语隔离", "辅助体系晋升条件",
        )),
        ("L12", "governance", "answer_boundary_source", (
            "禁止断语", "证据化回答", "候选状态表达", "成而不纯表达", "被反证压制表达",
            "岁运波动表达", "证据不足不输出", "医疗法律金融边界", "隐私边界", "LLM 表达层边界",
            "EvidencePack 必经", "Verifier 必经",
        )),
    )


def _evidence_requirements(node_id: str) -> tuple[str, ...]:
    mapping = {
        "L0": ("ChartFacts", "calendar_metadata", "pillar_position"),
        "L1": ("element_distribution", "month_command", "climate_context"),
        "L2": ("support_pressure", "root_evidence", "month_command"),
        "L3": ("ten_god_label", "source_layer", "day_master_relation"),
        "L4": ("stem_branch_pair", "relation_type", "palace_position"),
        "L5": ("month_command", "ten_god_structure", "clear_or_mixed_evidence"),
        "L6": ("capacity_state", "element_flow", "path_counterevidence"),
        "L7": ("pillar_position", "palace_target", "branch_or_ten_god_evidence"),
        "L8": ("actor", "target", "medium", "path_continuity"),
        "L9": ("natal_layer", "luck_layer", "flow_layer", "trigger_relation"),
        "L10": ("BaziFeature", "DecisionState", "TopicProjection"),
        "L11": ("auxiliary_symbol", "source_school", "activation_review"),
        "L12": ("EvidencePack", "AnswerPlan", "Verifier"),
    }
    return mapping[node_id]


def _feature_targets(node_id: str) -> tuple[str, ...]:
    mapping = {
        "L0": ("feature.chart_fact",),
        "L1": ("feature.element", "feature.useful_god"),
        "L2": ("feature.strength",),
        "L3": ("feature.ten_god",),
        "L4": ("feature.branch",),
        "L5": ("feature.pattern",),
        "L6": ("feature.useful_god",),
        "L7": ("feature.palace", "feature.branch", "feature.ten_god"),
        "L8": ("feature.blind_lifa", "feature.pattern"),
        "L9": ("feature.time",),
        "L10": ("feature.wealth", "feature.career", "feature.relationship", "feature.romance", "feature.health"),
        "L11": ("feature.auxiliary_archive",),
        "L12": ("answer.boundary", "answer.evidence"),
    }
    return mapping[node_id]


def _rule_path_candidate(node_id: str) -> str:
    mapping = {
        "L0": "fact_extraction_only",
        "L1": "element_climate_evidence_path",
        "L2": "capacity_arbitration_path",
        "L3": "ten_god_role_path",
        "L4": "stem_branch_relation_path",
        "L5": "pattern_candidate_path",
        "L6": "useful_god_candidate_path",
        "L7": "palace_projection_path",
        "L8": "blind_lifa_mechanism_path",
        "L9": "time_activation_path",
        "L10": "topic_projection_path",
        "L11": "archive_review_path",
        "L12": "answer_governance_path",
    }
    return mapping[node_id]
