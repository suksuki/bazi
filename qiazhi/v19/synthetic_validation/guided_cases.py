from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping

from v19.agent.structure import SIX_CLASHES, SIX_COMBINATIONS, THREE_HARMONIES, _pillar


GUIDED_SYNTHETIC_CASE_SCHEMA_VERSION = "v19.guided_synthetic_case.v1"
THREE_MEETINGS = [("寅", "卯", "辰"), ("巳", "午", "未"), ("申", "酉", "戌"), ("亥", "子", "丑")]
SIX_HARMS = [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")]
SIX_BREAKS = [("子", "酉"), ("丑", "辰"), ("寅", "亥"), ("卯", "午"), ("巳", "申"), ("未", "戌")]

DEFAULT_FORBIDDEN_GUIDED_TEXT = [
    "rule_id",
    "signal_id",
    "source_signal_id",
    "question_basis",
    "GUIDED_ANSWER",
    "DETERMINISTIC",
    "ResultCard",
    "income_stability",
    "不是财运预测",
    "不等同于财运预测",
]


@dataclass(frozen=True)
class GuidedSyntheticCase:
    case_id: str
    chart: Dict[str, Any]
    question_key: str
    message: str
    structure_label: str = ""
    collision_focus: str = ""
    time_context: Dict[str, Any] = field(default_factory=dict)
    expected_recommended_keys: List[str] = field(default_factory=list)
    expected_wealth_question_keys: List[str] = field(default_factory=lambda: ["q_income_stability"])
    expected_answer_kind: str = ""
    expected_source_signal_category: str = ""
    expected_knowledge_ids: List[str] = field(default_factory=list)
    expected_relation_types: List[str] = field(default_factory=list)
    expected_text_contains: List[str] = field(default_factory=list)
    forbidden_text: List[str] = field(default_factory=lambda: list(DEFAULT_FORBIDDEN_GUIDED_TEXT))
    tags: List[str] = field(default_factory=list)
    knowledge_tags: List[str] = field(default_factory=list)
    schema_version: str = GUIDED_SYNTHETIC_CASE_SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "GuidedSyntheticCase":
        return cls(
            case_id=str(payload.get("case_id") or ""),
            chart=dict(payload.get("chart") or {}),
            question_key=str(payload.get("question_key") or ""),
            message=str(payload.get("message") or ""),
            structure_label=str(payload.get("structure_label") or ""),
            collision_focus=str(payload.get("collision_focus") or ""),
            time_context=dict(payload.get("time_context") or {}),
            expected_recommended_keys=[str(item) for item in payload.get("expected_recommended_keys", [])],
            expected_wealth_question_keys=[str(item) for item in payload.get("expected_wealth_question_keys", ["q_income_stability"])],
            expected_answer_kind=str(payload.get("expected_answer_kind") or ""),
            expected_source_signal_category=str(payload.get("expected_source_signal_category") or ""),
            expected_knowledge_ids=[str(item) for item in payload.get("expected_knowledge_ids", [])],
            expected_relation_types=[str(item) for item in payload.get("expected_relation_types", [])],
            expected_text_contains=[str(item) for item in payload.get("expected_text_contains", [])],
            forbidden_text=[str(item) for item in payload.get("forbidden_text", DEFAULT_FORBIDDEN_GUIDED_TEXT)],
            tags=[str(item) for item in payload.get("tags", [])],
            knowledge_tags=[str(item) for item in payload.get("knowledge_tags", [])],
            schema_version=str(payload.get("schema_version") or GUIDED_SYNTHETIC_CASE_SCHEMA_VERSION),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "chart": dict(self.chart),
            "time_context": dict(self.time_context),
            "question_key": self.question_key,
            "message": self.message,
            "structure_label": self.structure_label,
            "collision_focus": self.collision_focus,
            "expected_recommended_keys": list(self.expected_recommended_keys),
            "expected_wealth_question_keys": list(self.expected_wealth_question_keys),
            "expected_answer_kind": self.expected_answer_kind,
            "expected_source_signal_category": self.expected_source_signal_category,
            "expected_knowledge_ids": list(self.expected_knowledge_ids),
            "expected_relation_types": list(self.expected_relation_types),
            "expected_text_contains": list(self.expected_text_contains),
            "forbidden_text": list(self.forbidden_text),
            "tags": list(self.tags),
            "knowledge_tags": list(self.knowledge_tags),
        }


def make_synthetic_chart(case_id: str, pillars: Mapping[str, str], *, relations: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    pillar_rows = {name: _pillar_from_display(str(pillars.get(name) or "")) for name in ["year", "month", "day", "hour"]}
    return {
        "status": "ok",
        "chart_id": case_id,
        "calendar_note": "synthetic_explicit_pillars_no_birthdate",
        "pillars": pillar_rows,
        "day_master": {
            "stem": pillar_rows["day"]["stem"],
            "element": pillar_rows["day"]["stem_element"],
            "yin_yang": pillar_rows["day"]["stem_yin_yang"],
        },
        "relations": {"items": relations if relations is not None else _auto_relation_items(pillar_rows)},
    }


def make_synthetic_time_context(
    chart: Dict[str, Any],
    *,
    luck_pillar: str = "",
    flow_pillar: str = "",
    flow_year: int = 2026,
    luck_relations: Dict[str, List[str]] | None = None,
    flow_relations: Dict[str, List[str]] | None = None,
) -> Dict[str, Any]:
    luck = {
        "start_age": 8,
        "end_age": 17,
        "pillar": _pillar_from_display(luck_pillar),
        "relations_with_natal": dict(luck_relations or {}),
    } if luck_pillar else None
    flow = {
        "year": flow_year,
        "pillar": _pillar_from_display(flow_pillar),
        "relations_with_natal": dict(flow_relations or {}),
    } if flow_pillar else {"year": flow_year, "pillar": {}, "relations_with_natal": {}}
    return {"natal": chart, "luck_cycle": luck, "flow_year": flow}


def _pillar_from_display(display: str) -> Dict[str, str]:
    text = str(display or "").strip()
    if len(text) < 2:
        raise ValueError(f"invalid synthetic pillar: {display!r}")
    return _pillar(text[0], text[1])


def _auto_relation_items(pillars: Mapping[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    branches = [(name, str(pillar.get("branch") or "")) for name, pillar in pillars.items()]
    rows: List[Dict[str, Any]] = []
    for left_index, (left_name, left) in enumerate(branches):
        if not left:
            continue
        for right_name, right in branches[left_index + 1 :]:
            if not right:
                continue
            for relation_type, pairs in [
                ("six_combination", SIX_COMBINATIONS),
                ("six_clash", SIX_CLASHES),
                ("harm", SIX_HARMS),
                ("break", SIX_BREAKS),
            ]:
                if _has_pair(pairs, left, right):
                    rows.append({"type": relation_type, "branches": f"{left}{right}", "pillars": [left_name, right_name]})
    present = {branch for _, branch in branches if branch}
    for relation_type, groups in [("three_harmony", THREE_HARMONIES), ("three_meeting", THREE_MEETINGS)]:
        for group in groups:
            if set(group) <= present:
                rows.append(
                    {
                        "type": relation_type,
                        "branches": "".join(group),
                        "pillars": [name for name, branch in branches if branch in group],
                    }
                )
    return rows


def _has_pair(pairs: List[tuple[str, str]], left: str, right: str) -> bool:
    return any({left, right} == {pair_left, pair_right} for pair_left, pair_right in pairs)


P10_GUIDED_SYNTHETIC_CASES = [
    GuidedSyntheticCase(
        case_id="syn.guided.month_command_boundary",
        chart=make_synthetic_chart("syn.guided.month_command_boundary", {"year": "甲子", "month": "丁巳", "day": "庚申", "hour": "乙酉"}),
        question_key="q_month_command_anchor",
        message="月令在这张命盘里先提供了什么结构背景？",
        structure_label="机会型-月令边界",
        collision_focus="month_command_strength_boundary",
        expected_recommended_keys=["q_month_command_anchor"],
        expected_answer_kind="metadata_boundary",
        expected_source_signal_category="strength_model",
        expected_knowledge_ids=["p10.month_command_season_not_verdict"],
        expected_text_contains=["月令不能单独推出身强、身弱或好坏"],
        tags=["p10", "month_command", "knowledge_retrieval"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.ten_god_visible_hidden",
        chart=make_synthetic_chart("syn.guided.ten_god_visible_hidden", {"year": "甲寅", "month": "辛酉", "day": "戊辰", "hour": "癸亥"}),
        question_key="q_ten_god_metadata",
        message="十神标签在这里为什么只是关系元数据，而不是断语？",
        structure_label="机会型-十神透藏混合",
        collision_focus="ten_god_visible_vs_hidden",
        expected_recommended_keys=["q_ten_god_metadata"],
        expected_answer_kind="metadata_boundary",
        expected_source_signal_category="ten_god",
        expected_knowledge_ids=["p10.ten_god_five_family_plain_language", "p10.ten_god_visible_hidden_boundary"],
        expected_text_contains=["五类关系", "藏干层面"],
        tags=["p10", "ten_god", "visible_hidden_boundary"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.hidden_stem_complete_mapping",
        chart=make_synthetic_chart("syn.guided.hidden_stem_complete_mapping", {"year": "己丑", "month": "戊辰", "day": "丁未", "hour": "壬戌"}),
        question_key="q_hidden_stem_role",
        message="藏干在这张命盘里只是补充信息，还是会影响结构理解？",
        structure_label="稳定型-藏干完整映射",
        collision_focus="hidden_stem_complete_mapping",
        expected_recommended_keys=["q_hidden_stem_role"],
        expected_answer_kind="metadata_boundary",
        expected_source_signal_category="hidden_stem",
        expected_knowledge_ids=["p10.branch_hidden_stem_complete_mapping"],
        expected_text_contains=["直接透出", "藏在地支里面"],
        tags=["p10", "hidden_stem", "complete_mapping"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.branch_penalty_harm_break",
        chart=make_synthetic_chart("syn.guided.branch_penalty_harm_break", {"year": "甲子", "month": "己未", "day": "乙卯", "hour": "庚午"}),
        question_key="q_branch_relation_detail",
        message="命盘中的冲害刑破属于哪类结构关系？为什么先读为结构提示？",
        structure_label="波动型-刑害破边界",
        collision_focus="branch_penalty_harm_break",
        expected_recommended_keys=["q_branch_relation_detail"],
        expected_answer_kind="branch_relation",
        expected_source_signal_category="branch_relation",
        expected_knowledge_ids=["p10.branch_penalty_harm_break_boundary"],
        expected_relation_types=["harm", "break"],
        expected_text_contains=["刑、害、破", "不能从名称直接扩写"],
        tags=["p10", "branch_relation", "harm_break"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.three_meeting_boundary",
        chart=make_synthetic_chart("syn.guided.three_meeting_boundary", {"year": "甲寅", "month": "乙卯", "day": "戊辰", "hour": "辛酉"}),
        question_key="q_branch_relation_detail",
        message="如果出现三会结构，它在这里只表示什么结构连接？",
        structure_label="机会型-三会结构",
        collision_focus="three_meeting_boundary",
        expected_recommended_keys=["q_branch_relation_detail"],
        expected_answer_kind="branch_relation",
        expected_source_signal_category="branch_relation",
        expected_knowledge_ids=["p10.branch_three_meeting_boundary"],
        expected_relation_types=["three_meeting"],
        expected_text_contains=["三会"],
        tags=["p10", "branch_relation", "three_meeting"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.time_relation_context_only",
        chart=make_synthetic_chart("syn.guided.time_relation_context_only", {"year": "甲子", "month": "戊辰", "day": "庚戌", "hour": "乙酉"}),
        time_context=make_synthetic_time_context(
            make_synthetic_chart("syn.guided.time_relation_context_only", {"year": "甲子", "month": "戊辰", "day": "庚戌", "hour": "乙酉"}),
            luck_pillar="戊午",
            flow_pillar="丙辰",
            flow_relations={"clashes": ["辰戌"]},
        ),
        question_key="q_time_vs_natal_relation",
        message="大运、流年和本命发生关系时，哪些只算背景，哪些才算本命结构？",
        structure_label="波动型-时间层碰撞",
        collision_focus="time_layer_relation_boundary",
        expected_recommended_keys=["kbq_time_vs_natal_relation"],
        expected_answer_kind="branch_relation",
        expected_source_signal_category="branch_relation",
        expected_relation_types=["clash"],
        expected_text_contains=["时间背景", "流年"],
        tags=["p10", "time_layer", "relation_context"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.vault_hidden_stem_boundary",
        chart=make_synthetic_chart("syn.guided.vault_hidden_stem_boundary", {"year": "己丑", "month": "戊辰", "day": "丁未", "hour": "壬戌"}),
        question_key="q_vault_structure",
        message="这张命盘里的墓库结构，应该如何只按结构层阅读？",
        structure_label="稳定型-墓库承载",
        collision_focus="vault_hidden_stem_boundary",
        expected_recommended_keys=["kbq_vault_structure"],
        expected_answer_kind="vault",
        expected_source_signal_category="vault",
        expected_text_contains=["墓库", "藏干"],
        tags=["p10", "vault", "hidden_stem"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.income_structure_no_internal_terms",
        chart=make_synthetic_chart("syn.guided.income_structure_no_internal_terms", {"year": "戊辰", "month": "己未", "day": "戊午", "hour": "癸亥"}),
        question_key="q_income_stability",
        message="我的收入稳定性结构如何？",
        structure_label="稳定型-财富元素清晰",
        collision_focus="income_structure_user_copy",
        expected_recommended_keys=["q_income_stability"],
        expected_answer_kind="income_structure",
        expected_source_signal_category="wealth_feature",
        expected_text_contains=["收入稳定性结构", "财富结构"],
        tags=["p10", "income_structure", "user_copy"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.branch_clash_combination_collision",
        chart=make_synthetic_chart("syn.guided.branch_clash_combination_collision", {"year": "甲子", "month": "己丑", "day": "戊午", "hour": "庚申"}),
        question_key="q_branch_relation_detail",
        message="当前看得到的冲合关系，分别发生在本命还是时间背景？",
        structure_label="波动型-冲合并见",
        collision_focus="branch_clash_combination_collision",
        expected_recommended_keys=["q_branch_relation_detail"],
        expected_answer_kind="branch_relation",
        expected_source_signal_category="branch_relation",
        expected_relation_types=["clash", "combination"],
        expected_text_contains=["出现冲", "出现合"],
        tags=["p10", "branch_relation", "clash_combination"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.income_wealth_missing_unstable",
        chart=make_synthetic_chart("syn.guided.income_wealth_missing_unstable", {"year": "戊辰", "month": "丁巳", "day": "戊午", "hour": "丙辰"}),
        question_key="q_income_stability",
        message="我的收入稳定性结构如何？",
        structure_label="波动型-财富元素缺失",
        collision_focus="income_wealth_missing",
        expected_recommended_keys=["q_income_stability"],
        expected_answer_kind="income_structure",
        expected_source_signal_category="wealth_feature",
        expected_text_contains=["收入稳定性结构", "财富结构出现度"],
        tags=["p10", "income_structure", "wealth_missing"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.income_wealth_disrupted_volatility",
        chart=make_synthetic_chart("syn.guided.income_wealth_disrupted_volatility", {"year": "戊辰", "month": "丁巳", "day": "戊午", "hour": "壬子"}),
        question_key="q_income_stability",
        message="当前结构中哪些因素影响收入稳定？",
        structure_label="波动型-财富可达被冲",
        collision_focus="income_wealth_access_disrupted",
        expected_recommended_keys=["q_income_stability"],
        expected_answer_kind="income_structure",
        expected_source_signal_category="wealth_feature",
        expected_text_contains=["财富可达性", "波动性"],
        tags=["p10", "income_structure", "wealth_disrupted"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.income_three_harmony_binding",
        chart=make_synthetic_chart("syn.guided.income_three_harmony_binding", {"year": "戊申", "month": "壬子", "day": "戊辰", "hour": "辛酉"}),
        question_key="q_income_stability",
        message="这个结果主要由哪几个结构信号共同形成？",
        structure_label="机会型-三合牵制",
        collision_focus="income_structure_binding",
        expected_recommended_keys=["q_income_stability"],
        expected_answer_kind="income_structure",
        expected_source_signal_category="wealth_feature",
        expected_relation_types=["three_harmony"],
        expected_text_contains=["结构牵制", "财富结构"],
        tags=["p10", "income_structure", "three_harmony"],
    ),
]


P11_GUIDED_SYNTHETIC_CASES = P10_GUIDED_SYNTHETIC_CASES + [
    GuidedSyntheticCase(
        case_id="syn.guided.p11.branch_clash_harm_collision",
        chart=make_synthetic_chart("syn.guided.p11.branch_clash_harm_collision", {"year": "甲子", "month": "丙午", "day": "乙未", "hour": "庚申"}),
        question_key="q_branch_relation_detail",
        message="命盘同时出现冲和害时，应该如何只按结构关系阅读？",
        structure_label="波动型-冲害并见",
        collision_focus="branch_clash_harm_collision",
        expected_recommended_keys=["q_branch_relation_detail"],
        expected_answer_kind="branch_relation",
        expected_source_signal_category="branch_relation",
        expected_relation_types=["clash", "harm"],
        expected_text_contains=["出现冲", "出现害"],
        tags=["p11", "branch_relation", "clash_harm"],
        knowledge_tags=["ku:branch_relation", "ku:penalty_harm_break_boundary"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.p11.branch_combination_break_collision",
        chart=make_synthetic_chart("syn.guided.p11.branch_combination_break_collision", {"year": "甲子", "month": "己丑", "day": "辛酉", "hour": "戊辰"}),
        question_key="q_branch_relation_detail",
        message="命盘同时出现合和破时，哪些只是结构连接，哪些需要保持边界？",
        structure_label="波动型-合破并见",
        collision_focus="branch_combination_break_collision",
        expected_recommended_keys=["q_branch_relation_detail"],
        expected_answer_kind="branch_relation",
        expected_source_signal_category="branch_relation",
        expected_relation_types=["combination", "break"],
        expected_text_contains=["出现合", "出现破"],
        tags=["p11", "branch_relation", "combination_break"],
        knowledge_tags=["ku:branch_relation", "ku:penalty_harm_break_boundary"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.p11.three_harmony_three_meeting_layered",
        chart=make_synthetic_chart("syn.guided.p11.three_harmony_three_meeting_layered", {"year": "戊申", "month": "壬子", "day": "戊辰", "hour": "辛卯"}),
        time_context=make_synthetic_time_context(
            make_synthetic_chart("syn.guided.p11.three_harmony_three_meeting_layered", {"year": "戊申", "month": "壬子", "day": "戊辰", "hour": "辛卯"}),
            flow_pillar="甲寅",
            flow_relations={"three_meeting": ["寅卯", "寅辰"]},
        ),
        question_key="q_branch_relation_detail",
        message="三合在本命、三会在流年背景时，应该如何分层阅读？",
        structure_label="机会型-三合三会分层",
        collision_focus="three_harmony_three_meeting_layered_collision",
        expected_recommended_keys=["q_branch_relation_detail"],
        expected_answer_kind="branch_relation",
        expected_source_signal_category="branch_relation",
        expected_relation_types=["three_harmony", "three_meeting"],
        expected_text_contains=["出现三合", "出现三会", "时间背景"],
        tags=["p11", "branch_relation", "three_harmony", "three_meeting", "time_layer"],
        knowledge_tags=["ku:branch_relation", "ku:three_meeting_boundary", "ku:time_context_boundary"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.p11.ten_god_visible_hidden_conflict",
        chart=make_synthetic_chart("syn.guided.p11.ten_god_visible_hidden_conflict", {"year": "甲寅", "month": "癸丑", "day": "戊辰", "hour": "辛酉"}),
        question_key="q_ten_god_metadata",
        message="透出的十神和藏干层十神不同，先按什么边界理解？",
        structure_label="机会型-透藏十神冲突",
        collision_focus="ten_god_visible_hidden_conflict",
        expected_recommended_keys=["q_ten_god_metadata"],
        expected_answer_kind="metadata_boundary",
        expected_source_signal_category="ten_god",
        expected_knowledge_ids=["p10.ten_god_five_family_plain_language", "p10.ten_god_visible_hidden_boundary"],
        expected_text_contains=["五类关系", "藏干层面"],
        tags=["p11", "ten_god", "visible_hidden_conflict"],
        knowledge_tags=["ku:ten_god_metadata", "ku:visible_hidden_boundary"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.p11.income_wealth_visible_clashed",
        chart=make_synthetic_chart("syn.guided.p11.income_wealth_visible_clashed", {"year": "甲子", "month": "丁巳", "day": "戊午", "hour": "壬戌"}),
        question_key="q_income_stability",
        message="财富元素可见但被冲时，收入稳定性结构怎么读？",
        structure_label="波动型-财富可见被冲",
        collision_focus="income_wealth_visible_clashed",
        expected_recommended_keys=["q_income_stability"],
        expected_answer_kind="income_structure",
        expected_source_signal_category="wealth_feature",
        expected_relation_types=["clash"],
        expected_text_contains=["财富可达性", "disrupted"],
        tags=["p11", "income_structure", "wealth_visible", "wealth_clashed"],
        knowledge_tags=["ku:income_stability", "ku:wealth_accessibility"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.p11.income_wealth_visible_bound",
        chart=make_synthetic_chart("syn.guided.p11.income_wealth_visible_bound", {"year": "壬子", "month": "己丑", "day": "戊辰", "hour": "丙申"}),
        question_key="q_income_stability",
        message="财富元素可见但被合住时，收入稳定性结构怎么读？",
        structure_label="机会型-财富可见被合",
        collision_focus="income_wealth_visible_bound",
        expected_recommended_keys=["q_income_stability"],
        expected_answer_kind="income_structure",
        expected_source_signal_category="wealth_feature",
        expected_relation_types=["combination"],
        expected_text_contains=["财富可达性", "bound"],
        tags=["p11", "income_structure", "wealth_visible", "wealth_bound"],
        knowledge_tags=["ku:income_stability", "ku:wealth_accessibility"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.p11.time_trigger_relation_no_natal_mutation",
        chart=make_synthetic_chart("syn.guided.p11.time_trigger_relation_no_natal_mutation", {"year": "甲子", "month": "戊辰", "day": "庚戌", "hour": "乙酉"}),
        time_context=make_synthetic_time_context(
            make_synthetic_chart("syn.guided.p11.time_trigger_relation_no_natal_mutation", {"year": "甲子", "month": "戊辰", "day": "庚戌", "hour": "乙酉"}),
            luck_pillar="戊午",
            flow_pillar="丙辰",
            flow_relations={"clashes": ["辰戌"]},
        ),
        question_key="q_time_vs_natal_relation",
        message="时间层触发关系时，为什么不能改写本命结构？",
        structure_label="波动型-时间触发不改本命",
        collision_focus="time_trigger_relation_no_natal_mutation",
        expected_recommended_keys=["kbq_time_vs_natal_relation"],
        expected_answer_kind="branch_relation",
        expected_source_signal_category="branch_relation",
        expected_relation_types=["clash"],
        expected_text_contains=["时间背景", "流年", "冲"],
        tags=["p11", "time_layer", "branch_relation", "no_natal_mutation"],
        knowledge_tags=["ku:time_context_boundary", "ku:branch_relation"],
    ),
    GuidedSyntheticCase(
        case_id="syn.guided.p11.month_command_neutral_with_income_collision",
        chart=make_synthetic_chart("syn.guided.p11.month_command_neutral_with_income_collision", {"year": "庚申", "month": "戊辰", "day": "壬子", "hour": "丁未"}),
        question_key="q_month_command_anchor",
        message="月令、收入结构和地支关系同时出现时，月令为什么仍只是结构背景？",
        structure_label="稳定型-月令收入碰撞",
        collision_focus="month_command_income_relation_boundary",
        expected_recommended_keys=["q_month_command_anchor", "q_income_stability"],
        expected_answer_kind="metadata_boundary",
        expected_source_signal_category="strength_model",
        expected_knowledge_ids=["p10.month_command_season_not_verdict"],
        expected_text_contains=["月令不能单独推出身强、身弱或好坏"],
        tags=["p11", "month_command", "income_structure", "boundary"],
        knowledge_tags=["ku:month_command_boundary", "ku:income_stability"],
    ),
]
