from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor


@dataclass(frozen=True)
class PractitionerBenchmarkCase:
    case_id: str
    description: str
    four_pillars: dict[str, str]
    luck_pillar: str = "—"
    flow_pillar: str = "—"
    gender: str = "male"
    audit_focus: tuple[str, ...] = ()
    expected_relation_families: tuple[str, ...] = ()
    expected_dynamic_families: tuple[str, ...] = ()
    forbidden_relation_families: tuple[str, ...] = ()
    expected_top_contains: tuple[str, ...] = ()
    expected_leader: str | None = None
    reviewer_note: str = ""


@dataclass(frozen=True)
class PractitionerBenchmarkRun:
    case: PractitionerBenchmarkCase
    scores: dict[str, float]
    top: list[str]
    total: float
    meta: dict[str, Any]


def run_practitioner_case(case: PractitionerBenchmarkCase) -> PractitionerBenchmarkRun:
    scores, top, total, meta = calc_deity_scores(
        four_pillars=case.four_pillars,
        luck_pillar=case.luck_pillar,
        flow_pillar=case.flow_pillar,
        gender=case.gender,
    )
    pt = {
        "four_pillars": dict(case.four_pillars),
        "luck_pillar": case.luck_pillar,
        "flow_pillar": case.flow_pillar,
        "gender": case.gender,
        "ten_gods_base_l0": dict(scores),
        "ten_gods_runtime": dict(scores),
        "meta": dict(meta or {}),
        "_is_current_focus": True,
    }
    hydrate_v17_physics_tensor(pt)
    return PractitionerBenchmarkRun(
        case=case,
        scores={str(key): float(val or 0.0) for key, val in dict(scores or {}).items()},
        top=[str(item) for item in list(top or [])],
        total=float(total or 0.0),
        meta=dict((pt.get("meta") or {}) if isinstance(pt.get("meta"), dict) else {}),
    )


def practitioner_relation_families(run: PractitionerBenchmarkRun) -> set[str]:
    return {
        str(row.get("family_key") or "")
        for row in (run.meta.get("relation_formation_summary") or [])
        if isinstance(row, dict) and str(row.get("family_key") or "").strip()
    }


def practitioner_dynamic_families(run: PractitionerBenchmarkRun) -> set[str]:
    return {
        str(row.get("family_key") or "")
        for row in (run.meta.get("relation_dynamics_summary") or [])
        if isinstance(row, dict) and str(row.get("family_key") or "").strip()
    }


def practitioner_relation_row(
    run: PractitionerBenchmarkRun,
    family_key: str,
) -> dict[str, Any] | None:
    for row in (run.meta.get("relation_formation_summary") or []):
        if isinstance(row, dict) and str(row.get("family_key") or "") == family_key:
            return row
    return None


def practitioner_dynamic_row(
    run: PractitionerBenchmarkRun,
    family_key: str,
) -> dict[str, Any] | None:
    for row in (run.meta.get("relation_dynamics_summary") or []):
        if isinstance(row, dict) and str(row.get("family_key") or "") == family_key:
            return row
    return None


def practitioner_top_scores(
    run: PractitionerBenchmarkRun,
    limit: int = 6,
) -> list[tuple[str, float]]:
    rows = sorted(run.scores.items(), key=lambda item: item[1], reverse=True)
    return [(str(god), float(score or 0.0)) for god, score in rows[:limit]]


def practitioner_relation_snapshot(
    run: PractitionerBenchmarkRun,
) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in (run.meta.get("relation_formation_summary") or [])
        if isinstance(row, dict)
    ]


def practitioner_dynamic_snapshot(
    run: PractitionerBenchmarkRun,
) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in (run.meta.get("relation_dynamics_summary") or [])
        if isinstance(row, dict)
    ]


PRACTITIONER_METAL_MIX_GENGZI_BINGWU = PractitionerBenchmarkCase(
    case_id="real.audit.metal_mix_gengzi_bingwu",
    description="丁巳/乙巳/乙丑/乙酉，庚子大运、丙午流年。校验巳酉丑三合金、子丑六合与多重冲扰并存时的官杀轴与误判三会问题。",
    four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
    luck_pillar="庚子",
    flow_pillar="丙午",
    audit_focus=("巳酉丑三合金", "子丑六合", "子巳暗合", "不得误判巳午未三会"),
    expected_relation_families=("sanhe", "liuhe", "anhe"),
    expected_dynamic_families=("sanhe", "chong", "stem_fusion_transform"),
    forbidden_relation_families=("sanhui",),
    expected_top_contains=("正官", "七杀", "伤官"),
    expected_leader="正官",
    reviewer_note="这张盘用于压住“三会误判”和“官杀轴是否被三合金真实抬起”两类回归风险。",
)


PRACTITIONER_METAL_MIX_XINCHOU_YIWEI = PractitionerBenchmarkCase(
    case_id="real.audit.metal_mix_xinchou_yiwei",
    description="丁巳/乙巳/乙丑/乙酉，辛丑大运、乙未流年。校验辛金纯透且丑支重复时，巳酉丑三合金如何把七杀推到绝对主轴。",
    four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
    luck_pillar="辛丑",
    flow_pillar="乙未",
    audit_focus=("辛金透干", "丑支重叠", "三合金满配", "七杀主轴"),
    expected_relation_families=("sanhe",),
    expected_dynamic_families=("sanhe", "chong", "xing"),
    forbidden_relation_families=("sanhui",),
    expected_top_contains=("七杀", "伤官", "正官"),
    expected_leader="七杀",
    reviewer_note="这是首批真实样盘里的‘强七杀’锚盘，适合作为官杀纯度与三合金上限的长期回归样本。",
)


PRACTITIONER_FIRE_WATER_GENGXU_BINGWU = PractitionerBenchmarkCase(
    case_id="real.audit.fire_water_gengxu_bingwu",
    description="壬寅/甲辰/丙子/甲午，庚戌大运、丙午流年。校验寅午戌三合火与子辰半合水并存时，系统能否同时保留火局与水路，不误判为三会。",
    four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
    luck_pillar="庚戌",
    flow_pillar="丙午",
    audit_focus=("寅午戌三合火", "子辰半合水", "火水并存", "不得误判三会"),
    expected_relation_families=("sanhe", "banhe_muwang"),
    expected_dynamic_families=("sanhe", "banhe_muwang", "chong"),
    forbidden_relation_families=("sanhui",),
    expected_top_contains=("劫财", "比肩", "正官"),
    reviewer_note="这张盘用于观察多路结构共存时，系统是否能同时保留火局主势与水路侧势，而不是把其中一路抹掉。",
)


PRACTITIONER_BENCHMARK_CASES: tuple[PractitionerBenchmarkCase, ...] = (
    PRACTITIONER_METAL_MIX_GENGZI_BINGWU,
    PRACTITIONER_METAL_MIX_XINCHOU_YIWEI,
    PRACTITIONER_FIRE_WATER_GENGXU_BINGWU,
)


def practitioner_case_ids() -> tuple[str, ...]:
    return tuple(case.case_id for case in PRACTITIONER_BENCHMARK_CASES)
