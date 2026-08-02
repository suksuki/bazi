from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal

MINGLI_AGENT_METHOD_DISTILLATION_VERSION = (
    "v60.mingli-agent-method-distillation.001"
)

OUTPUT_TO_PRESSURE = "bazi.mechanism.output-to-pressure@1"
OUTPUT_TO_WEALTH = "bazi.mechanism.output-to-wealth@1"

MethodGate = Literal["SUPPORTED", "CONDITIONAL", "BROKEN", "UNRESOLVED"]


_CHECK_GUIDANCE: dict[str, dict[str, dict[str, object]]] = {
    OUTPUT_TO_PRESSURE: {
        "OUTPUT_SOURCE_AVAILABILITY": {
            "question": "精确到食神或伤官后，来源是否有真实位置与力量？",
            "supports_when": "来源明透或有已准入的有效出处",
            "opposes_when": "来源不存在、被夺，或仅凭结构名称补出",
            "conditional_when": "来源仅藏或力量受制",
            "required_fact_keys": ("exact_source", "source_manifestation"),
            "forbidden_shortcuts": ("食伤成员存在即来源可用",),
            "counterexample": "有食伤不等于食伤已经能够制杀或制官",
        },
        "OFFICIAL_KILLING_ROLE_POSITIONED": {
            "question": "目标究竟是七杀还是正官，是否构成全盘有效压力？",
            "supports_when": "目标类型、位置与压力角色均已明确",
            "opposes_when": "把正官七杀混称，或目标并非整盘压力",
            "conditional_when": "目标仅藏或压力角色仍与其他路径竞争",
            "required_fact_keys": ("exact_target", "target_manifestation"),
            "forbidden_shortcuts": ("官杀成员存在即成为核心压力",),
            "counterexample": "七杀存在不等于七杀已成为整盘主轴",
        },
        "DAY_MASTER_CAPACITY": {
            "question": "日主能否承受泄身与官杀压力，并持续调动来源？",
            "supports_when": "季节、根、印比与泄耗比较后仍有承载",
            "opposes_when": "泄耗压力超过可持续承载且无救应",
            "conditional_when": "身弱与从势竞争尚未裁决",
            "required_fact_keys": ("season", "root", "peer", "resource"),
            "forbidden_shortcuts": ("按五行或同类数量投票",),
            "counterexample": "无根而有浮比，不等于当然身强或当然从势",
        },
        "VISIBLE_HIDDEN_REACHABILITY": {
            "question": "精确来源与精确目标是否在同层或有已准入桥梁相接？",
            "supports_when": "同层直达或已有准入关系桥",
            "opposes_when": "来源与目标只分别存在于显藏两层且没有桥",
            "conditional_when": "同支局部相邻或组合改向仍待裁决",
            "required_fact_keys": ("source_manifestation", "target_manifestation"),
            "forbidden_shortcuts": ("来源和目标各自存在即视为可达",),
            "counterexample": "丁明透、辛仅藏且无桥时不能直接写丁制辛",
        },
        "RESOURCE_OR_OTHER_BLOCKER_RESOLUTION": {
            "question": "印夺食、财居中、组合改向等阻断是否已解决？",
            "supports_when": "阻断不存在、很弱或已有清晰救应",
            "opposes_when": "财居中形成食伤生财生杀，或强印夺食占上风",
            "conditional_when": "三合仅成势、是否化局与改向未定",
            "required_fact_keys": ("resource", "wealth_bridge", "structure_candidates"),
            "forbidden_shortcuts": ("发现阻断反而记为支持",),
            "counterexample": "财星居中时不得同时无条件加强直接制杀",
        },
        "SOURCE_AND_TARGET_SAME_LAYER": {
            "question": "来源与目标是否具备同层直接作用条件？",
            "supports_when": "精确来源与目标同层且没有更强改向",
            "opposes_when": "一方明透、一方仅藏且无已准入通道",
            "conditional_when": "同支局部链存在但整体作用未定",
            "required_fact_keys": ("exact_role_paths",),
            "forbidden_shortcuts": ("跨层成员齐备即视为直接作用",),
            "counterexample": "食神透而七杀仅藏，不自动等于食神制杀",
        },
    },
    OUTPUT_TO_WEALTH: {
        "OUTPUT_SOURCE_AVAILABILITY": {
            "question": "精确到食神或伤官后，来源是否有真实位置与力量？",
            "supports_when": "来源明透或有已准入的有效出处",
            "opposes_when": "来源不存在、被夺，或仅凭结构名称补出",
            "conditional_when": "来源仅藏或力量受制",
            "required_fact_keys": ("exact_source", "source_manifestation"),
            "forbidden_shortcuts": ("食伤成员存在即来源可用",),
            "counterexample": "有食伤不等于已经形成可持续产出",
        },
        "WEALTH_TARGET_REACHABILITY": {
            "question": "正财或偏财目标真实存在，并能承接具体食伤来源吗？",
            "supports_when": "财目标存在且同层、同支或经准入通道可达",
            "opposes_when": "财目标不存在，或完全被夺、冲散、改向",
            "conditional_when": "财仅藏但存在局部相生链候选",
            "required_fact_keys": ("exact_target", "target_manifestation"),
            "forbidden_shortcuts": ("财不透即否定所有生财路径",),
            "counterexample": "同支食伤与财可以是局部链候选，但不是结果证明",
        },
        "DAY_MASTER_CAPACITY": {
            "question": "日主能否持续承担泄身与财耗？",
            "supports_when": "季节、根、印比与泄耗比较后仍能持续输出",
            "opposes_when": "身弱不任泄耗且无救应",
            "conditional_when": "身弱与从势竞争尚未裁决",
            "required_fact_keys": ("season", "root", "peer", "resource"),
            "forbidden_shortcuts": ("用承载一项直接决定两张候选胜负",),
            "counterexample": "路径存在与路径是否可用必须分开",
        },
        "RESOURCE_SUPPRESSION_RESOLUTION": {
            "question": "印星对食伤来源的抑制是否占上风？",
            "supports_when": "印不夺食，或有通关使输出仍可持续",
            "opposes_when": "强印直接压制主要食伤来源",
            "conditional_when": "印仅藏、有效度仍待整盘比较",
            "required_fact_keys": ("resource", "exact_source"),
            "forbidden_shortcuts": ("见印即判夺食",),
            "counterexample": "弱藏印不能机械取消全部输出",
        },
        "PEER_COMPETITION_RESOLUTION": {
            "question": "比劫是否真正争夺财目标，还是只形成承载竞争证据？",
            "supports_when": "比劫无力争财或已有清晰分流与承接",
            "opposes_when": "有效比劫直接争夺财目标并占上风",
            "conditional_when": "比劫浮透无根，作用强度未定",
            "required_fact_keys": ("peer", "exact_target"),
            "forbidden_shortcuts": ("见比劫即断破财或第三者",),
            "counterexample": "浮透比肩只构成竞争证据，不等于结果事件",
        },
    },
}

_ROLE_PAIRS = {
    OUTPUT_TO_PRESSURE: (
        ("食神", "七杀", "FOOD_GOD_TO_SEVEN_KILLING", "食神制杀候选"),
        ("伤官", "七杀", "HURTING_OFFICIAL_TO_SEVEN_KILLING", "伤官制杀候选"),
        ("伤官", "正官", "HURTING_OFFICIAL_TO_PROPER_OFFICIAL", "伤官见官／制官候选"),
        ("食神", "正官", "FOOD_GOD_TO_PROPER_OFFICIAL", "食神与正官关系候选"),
    ),
    OUTPUT_TO_WEALTH: (
        ("食神", "正财", "FOOD_GOD_TO_DIRECT_WEALTH", "食神生正财候选"),
        ("食神", "偏财", "FOOD_GOD_TO_INDIRECT_WEALTH", "食神生偏财候选"),
        ("伤官", "正财", "HURTING_OFFICIAL_TO_DIRECT_WEALTH", "伤官生正财候选"),
        ("伤官", "偏财", "HURTING_OFFICIAL_TO_INDIRECT_WEALTH", "伤官生偏财候选"),
    ),
}


def distilled_check_guidance(
    pattern_ref: str,
    required_checks: Sequence[str],
    *,
    compact: bool = False,
) -> tuple[dict[str, object], ...]:
    guidance = _CHECK_GUIDANCE.get(pattern_ref, {})
    if compact:
        return tuple(
            {
                "check_code": check_code,
                "ruling_rule": (
                    f"SUPPORTS={guidance[check_code]['supports_when']}；"
                    f"OPPOSES={guidance[check_code]['opposes_when']}；"
                    f"其余按条件完整度裁 CONDITIONAL 或 UNRESOLVED"
                ),
                "forbidden_shortcut": guidance[check_code]["forbidden_shortcuts"][0],
            }
            for check_code in required_checks
            if check_code in guidance
        )
    return tuple(
        {"check_code": check_code, **guidance[check_code]}
        for check_code in required_checks
        if check_code in guidance
    )


def exact_role_paths(
    pattern_ref: str,
    ten_god_occurrences: Mapping[str, Sequence[str]],
) -> tuple[dict[str, object], ...]:
    paths: list[dict[str, object]] = []
    for source, target, path_ref, label in _ROLE_PAIRS.get(pattern_ref, ()):
        source_coordinates = tuple(ten_god_occurrences.get(source, ()))
        target_coordinates = tuple(ten_god_occurrences.get(target, ()))
        if not source_coordinates or not target_coordinates:
            continue
        paths.append(
            {
                "role_path_ref": path_ref,
                "label": label,
                "source": {
                    "ten_god": source,
                    "coordinates": source_coordinates,
                    "manifestation": _manifestation(source_coordinates),
                },
                "target": {
                    "ten_god": target,
                    "coordinates": target_coordinates,
                    "manifestation": _manifestation(target_coordinates),
                },
                "identity_rule": "必须按本子路径裁决，禁止退回食伤／官杀／财星组名",
            }
        )
    return tuple(paths)


def bound_method_context(
    *,
    pattern_ref: str,
    ten_god_occurrences: Mapping[str, Sequence[str]],
    root_candidates: Sequence[str],
    visible_peers: Sequence[str],
    hidden_resources: Sequence[str],
) -> dict[str, object]:
    return {
        "method_asset_ref": MINGLI_AGENT_METHOD_DISTILLATION_VERSION,
        "governance_status": "OWNER_AUTHORIZED_RESEARCH_CANDIDATE",
        "exact_role_paths": exact_role_paths(pattern_ref, ten_god_occurrences),
        "capacity_fact_lock": {
            "root_candidates": tuple(root_candidates),
            "visible_peers": tuple(visible_peers),
            "hidden_resources": tuple(hidden_resources),
            "counting_forbidden": True,
        },
    }


def day_master_regime_method_asset(
    *,
    seasonal_relation: str,
    root_candidates: Sequence[str],
    visible_peers: Sequence[str],
    hidden_resources: Sequence[str],
) -> dict[str, object]:
    return {
        "method_asset_ref": "REGIME_WEAK_VS_FOLLOW_TREND_001",
        "governance_status": "OWNER_AUTHORIZED_RESEARCH_CANDIDATE",
        "observed_facts": {
            "seasonal_relation": seasonal_relation,
            "root_candidates": tuple(root_candidates),
            "visible_peers": tuple(visible_peers),
            "hidden_resources": tuple(hidden_resources),
        },
        "candidate_states": (
            {
                "state": "ORDINARY_WEAK",
                "requires": "受泄克，但仍有经比较后有效的自立或支持点",
            },
            {
                "state": "FOLLOWING_TENDENCY",
                "requires": "无有效根、印比不可用、异类趋势闭合且无反向力量",
            },
            {
                "state": "FALSE_FOLLOW_COMPETITION",
                "maps_to_output": "WEAK_OR_UNCERTAIN",
                "requires": "无根而仍有浮比、弱藏印或合化未定等竞争证据",
            },
        ),
        "hard_rules": (
            "有有效根或透而有根的印比时不得判从",
            "仅凭无根不得判从",
            "三合成员齐备不得直接当作合化后的承载能力",
            "未完成身弱／从势竞争审计不得输出喜忌",
        ),
    }


def domain_method_assets(
    *,
    gender: str,
    ten_god_occurrences: Mapping[str, Sequence[str]],
    spouse_palace: Mapping[str, object],
) -> dict[str, object]:
    normalized_gender = gender.strip().lower()
    spouse_labels = (
        ("正财", "偏财")
        if normalized_gender == "male"
        else ("正官", "七杀")
        if normalized_gender == "female"
        else ()
    )
    return {
        "relationship": {
            "method_asset_ref": "RELATION_SPOUSE_STAR_AND_PALACE_TWO_AXIS_001",
            "gender_fact": normalized_gender,
            "spouse_star_labels": spouse_labels,
            "spouse_star_coordinates": tuple(
                {
                    "ten_god": label,
                    "coordinates": tuple(ten_god_occurrences.get(label, ())),
                }
                for label in spouse_labels
            ),
            "spouse_palace": dict(spouse_palace),
            "minimum_axes": ("SPOUSE_STAR", "SPOUSE_PALACE"),
            "forbidden_shortcuts": (
                "单枚偏印推出精神共鸣或情感安全",
                "单枚比劫推出竞争或第三者",
                "财坐夫妻宫推出配偶富裕或婚姻稳定",
                "官杀强弱替代男命财星通道",
            ),
        },
        "family": {
            "method_asset_ref": "FAMILY_SCOPE_AND_TWO_AXIS_001",
            "required_scope": ("FAMILY_OF_ORIGIN", "CURRENT_HOUSEHOLD", "PARENT_CHILD"),
            "minimum_axes": ("DECLARED_SCOPE", "PALACE", "STAR_OR_RELATION"),
            "reconciliation_reserved_axis": "LIFE_CASE_OBSERVATION",
            "forbidden_shortcuts": (
                "单枚偏印推出家庭精神滋养或安全感",
                "原生家庭与当前家庭复用同一段判断",
            ),
        },
    }


def cross_card_discriminator() -> dict[str, object]:
    return {
        "method_asset_ref": "OUTPUT_WEALTH_VS_CONTROL_KILLING_001",
        "shared_checks_not_decisive_alone": (
            "OUTPUT_SOURCE_AVAILABILITY",
            "DAY_MASTER_CAPACITY",
        ),
        "pressure_decisive_checks": (
            "OFFICIAL_KILLING_ROLE_POSITIONED",
            "VISIBLE_HIDDEN_REACHABILITY",
            "RESOURCE_OR_OTHER_BLOCKER_RESOLUTION",
            "SOURCE_AND_TARGET_SAME_LAYER",
        ),
        "wealth_decisive_checks": (
            "WEALTH_TARGET_REACHABILITY",
            "RESOURCE_SUPPRESSION_RESOLUTION",
            "PEER_COMPETITION_RESOLUTION",
        ),
        "decision_rule": "先裁路径存在，再裁路径主导，最后裁路径是否可用",
    }


def research_regime_outcome(
    *,
    effective_root: bool,
    rooted_visible_support: bool,
    visible_peer_competition: bool,
    hidden_resource_competition: bool,
    dominant_chain_closed: bool,
) -> str:
    """Synthetic-only invariant evaluator; never writes a professional verdict."""

    if effective_root or rooted_visible_support:
        return "ORDINARY_WEAK"
    if not dominant_chain_closed:
        return "UNRESOLVED"
    if visible_peer_competition or hidden_resource_competition:
        return "FALSE_FOLLOW_CANDIDATE"
    return "FOLLOW_TREND_CANDIDATE"


def research_output_path_gate(
    *,
    pattern_ref: str,
    source_present: bool,
    target_present: bool,
    source_target_reachable: bool,
    target_is_seven_killing: bool = False,
    wealth_bridge_present: bool = False,
    peer_competition_resolved: bool = True,
) -> MethodGate:
    """Synthetic-only flip/hold oracle for the first two distilled method cards."""

    if not source_present or not target_present:
        return "BROKEN"
    if not source_target_reachable:
        return "BROKEN"
    if pattern_ref == OUTPUT_TO_PRESSURE:
        if not target_is_seven_killing or wealth_bridge_present:
            return "CONDITIONAL"
        return "SUPPORTED"
    if pattern_ref == OUTPUT_TO_WEALTH:
        return "SUPPORTED" if peer_competition_resolved else "CONDITIONAL"
    return "UNRESOLVED"


def _manifestation(coordinates: Sequence[str]) -> str:
    visible = any("干" in item and "支藏" not in item for item in coordinates)
    hidden = any("支藏" in item for item in coordinates)
    if visible and hidden:
        return "VISIBLE_AND_HIDDEN"
    if visible:
        return "VISIBLE_ONLY"
    return "HIDDEN_ONLY"
