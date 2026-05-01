from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BaziDimension:
    dimension_key: str
    layer: str
    label: str
    purpose: str
    domains: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DIMENSIONS: tuple[BaziDimension, ...] = (
    BaziDimension(
        "dimension.foundation_capacity",
        "micro",
        "根基承载维度",
        "日主、月令、根气、扶助压力等基础承载判断。",
        ("strength",),
    ),
    BaziDimension(
        "dimension.structural_symbols",
        "micro",
        "结构符号维度",
        "十神、五行、地支互动等命局内部结构材料。",
        ("ten_god", "element", "branch"),
    ),
    BaziDimension(
        "dimension.arbitration_path",
        "decision",
        "裁决路径维度",
        "格局、用神、候选路径和需要命理师复核的判断入口。",
        ("useful_god", "pattern"),
    ),
    BaziDimension(
        "dimension.temporal_trigger",
        "time",
        "时间触发维度",
        "大运、流年、流月与原局之间的显式触发背景。",
        ("time",),
    ),
    BaziDimension(
        "dimension.applied_life_theme",
        "macro",
        "主题投影维度",
        "财富、事业、关系、健康边界等用户关心的测算主题。",
        ("wealth", "career", "relationship", "health"),
    ),
)

_DIMENSION_BY_DOMAIN = {
    domain: dimension
    for dimension in DIMENSIONS
    for domain in dimension.domains
}


def dimension_for_domain(domain: str) -> BaziDimension:
    return _DIMENSION_BY_DOMAIN.get(
        domain,
        BaziDimension(
            "dimension.unknown",
            "micro",
            "未归类命理维度",
            "尚未归入维度体系的命理材料。",
            (domain,),
        ),
    )


def dimension_payload(domain: str) -> dict[str, str]:
    dimension = dimension_for_domain(domain)
    return {
        "dimension_key": dimension.dimension_key,
        "dimension_layer": dimension.layer,
        "dimension_label": dimension.label,
    }


def bazi_dimension_manifest() -> dict[str, object]:
    return {
        "version": "v20.bazi_dimension_manifest.v1",
        "status": "ready",
        "dimensions": [dimension.to_dict() for dimension in DIMENSIONS],
        "domain_dimension_map": {
            domain: {
                "dimension_key": dimension.dimension_key,
                "dimension_layer": dimension.layer,
                "dimension_label": dimension.label,
            }
            for dimension in DIMENSIONS
            for domain in dimension.domains
        },
        "runtime_role": "shared_coordinate_system_for_knowledge_rules_portraits_questions_answers",
        "runtime_mutation": False,
        "guardrails": [
            "DIMENSIONS_CLASSIFY_BAZI_MATERIAL_NOT_VERDICTS",
            "MICRO_DIMENSIONS_FEED_MACRO_PROJECTIONS",
            "APPLIED_THEME_DIMENSIONS_REQUIRE_STRUCTURAL_EVIDENCE",
            "NO_RUNTIME_RULE_ACTIVATION",
        ],
    }
