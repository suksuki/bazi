from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.testing.parameter_candidate_runner import build_parameter_experiments_from_report
from v17_rebirth.testing.synthetic_tuning_bridge import build_parameter_candidate_plan


SYNTHETIC_BATCH_LAB_VERSION = "v17.synthetic_batch_lab.v1"


@dataclass(frozen=True)
class SyntheticBatchCase:
    case_id: str
    description: str
    four_pillars: dict[str, str]
    luck_pillar: str = ""
    flow_pillar: str = ""
    gender: str = "male"
    tags: tuple[str, ...] = ()
    expected_relation_families: tuple[str, ...] = ()
    expected_dynamic_families: tuple[str, ...] = ()
    forbidden_relation_families: tuple[str, ...] = ()
    forbidden_dynamic_families: tuple[str, ...] = ()


@dataclass(frozen=True)
class BatchAnomaly:
    case_id: str
    anomaly_type: str
    message: str
    parameter_family: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "anomaly_type": self.anomaly_type,
            "message": self.message,
            "parameter_family": self.parameter_family,
        }


@dataclass(frozen=True)
class SyntheticBatchRun:
    case: SyntheticBatchCase
    passed: bool
    top: tuple[str, ...]
    total: float
    relation_families: tuple[str, ...]
    dynamic_families: tuple[str, ...]
    anomalies: tuple[BatchAnomaly, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case.case_id,
            "passed": bool(self.passed),
            "top": list(self.top),
            "total": round(float(self.total or 0.0), 4),
            "relation_families": list(self.relation_families),
            "dynamic_families": list(self.dynamic_families),
            "anomalies": [item.to_dict() for item in self.anomalies],
        }


BATCH_SANHE_MONTH_VISIBLE = SyntheticBatchCase(
    case_id="batch.relation.sanhe.metal.month_visible",
    description="巳酉丑三合金，月干辛透，批量校验三合可见支撑。",
    four_pillars={"year": "丁巳", "month": "辛丑", "day": "甲辰", "hour": "丙酉"},
    tags=("batch", "relation", "sanhe", "visible"),
    expected_relation_families=("sanhe",),
)

BATCH_SANHE_NO_VISIBLE = SyntheticBatchCase(
    case_id="batch.relation.sanhe.metal.no_visible",
    description="巳酉丑三合金，无月/日干金透，批量校验基础成局。",
    four_pillars={"year": "丁巳", "month": "乙丑", "day": "甲辰", "hour": "丙酉"},
    tags=("batch", "relation", "sanhe", "no_visible"),
    expected_relation_families=("sanhe",),
)

BATCH_SANHUI_WOOD_FULL = SyntheticBatchCase(
    case_id="batch.relation.sanhui.wood.full",
    description="寅卯辰三会木齐全，批量校验三会完整 gate。",
    four_pillars={"year": "甲寅", "month": "乙卯", "day": "丙辰", "hour": "丁巳"},
    tags=("batch", "relation", "sanhui"),
    expected_relation_families=("sanhui",),
)

BATCH_INCOMPLETE_SANHUI_GUARD = SyntheticBatchCase(
    case_id="batch.relation.sanhui.fire.incomplete_guard",
    description="巳巳丑酉 + 子 + 午 不得误判巳午未三会火局。",
    four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
    luck_pillar="庚子",
    flow_pillar="丙午",
    tags=("batch", "relation", "sanhui_guard"),
    expected_relation_families=("sanhe",),
    forbidden_relation_families=("sanhui",),
    forbidden_dynamic_families=("sanhui",),
)

BATCH_LIUHE_NATAL = SyntheticBatchCase(
    case_id="batch.runtime.liuhe.natal",
    description="子丑六合落原局，批量校验原局绑定。",
    four_pillars={"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁辰"},
    tags=("batch", "runtime", "liuhe", "natal"),
    expected_relation_families=("liuhe",),
    expected_dynamic_families=("liuhe",),
)

BATCH_LIUHE_LUCK = SyntheticBatchCase(
    case_id="batch.runtime.liuhe.luck",
    description="子丑六合由大运接入，批量校验背景场。",
    four_pillars={"year": "甲子", "month": "丙寅", "day": "丁卯", "hour": "戊辰"},
    luck_pillar="己丑",
    tags=("batch", "runtime", "liuhe", "luck"),
    expected_relation_families=("liuhe",),
    expected_dynamic_families=("liuhe",),
)

BATCH_LIUHE_FLOW = SyntheticBatchCase(
    case_id="batch.runtime.liuhe.flow",
    description="子丑六合由流年接入，批量校验年度扰动。",
    four_pillars={"year": "甲子", "month": "丙寅", "day": "丁卯", "hour": "戊辰"},
    flow_pillar="己丑",
    tags=("batch", "runtime", "liuhe", "flow"),
    expected_relation_families=("liuhe",),
    expected_dynamic_families=("liuhe",),
)

BATCH_CHONG_BASELINE = SyntheticBatchCase(
    case_id="batch.dynamics.chong.ziwu",
    description="子午冲，批量校验冲的能量轴和稳定性轴。",
    four_pillars={"year": "甲子", "month": "乙午", "day": "丙寅", "hour": "丁卯"},
    tags=("batch", "dynamics", "chong"),
    expected_dynamic_families=("chong",),
)

BATCH_HAI_BASELINE = SyntheticBatchCase(
    case_id="batch.dynamics.hai.ziweihai",
    description="子未害，批量校验暗损轴。",
    four_pillars={"year": "甲子", "month": "乙未", "day": "丙寅", "hour": "丁卯"},
    tags=("batch", "dynamics", "hai"),
    expected_dynamic_families=("hai",),
)

BATCH_CLIMATE_HOT_DRY = SyntheticBatchCase(
    case_id="batch.climate.hot_dry",
    description="巳午未火土燥热，批量校验 climate field 不缺失且数值有限。",
    four_pillars={"year": "丙午", "month": "丁巳", "day": "乙未", "hour": "丙午"},
    luck_pillar="己未",
    flow_pillar="丁巳",
    tags=("batch", "climate", "hot_dry"),
)

BATCH_CLIMATE_COLD_WET = SyntheticBatchCase(
    case_id="batch.climate.cold_wet",
    description="亥子丑水寒湿，批量校验 climate field 不缺失且数值有限。",
    four_pillars={"year": "壬子", "month": "癸亥", "day": "乙丑", "hour": "癸亥"},
    luck_pillar="壬子",
    flow_pillar="癸亥",
    tags=("batch", "climate", "cold_wet"),
)


DEFAULT_SYNTHETIC_BATCH_CASES: tuple[SyntheticBatchCase, ...] = (
    BATCH_SANHE_MONTH_VISIBLE,
    BATCH_SANHE_NO_VISIBLE,
    BATCH_SANHUI_WOOD_FULL,
    BATCH_INCOMPLETE_SANHUI_GUARD,
    BATCH_LIUHE_NATAL,
    BATCH_LIUHE_LUCK,
    BATCH_LIUHE_FLOW,
    BATCH_CHONG_BASELINE,
    BATCH_HAI_BASELINE,
    BATCH_CLIMATE_HOT_DRY,
    BATCH_CLIMATE_COLD_WET,
)


def run_batch_case(case: SyntheticBatchCase) -> SyntheticBatchRun:
    anomalies: list[BatchAnomaly] = []
    try:
        scores, top, total, meta = calc_deity_scores(
            four_pillars=case.four_pillars,
            luck_pillar=case.luck_pillar,
            flow_pillar=case.flow_pillar,
            gender=case.gender,
        )
    except Exception as exc:
        anomaly = BatchAnomaly(
            case_id=case.case_id,
            anomaly_type="runtime_crash",
            message=str(exc),
            parameter_family="runtime.stability",
        )
        return SyntheticBatchRun(
            case=case,
            passed=False,
            top=(),
            total=0.0,
            relation_families=(),
            dynamic_families=(),
            anomalies=(anomaly,),
        )

    scores = dict(scores or {})
    top = tuple(str(item) for item in list(top or []))
    total = float(total or 0.0)
    meta = dict(meta or {})
    relation_families = _families_from_rows(meta.get("relation_formation_summary"))
    dynamic_families = _families_from_rows(meta.get("relation_dynamics_summary"))

    anomalies.extend(_basic_invariant_anomalies(case, scores=scores, top=top, total=total, meta=meta))
    anomalies.extend(
        _family_anomalies(
            case,
            relation_families=relation_families,
            dynamic_families=dynamic_families,
        )
    )
    anomalies.extend(_summary_range_anomalies(case, meta=meta))

    return SyntheticBatchRun(
        case=case,
        passed=not anomalies,
        top=top,
        total=total,
        relation_families=relation_families,
        dynamic_families=dynamic_families,
        anomalies=tuple(anomalies),
    )


def build_synthetic_batch_report(
    cases: Iterable[SyntheticBatchCase] = DEFAULT_SYNTHETIC_BATCH_CASES,
) -> dict[str, Any]:
    runs = [run_batch_case(case) for case in cases]
    family_counts: Counter[str] = Counter()
    for run in runs:
        for anomaly in run.anomalies:
            family_counts[anomaly.parameter_family] += 1
    candidate_plan = build_parameter_candidate_plan(dict(family_counts))
    experiment_report = {
        "protocol": "v17.synthetic_tuning_bridge.v1",
        "audits": [
            {"case_id": run.case.case_id}
            for run in runs
            if not run.passed
        ],
        "parameter_candidate_plan": candidate_plan,
    }
    return {
        "protocol": SYNTHETIC_BATCH_LAB_VERSION,
        "case_count": len(runs),
        "passed_count": sum(1 for run in runs if run.passed),
        "failed_count": sum(1 for run in runs if not run.passed),
        "runs": [run.to_dict() for run in runs],
        "anomalies": [
            anomaly.to_dict()
            for run in runs
            for anomaly in run.anomalies
        ],
        "parameter_family_counts": dict(family_counts),
        "parameter_candidate_plan": candidate_plan,
        "parameter_experiments": build_parameter_experiments_from_report(experiment_report),
        "learning_loop_state": (
            "batch_green_no_parameter_adjustment"
            if not family_counts
            else "batch_anomalies_require_manual_parameter_review"
        ),
    }


def _families_from_rows(rows: Any) -> tuple[str, ...]:
    out = {
        str(row.get("family_key") or "").strip()
        for row in (rows or [])
        if isinstance(row, dict) and str(row.get("family_key") or "").strip()
    }
    return tuple(sorted(out))


def _basic_invariant_anomalies(
    case: SyntheticBatchCase,
    *,
    scores: dict[str, Any],
    top: tuple[str, ...],
    total: float,
    meta: dict[str, Any],
) -> list[BatchAnomaly]:
    anomalies: list[BatchAnomaly] = []
    if not top:
        anomalies.append(
            BatchAnomaly(case.case_id, "top_empty", "No top ten-god axis emitted.", "ten_gods.calibration")
        )
    if not math.isfinite(total) or total <= 0.0:
        anomalies.append(
            BatchAnomaly(case.case_id, "invalid_total", f"Invalid total: {total}", "ten_gods.calibration")
        )
    for god, value in scores.items():
        try:
            score = float(value or 0.0)
        except (TypeError, ValueError):
            score = math.nan
        if not math.isfinite(score) or score < 0.0:
            anomalies.append(
                BatchAnomaly(
                    case.case_id,
                    "invalid_score",
                    f"{god} has invalid score {value}.",
                    "ten_gods.calibration",
                )
            )
    climate = meta.get("climate_field")
    if not isinstance(climate, dict):
        anomalies.append(
            BatchAnomaly(case.case_id, "missing_climate_field", "Missing climate_field.", "climate_field")
        )
    else:
        for key in ("thermal_index", "moisture_index", "climate_tension"):
            try:
                value = float(climate.get(key, 0.0) or 0.0)
            except (TypeError, ValueError):
                value = math.nan
            if not math.isfinite(value):
                anomalies.append(
                    BatchAnomaly(
                        case.case_id,
                        "invalid_climate_value",
                        f"{key} is not finite.",
                        "climate_field",
                    )
                )
    return anomalies


def _family_anomalies(
    case: SyntheticBatchCase,
    *,
    relation_families: tuple[str, ...],
    dynamic_families: tuple[str, ...],
) -> list[BatchAnomaly]:
    anomalies: list[BatchAnomaly] = []
    relation_set = set(relation_families)
    dynamic_set = set(dynamic_families)
    for family in case.expected_relation_families:
        if family not in relation_set:
            anomalies.append(
                BatchAnomaly(
                    case.case_id,
                    "missing_expected_relation",
                    f"Expected relation family {family} missing.",
                    f"relation_formation.{family}",
                )
            )
    for family in case.expected_dynamic_families:
        if family not in dynamic_set:
            anomalies.append(
                BatchAnomaly(
                    case.case_id,
                    "missing_expected_dynamic",
                    f"Expected dynamic family {family} missing.",
                    f"relation_dynamics.{family}",
                )
            )
    for family in case.forbidden_relation_families:
        if family in relation_set:
            anomalies.append(
                BatchAnomaly(
                    case.case_id,
                    "forbidden_relation_present",
                    f"Forbidden relation family {family} present.",
                    f"relation_gate.{family}",
                )
            )
    for family in case.forbidden_dynamic_families:
        if family in dynamic_set:
            anomalies.append(
                BatchAnomaly(
                    case.case_id,
                    "forbidden_dynamic_present",
                    f"Forbidden dynamic family {family} present.",
                    f"relation_gate.{family}",
                )
            )
    return anomalies


def _summary_range_anomalies(case: SyntheticBatchCase, *, meta: dict[str, Any]) -> list[BatchAnomaly]:
    anomalies: list[BatchAnomaly] = []
    for row in meta.get("relation_formation_summary") or []:
        if not isinstance(row, dict):
            continue
        family = str(row.get("family_key") or "unknown").strip() or "unknown"
        for key in ("formation_ratio",):
            if key not in row:
                continue
            value = _safe_float(row.get(key))
            if value is None or value < 0.0 or value > 1.2:
                anomalies.append(
                    BatchAnomaly(
                        case.case_id,
                        "formation_ratio_out_of_range",
                        f"{family}.{key} out of range: {row.get(key)}",
                        f"relation_formation.{family}",
                    )
                )
        if "formation_percent" in row:
            value = _safe_float(row.get("formation_percent"))
            if value is None or value < 0.0 or value > 120.0:
                anomalies.append(
                    BatchAnomaly(
                        case.case_id,
                        "formation_percent_out_of_range",
                        f"{family}.formation_percent out of range: {row.get('formation_percent')}",
                        f"relation_formation.{family}",
                    )
                )
    for row in meta.get("relation_dynamics_summary") or []:
        if not isinstance(row, dict):
            continue
        family = str(row.get("family_key") or "unknown").strip() or "unknown"
        for key in ("energy_effect_ratio", "stability_delta_ratio", "free_energy_lock_ratio"):
            if key not in row:
                continue
            value = _safe_float(row.get(key))
            if value is None or abs(value) > 3.0:
                anomalies.append(
                    BatchAnomaly(
                        case.case_id,
                        "relation_dynamics_out_of_range",
                        f"{family}.{key} out of range: {row.get(key)}",
                        f"relation_dynamics.{family}",
                    )
                )
    return anomalies


def _safe_float(value: Any) -> float | None:
    try:
        result = float(value or 0.0)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None

