from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal

from abu_v60.mingli.agent_root_gate import MINGLI_EFFECTIVE_ROOT_METHOD_VERSION

MINGLI_AGENT_METHOD_DISTILLATION_VERSION = "v60.mingli-agent-method-distillation.006"

OUTPUT_TO_PRESSURE = "bazi.mechanism.output-to-pressure@1"
OUTPUT_TO_WEALTH = "bazi.mechanism.output-to-wealth@1"
WEALTH_TO_PRESSURE = "bazi.mechanism.wealth-to-pressure@1"
PRESSURE_RESOURCE_SELF = "bazi.mechanism.pressure-resource-self@1"

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
    WEALTH_TO_PRESSURE: {
        "WEALTH_SOURCE_AVAILABILITY": {
            "question": "精确到正财或偏财后，财富来源是否真实存在并能持续发起路径？",
            "supports_when": "财源明透或有已准入的有效出处",
            "opposes_when": "财源不存在、被夺或只是结构名称",
            "conditional_when": "财源仅藏或仍受比劫、印食路径竞争",
            "required_fact_keys": ("exact_source", "source_manifestation"),
            "forbidden_shortcuts": ("见财星即认定财能生官杀",),
            "counterexample": "财星存在不等于财富路径已经能够主导官杀",
        },
        "PRESSURE_TARGET_REACHABILITY": {
            "question": "目标是正官还是七杀，财源与该精确目标是否真实可达？",
            "supports_when": "官杀目标定位且与财源同层或有准入桥",
            "opposes_when": "目标不存在，或显藏分层且没有桥",
            "conditional_when": "目标仅藏、局部相生存在但全盘主导未定",
            "required_fact_keys": ("exact_target", "target_manifestation"),
            "forbidden_shortcuts": ("把正官七杀合称后直接判财生官杀",),
            "counterexample": "明财与仅藏官杀之间没有通道时不能写成已生",
        },
        "DAY_MASTER_CAPACITY": {
            "question": "日主能否承受财耗与官杀压力形成的连续负荷？",
            "supports_when": "根、印比与全盘制化足以承接连续负荷",
            "opposes_when": "财官压力闭合而日主无可持续承载或救应",
            "conditional_when": "身弱、从势与救应竞争尚未裁决",
            "required_fact_keys": ("season", "root", "peer", "resource"),
            "forbidden_shortcuts": ("按同类数量投票决定承载",),
            "counterexample": "路径存在不等于日主可以承受路径结果",
        },
        "VISIBLE_HIDDEN_REACHABILITY": {
            "question": "财源与官杀目标是否同层，或存在可点名的显藏桥？",
            "supports_when": "精确坐标同层直达或有已准入桥梁",
            "opposes_when": "一方明透、一方仅藏且没有桥",
            "conditional_when": "藏到藏存在局部候选但作用条件未闭合",
            "required_fact_keys": ("source_manifestation", "target_manifestation"),
            "forbidden_shortcuts": ("同为藏干即自动可达",),
            "counterexample": "明财不能因官杀藏于另一支就自动形成直达",
        },
        "COMPETING_PATH_RESOLUTION": {
            "question": "食伤生财、财被夺或印化官杀等竞争路径是否已比较？",
            "supports_when": "竞争路径弱、被阻或已有清晰主次",
            "opposes_when": "另一条路径更闭合并改变财官主导方向",
            "conditional_when": "多条路径并存但主次仍需整盘裁决",
            "required_fact_keys": ("structure_candidates", "exact_role_paths"),
            "forbidden_shortcuts": ("只看财官成员而跳过竞争路径",),
            "counterexample": "财居中也可能承接食伤，不必然以生官杀为主",
        },
    },
    PRESSURE_RESOURCE_SELF: {
        "PRESSURE_SOURCE_AVAILABILITY": {
            "question": "精确到正官或七杀后，压力来源是否真实并具备全盘角色？",
            "supports_when": "官杀来源定位且确实构成整盘压力",
            "opposes_when": "来源不存在或只是孤立成员",
            "conditional_when": "来源仅藏或与其他压力路径竞争",
            "required_fact_keys": ("exact_source", "source_manifestation"),
            "forbidden_shortcuts": ("见官杀即认定压力已成立",),
            "counterexample": "孤立七杀不等于已经成为全盘压力源",
        },
        "RESOURCE_BRIDGE_REACHABILITY": {
            "question": "正印或偏印能否从精确官杀来源承接，并继续指向日主？",
            "supports_when": "官杀、印与日主坐标有连续准入路径",
            "opposes_when": "印不存在、被坏或与官杀和日主均无通道",
            "conditional_when": "印仅藏或只闭合其中一段",
            "required_fact_keys": ("exact_role_paths", "resource"),
            "forbidden_shortcuts": ("官杀与印都存在即认定杀印相生",),
            "counterexample": "官杀生印与印生日主两段必须分别成立",
        },
        "SELF_TARGET_CAPACITY": {
            "question": "日主能否真实承接印桥，而不是只在名义上成为终点？",
            "supports_when": "印桥可达且日主有承接与转化条件",
            "opposes_when": "印桥被阻或日主无法承接连续压力",
            "conditional_when": "根、印比与泄耗比较尚未闭合",
            "required_fact_keys": ("season", "root", "peer", "resource"),
            "forbidden_shortcuts": ("见印即认定日主受生",),
            "counterexample": "印星存在不等于压力已经转为日主可用支持",
        },
        "COMPETING_PATH_RESOLUTION": {
            "question": "财生官杀、食伤制官杀或财坏印等竞争路径是否已比较？",
            "supports_when": "竞争路径弱、被阻或不改变官印主轴",
            "opposes_when": "另一条路径更闭合并破坏官印连续性",
            "conditional_when": "竞争路径并存但主次未闭合",
            "required_fact_keys": ("structure_candidates", "exact_role_paths"),
            "forbidden_shortcuts": ("只凭官印成员数量决定主轴",),
            "counterexample": "食伤直制官杀时不能同时无条件认定官印相生",
        },
        "SOURCE_BRIDGE_SAME_LAYER": {
            "question": "官杀来源与印桥是否同层或有已准入连接？",
            "supports_when": "精确官杀与精确印同层或有准入桥",
            "opposes_when": "两者显藏分离且没有桥",
            "conditional_when": "同支藏层候选存在但整体作用未定",
            "required_fact_keys": ("exact_role_paths",),
            "forbidden_shortcuts": ("官印各自存在即视为第一段闭合",),
            "counterexample": "明官与异支藏印不能自动写成官生印",
        },
        "BRIDGE_TARGET_SAME_LAYER": {
            "question": "印桥与日主之间是否具备可到达、可承接的第二段？",
            "supports_when": "精确印坐标可达日主且承接条件成立",
            "opposes_when": "印与日主分层断开或印已被破坏",
            "conditional_when": "生扶方向存在但有效度尚待整盘比较",
            "required_fact_keys": ("exact_role_paths",),
            "forbidden_shortcuts": ("印生日主的五行关系即等于本盘做功",),
            "counterexample": "理论相生不能替代本盘第二段坐标与承载审计",
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
    WEALTH_TO_PRESSURE: (
        ("正财", "正官", "DIRECT_WEALTH_TO_PROPER_OFFICIAL", "正财生正官候选"),
        ("正财", "七杀", "DIRECT_WEALTH_TO_SEVEN_KILLING", "正财生七杀候选"),
        ("偏财", "正官", "INDIRECT_WEALTH_TO_PROPER_OFFICIAL", "偏财生正官候选"),
        ("偏财", "七杀", "INDIRECT_WEALTH_TO_SEVEN_KILLING", "偏财生七杀候选"),
    ),
}

_ROLE_TRIPLES = {
    PRESSURE_RESOURCE_SELF: (
        (
            "正官",
            "正印",
            "日主",
            "PROPER_OFFICIAL_TO_DIRECT_RESOURCE_TO_SELF",
            "正官生正印生日主候选",
        ),
        (
            "正官",
            "偏印",
            "日主",
            "PROPER_OFFICIAL_TO_INDIRECT_RESOURCE_TO_SELF",
            "正官生偏印生日主候选",
        ),
        (
            "七杀",
            "正印",
            "日主",
            "SEVEN_KILLING_TO_DIRECT_RESOURCE_TO_SELF",
            "七杀生正印生日主候选",
        ),
        (
            "七杀",
            "偏印",
            "日主",
            "SEVEN_KILLING_TO_INDIRECT_RESOURCE_TO_SELF",
            "七杀生偏印生日主候选",
        ),
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
                    f"SUPPORTS:{guidance[check_code]['supports_when']}；"
                    f"OPPOSES:{guidance[check_code]['opposes_when']}"
                ),
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
    for source, bridge, target, path_ref, label in _ROLE_TRIPLES.get(pattern_ref, ()):
        source_coordinates = tuple(ten_god_occurrences.get(source, ()))
        bridge_coordinates = tuple(ten_god_occurrences.get(bridge, ()))
        target_coordinates = tuple(ten_god_occurrences.get(target, ()))
        if not source_coordinates or not bridge_coordinates or not target_coordinates:
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
                "bridge": {
                    "ten_god": bridge,
                    "coordinates": bridge_coordinates,
                    "manifestation": _manifestation(bridge_coordinates),
                },
                "target": {
                    "ten_god": target,
                    "coordinates": target_coordinates,
                    "manifestation": _manifestation(target_coordinates),
                },
                "identity_rule": "两段必须分别裁决，禁止以官印相生组名替代坐标与可达性",
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
    root_candidate_assessments: Sequence[Mapping[str, object]],
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
        "root_candidate_assessments": tuple(dict(item) for item in root_candidate_assessments),
        "minimum_anti_follow_scope": {
            "gate_version": MINGLI_EFFECTIVE_ROOT_METHOD_VERSION,
            "rule": (
                "日主同字位于某支第一藏干，且该支没有准入的原局六冲／六合成员关系时，"
                "只在排除直接从势的最低范围内将该坐标裁为有效根"
            ),
            "does_not_prove": (
                "DAY_MASTER_STRONG",
                "USEFUL_ROOT",
                "MECHANISM_AVAILABLE",
                "AUSPICIOUSNESS",
            ),
            "other_candidates": "仍须按月令、位置与全盘制化逐项裁决",
        },
        "candidate_states": (
            {
                "state": "NON_WEAK_OUTSIDE_SCOPE",
                "requires": (
                    "整盘已裁为 STRONG、BALANCED 或 SPECIALIZED_TENDENCY；"
                    "本子审计只记录其退出身弱／从势二分"
                ),
            },
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
        "ordered_exit_decision_table": (
            {
                "priority": 1,
                "when": "day_master_state IN STRONG,BALANCED,SPECIALIZED_TENDENCY",
                "classification": "NON_WEAK_OUTSIDE_SCOPE",
            },
            {
                "priority": 2,
                "when": (
                    "day_master_state=WEAK AND (effective_root_status=PRESENT OR "
                    "rooted_visible_support_status=PRESENT)"
                ),
                "classification": "ORDINARY_WEAK",
            },
            {
                "priority": 3,
                "when": (
                    "effective_root_status=UNRESOLVED OR "
                    "rooted_visible_support_status=UNRESOLVED OR "
                    "dominant_chain_status!=CLOSED"
                ),
                "classification": "UNRESOLVED",
            },
            {
                "priority": 4,
                "when": (
                    "root_and_rooted_support=ABSENT AND dominant_chain_status=CLOSED "
                    "AND competition_kinds NONEMPTY"
                ),
                "classification": "FALSE_FOLLOW_COMPETITION",
            },
            {
                "priority": 5,
                "when": (
                    "root_and_rooted_support=ABSENT AND dominant_chain_status=CLOSED "
                    "AND competition_kinds EMPTY"
                ),
                "day_master_state": "FOLLOWING_TENDENCY",
                "classification": "FOLLOW_TREND",
            },
        ),
        "required_typed_output": (
            "effective_root_status",
            "effective_root_coordinates",
            "rooted_visible_support_status",
            "dominant_chain_status",
            "competition_kinds",
            "classification",
        ),
        "typed_field_rules": {
            "support_selection_root_status": ("只表示 root_candidates 是否非空，不是有效根裁决"),
            "rooted_visible_support_status": (
                "visible_peers 为空时必须为 ABSENT；这不改变 effective_root_status"
            ),
            "unresolved_is_complete_output": (
                "方法未闭合时返回完整 regime_decision 并使用 UNRESOLVED，不得省略字段"
            ),
            "coordinates_follow_status": (
                "effective_root_status 不是 PRESENT 时 effective_root_coordinates 必须为空"
            ),
            "classification_follows_status": (
                "WEAK 且 effective_root_status=PRESENT 时 classification=ORDINARY_WEAK；"
                "STRONG、BALANCED 或 SPECIALIZED_TENDENCY 时固定为 NON_WEAK_OUTSIDE_SCOPE；"
                "没有有效根与有根明透支持时禁止 ORDINARY_WEAK"
            ),
            "competition_is_exhaustive": (
                "hidden_resources 非空必须列 HIDDEN_RESOURCE；visible_peers 非空且未形成"
                "有根明透支持时必须列 VISIBLE_PEER"
            ),
            "minimum_evidence": "regime evidence_ids 必须包含 day_master_support evidence_id",
        },
        "hard_rules": (
            "有有效根或透而有根的印比时不得判从",
            "minimum_anti_follow_gate 为 PRESENT 的坐标不得写成余气或继续保留有效根未决",
            "存在根候选但没有明确失效证据时不得裁为 ABSENT，只能 PRESENT 或 UNRESOLVED",
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
    day_master_state: str = "WEAK",
    effective_root: bool,
    rooted_visible_support: bool,
    visible_peer_competition: bool,
    hidden_resource_competition: bool,
    dominant_chain_closed: bool,
) -> str:
    """Synthetic-only invariant evaluator; never writes a professional verdict."""

    if day_master_state in {"STRONG", "BALANCED", "SPECIALIZED_TENDENCY"}:
        return "NON_WEAK_OUTSIDE_SCOPE"
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
