from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.api.runtime import run_runtime_from_pillars
from v20.validation.case_matrix import build_regression_rule_synthetic_case_payloads
from v20.storage.local_jsonl import local_jsonl_store_from_env


@dataclass(frozen=True)
class SyntheticRuleCase:
    case_id: str
    pillar_displays: tuple[str, str, str, str]
    question_key: str
    expected_rule_domains: tuple[str, ...]
    expected_feature_prefixes: tuple[str, ...]
    expected_question_keys: tuple[str, ...]
    flow_year_pillar: str = ""
    luck_pillar: str = ""
    flow_month_pillar: str = ""
    forbidden_text: tuple[str, ...] = ("发财", "破财", "疾病", "一定", "必然")
    notes: str = ""
    guardrails: tuple[str, ...] = (
        "SYNTHETIC_RULE_CASE_HAS_EXPECTED_FEATURE_COLLISIONS",
        "NO_DESTINY_TRUTH_LABEL",
        "NO_EVENT_OUTCOME_LABEL",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


RULE_SYNTHETIC_CASES: tuple[SyntheticRuleCase, ...] = (
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.wealth_visible_focus",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_income_stability",
        expected_rule_domains=("wealth", "ten_god", "strength"),
        expected_feature_prefixes=(
            "feature.wealth.visible_material",
            "feature.ten_god.focus.zheng_cai",
        ),
        expected_question_keys=("q_income_stability",),
        notes="财星材料显现，用来验证财星规则裁决是否能命中当前盘特征。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.branch_collision",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_branch_relation_detail",
        expected_rule_domains=("branch",),
        expected_feature_prefixes=(
            "feature.branch.visible_relation",
            "feature.branch.relation_type.clash",
        ),
        expected_question_keys=("q_branch_relation_detail",),
        notes="原局地支冲破并见，用来验证地支关系规则裁决的碰撞能力。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.element_prominent",
        pillar_displays=("壬寅", "甲辰", "丙子", "甲午"),
        question_key="q_element_balance",
        expected_rule_domains=("element",),
        expected_feature_prefixes=(
            "feature.element.prominent.wood",
            "feature.element.weak.metal",
        ),
        expected_question_keys=("q_element_balance",),
        notes="木偏显、金偏弱，用来验证五行规则裁决是否命中特征而不落入健康断语。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.time_trigger",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_time_layer_context",
        expected_rule_domains=("time",),
        expected_feature_prefixes=(
            "feature.time.explicit_context",
            "feature.time.relation_type.",
            "feature.time.ten_god.",
        ),
        expected_question_keys=("q_time_layer_context", "q_time_relation_triggers"),
        flow_year_pillar="丙午",
        luck_pillar="甲申",
        notes="显式大运流年进入，只验证时间层触发规则，不生成应期断语。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.calendar_boundary",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_time_layer_context",
        expected_rule_domains=("time",),
        expected_feature_prefixes=(
            "feature.time.explicit_context",
        ),
        expected_question_keys=("q_time_layer_context",),
        flow_year_pillar="丙午",
        notes="排盘边界只验证时间层上下文和不确定性表达，不把真太阳时或早晚子时直接变成命理结论。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.useful_god_candidate_gate",
        pillar_displays=("壬寅", "甲辰", "丙子", "甲午"),
        question_key="q_useful_god_candidates",
        expected_rule_domains=("useful_god", "strength", "element"),
        expected_feature_prefixes=(
            "feature.useful_god.candidate_paths",
            "feature.useful_god.evidence_gate",
            "feature.element.",
        ),
        expected_question_keys=("q_useful_god_candidates",),
        notes="用神只能作为候选路径，验证用神门槛不会直接定喜忌。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.pattern_review_gate",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_pattern_structure",
        expected_rule_domains=("pattern",),
        expected_feature_prefixes=("feature.pattern.review_index",),
        expected_question_keys=("q_pattern_structure",),
        notes="格局只进入复核路径，验证不会直接定格局等级或成败。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.auxiliary_symbol_low_weight",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_pattern_structure",
        expected_rule_domains=("pattern",),
        expected_feature_prefixes=("feature.pattern.review_index",),
        expected_question_keys=("q_pattern_structure",),
        notes="神煞、空亡、十二长生、纳音只允许作为低权重辅助，不允许替代格局、十神、强弱和时间层证据。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.career_projection",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_career_structure",
        expected_rule_domains=("career", "ten_god"),
        expected_feature_prefixes=(
            "feature.ten_god.focus.zheng_guan",
            "feature.branch.visible_relation",
        ),
        expected_question_keys=("q_career_structure",),
        notes="事业只能作为十神、格局、承载力和地支互动上的应用投影。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.relationship_projection",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_relationship_structure",
        expected_rule_domains=("relationship", "branch"),
        expected_feature_prefixes=(
            "feature.branch.visible_relation",
            "feature.ten_god.visible_relation",
        ),
        expected_question_keys=("q_relationship_structure",),
        notes="关系主题必须回到地支互动、十神来源和承接边界，不能直接断关系事件。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.study_exam_topic",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_career_structure",
        expected_rule_domains=("career", "ten_god"),
        expected_feature_prefixes=(
            "feature.ten_god.focus.zheng_guan",
            "feature.branch.visible_relation",
        ),
        expected_question_keys=("q_career_structure",),
        notes="学业考试专题只验证印星/食伤/官杀/承载力路径，不承诺成绩、录取或证书结果。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.children_family_topic",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_relationship_structure",
        expected_rule_domains=("relationship", "branch"),
        expected_feature_prefixes=(
            "feature.branch.visible_relation",
            "feature.ten_god.visible_relation",
        ),
        expected_question_keys=("q_relationship_structure",),
        notes="子女家庭专题只验证食伤、时柱、互动和承接边界，不推断隐私或确定事件。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.migration_topic",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_time_layer_context",
        expected_rule_domains=("time", "branch"),
        expected_feature_prefixes=(
            "feature.time.explicit_context",
            "feature.branch.visible_relation",
        ),
        expected_question_keys=("q_time_layer_context", "q_time_relation_triggers"),
        flow_year_pillar="丙午",
        luck_pillar="甲申",
        notes="迁移远行专题只验证原局动象和岁运触发，不断搬迁日期、事故或移民结果。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.housing_property_topic",
        pillar_displays=("壬寅", "甲辰", "丙子", "甲午"),
        question_key="q_income_stability",
        expected_rule_domains=("wealth", "branch"),
        expected_feature_prefixes=(
            "feature.element.prominent.wood",
            "feature.branch.visible_relation",
        ),
        expected_question_keys=("q_income_stability",),
        notes="房产居住专题只验证财库、动象、家庭约束和承接边界，不断房价、贷款或搬迁结果。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.social_cooperation_topic",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_relationship_structure",
        expected_rule_domains=("relationship", "branch"),
        expected_feature_prefixes=(
            "feature.branch.visible_relation",
            "feature.ten_god.visible_relation",
        ),
        expected_question_keys=("q_relationship_structure",),
        notes="人际合作专题只验证比劫、食伤、财官牵动和地支互动，不推断背叛、诉讼或合作结果。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.startup_management_topic",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_career_structure",
        expected_rule_domains=("career", "wealth", "ten_god"),
        expected_feature_prefixes=(
            "feature.ten_god.focus.zheng_guan",
            "feature.branch.visible_relation",
        ),
        expected_question_keys=("q_career_structure",),
        notes="创业管理专题只验证输出、财路、规则压力、协作和承载力，不承诺创业成败或收益时间。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.palace_topic_projection",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_relationship_structure",
        expected_rule_domains=("relationship", "branch"),
        expected_feature_prefixes=(
            "feature.branch.visible_relation",
            "feature.ten_god.visible_relation",
        ),
        expected_question_keys=("q_relationship_structure",),
        notes="宫位象法只验证主题落点和证据复核，不从单个宫位推断亲属、伴侣、职业或时间结果。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.palace_career_position_boundary",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_career_structure",
        expected_rule_domains=("career", "branch"),
        expected_feature_prefixes=(
            "feature.ten_god.focus.zheng_guan",
            "feature.branch.visible_relation",
        ),
        expected_question_keys=("q_career_structure",),
        notes="宫位事业投射只验证职业主题落点和十神/地支证据，不从事业宫位直接断职位、升降或单位结果。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.palace_hour_family_boundary",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_relationship_structure",
        expected_rule_domains=("relationship", "branch"),
        expected_feature_prefixes=(
            "feature.branch.visible_relation",
            "feature.ten_god.visible_relation",
        ),
        expected_question_keys=("q_relationship_structure",),
        notes="时柱和晚景/子女宫位只验证主题承接边界，不推断子女事件、家庭隐私或晚年确定结果。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.blind_lifa_auxiliary_boundary",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_pattern_structure",
        expected_rule_domains=("pattern",),
        expected_feature_prefixes=("feature.pattern.review_index",),
        expected_question_keys=("q_pattern_structure",),
        notes="盲派象法只验证辅助取象和结构复核，不让单个象法线索替代强弱、十神、格局或时间证据。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.blind_lifa_zuogong_chain_boundary",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_pattern_structure",
        expected_rule_domains=("pattern",),
        expected_feature_prefixes=("feature.pattern.review_index",),
        expected_question_keys=("q_pattern_structure",),
        notes="盲派做功链只验证动作链条和结构承接，不从一个做功线索直接断成败、财富或关系事件。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.blind_lifa_counterevidence_boundary",
        pillar_displays=("壬寅", "甲辰", "丙子", "甲午"),
        question_key="q_pattern_structure",
        expected_rule_domains=("pattern", "element"),
        expected_feature_prefixes=(
            "feature.pattern.review_index",
            "feature.element.prominent.wood",
        ),
        expected_question_keys=("q_pattern_structure",),
        notes="盲派取象必须允许反证进入，验证象法线索不能压过五行气候、承载和结构复核。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.answer_governance_boundary",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_pattern_structure",
        expected_rule_domains=("pattern",),
        expected_feature_prefixes=("feature.pattern.review_index",),
        expected_question_keys=("q_pattern_structure",),
        notes="回答治理验证证据范围、边界和下一步问题，不从候选结构输出确定运势或精确事件。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.answer_governance_role_boundary",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_relationship_structure",
        expected_rule_domains=("relationship", "branch"),
        expected_feature_prefixes=(
            "feature.branch.visible_relation",
            "feature.ten_god.visible_relation",
        ),
        expected_question_keys=("q_relationship_structure",),
        notes="回答治理角色边界验证游客/用户/命理师/管理员各自表达密度，不把内部治理信号泄露给游客。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.answer_governance_next_step_boundary",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_time_layer_context",
        expected_rule_domains=("time", "pattern"),
        expected_feature_prefixes=(
            "feature.time.explicit_context",
            "feature.pattern.review_index",
        ),
        expected_question_keys=("q_time_layer_context", "q_time_relation_triggers"),
        flow_year_pillar="丙午",
        luck_pillar="甲申",
        notes="回答治理下一步问题验证必须输出可复核方向，不从时间层触发写成确定应期或事件。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.ten_god_position_layer_boundary",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_ten_god_focus",
        expected_rule_domains=("ten_god", "branch"),
        expected_feature_prefixes=(
            "feature.ten_god.visible_relation",
            "feature.branch.visible_relation",
        ),
        expected_question_keys=("q_ten_god_focus",),
        notes="十神位置层只验证年/月/日/时和明暗来源，不从单个十神直接断性格、事业、财富或关系结果。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.branch_arbitration_clash_combine_boundary",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_branch_relation_detail",
        expected_rule_domains=("branch",),
        expected_feature_prefixes=(
            "feature.branch.visible_relation",
            "feature.branch.relation_type.clash",
        ),
        expected_question_keys=("q_branch_relation_detail",),
        notes="冲合并见只验证关系仲裁和干扰证据，不把冲合刑害破名称写成吉凶或事件。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.pattern_false_following_counterexample",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_pattern_structure",
        expected_rule_domains=("pattern",),
        expected_feature_prefixes=("feature.pattern.review_index",),
        expected_question_keys=("q_pattern_structure",),
        notes="假从和破格反例验证格局必须先看根气、逆势材料和清浊混杂。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.time_fuyin_fanyin_storage_boundary",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_time_layer_context",
        expected_rule_domains=("time", "branch"),
        expected_feature_prefixes=(
            "feature.time.explicit_context",
            "feature.branch.visible_relation",
        ),
        expected_question_keys=("q_time_layer_context", "q_time_relation_triggers"),
        flow_year_pillar="甲午",
        luck_pillar="甲子",
        notes="伏吟反吟和墓库开闭只验证时间层牵动，不输出准确应期、事故、疾病、交易或关系结果。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.palace_application_detail_boundary",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        question_key="q_relationship_structure",
        expected_rule_domains=("relationship", "branch"),
        expected_feature_prefixes=(
            "feature.branch.visible_relation",
            "feature.ten_god.visible_relation",
        ),
        expected_question_keys=("q_relationship_structure",),
        notes="夫妻宫、事业环境和时柱家庭晚景只定位主题，不从宫位细分直接断伴侣、职业、子女或晚年事件。",
    ),
    SyntheticRuleCase(
        case_id="v20.rule.synthetic.health_balance_boundary",
        pillar_displays=("壬寅", "甲辰", "丙子", "甲午"),
        question_key="q_health_balance_boundary",
        expected_rule_domains=("health", "element"),
        expected_feature_prefixes=(
            "feature.element.prominent.wood",
            "feature.element.weak.metal",
        ),
        expected_question_keys=("q_health_balance_boundary",),
        notes="健康相关只能验证五行平衡和结构压力边界，不能生成疾病判断。",
    ),
)


def _read_case_count_from_env(
    env_name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    try:
        value = int(os.getenv(env_name, str(default)))
    except ValueError:
        return default
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def _build_matrix_rule_synthetic_cases(
    *,
    case_count: int | None = None,
) -> tuple[SyntheticRuleCase, ...]:
    target = case_count if case_count is not None else _read_case_count_from_env(
        "V20_RULE_SYNTHETIC_CASE_TARGET",
        default=24,
        minimum=0,
        maximum=3000,
    )
    payloads = build_regression_rule_synthetic_case_payloads(case_count=target)
    rows: list[SyntheticRuleCase] = []
    for payload in payloads:
        rows.append(
            SyntheticRuleCase(
                case_id=str(payload["case_id"]),
                pillar_displays=tuple(payload["pillar_displays"]),
                question_key=str(payload.get("question_key", "")),
                expected_rule_domains=tuple(payload["expected_rule_domains"]),
                expected_feature_prefixes=tuple(payload["expected_feature_prefixes"]),
                expected_question_keys=tuple(payload["expected_question_keys"]),
                notes=str(payload["notes"]),
            )
        )
    return tuple(rows)


RULE_SYNTHETIC_CASES = RULE_SYNTHETIC_CASES + _build_matrix_rule_synthetic_cases()


def run_rule_synthetic_suite(cases: tuple[SyntheticRuleCase, ...] = RULE_SYNTHETIC_CASES) -> dict[str, object]:
    results = [_evaluate_rule_case(case) for case in cases]
    failures = [failure for result in results for failure in result["failures"]]
    return {
        "version": "v20.rule_synthetic_suite.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "case_count": len(results),
        "results": results,
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_RULE_SUITE_IS_RULE_COLLISION_VALIDATION",
            "KNOWLEDGE_RULES_ARE_TESTED_AGAINST_SYNTHETIC_CHARTS",
            "FULL_CORPUS_IS_NOT_RULE_TRUTH",
            "ACTIVE_RULE_ITERATION",
        ],
    }


def build_rule_synthetic_training_report(
    cases: tuple[SyntheticRuleCase, ...] = RULE_SYNTHETIC_CASES,
) -> dict[str, object]:
    suite = run_rule_synthetic_suite(cases)
    domain_rows: dict[str, dict[str, object]] = {}
    rule_rows: dict[str, dict[str, object]] = {}

    for result in suite["results"]:
        if not isinstance(result, dict):
            continue
        case_id = str(result.get("case_id", ""))
        expected_domains_tuple = _as_tuple_of_str(result.get("expected_rule_domains", ()))
        candidate_rule_domains = _as_tuple_of_str(result.get("candidate_rule_domains", ()))
        matched_by_domain = result.get("matched_feature_ids_by_domain", {})
        matched_rules_by_domain = result.get("matched_rule_keys_by_domain", {})
        matched_rules = _as_tuple_of_str(result.get("matched_rule_keys", ()))
        case_passed = result.get("ok") is True
        case_feature_ids = _as_tuple_of_str(result.get("feature_ids", ()))
        domains_for_case = tuple(dict.fromkeys((*expected_domains_tuple, *candidate_rule_domains)))

        for key in domains_for_case:
            row = domain_rows.setdefault(
                key,
                {
                    "domain": key,
                    "case_count": 0,
                    "pass_count": 0,
                    "fail_count": 0,
                    "matched_feature_ids": set(),
                    "case_ids": [],
                    "matched_rule_keys": set(),
                },
            )
            row["case_count"] = int(row["case_count"]) + 1
            row["case_ids"].append(case_id)
            if case_passed:
                row["pass_count"] = int(row["pass_count"]) + 1
            else:
                row["fail_count"] = int(row["fail_count"]) + 1
            row["matched_feature_ids"].update(_as_tuple_of_str(matched_by_domain.get(key, ())))
            row["matched_rule_keys"].update(_as_tuple_of_str(matched_rules_by_domain.get(key, ())))

        for rule_key in matched_rules:
            rule_row = rule_rows.setdefault(
                rule_key,
                {
                    "rule_key": rule_key,
                    "case_count": 0,
                    "pass_count": 0,
                    "fail_count": 0,
                    "matched_feature_ids": set(),
                    "case_ids": [],
                    "domains": set(),
                    "source_domain": set(),
                },
            )
            rule_row["case_count"] = int(rule_row["case_count"]) + 1
            if case_passed:
                rule_row["pass_count"] = int(rule_row["pass_count"]) + 1
            else:
                rule_row["fail_count"] = int(rule_row["fail_count"]) + 1
            rule_row["case_ids"].append(case_id)
            rule_row["domains"].update(candidate_rule_domains or expected_domains_tuple)
            rule_row["source_domain"].update(candidate_rule_domains or expected_domains_tuple)
            for key in matched_rules_by_domain:
                for domain_rule_key in _as_tuple_of_str(matched_rules_by_domain.get(key, ())):
                    if domain_rule_key == rule_key:
                        rule_row["matched_feature_ids"].update(_as_tuple_of_str(matched_by_domain.get(key, ())))
            if not rule_row["matched_feature_ids"]:
                rule_row["matched_feature_ids"].update(case_feature_ids)

    rule_domain_training = []
    for row in domain_rows.values():
        case_count = int(row["case_count"])
        pass_count = int(row["pass_count"])
        confidence = round(pass_count / case_count, 4) if case_count else 0.0
        rule_domain_training.append(
            {
                "domain": row["domain"],
                "case_count": case_count,
                "pass_count": pass_count,
                "fail_count": int(row["fail_count"]),
                "synthetic_confidence": confidence,
                "matched_feature_ids": sorted(row["matched_feature_ids"])[:16],
                "matched_rule_keys": tuple(sorted(row.get("matched_rule_keys", set()))),
                "case_ids": row["case_ids"],
                "training_action": "eligible_for_active_weight" if confidence >= 1.0 else "add_counterexample_or_fix_atoms",
                "runtime_allowed": True,
            }
        )

    rule_training = []
    for row in rule_rows.values():
        case_count = int(row["case_count"])
        pass_count = int(row["pass_count"])
        confidence = round(pass_count / case_count, 4) if case_count else 0.0
        rule_training.append(
            {
                "rule_key": row["rule_key"],
                "case_count": case_count,
                "pass_count": pass_count,
                "fail_count": int(row["fail_count"]),
                "synthetic_confidence": confidence,
                "matched_feature_ids": sorted(row["matched_feature_ids"])[:16],
                "case_ids": row["case_ids"],
                "domains": tuple(sorted(row["domains"])),
                "source_domains": tuple(sorted(row["source_domain"])),
                "training_action": "eligible_for_active_weight" if confidence >= 1.0 else "add_counterexample_or_fix_atoms",
                "runtime_allowed": True,
            }
        )

    gap_count = len(suite["failures"])
    return {
        "version": "v20.rule_synthetic_training_report.v1",
        "status": "ready" if suite["ok"] else "needs_review",
        "suite_status": suite["status"],
        "case_count": suite["case_count"],
        "failure_count": gap_count,
        "quality_findings": (
            [f"synthetic_gap_count:{gap_count}"]
            if gap_count
            else []
        ),
        "rule_domain_training": sorted(rule_domain_training, key=lambda row: str(row["domain"])),
        "rule_training": sorted(rule_training, key=lambda row: str(row["rule_key"])),
        "training_scope": [
            "rule_atom_collision_validation",
            "synthetic_counterexample_gap_detection",
            "active_rule_weight_iteration",
        ],
        "not_training_scope": [
            "destiny_truth_learning",
            "fortune_outcome_prediction",
            "full_corpus_rule_truth_learning",
        ],
        "suite": suite,
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_TRAINING_IS_VALIDATION_SIGNAL",
            "RULES_COME_FROM_KNOWLEDGE_AND_LLM_DRAFTS",
            "FULL_CORPUS_REMAINS_PRIOR_AND_COVERAGE_ONLY",
            "PROMOTION_REQUIRES_DECISION_REGISTRY",
            "SYNTHETIC_GAPS_ARE_LEARNING_SIGNALS_NOT_RUNTIME_BLOCKERS",
        ],
    }


def write_rule_synthetic_training_artifact(
    *,
    cases: tuple[SyntheticRuleCase, ...] = RULE_SYNTHETIC_CASES,
    output_dir: Path | None = None,
) -> dict[str, object]:
    report = build_rule_synthetic_training_report(cases=cases)
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "rule_synthetic"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"rule_synthetic_training_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.rule_synthetic_training_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "case_count": report["case_count"],
        "failure_count": report["failure_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RULE_ACTIVATION",
        ],
    }


def read_rule_synthetic_training_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "rule_synthetic") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.rule_synthetic_training_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _evaluate_rule_case(case: SyntheticRuleCase) -> dict[str, object]:
    runtime = run_runtime_from_pillars(
        *case.pillar_displays,
        input_id=case.case_id,
        question_key=case.question_key,
        flow_year_pillar=case.flow_year_pillar,
        luck_pillar=case.luck_pillar,
        flow_month_pillar=case.flow_month_pillar,
    )
    features = [row for row in runtime["feature_layer"]["features"] if isinstance(row, dict)]
    feature_ids = tuple(str(row.get("feature_id", "")) for row in features if row.get("feature_id"))
    questions = tuple(
        str(row.get("question_key", ""))
        for row in runtime.get("questions", ())
        if isinstance(row, dict) and row.get("question_key")
    )
    decisions = tuple(
        row for row in runtime.get("decision_report", {}).get("decisions", ()) if isinstance(row, dict)
    )
    hits = tuple(
        row for row in runtime.get("decision_report", {}).get("hits", ()) if isinstance(row, dict)
    )
    matched_decision_rows = tuple(decisions + hits)
    candidate_domains = _decision_domains(matched_decision_rows)

    matched_by_domain: dict[str, tuple[str, ...]] = {}
    matched_rule_keys_by_domain: dict[str, tuple[str, ...]] = {}
    matched_rule_keys: set[str] = set()
    features_by_domain: dict[str, set[str]] = defaultdict(set)
    rules_by_domain: dict[str, set[str]] = defaultdict(set)

    for row in matched_decision_rows:
        rule_key = str(row.get("rule_key", "")).strip()
        feature_ids = _as_tuple_of_str(row.get("feature_ids", ()))
        if rule_key:
            matched_rule_keys.add(rule_key)
        for domain in _row_domains(row):
            if feature_ids:
                features_by_domain[domain].update(feature_ids)
            if rule_key:
                rules_by_domain[domain].add(rule_key)

    matched_by_domain = {key: tuple(values) for key, values in features_by_domain.items()}
    matched_rule_keys_by_domain = {key: tuple(sorted(values)) for key, values in rules_by_domain.items()}

    failures = []
    for prefix in case.expected_feature_prefixes:
        if not any(feature_id.startswith(prefix) for feature_id in feature_ids):
            failures.append(f"missing_expected_feature_prefix:{case.case_id}:{prefix}")
    for key in case.expected_question_keys:
        if key not in questions:
            failures.append(f"missing_expected_question:{case.case_id}:{key}")
    for domain in case.expected_rule_domains:
        if domain not in candidate_domains:
            failures.append(f"missing_expected_decision_domain:{case.case_id}:{domain}")
        elif not matched_by_domain.get(domain):
            failures.append(f"decision_domain_without_feature_anchor:{case.case_id}:{domain}")
    answer_text = str(runtime.get("answer_text", ""))
    for text in case.forbidden_text:
        if text and text in answer_text:
            failures.append(f"forbidden_text:{case.case_id}:{text}")
    return {
        "version": "v20.rule_synthetic_case_result.v1",
        "case_id": case.case_id,
        "ok": not failures,
        "failures": failures,
        "expected_rule_domains": case.expected_rule_domains,
        "candidate_rule_domains": candidate_domains,
        "expected_feature_prefixes": case.expected_feature_prefixes,
        "feature_ids": feature_ids,
        "matched_feature_ids_by_domain": matched_by_domain,
        "matched_rule_keys_by_domain": matched_rule_keys_by_domain,
        "matched_rule_keys": tuple(sorted(matched_rule_keys)),
        "question_keys": questions,
        "selected_question_key": _selected_question_key(runtime),
        "answer_boundary_ok": not any(text and text in answer_text for text in case.forbidden_text),
        "runtime_mutation": False,
        "guardrails": ["SYNTHETIC_CASE_RESULT_ONLY", "ACTIVE_RULE_ITERATION"],
    }


def _decision_domains(rows: tuple[dict[str, object], ...]) -> tuple[str, ...]:
    domains: list[str] = []
    for row in rows:
        domains.extend(_row_domains(row))
    return tuple(dict.fromkeys(domain for domain in domains if domain))


def _row_domains(row: dict[str, object]) -> tuple[str, ...]:
    domains = [str(row.get("domain", ""))]
    rule_key = str(row.get("rule_key", ""))
    for marker, domain in (
        (".ten_god.", "ten_god"),
        (".wealth.", "wealth"),
        (".strength.", "strength"),
        (".branch.", "branch"),
        (".time.", "time"),
        (".element.", "element"),
        (".useful_god.", "useful_god"),
        (".pattern.", "pattern"),
    ):
        if marker in rule_key:
            domains.append(domain)
    return tuple(dict.fromkeys(domain for domain in domains if domain))


def _selected_question_key(runtime: dict[str, object]) -> str:
    selected_question = runtime.get("selected_question", {})
    if isinstance(selected_question, dict):
        return str(selected_question.get("question_key", ""))
    return ""


def _as_tuple_of_str(value: object) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        return ()
    return tuple(str(row) for row in value if str(row))
