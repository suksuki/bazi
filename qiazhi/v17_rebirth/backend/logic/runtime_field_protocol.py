from __future__ import annotations

from typing import Dict, List, Tuple


CORE_GRAPH_POSITION_WEIGHTS: Dict[str, float] = {
    "year": 0.72,
    "month": 1.00,
    "day": 0.92,
    "hour": 0.85,
    "luck": 0.88,
    "flow": 0.56,
}

CORE_GRAPH_DISTANCE_WEIGHTS: Dict[int, float] = {
    0: 1.00,
    1: 0.78,
    2: 0.52,
    3: 0.31,
}

# L0 根气/透干动态层的运流作用域权重，不与 Core 图边权等同。
ROOT_SCOPE_WEIGHTS: Dict[str, float] = {
    "year": 0.48,
    "month": 1.0,
    "day": 0.68,
    "hour": 0.82,
    "luck": 0.92,
    "flow": 0.42,
}

# Work Path 的来源域系数，描述“这条路径来自哪里”。
WORK_ORIGIN_SCOPE_FACTORS: Dict[str, float] = {
    "luck": 1.16,
    "flow": 0.84,
    "runtime": 1.08,
    "mixed": 1.08,
    "natal": 1.0,
    "natal_basis": 1.0,
    "natal_projection": 1.0,
}

RUNTIME_FIELD_ANCHOR_PRIORITY: Tuple[str, ...] = ("day", "month", "hour", "year")
RUNTIME_FIELD_ANCHOR_PRIORITY_LABEL = "日柱/日支 > 月柱/月令 > 时柱 > 年柱"

_DYNAMIC_EDGE_RULES: Dict[Tuple[str, str], Dict[str, object]] = {
    ("luck", "day"): {
        "weight": 1.00,
        "mode": "background_core",
        "priority": 1,
        "runtime_role": "background_field",
        "summary": "大运背景场优先贴近日柱/日支。",
    },
    ("day", "luck"): {
        "weight": 1.00,
        "mode": "background_core",
        "priority": 1,
        "runtime_role": "background_field",
        "summary": "日柱对大运场的响应最直接。",
    },
    ("luck", "month"): {
        "weight": 0.96,
        "mode": "background_field",
        "priority": 2,
        "runtime_role": "background_field",
        "summary": "大运作为背景场，会强力改写月令环境。",
    },
    ("month", "luck"): {
        "weight": 0.96,
        "mode": "background_field",
        "priority": 2,
        "runtime_role": "background_field",
        "summary": "月令是大运背景场的第一环境受体。",
    },
    ("luck", "hour"): {
        "weight": 0.80,
        "mode": "background_periphery",
        "priority": 3,
        "runtime_role": "background_field",
        "summary": "大运对时柱生效，但弱于日月两端。",
    },
    ("hour", "luck"): {
        "weight": 0.80,
        "mode": "background_periphery",
        "priority": 3,
        "runtime_role": "background_field",
        "summary": "时柱会受大运背景场调制，但不属核心锚点。",
    },
    ("luck", "year"): {
        "weight": 0.74,
        "mode": "background_periphery",
        "priority": 4,
        "runtime_role": "background_field",
        "summary": "大运可牵动年柱，但已处外围。",
    },
    ("year", "luck"): {
        "weight": 0.74,
        "mode": "background_periphery",
        "priority": 4,
        "runtime_role": "background_field",
        "summary": "年柱响应大运背景场，优先级最低。",
    },
    ("flow", "day"): {
        "weight": 0.90,
        "mode": "yearly_trigger",
        "priority": 1,
        "runtime_role": "yearly_perturbation",
        "summary": "流年以年度扰动形式优先触发日柱/日支。",
    },
    ("day", "flow"): {
        "weight": 0.90,
        "mode": "yearly_trigger",
        "priority": 1,
        "runtime_role": "yearly_perturbation",
        "summary": "日柱对流年扰动最敏感。",
    },
    ("flow", "month"): {
        "weight": 0.84,
        "mode": "seasonal_trigger",
        "priority": 2,
        "runtime_role": "yearly_perturbation",
        "summary": "流年也会打月令，但通常作为季节性触发。",
    },
    ("month", "flow"): {
        "weight": 0.84,
        "mode": "seasonal_trigger",
        "priority": 2,
        "runtime_role": "yearly_perturbation",
        "summary": "月令可承接流年扰动，但弱于日柱直击。",
    },
    ("flow", "hour"): {
        "weight": 0.72,
        "mode": "peripheral_trigger",
        "priority": 3,
        "runtime_role": "yearly_perturbation",
        "summary": "流年对时柱属于外围触发。",
    },
    ("hour", "flow"): {
        "weight": 0.72,
        "mode": "peripheral_trigger",
        "priority": 3,
        "runtime_role": "yearly_perturbation",
        "summary": "时柱承接流年事件性较强，但权重次于日月。",
    },
    ("flow", "year"): {
        "weight": 0.64,
        "mode": "peripheral_trigger",
        "priority": 4,
        "runtime_role": "yearly_perturbation",
        "summary": "流年与年柱耦合最外围。",
    },
    ("year", "flow"): {
        "weight": 0.64,
        "mode": "peripheral_trigger",
        "priority": 4,
        "runtime_role": "yearly_perturbation",
        "summary": "年柱对流年扰动的承接优先级最低。",
    },
    ("luck", "flow"): {
        "weight": 0.88,
        "mode": "runtime_cascade",
        "priority": 1,
        "runtime_role": "runtime_cascade",
        "summary": "流年在大运场中触发，不宜线性表述成谁先打谁。",
    },
    ("flow", "luck"): {
        "weight": 0.88,
        "mode": "runtime_cascade",
        "priority": 1,
        "runtime_role": "runtime_cascade",
        "summary": "运流之间先形成级联，再共同作用原局。",
    },
}

DEFAULT_DYNAMIC_EDGE_WEIGHTS: Dict[Tuple[str, str], float] = {
    pair: float(rule["weight"]) for pair, rule in _DYNAMIC_EDGE_RULES.items()
}

DEFAULT_DYNAMIC_EDGE_MODES: Dict[Tuple[str, str], str] = {
    pair: str(rule["mode"]) for pair, rule in _DYNAMIC_EDGE_RULES.items()
}

DYNAMIC_MODE_DESCRIPTIONS: Dict[str, str] = {
    "background_core": "大运背景场直贴核心锚点（日柱/日支）。",
    "background_field": "大运背景场强力改写月令与主环境。",
    "background_periphery": "大运背景场仍有效，但已进入外围柱位。",
    "yearly_trigger": "流年以年度扰动直击核心事件位。",
    "seasonal_trigger": "流年对月令/环境位的季节性触发。",
    "peripheral_trigger": "流年对外围柱位的次级事件触发。",
    "runtime_cascade": "流年在大运场中级联，不按线性先后理解。",
}


def dynamic_edge_rule(source: str, target: str) -> Dict[str, object]:
    return dict(_DYNAMIC_EDGE_RULES.get((str(source), str(target)), {}))


def dynamic_edge_metadata(source: str, target: str) -> Dict[str, object]:
    rule = dynamic_edge_rule(source, target)
    if not rule:
        return {"coupling_mode": "dynamic_trigger"}
    mode = str(rule.get("mode") or "dynamic_trigger")
    return {
        "coupling_mode": mode,
        "coupling_priority": int(rule.get("priority") or 9),
        "runtime_role": str(rule.get("runtime_role") or "dynamic_trigger"),
        "mode_description": str(DYNAMIC_MODE_DESCRIPTIONS.get(mode) or ""),
        "mode_summary": str(rule.get("summary") or ""),
    }


def runtime_field_prompt_lines() -> List[str]:
    return [
        "运流解释合同：大运更像背景场，流年更像年度扰动；不是线性先后，而是流年在大运场中触发原局关键节点。",
        f"运流解释合同：当前 Core 图优先耦合顺序为{RUNTIME_FIELD_ANCHOR_PRIORITY_LABEL}；大运权重大于流年。",
        "运流解释合同：dynamic_trigger 细分为 background_core/background_field/background_periphery、yearly_trigger/seasonal_trigger/peripheral_trigger，以及 runtime_cascade。",
    ]


def runtime_field_protocol_payload() -> Dict[str, object]:
    return {
        "anchor_priority": list(RUNTIME_FIELD_ANCHOR_PRIORITY),
        "anchor_priority_label": RUNTIME_FIELD_ANCHOR_PRIORITY_LABEL,
        "core_graph_position_weights": dict(CORE_GRAPH_POSITION_WEIGHTS),
        "core_graph_distance_weights": dict(CORE_GRAPH_DISTANCE_WEIGHTS),
        "root_scope_weights": dict(ROOT_SCOPE_WEIGHTS),
        "work_origin_scope_factors": dict(WORK_ORIGIN_SCOPE_FACTORS),
        "dynamic_edge_weights": {
            f"{source}->{target}": float(rule["weight"])
            for (source, target), rule in _DYNAMIC_EDGE_RULES.items()
        },
        "dynamic_edge_modes": {
            f"{source}->{target}": str(rule["mode"])
            for (source, target), rule in _DYNAMIC_EDGE_RULES.items()
        },
        "dynamic_edge_priorities": {
            f"{source}->{target}": int(rule["priority"])
            for (source, target), rule in _DYNAMIC_EDGE_RULES.items()
        },
        "dynamic_mode_descriptions": dict(DYNAMIC_MODE_DESCRIPTIONS),
    }
