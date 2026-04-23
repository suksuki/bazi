from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.logic.core_engine.god_ring_resolver_core import resolve_god_ring_core
from v17_rebirth.backend.logic.L2_structure_patterns import risk_matrix
from v17_rebirth.backend.logic.L2_structure_patterns.pattern_specializations import (
    CaiPoYinPatternPlugin,
    ShiShenZhiShaPatternPlugin,
    ShangGuanPeiYinPatternPlugin,
)
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
    expected_dynamic_families: tuple[str, ...] = ()


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


@dataclass(frozen=True)
class SyntheticPatternCase:
    case_id: str
    layer: str
    description: str
    plugin_cls: type
    tensor: dict[str, Any]
    expected_pattern: str
    expected_target_god: str
    expected_use_bias: tuple[str, ...] = ()
    expected_taboo_bias: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class SyntheticPatternRun:
    case: SyntheticPatternCase
    facts: list[V17Fact]
    authority: dict[str, Any]
    resolved: dict[str, Any]


@dataclass(frozen=True)
class SyntheticCoreCase:
    case_id: str
    layer: str
    description: str
    four_pillars: dict[str, str]
    deity_scores: dict[str, float]
    luck_pillar: str = ""
    flow_pillar: str = ""
    decision_rows: tuple[dict[str, Any], ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class SyntheticCoreRun:
    case: SyntheticCoreCase
    result: dict[str, Any]


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


def relation_dynamics_rows(run: SyntheticRun, family_key: str | None = None) -> list[dict[str, Any]]:
    rows = [
        row
        for row in (run.meta.get("relation_dynamics_summary") or [])
        if isinstance(row, dict)
    ]
    if family_key is None:
        return rows
    return [row for row in rows if str(row.get("family_key") or "") == family_key]


def relation_dynamics_row(run: SyntheticRun, family_key: str) -> dict[str, Any] | None:
    rows = relation_dynamics_rows(run, family_key)
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


def _decision_rows_from_facts(*, plugin_id: str, case_id: str, facts: list[V17Fact]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, fact in enumerate(facts):
        meta = dict(fact.meta or {}) if isinstance(fact.meta, dict) else {}
        bias = dict(meta.get("god_ring_bias") or {}) if isinstance(meta.get("god_ring_bias"), dict) else {}
        if not bias:
            continue
        impact: dict[str, Any] = {
            "target_god": str(meta.get("target_god") or fact.target_god or "").strip(),
            "god_ring_bias": bias,
        }
        work_evidence = meta.get("work_evidence")
        if isinstance(work_evidence, dict) and work_evidence:
            impact["work_evidence"] = deepcopy(work_evidence)
        narrative_hint = str(meta.get("pattern_candidate") or fact.text or "").strip()
        if narrative_hint:
            impact["narrative_hint"] = narrative_hint
        rows.append(
            {
                "id": f"{case_id}:{idx}",
                "plugin_id": plugin_id,
                "label": str(meta.get("pattern_candidate") or fact.text or "").strip(),
                "title": str(fact.text or "").strip(),
                "target_god": str(meta.get("target_god") or fact.target_god or "").strip(),
                "physical_impact": impact,
            }
        )
    return rows


def run_pattern_case(case: SyntheticPatternCase) -> SyntheticPatternRun:
    plugin = case.plugin_cls()
    tensor = deepcopy(case.tensor)
    facts = list(plugin.collect_v17_facts(tensor))
    routed_tensor = deepcopy(case.tensor)
    routed_tensor["pending_decisions"] = _decision_rows_from_facts(
        plugin_id=str(plugin.plugin_id),
        case_id=case.case_id,
        facts=facts,
    )
    routed_tensor.setdefault("auto_resolutions", [])
    authority_facts = list(ZiPingGodRingResolverPlugin().collect_v17_facts(routed_tensor))
    authority = authority_facts[0].meta.get("god_ring_authority") if authority_facts and isinstance(authority_facts[0].meta, dict) else {}
    resolved = resolve_god_ring_authority(
        raw_physics={"meta": {"god_ring_authority": dict(authority or {})}},
        ranked_pairs=_ranked_pairs_from_tensor(routed_tensor),
    )
    return SyntheticPatternRun(
        case=case,
        facts=facts,
        authority=dict(authority or {}),
        resolved=dict(resolved or {}),
    )


def pattern_case_fact(run: SyntheticPatternRun) -> V17Fact | None:
    for fact in run.facts:
        if str((fact.meta or {}).get("pattern_candidate") or "") == run.case.expected_pattern:
            return fact
    return run.facts[0] if run.facts else None


def run_core_case(case: SyntheticCoreCase) -> SyntheticCoreRun:
    result = resolve_god_ring_core(
        four_pillars=dict(case.four_pillars),
        deity_scores={str(key): float(val or 0.0) for key, val in dict(case.deity_scores).items()},
        luck_pillar=case.luck_pillar,
        flow_pillar=case.flow_pillar,
        decision_rows=[dict(row) for row in case.decision_rows],
    )
    return SyntheticCoreRun(case=case, result=dict(result or {}))


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

L1_LIUHE_BASELINE = SyntheticCase(
    case_id="l1.relation.liuhe.baseline",
    layer="L1",
    description="子丑六合土势，验证六合基础倍率与弱成局口径。",
    four_pillars={"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
    tags=("relation", "liuhe", "baseline"),
    expected_relation_families=("liuhe",),
)

L1_BANHE_SHENGWANG = SyntheticCase(
    case_id="l1.relation.banhe.shengwang",
    layer="L1",
    description="巳酉生旺半合金势，验证生旺半合高于墓旺半合的基础倍率。",
    four_pillars={"year": "丁巳", "month": "乙未", "day": "甲辰", "hour": "丙酉"},
    tags=("relation", "banhe", "shengwang"),
    expected_relation_families=("banhe_shengwang",),
)

L1_BANHE_MUWANG = SyntheticCase(
    case_id="l1.relation.banhe.muwang",
    layer="L1",
    description="丑酉墓旺半合金势，验证墓旺半合倍率与受扰成局状态。",
    four_pillars={"year": "丁酉", "month": "乙丑", "day": "甲辰", "hour": "丙午"},
    tags=("relation", "banhe", "muwang"),
    expected_relation_families=("banhe_muwang",),
)

L1_GONGHE_BASELINE = SyntheticCase(
    case_id="l1.relation.gonghe.baseline",
    layer="L1",
    description="丑巳拱合金势，验证拱合低于半合/六合的基础倍率。",
    four_pillars={"year": "丁巳", "month": "乙丑", "day": "甲辰", "hour": "丙未"},
    tags=("relation", "gonghe", "baseline"),
    expected_relation_families=("gonghe",),
)

L1_ANHE_BASELINE = SyntheticCase(
    case_id="l1.relation.anhe.baseline",
    layer="L1",
    description="子未暗合基线盘，验证暗合更偏绑定/蛰伏，稳定性上升但自由能锁定更明显。",
    four_pillars={"year": "甲寅", "month": "乙未", "day": "丙子", "hour": "丁午"},
    tags=("relation", "anhe", "baseline"),
    expected_relation_families=("anhe",),
    expected_dynamic_families=("anhe",),
)

L1_STEM_FUSION_RUNTIME = SyntheticCase(
    case_id="l1.relation.stem_fusion.runtime",
    layer="L1",
    description="乙庚五合在月干-大运命中，验证 stem_fusion 进入 relation_dynamics 与 visible bonuses，而非 relation_formation_summary 主目录。",
    four_pillars={"year": "辛酉", "month": "乙酉", "day": "乙丑", "hour": "丁卯"},
    luck_pillar="庚辰",
    tags=("relation", "stem_fusion", "runtime"),
    expected_relation_families=("banhe_muwang", "liuhe"),
    expected_dynamic_families=("stem_fusion_transform",),
)

L1_CHONG_BASELINE = SyntheticCase(
    case_id="l1.relation.chong.baseline",
    layer="L1",
    description="子午冲基线盘，验证冲走激发轴、稳定性显著下降。",
    four_pillars={"year": "甲子", "month": "乙午", "day": "丙寅", "hour": "丁卯"},
    tags=("relation", "chong", "baseline"),
    expected_dynamic_families=("chong",),
)

L1_HAI_BASELINE = SyntheticCase(
    case_id="l1.relation.hai.baseline",
    layer="L1",
    description="子未害基线盘，验证害走暗损轴、稳定性缓降。",
    four_pillars={"year": "甲子", "month": "乙未", "day": "丙寅", "hour": "丁卯"},
    tags=("relation", "hai", "baseline"),
    expected_dynamic_families=("hai",),
)

L1_PO_BASELINE = SyntheticCase(
    case_id="l1.relation.po.baseline",
    layer="L1",
    description="子酉破基线盘，验证破走解构轴、稳定性断裂快于害。",
    four_pillars={"year": "甲子", "month": "乙酉", "day": "丙寅", "hour": "丁卯"},
    tags=("relation", "po", "baseline"),
    expected_dynamic_families=("po",),
)

L1_KE_BASELINE = SyntheticCase(
    case_id="l1.relation.ke.baseline",
    layer="L1",
    description="卯丑/寅丑相克基线盘，验证克走压制转移轴并伴随稳定性下降。",
    four_pillars={"year": "甲卯", "month": "乙丑", "day": "丙寅", "hour": "丁巳"},
    tags=("relation", "ke", "baseline"),
    expected_dynamic_families=("ke",),
)

L1_XING_BASELINE = SyntheticCase(
    case_id="l1.relation.xing.baseline",
    layer="L1",
    description="子卯刑基线盘，验证刑走内耗轴，总能量未必掉光，但有效输出与稳定性一起打折。",
    four_pillars={"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁巳"},
    tags=("relation", "xing", "baseline"),
    expected_relation_families=("anhe",),
    expected_dynamic_families=("xing",),
)

RUNTIME_LIUHE_LUCK_BACKGROUND = SyntheticCase(
    case_id="runtime.relation.liuhe.luck_background",
    layer="MASTER",
    description="同一子丑六合放在大运背景场，验证背景场强于流年扰动。",
    four_pillars={"year": "甲子", "month": "丙寅", "day": "丁卯", "hour": "戊辰"},
    luck_pillar="己丑",
    tags=("runtime_field", "liuhe", "luck_background"),
    expected_relation_families=("liuhe",),
    expected_dynamic_families=("liuhe",),
)

RUNTIME_LIUHE_NATAL_BASELINE = SyntheticCase(
    case_id="runtime.relation.liuhe.natal_baseline",
    layer="MASTER",
    description="同一子丑六合直接落在原局，验证原局结构型绑定高于大运背景场与流年扰动。",
    four_pillars={"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁辰"},
    tags=("runtime_field", "liuhe", "natal_baseline"),
    expected_relation_families=("liuhe",),
    expected_dynamic_families=("liuhe",),
)

RUNTIME_LIUHE_FLOW_TRIGGER = SyntheticCase(
    case_id="runtime.relation.liuhe.flow_trigger",
    layer="MASTER",
    description="同一子丑六合放在流年扰动，验证弱于大运背景场。",
    four_pillars={"year": "甲子", "month": "丙寅", "day": "丁卯", "hour": "戊辰"},
    flow_pillar="己丑",
    tags=("runtime_field", "liuhe", "flow_trigger"),
    expected_relation_families=("liuhe",),
    expected_dynamic_families=("liuhe",),
)

RUNTIME_HAI_LUCK_BACKGROUND = SyntheticCase(
    case_id="runtime.relation.hai.luck_background",
    layer="MASTER",
    description="同一子未害放在大运背景场，验证背景场的暗损强于流年扰动。",
    four_pillars={"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁卯"},
    luck_pillar="戊未",
    tags=("runtime_field", "hai", "luck_background"),
    expected_dynamic_families=("hai",),
)

RUNTIME_HAI_NATAL_BASELINE = SyntheticCase(
    case_id="runtime.relation.hai.natal_baseline",
    layer="MASTER",
    description="同一子未害直接落在原局，验证原局慢性暗损高于大运背景场与流年扰动。",
    four_pillars={"year": "甲子", "month": "乙未", "day": "丙寅", "hour": "丁卯"},
    tags=("runtime_field", "hai", "natal_baseline"),
    expected_dynamic_families=("hai",),
)

RUNTIME_HAI_FLOW_TRIGGER = SyntheticCase(
    case_id="runtime.relation.hai.flow_trigger",
    layer="MASTER",
    description="同一子未害放在流年扰动，验证暗损低于大运背景场。",
    four_pillars={"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁卯"},
    flow_pillar="戊未",
    tags=("runtime_field", "hai", "flow_trigger"),
    expected_dynamic_families=("hai",),
)

RUNTIME_SANHUI_RESONANCE = SyntheticCase(
    case_id="runtime.relation.sanhui.resonance",
    layer="MASTER",
    description="寅卯辰三会在大运与流年双重入局，验证背景场与扰动共振时的高成局高稳定输出。",
    four_pillars={"year": "甲寅", "month": "乙卯", "day": "丙辰", "hour": "丁巳"},
    luck_pillar="戊卯",
    flow_pillar="己寅",
    tags=("runtime_field", "sanhui", "resonance"),
    expected_relation_families=("sanhui",),
    expected_dynamic_families=("sanhui",),
)

RUNTIME_BANHE_INTERRUPTION = SyntheticCase(
    case_id="runtime.relation.banhe.interruption",
    layer="MASTER",
    description="卯未墓旺半合遇酉冲与子酉破，验证运流中断时成局仍可见但稳定性被破坏。",
    four_pillars={"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁辰"},
    luck_pillar="戊未",
    flow_pillar="己酉",
    tags=("runtime_field", "banhe", "interruption"),
    expected_relation_families=("banhe_muwang", "liuhe"),
    expected_dynamic_families=("chong", "po"),
)

MASTER_BRANCH_CLUSTER = SyntheticCase(
    case_id="master.branch_cluster.fire_vs_water",
    layer="MASTER",
    description="用户校盘样盘：寅午戌火局与子辰半合水并存，用于观察合化、重支与冲扰共存。",
    four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
    luck_pillar="庚戌",
    flow_pillar="丙午",
    tags=("master", "relation", "user_review"),
    expected_relation_families=("sanhe", "banhe_muwang"),
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

L2_RISK_OWL_FOOD = SyntheticRiskCase(
    case_id="l2.judgement.owl_food",
    layer="L2",
    description="偏印压食神的风险样盘，要求吐出枭印夺食候选，并把食神保护、偏印压到忌侧。",
    tensor={
        "four_pillars": {"year": "辛酉", "month": "壬辰", "day": "丙午", "hour": "甲寅"},
        "ten_gods_absolute": {"偏印": 16.0, "食神": 10.0},
        "meta": {"interaction_v2": {}},
    },
    expected_patterns=("枭印夺食",),
    tags=("judgement", "risk_matrix", "owl_food"),
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

L2_AUTHORITY_BLIND_THEME_PARALLEL = SyntheticAuthorityCase(
    case_id="l2.authority.blind_theme_parallel",
    layer="L2",
    description="盲派主题作为并行专题推用推忌，但不覆盖子平 authority，用于校验 blind bias_only 桥接。",
    tensor={
        "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        "ten_gods_base_l0": {"伤官": 58.0, "食神": 44.0, "正财": 22.0, "偏财": 16.0, "正官": 18.0, "偏印": 11.0},
        "ten_gods_runtime": {"伤官": 58.0, "食神": 44.0, "正财": 22.0, "偏财": 16.0, "正官": 18.0, "偏印": 11.0},
        "energy_meta": {
            "month_command_god": "伤官",
            "season_power": {"month_branch": "巳"},
            "ten_gods_decomposition_l0": {
                "伤官": {"manifest": 18.0, "root": 8.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 26.0},
                "食神": {"manifest": 12.0, "root": 7.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 19.0},
                "正财": {"manifest": 8.0, "root": 4.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 12.0},
                "偏财": {"manifest": 6.0, "root": 3.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 9.0},
                "正官": {"manifest": 7.0, "root": 4.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 11.0},
                "偏印": {"manifest": 5.0, "root": 3.0, "momentum": 0.0, "momentum_month_order": 0.0, "momentum_stage": 0.0, "momentum_stage_lu": 0.0, "momentum_stage_blade": 0.0, "momentum_stage_general": 0.0, "momentum_structure": 0.0, "momentum_auxiliary": 0.0, "momentum_other": 0.0, "hidden": 0.0, "total": 8.0},
            },
        },
        "meta": {
            "blind_theme": {
                "contract": "v17.blind.theme.v1",
                "primary_route": "食伤生财",
                "body_mode": "disturbed_body",
                "confidence": 0.84,
                "use_candidates": ["食伤", "正财"],
                "taboo_candidates": ["强印", "正官"],
                "house_roles": {"食伤": "outside", "正财": "inside", "偏财": "inside", "偏印": "bridge"},
                "runtime_switches": ["己亥运中食伤生财抢权"],
                "authority_bridge_mode": "bias_only",
            }
        },
        "pending_decisions": [],
        "auto_resolutions": [],
    },
    tags=("authority", "blind_theme", "ziping"),
)

CORE_AUTHORITY_OFFICER_CONTEST = SyntheticCoreCase(
    case_id="core.authority.officer_contest",
    layer="MASTER",
    description="伤官与正官高争衡，验证 authority 能把高能低稳的官杀压到忌侧，并把食伤推到用侧。",
    four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
    luck_pillar="辛丑",
    flow_pillar="己未",
    deity_scores={"伤官": 84.0, "正官": 74.0, "食神": 32.0},
    decision_rows=(
        {
            "id": "row_officer_hurt",
            "target_god": "正官",
            "source": "l2.risk.risk_matrix",
            "plugin_id": "l2.risk.risk_matrix",
            "source_label": "伤官见官",
            "label": "伤官见官：高争衡",
            "physical_impact": {
                "target_god": "正官",
                "impact_ratio": 0.0,
                "match_ratio": 0.86,
                "work_evidence": {
                    "relation_family": "risk_officer_hurt_contest",
                    "target_god": "正官",
                    "members": ["伤官", "正官"],
                    "targets": ["正官"],
                    "counterpart_gods": ["伤官"],
                    "effect_type": "disrupt",
                    "layer": "cross_layer",
                    "origin_scope": "natal",
                    "condition_state": "contested",
                    "impact_ratio": 0.0,
                    "match_ratio": 0.86,
                    "path_strength": 0.42,
                },
            },
        },
        {
            "id": "row_shang_gang",
            "target_god": "伤官",
            "source": "l1.physics.op_branch_muku",
            "plugin_id": "l1.physics.op_branch_muku",
            "source_label": "三合生伤官",
            "label": "三合透支",
            "physical_impact": {
                "target_god": "伤官",
                "impact_ratio": 0.36,
                "match_ratio": 0.77,
                "work_evidence": {
                    "relation_family": "sanhe",
                    "target_god": "伤官",
                    "members": ["乙", "丙", "丁"],
                    "targets": ["伤官"],
                    "counterpart_gods": ["正官"],
                    "effect_type": "benefit",
                    "layer": "branch",
                    "origin_scope": "luck",
                    "condition_state": "manifested",
                    "impact_ratio": 0.36,
                    "match_ratio": 0.77,
                    "path_strength": 0.48,
                },
            },
        },
    ),
    tags=("core", "authority", "contest"),
)

CORE_AUTHORITY_POSITIVE_PATH = SyntheticCoreCase(
    case_id="core.authority.positive_path",
    layer="MASTER",
    description="正向五合路径胜出，验证稳定正向路径能压过高波动伤官线。",
    four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
    luck_pillar="庚子",
    flow_pillar="丙午",
    deity_scores={"伤官": 74.0, "食神": 53.0, "正官": 15.0, "七杀": 9.0},
    decision_rows=(
        {
            "id": "row_guan",
            "target_god": "正官",
            "source": "l1.physics.op_stem_fusion",
            "plugin_id": "l1.physics.op_stem_fusion",
            "source_label": "天干五合",
            "label": "乙庚合",
            "physical_impact": {
                "target_god": "正官",
                "impact_ratio": 0.32,
                "match_ratio": 0.84,
                "work_evidence": {
                    "relation_family": "stem_fusion",
                    "target_god": "正官",
                    "targets": ["正官"],
                    "members": ["庚", "乙"],
                    "effect_type": "transform",
                    "layer": "stem",
                    "origin_scope": "luck",
                    "condition_state": "formed",
                    "impact_ratio": 0.32,
                    "match_ratio": 0.84,
                    "path_strength": 0.41,
                },
            },
        },
        {
            "id": "row_shang",
            "target_god": "伤官",
            "source": "l1.physics.op_branch_liuchong",
            "plugin_id": "l1.physics.op_branch_liuchong",
            "source_label": "六冲耗伤官",
            "label": "巳午冲伤官",
            "physical_impact": {
                "target_god": "伤官",
                "impact_ratio": -0.28,
                "match_ratio": 0.77,
                "work_evidence": {
                    "relation_family": "liu_chong",
                    "target_god": "伤官",
                    "targets": ["伤官"],
                    "members": ["巳", "午"],
                    "effect_type": "harm",
                    "layer": "branch",
                    "origin_scope": "flow",
                    "condition_state": "supported",
                    "impact_ratio": -0.28,
                    "match_ratio": 0.77,
                    "path_strength": 0.33,
                },
            },
        },
    ),
    tags=("core", "authority", "positive_path"),
)

CORE_AUTHORITY_BRIDGE_PRESENT = SyntheticCoreCase(
    case_id="core.authority.bridge_present",
    layer="MASTER",
    description="官杀强压且盘内已有印桥，验证通关链会自然进入 use 候选并保留路径预览。",
    four_pillars={"year": "甲寅", "month": "丁巳", "day": "戊辰", "hour": "乙卯"},
    deity_scores={"七杀": 42.0, "正官": 34.0, "正印": 20.0, "偏印": 16.0, "比肩": 28.0, "劫财": 14.0},
    tags=("core", "authority", "tongguan"),
)

CORE_AUTHORITY_BRIDGE_EXTERNAL = SyntheticCoreCase(
    case_id="core.authority.bridge_external",
    layer="MASTER",
    description="盘内无印而官杀压身，验证外来通关神会被投影为 authority 候选与外部桥接路径。",
    four_pillars={"year": "甲寅", "month": "乙卯", "day": "戊辰", "hour": "甲寅"},
    deity_scores={"七杀": 44.0, "正官": 36.0, "比肩": 24.0, "劫财": 8.0, "正印": 0.0, "偏印": 0.0},
    tags=("core", "authority", "tongguan_external"),
)

L2_PATTERN_SHISHEN_ZHISHA = SyntheticPatternCase(
    case_id="l2.pattern.shishen_zhisha",
    layer="L2",
    description="专题插件样盘：食神制杀应把食神推入用神线，并把七杀压入忌线。",
    plugin_cls=ShiShenZhiShaPatternPlugin,
    tensor={
        "four_pillars": {"year": "甲申", "month": "庚申", "day": "壬午", "hour": "甲辰"},
        "ten_gods_runtime": {"七杀": 26.0, "食神": 22.0, "偏印": 3.0},
    },
    expected_pattern="食神制杀",
    expected_target_god="七杀",
    expected_use_bias=("食神",),
    expected_taboo_bias=("七杀",),
    tags=("pattern", "specialization", "shishen_zhisha"),
)

L2_PATTERN_SHANGGUAN_PEIYIN = SyntheticPatternCase(
    case_id="l2.pattern.shangguan_peiyin",
    layer="L2",
    description="专题插件样盘：伤官配印应把伤官与印线一起推入用神候选。",
    plugin_cls=ShangGuanPeiYinPatternPlugin,
    tensor={
        "four_pillars": {"year": "甲子", "month": "丙午", "day": "乙酉", "hour": "壬辰"},
        "ten_gods_runtime": {"伤官": 28.0, "正印": 18.0, "偏印": 3.0},
    },
    expected_pattern="伤官配印",
    expected_target_god="伤官",
    expected_use_bias=("伤官", "正印"),
    expected_taboo_bias=(),
    tags=("pattern", "specialization", "shangguan_peiyin"),
)

L2_PATTERN_CAIPOYIN = SyntheticPatternCase(
    case_id="l2.pattern.caipoyin",
    layer="L2",
    description="专题插件样盘：财破印应保护印线并把财线压到忌神侧。",
    plugin_cls=CaiPoYinPatternPlugin,
    tensor={
        "four_pillars": {"year": "甲子", "month": "辛酉", "day": "甲午", "hour": "己丑"},
        "ten_gods_runtime": {"正印": 18.0, "偏印": 6.0, "正财": 23.0, "偏财": 9.0},
    },
    expected_pattern="财破印",
    expected_target_god="正印",
    expected_use_bias=("正印",),
    expected_taboo_bias=("正财", "偏财"),
    tags=("pattern", "specialization", "caipoyin"),
)


SYNTHETIC_CASES: tuple[SyntheticCase, ...] = (
    L0_FLOATING_PEER,
    L0_ROOTED_PEER,
    L1_SANHE_NO_VISIBLE,
    L1_SANHE_DAY_VISIBLE,
    L1_SANHE_MONTH_VISIBLE,
    L1_SANHUI_MONTH_VISIBLE,
    L1_LIUHE_BASELINE,
    L1_BANHE_SHENGWANG,
    L1_BANHE_MUWANG,
    L1_GONGHE_BASELINE,
    L1_ANHE_BASELINE,
    L1_STEM_FUSION_RUNTIME,
    L1_CHONG_BASELINE,
    L1_HAI_BASELINE,
    L1_PO_BASELINE,
    L1_KE_BASELINE,
    L1_XING_BASELINE,
    RUNTIME_LIUHE_NATAL_BASELINE,
    RUNTIME_LIUHE_LUCK_BACKGROUND,
    RUNTIME_LIUHE_FLOW_TRIGGER,
    RUNTIME_HAI_NATAL_BASELINE,
    RUNTIME_HAI_LUCK_BACKGROUND,
    RUNTIME_HAI_FLOW_TRIGGER,
    RUNTIME_SANHUI_RESONANCE,
    RUNTIME_BANHE_INTERRUPTION,
    MASTER_BRANCH_CLUSTER,
)

SYNTHETIC_RISK_CASES: tuple[SyntheticRiskCase, ...] = (
    L2_RISK_OFFICER_JUDGEMENT,
    L2_RISK_OWL_FOOD,
)

SYNTHETIC_AUTHORITY_CASES: tuple[SyntheticAuthorityCase, ...] = (
    L2_AUTHORITY_BIAS_REROUTE,
    L2_AUTHORITY_TONGGUAN_PRESENT,
    L2_AUTHORITY_BLIND_THEME_PARALLEL,
)

SYNTHETIC_PATTERN_CASES: tuple[SyntheticPatternCase, ...] = (
    L2_PATTERN_SHISHEN_ZHISHA,
    L2_PATTERN_SHANGGUAN_PEIYIN,
    L2_PATTERN_CAIPOYIN,
)

SYNTHETIC_CORE_CASES: tuple[SyntheticCoreCase, ...] = (
    CORE_AUTHORITY_OFFICER_CONTEST,
    CORE_AUTHORITY_POSITIVE_PATH,
    CORE_AUTHORITY_BRIDGE_PRESENT,
    CORE_AUTHORITY_BRIDGE_EXTERNAL,
)


def case_ids() -> tuple[str, ...]:
    return tuple(case.case_id for case in SYNTHETIC_CASES)


def risk_case_ids() -> tuple[str, ...]:
    return tuple(case.case_id for case in SYNTHETIC_RISK_CASES)


def authority_case_ids() -> tuple[str, ...]:
    return tuple(case.case_id for case in SYNTHETIC_AUTHORITY_CASES)


def pattern_case_ids() -> tuple[str, ...]:
    return tuple(case.case_id for case in SYNTHETIC_PATTERN_CASES)


def core_case_ids() -> tuple[str, ...]:
    return tuple(case.case_id for case in SYNTHETIC_CORE_CASES)
