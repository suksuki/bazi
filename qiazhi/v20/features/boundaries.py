from __future__ import annotations

DEFAULT_BOUNDARY = "只解释结构和证据，不输出固定吉凶。"

BOUNDARIES = {
    "strength": "只解释日主承载力证据，不直接硬判身强或身弱。",
    "useful_god": "只解释候选路径和缺口证据，不直接定死喜忌。",
    "ten_god": "只解释十神来源层和关系元信息，不凭单一十神推出人生结果。",
    "element": "只解释五行分布与结构偏向，不直接推出健康或吉凶结果。",
    "branch": "只解释可见地支关系及其层级，不直接推出好坏结果。",
    "time": "时间层只作为触发或背景，不输出无证据支撑的具体时间点。",
    "wealth": "只解释财星材料和结构路径，不直接判断收益结果。",
    "pattern": "格局只作为审查索引，不直接断定成败高低。",
}


def boundary_for(domain: str) -> str:
    return BOUNDARIES.get(domain, DEFAULT_BOUNDARY)
