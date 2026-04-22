from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.logic.L2_structure_patterns import risk_matrix
from v17_rebirth.backend.logic.L2_structure_patterns.ziping_family import ZiPingGodRingResolverPlugin
from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.services.god_ring_authority import resolve_god_ring_authority


@dataclass(frozen=True)
class SyntheticCase:
    case_id: str
    layer: str
    description: str
    four_pillars: dict[str, str]
    luck_pillar: str = "—"
    flow_pillar: str = "—"
    gender: str = "male"
    tags: tuple[str, ...] = ()
    expected_relation_families: tuple[str, ...] = ()


@dataclass(frozen=True)
class SyntheticRun:
    case: SyntheticCase
    scores: dict[str, float]
    top: list[str]
    total: float
    meta: dict[str, Any]


@dataclass(frozen=True)
class SyntheticRiskCase:
    case_id: str
    layer: str
    description: str
    tensor: dict[str, Any]
    expected_patterns: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class SyntheticRiskRun:
    case: SyntheticRiskCase
    facts: list[V17Fact]


@dataclass(frozen=True)
class SyntheticAuthorityCase:
    case_id: str
    layer: str
    description: str
    tensor: dict[str, Any]
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class SyntheticAuthorityRun:
    case: SyntheticAuthorityCase
    facts: list[V17Fact]
    authority: dict[str, Any]
    resolved: dict[str, Any]


def run_case(case: SyntheticCase) -> SyntheticRun:
    scores, top, total, meta = calc_deity_scores(
        four_pillars=case.four_pillars,
        luck_pillar=case.luck_pillar,
        flow_pillar=case.flow_pillar,
        gender=case.gender,
    )
    return SyntheticRun(
        case=case,
        scores={str(key): float(val or 0.0) for key, val in dict(scores).items()},
        top=[str(item) for item in list(top)],
        total=float(total or 0.0),
        meta=dict(meta or {}),
    )


def score_of(run: SyntheticRun, god: str) -> float:
    return float(run.scores.get(god, 0.0) or 0.0)


def relation_rows(run: SyntheticRun, family_key: str | None = None) -> list[dict[str, Any]]:
    rows = [
        row
        for row in (run.meta.get("relation_formation_summary") or [])
        if isinstance(row, dict)
    ]
    if family_key is None:
        return rows
    return [row for row in rows if str(row.get("family_key") or "") == family_key]


def relation_row(run: SyntheticRun, family_key: str) -> dict[str, Any] | None:
    rows = relation_rows(run, family_key)
    return rows[0] if rows else None


def run_risk_case(case: SyntheticRiskCase) -> SyntheticRiskRun:
    facts = list(risk_matrix.PLUGIN.collect_v17_facts(dict(case.tensor)))
    return SyntheticRiskRun(case=case, facts=facts)


def pattern_fact(run: SyntheticRiskRun, pattern_name: str) -> V17Fact | None:
    for fact in run.facts:
        if str((fact.meta or {}).get("pattern_candidate") or "") == pattern_name:
            return fact
    return None


def _ranked_pairs_from_tensor(tensor: dict[str, Any]) -> list[tuple[str, float]]:
    raw = tensor.get("ten_gods_runtime") if isinstance(tensor.get("ten_gods_runtime"), dict) else {}
    rows = [(str(god or "").strip(), float(score or 0.0)) for god, score in raw.items() if str(god or "").strip()]
    rows.sort(key=lambda item: item[1], reverse=True)
    return rows


def run_authority_case(case: SyntheticAuthorityCase) -> SyntheticAuthorityRun:
    facts = list(ZiPingGodRingResolverPlugin().collect_v17_facts(dict(case.tensor)))
    authority = facts[0].meta.get("god_ring_authority") if facts and isinstance(facts[0].meta, dict) else {}
    resolved = resolve_god_ring_authority(
        raw_physics={"meta": {"god_ring_authority": dict(authority or {})}},
        ranked_pairs=_ranked_pairs_from_tensor(case.tensor),
    )
    return SyntheticAuthorityRun(
        case=case,
        facts=facts,
        authority=dict(authority or {}),
        resolved=dict(resolved or {}),
    )


L0_FLOATING_PEER = SyntheticCase(
    case_id="l0.static.floating_peer",
    layer="L0",
    description="月干/时干同党显化但无根，验证虚浮不应高于通根样盘。",
    four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
    luck_pillar="庚子",
    flow_pillar="丙午",
    tags=("static_basis", "peer", "floating"),
    expected_relation_families=("sanhe",),
)

L0_ROOTED_PEER = SyntheticCase(
    case_id="l0.static.rooted_peer",
    layer="L0",
    description="比肩通根且多支承载，作为 floating peer 对照盘。",
    four_pillars={"year": "丁卯", "month": "乙卯", "day": "乙未", "hour": "乙亥"},
    luck_pillar="庚子",
    flow_pillar="丙午",
    tags=("static_basis", "peer", "rooted"),
    expected_relation_families=("sanhe",),
)

L1_SANHE_NO_VISIBLE = SyntheticCase(
    case_id="l1.relation.sanhe.no_visible",
    layer="L1",
    description="巳酉丑三合金局，无月干/日干可见金透，验证基础倍率口径。",
    four_pillars={"year": "丁巳", "month": "乙丑", "day": "甲辰", "hour": "丙酉"},
    tags=("relation", "sanhe", "no_visible"),
    expected_relation_families=("sanhe",),
)

L1_SANHE_DAY_VISIBLE = SyntheticCase(
    case_id="l1.relation.sanhe.day_visible",
    layer="L1",
    description="巳酉丑三合金局，日干庚金透出，验证日干动态有效但弱于月干。",
    four_pillars={"year": "丁巳", "month": "乙丑", "day": "庚辰", "hour": "丙酉"},
    tags=("relation", "sanhe", "day_visible"),
    expected_relation_families=("sanhe",),
)

L1_SANHE_MONTH_VISIBLE = SyntheticCase(
    case_id="l1.relation.sanhe.month_visible",
    layer="L1",
    description="巳酉丑三合金局，月干辛金透出，验证三合月干满配上限。",
    four_pillars={"year": "丁巳", "month": "辛丑", "day": "甲辰", "hour": "丙酉"},
    tags=("relation", "sanhe", "month_visible"),
    expected_relation_families=("sanhe",),
)

L1_SANHUI_MONTH_VISIBLE = SyntheticCase(
    case_id="l1.relation.sanhui.month_visible",
    layer="L1",
    description="寅卯辰三会木局，月干乙木透出，验证三会月干满配上限。",
    four_pillars={"year": "甲寅", "month": "乙卯", "day": "丙辰", "hour": "丁巳"},
    tags=("relation", "sanhui", "month_visible"),
    expected_relation_families=("sanhui",),
)

MASTER_BRANCH_CLUSTER = SyntheticCase(
    case_id="master.branch_cluster.fire_vs_water",
    layer="MASTER",
    description="用户校盘样盘：寅午戌火局与子辰半合水并存，用于观察合化、重支与冲扰共存。",
    four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
    luck_pillar="庚戌",
    flow_pillar="丙午",
    tags=("master", "relation", "user_review"),
    expected_relation_families=("sanhe", "banhe_muwang", "sanhui"),
)

L2_RISK_OFFICER_JUDGEMENT = SyntheticRiskCase(
    case_id="l2.judgement.officer_exhaust_pair",
    layer="L2",
    description="伤官压官的一边倒样盘，要求同时吐出伤官见官与伤官伤尽候选，用于判定型偏置校验。",
    tensor={
        "four_pillars": {"year": "癸亥", "month": "丙午", "day": "乙丑", "hour": "甲辰"},
        "ten_gods_absolute": {"伤官": 42.0, "正官": 12.0, "七杀": 2.0},
        "meta": {"interaction_v2": {"liu_chong": [], "san_he": []}, "stem_fusion_v1": {"cases": []}},
    },
    expected_patterns=("伤官见官", "伤官伤尽"),
    tags=("judgement", "risk_matrix", "officer"),
)

L2_AUTHORITY_BIAS_REROUTE = SyntheticAuthorityCase(
    case_id="l2.authority.bias_reroute",
    layer="L2",
    description="判定型插件把伤官推入用神线，并把正官推入忌向偏置，用于校验 authority 吸收 judgement bias。",
    tensor={
        "four_pillars": {"month": "丁亥", "day": "乙丑"},
        "ten_gods_base_l0": {"伤官": 62.0, "食神": 40.0, "正官": 20.0, "比肩": 10.0},
        "ten_gods_runtime": {"伤官": 62.0, "食神": 40.0, "正官": 20.0, "比肩": 10.0},
        "energy_meta": {
            "month_command_god": "伤官",
            "season_power": {"month_branch": "亥"},
            "ten_gods_decomposition_l0": {
                "伤官": {
                    "manifest": 22.0,
                    "root": 8.0,
                    "momentum": 0.0,
                    "momentum_month_order": 0.0,
                    "momentum_stage": 0.0,
                    "momentum_stage_lu": 0.0,
                    "momentum_stage_blade": 0.0,
                    "momentum_stage_general": 0.0,
                    "momentum_structure": 0.0,
                    "momentum_auxiliary": 0.0,
                    "momentum_other": 0.0,
                    "hidden": 0.0,
                    "total": 30.0,
                },
                "正官": {
                    "manifest": 8.0,
                    "root": 5.0,
                    "momentum": 4.6,
                    "momentum_month_order": 0.0,
                    "momentum_stage": 4.6,
                    "momentum_stage_lu": 4.6,
                    "momentum_stage_blade": 0.0,
                    "momentum_stage_general": 0.0,
                    "momentum_structure": 0.0,
                    "momentum_auxiliary": 0.0,
                    "momentum_other": 0.0,
                    "hidden": 0.0,
                    "total": 17.6,
                },
                "比肩": {
                    "manifest": 6.0,
                    "root": 2.0,
                    "momentum": 3.8,
                    "momentum_month_order": 0.0,
                    "momentum_stage": 3.8,
                    "momentum_stage_lu": 0.0,
                    "momentum_stage_blade": 3.8,
                    "momentum_stage_general": 0.0,
                    "momentum_structure": 0.0,
                    "momentum_auxiliary": 0.0,
                    "momentum_other": 0.0,
                    "hidden": 0.0,
                    "total": 11.8,
                },
            },
        },
        "auto_resolutions": [
            {"id": "auto_1", "target_god": "正官", "physical_impact": {"target_god": "正官", "impact_ratio": 0.22}},
            {"id": "auto_2", "target_god": "伤官", "physical_impact": {"target_god": "伤官", "impact_ratio": -0.18}},
        ],
        "pending_decisions": [
            {
                "id": "risk_1",
                "plugin_id": "l2.risk.risk_matrix",
                "label": "伤官见官",
                "target_god": "伤官",
                "physical_impact": {
                    "god_ring_bias": {
                        "use_bias": {"伤官": 0.32},
                        "taboo_bias": {"正官": 0.26},
                        "reason": "伤官见官",
                    }
                },
            }
        ],
    },
    tags=("authority", "judgement_bias", "ziping"),
)

L2_AUTHORITY_TONGGUAN_PRESENT = SyntheticAuthorityCase(
    case_id="l2.authority.tongguan_present",
    layer="L2",
    description="官杀强压且火桥已在盘中存在，要求 authority 直接吐出通关神候选。",
    tensor={
        "four_pillars": {"year": "甲寅", "month": "丁巳", "day": "戊辰", "hour": "乙卯"},
        "luck_pillar": "",
        "flow_pillar": "",
        "ten_gods_base_l0": {"七杀": 42.0, "正官": 34.0, "正印": 20.0, "偏印": 16.0, "比肩": 28.0, "劫财": 14.0},
        "ten_gods_runtime": {"七杀": 42.0, "正官": 34.0, "正印": 20.0, "偏印": 16.0, "比肩": 28.0, "劫财": 14.0},
        "energy_meta": {
            "month_command_god": "正官",
            "ten_gods_decomposition_l0": {
                "正官": {"manifest": 8.0, "root": 6.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 14.0},
                "七杀": {"manifest": 10.0, "root": 8.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 18.0},
                "正印": {"manifest": 6.0, "root": 5.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 11.0},
                "偏印": {"manifest": 5.0, "root": 4.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 9.0},
                "比肩": {"manifest": 7.0, "root": 6.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 13.0},
                "劫财": {"manifest": 4.0, "root": 3.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 7.0},
            },
        },
        "pending_decisions": [],
        "auto_resolutions": [],
    },
    tags=("authority", "tongguan", "ziping"),
)


SYNTHETIC_CASES: tuple[SyntheticCase, ...] = (
    L0_FLOATING_PEER,
    L0_ROOTED_PEER,
    L1_SANHE_NO_VISIBLE,
    L1_SANHE_DAY_VISIBLE,
    L1_SANHE_MONTH_VISIBLE,
    L1_SANHUI_MONTH_VISIBLE,
    MASTER_BRANCH_CLUSTER,
)

SYNTHETIC_RISK_CASES: tuple[SyntheticRiskCase, ...] = (
    L2_RISK_OFFICER_JUDGEMENT,
)

SYNTHETIC_AUTHORITY_CASES: tuple[SyntheticAuthorityCase, ...] = (
    L2_AUTHORITY_BIAS_REROUTE,
    L2_AUTHORITY_TONGGUAN_PRESENT,
)


def case_ids() -> tuple[str, ...]:
    return tuple(case.case_id for case in SYNTHETIC_CASES)


def risk_case_ids() -> tuple[str, ...]:
    return tuple(case.case_id for case in SYNTHETIC_RISK_CASES)


def authority_case_ids() -> tuple[str, ...]:
    return tuple(case.case_id for case in SYNTHETIC_AUTHORITY_CASES)
