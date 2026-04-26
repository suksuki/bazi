from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from v17_rebirth.backend.logic.L0_physics_fields.bazi_image_core import resolve_bazi_image
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import resolve_wealth_code
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import resolve_wealth_profile


SYNTHETIC_WEALTH_LAB_VERSION = "v17.synthetic_wealth_lab.v1"


@dataclass(frozen=True)
class SyntheticWealthCase:
    case_id: str
    description: str
    day_master_stem: str
    four_pillars: dict[str, str]
    ten_gods_runtime: dict[str, float]
    facts: tuple[str, ...] = ()
    luck_pillar: str = ""
    flow_pillar: str = ""
    flow_year: int | None = None
    authority: Mapping[str, Any] | None = None
    expected_primary_path_id: str = ""
    expected_source_contains: str = ""
    expected_secondary_path_ids: tuple[str, ...] = ()
    expected_vault_signal: bool | None = None
    expected_leakage_point_ids: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    parameter_family: str = "topic.wealth_code.path.calibration"
    layer: str = "L3_wealth_code"

    def to_catalog_row(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "layer": self.layer,
            "description": self.description,
            "tags": list(self.tags),
            "parameter_family": self.parameter_family,
        }


@dataclass(frozen=True)
class SyntheticWealthAnomaly:
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
class SyntheticWealthRun:
    case: SyntheticWealthCase
    passed: bool
    tensor: dict[str, Any]
    wealth_code: dict[str, Any]
    anomalies: tuple[SyntheticWealthAnomaly, ...]

    def to_dict(self) -> dict[str, Any]:
        primary = self.wealth_code.get("primary_wealth_path") if isinstance(self.wealth_code.get("primary_wealth_path"), dict) else {}
        return {
            "case_id": self.case.case_id,
            "passed": bool(self.passed),
            "primary_path_id": str(primary.get("id") or ""),
            "score": round(float(self.wealth_code.get("score") or 0.0), 4),
            "risk": round(float(self.wealth_code.get("risk") or 0.0), 4),
            "anomalies": [item.to_dict() for item in self.anomalies],
        }


WEALTH_OUTPUT_WORK_TO_MONEY_YI = SyntheticWealthCase(
    case_id="wealth.synthetic.output_work_to_money.yi",
    description="丁巳、乙巳、乙丑、乙酉，庚子运丙午年；典型食伤制杀叠食伤生财，验证财富主线必须回到做功变现。",
    day_master_stem="乙",
    four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
    luck_pillar="庚子",
    flow_pillar="丙午",
    flow_year=2026,
    ten_gods_runtime={
        "食神": 36.0,
        "伤官": 22.0,
        "正财": 30.0,
        "偏财": 20.0,
        "正官": 16.0,
        "七杀": 8.0,
        "正印": 10.0,
        "偏印": 6.0,
        "比肩": 10.0,
        "劫财": 8.0,
    },
    facts=(
        "格局候选：食伤生财，输出换财通道显性。",
        "格局候选：食伤制杀，制杀做功。",
    ),
    authority={"use_gods": ["食神", "伤官", "正财"], "taboo_gods": ["七杀"], "tongguan_gods": ["正官"], "confidence": 0.82},
    expected_primary_path_id="output_work_to_money",
    expected_source_contains="专业输出",
    expected_secondary_path_ids=("output_controls_pressure",),
    tags=("wealth", "output", "authority", "shishang_shengcai", "shishang_zhisha"),
)

WEALTH_DIRECT_CLIENT_RESOURCE = SyntheticWealthCase(
    case_id="wealth.synthetic.direct_wealth.client_resource",
    description="财星直取样本，验证明确客户、合同、现金流不被平台/画像摘要抢主路径。",
    day_master_stem="庚",
    four_pillars={"year": "甲子", "month": "乙卯", "day": "庚申", "hour": "戊辰"},
    luck_pillar="甲辰",
    flow_pillar="乙巳",
    flow_year=2025,
    ten_gods_runtime={
        "正财": 44.0,
        "偏财": 38.0,
        "食神": 10.0,
        "伤官": 8.0,
        "正官": 8.0,
        "七杀": 6.0,
        "正印": 8.0,
        "偏印": 5.0,
        "比肩": 5.0,
        "劫财": 4.0,
    },
    facts=("格局候选：财星直取，客户资源和现金流线索显性。",),
    authority={"use_gods": ["正财", "偏财"], "taboo_gods": ["劫财"], "confidence": 0.78},
    expected_primary_path_id="direct_wealth",
    expected_source_contains="长期项目",
    tags=("wealth", "direct_wealth", "client", "cashflow"),
)

WEALTH_PEER_LEAKAGE = SyntheticWealthCase(
    case_id="wealth.synthetic.peer_leakage.split",
    description="财旺见比劫样本，验证合作分账和现金流泄漏必须进入风险结构。",
    day_master_stem="庚",
    four_pillars={"year": "甲子", "month": "戊辰", "day": "庚申", "hour": "乙酉"},
    luck_pillar="辛酉",
    flow_pillar="乙卯",
    flow_year=2025,
    ten_gods_runtime={
        "偏财": 36.0,
        "正财": 32.0,
        "比肩": 30.0,
        "劫财": 28.0,
        "食神": 12.0,
        "伤官": 8.0,
        "正官": 6.0,
        "七杀": 5.0,
        "正印": 5.0,
        "偏印": 4.0,
    },
    facts=(
        "格局候选：比劫夺财，合作分账与竞争明显。",
        "墓库门态：辰为库，资金结构等待引动。",
    ),
    authority={"use_gods": ["正财", "偏财"], "taboo_gods": ["比肩", "劫财"], "confidence": 0.76},
    expected_primary_path_id="direct_wealth",
    expected_vault_signal=True,
    expected_leakage_point_ids=("peer_split",),
    expected_secondary_path_ids=("leakage_risk",),
    tags=("wealth", "leakage", "peer", "vault"),
    parameter_family="topic.wealth_code.leakage.calibration",
)

WEALTH_KNOWLEDGE_ASSET = SyntheticWealthCase(
    case_id="wealth.synthetic.knowledge_asset.caiyin",
    description="财印路径样本，验证资质、方法论、信用资产能成为财富承接，而不是被直接财星吞掉。",
    day_master_stem="甲",
    four_pillars={"year": "戊辰", "month": "癸亥", "day": "甲寅", "hour": "辛未"},
    luck_pillar="壬戌",
    flow_pillar="戊申",
    flow_year=2028,
    ten_gods_runtime={
        "正财": 30.0,
        "偏财": 22.0,
        "正印": 28.0,
        "偏印": 18.0,
        "食神": 8.0,
        "伤官": 6.0,
        "正官": 10.0,
        "七杀": 8.0,
        "比肩": 8.0,
        "劫财": 5.0,
    },
    facts=("格局候选：财印路径，财富需要资质、信用和方法论承接。",),
    authority={"use_gods": ["正财", "正印"], "taboo_gods": ["劫财"], "confidence": 0.74},
    expected_primary_path_id="wealth_seal_asset",
    expected_source_contains="平台",
    tags=("wealth", "caiyin", "knowledge_asset"),
    parameter_family="topic.wealth_code.asset.calibration",
)


SYNTHETIC_WEALTH_CASES: tuple[SyntheticWealthCase, ...] = (
    WEALTH_OUTPUT_WORK_TO_MONEY_YI,
    WEALTH_DIRECT_CLIENT_RESOURCE,
    WEALTH_PEER_LEAKAGE,
    WEALTH_KNOWLEDGE_ASSET,
)


def run_wealth_case(case: SyntheticWealthCase) -> SyntheticWealthRun:
    tensor = _tensor_for_case(case)
    meta = tensor.setdefault("meta", {})
    meta["bazi_image"] = resolve_bazi_image(tensor)["bazi_image"]
    meta["wealth_profile"] = resolve_wealth_profile(tensor)["wealth_profile"]
    wealth_code = resolve_wealth_code(tensor).get("wealth_code") or {}
    anomalies = tuple(_wealth_anomalies(case, wealth_code=wealth_code))
    return SyntheticWealthRun(
        case=case,
        passed=not anomalies,
        tensor=tensor,
        wealth_code=dict(wealth_code),
        anomalies=anomalies,
    )


def build_synthetic_wealth_report(
    cases: Iterable[SyntheticWealthCase] = SYNTHETIC_WEALTH_CASES,
) -> dict[str, Any]:
    runs = [run_wealth_case(case) for case in cases]
    family_counts: Counter[str] = Counter()
    family_cases: defaultdict[str, list[str]] = defaultdict(list)
    for run in runs:
        for anomaly in run.anomalies:
            family_counts[anomaly.parameter_family] += 1
            family_cases[anomaly.parameter_family].append(run.case.case_id)
    return {
        "protocol": SYNTHETIC_WEALTH_LAB_VERSION,
        "case_count": len(runs),
        "passed_count": sum(1 for run in runs if run.passed),
        "failed_count": sum(1 for run in runs if not run.passed),
        "runs": [run.to_dict() for run in runs],
        "parameter_family_counts": dict(family_counts),
        "learning_loop_state": (
            "ready_for_wealth_code_knowledge_or_formula_review"
            if family_counts
            else "wealth_synthetic_cases_green_collect_more_feedback"
        ),
        "parameter_candidate_plan": [
            {
                "candidate_id": f"candidate::{family}",
                "parameter_family": family,
                "issue_count": count,
                "recommended_action": "review_wealth_code_knowledge_formula_or_structured_claim_mapping",
                "safety_gate": "manual_review_required",
                "synthetic_cases": sorted(set(family_cases[family])),
            }
            for family, count in sorted(family_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def _tensor_for_case(case: SyntheticWealthCase) -> dict[str, Any]:
    tensor: dict[str, Any] = {
        "day_master_stem": case.day_master_stem,
        "four_pillars": dict(case.four_pillars),
        "luck_pillar": case.luck_pillar,
        "flow_pillar": case.flow_pillar,
        "ten_gods_runtime": dict(case.ten_gods_runtime),
        "facts": [
            {"fact": fact, "plugin": "synthetic.wealth_code.case"}
            for fact in case.facts
        ],
        "meta": {"god_ring_authority": dict(case.authority or {})},
    }
    if case.flow_year:
        tensor["flow_year"] = case.flow_year
    return tensor


def _wealth_anomalies(case: SyntheticWealthCase, *, wealth_code: Mapping[str, Any]) -> list[SyntheticWealthAnomaly]:
    anomalies: list[SyntheticWealthAnomaly] = []
    primary = wealth_code.get("primary_wealth_path") if isinstance(wealth_code.get("primary_wealth_path"), Mapping) else {}
    source = wealth_code.get("wealth_source") if isinstance(wealth_code.get("wealth_source"), Mapping) else {}
    vault = wealth_code.get("wealth_vault") if isinstance(wealth_code.get("wealth_vault"), Mapping) else {}
    secondary_ids = {
        str(row.get("id") or "")
        for row in wealth_code.get("secondary_paths") or []
        if isinstance(row, Mapping)
    }
    leakage_ids = {
        str(row.get("id") or "")
        for row in wealth_code.get("leakage_points") or []
        if isinstance(row, Mapping)
    }

    if case.expected_primary_path_id and str(primary.get("id") or "") != case.expected_primary_path_id:
        anomalies.append(
            SyntheticWealthAnomaly(
                case_id=case.case_id,
                anomaly_type="primary_path_mismatch",
                message=f"Expected primary wealth path {case.expected_primary_path_id}, got {primary.get('id') or 'none'}.",
                parameter_family=case.parameter_family,
            )
        )
    if case.expected_source_contains and case.expected_source_contains not in str(source.get("plain_source") or ""):
        anomalies.append(
            SyntheticWealthAnomaly(
                case_id=case.case_id,
                anomaly_type="source_language_mismatch",
                message=f"Expected wealth source to contain {case.expected_source_contains}.",
                parameter_family="topic.wealth_code.source_language.calibration",
            )
        )
    for expected_id in case.expected_secondary_path_ids:
        if expected_id not in secondary_ids:
            anomalies.append(
                SyntheticWealthAnomaly(
                    case_id=case.case_id,
                    anomaly_type="missing_secondary_path",
                    message=f"Expected secondary wealth path {expected_id}.",
                    parameter_family=case.parameter_family,
                )
            )
    if case.expected_vault_signal is not None and bool(vault.get("has_vault_signal")) is not bool(case.expected_vault_signal):
        anomalies.append(
            SyntheticWealthAnomaly(
                case_id=case.case_id,
                anomaly_type="vault_signal_mismatch",
                message=f"Expected vault signal {case.expected_vault_signal}, got {vault.get('has_vault_signal')}.",
                parameter_family="topic.wealth_code.vault.calibration",
            )
        )
    for expected_id in case.expected_leakage_point_ids:
        if expected_id not in leakage_ids:
            anomalies.append(
                SyntheticWealthAnomaly(
                    case_id=case.case_id,
                    anomaly_type="missing_leakage_point",
                    message=f"Expected leakage point {expected_id}.",
                    parameter_family="topic.wealth_code.leakage.calibration",
                )
            )
    if "topic.wealth_code.path.calibration" not in (wealth_code.get("learning_hooks") or []):
        anomalies.append(
            SyntheticWealthAnomaly(
                case_id=case.case_id,
                anomaly_type="missing_learning_hook",
                message="wealth_code did not expose topic.wealth_code.path.calibration.",
                parameter_family="topic.wealth_code.learning_hooks",
            )
        )
    return anomalies
