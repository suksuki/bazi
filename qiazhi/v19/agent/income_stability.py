from __future__ import annotations

from typing import Any, Dict, List

from v19.agent.structure import BRANCH_MAIN_STEM, STEM_ELEMENT, SIX_CLASHES, SIX_COMBINATIONS, THREE_HARMONIES

CONTROLS = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}
GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}
PILLAR_NAMES = ["year", "month", "day", "hour"]
RULE_VERSION = 1


def derive_income_stability(chart: Dict[str, Any]) -> Dict[str, Any]:
    pillars = dict(chart.get("pillars") or {})
    day_master = dict(chart.get("day_master") or {})
    day_element = str(day_master.get("element") or "")
    wealth_element = CONTROLS.get(day_element, "")
    touched_wealth_pillars = _find_wealth_pillars(pillars, wealth_element)
    branch_relations = _branch_relations(pillars)
    wealth_relation_counts = _count_wealth_relations(branch_relations, touched_wealth_pillars)
    clash_count = sum(1 for row in branch_relations if row.get("type") == "six_clash")
    three_harmony_count = sum(1 for row in branch_relations if row.get("type") == "three_harmony")
    strength = _self_capacity(pillars, day_element)
    wealth_presence = _wealth_presence(pillars, wealth_element)

    self_capacity = _map_self_capacity(strength["tendency"])
    wealth_presence_value = _map_wealth_presence(wealth_presence["count"])
    wealth_accessibility = _map_wealth_accessibility(wealth_presence_value, wealth_relation_counts["clash"], wealth_relation_counts["combination"])
    volatility = _map_volatility(clash_count)
    structure_binding = "present" if three_harmony_count > 0 else "none"
    income_stability = _map_income_stability(
        self_capacity=self_capacity,
        wealth_presence=wealth_presence_value,
        wealth_accessibility=wealth_accessibility,
        volatility=volatility,
        structure_binding=structure_binding,
    )

    signal_rows = [
        _signal(
            "self_capacity",
            self_capacity,
            "v19.income_stability.self_capacity",
            "map element support/pressure tendency into low/medium/high carrying capacity",
            [
                {"path": "element_balance.support_score", "value": strength["support_score"]},
                {"path": "element_balance.pressure_score", "value": strength["pressure_score"]},
                {"path": "element_balance.tendency", "value": strength["tendency"]},
            ],
            [("element_balance.support_score", strength["support_score"]), ("element_balance.pressure_score", strength["pressure_score"])],
            strength,
            _confidence_from_signal(self_capacity),
        ),
        _signal(
            "wealth_presence",
            wealth_presence_value,
            "v19.income_stability.wealth_presence",
            "count wealth-element contacts in visible pillar stem/branch metadata",
            [
                {"path": "wealth_element", "value": wealth_element},
                {"path": "wealth_presence.count", "value": wealth_presence["count"]},
                {"path": "wealth_presence.hits", "value": wealth_presence["hits"]},
            ],
            [("pillars.*.stem_element", "wealth_element"), ("pillars.*.branch_element", "wealth_element")],
            wealth_presence,
            _confidence_from_signal(wealth_presence_value),
        ),
        _signal(
            "wealth_accessibility",
            wealth_accessibility,
            "v19.income_stability.wealth_accessibility",
            "check whether branch relations touching wealth pillars are clear, bound, disrupted, or conflicted",
            [
                {"path": "touched_wealth_pillars", "value": touched_wealth_pillars},
                {"path": "wealth_relation_counts.clash", "value": wealth_relation_counts["clash"]},
                {"path": "wealth_relation_counts.combination", "value": wealth_relation_counts["combination"]},
            ],
            [("branch_relations touching wealth pillars", wealth_relation_counts)],
            wealth_relation_counts,
            _confidence_from_signal(wealth_accessibility),
        ),
        _signal(
            "volatility",
            volatility,
            "v19.income_stability.volatility",
            "map natal six-clash count into low/medium/high volatility",
            [{"path": "branch_relations[type=six_clash].count", "value": clash_count}],
            [("branch_relations[type=six_clash]", clash_count)],
            {"clash_count": clash_count},
            _confidence_from_signal(volatility),
        ),
        _signal(
            "structure_binding",
            structure_binding,
            "v19.income_stability.structure_binding",
            "detect whether three-harmony structure exists as a binding signal",
            [{"path": "branch_relations[type=three_harmony].count", "value": three_harmony_count}],
            [("branch_relations[type=three_harmony]", three_harmony_count)],
            {"three_harmony_count": three_harmony_count},
            0.82,
        ),
        _signal(
            "income_stability",
            income_stability,
            "v19.income_stability.aggregate",
            "aggregate bounded input signals into final income_stability structure signal",
            [
                {"path": "signals.self_capacity", "value": self_capacity},
                {"path": "signals.wealth_presence", "value": wealth_presence_value},
                {"path": "signals.wealth_accessibility", "value": wealth_accessibility},
                {"path": "signals.volatility", "value": volatility},
                {"path": "signals.structure_binding", "value": structure_binding},
            ],
            [("signals.*", "bounded_signal_values")],
            {},
            _confidence_from_signal(income_stability),
        ),
    ]

    return {
        "status": "ok",
        "supported_theme": "income_stability",
        "domain": "wealth",
        "is_prediction": False,
        "scope": "static_natal_structure_only",
        "version": "v19.income_stability.agent_adapter.v1",
        "touched_wealth_pillars": touched_wealth_pillars,
        "wealth_element": wealth_element,
        "signals": signal_rows,
        "rule_attribution": {
            "version": "v19.rule_attribution.v1",
            "signal_evidence": [_signal_evidence(row) for row in signal_rows],
            "feedback_mapping_path": "feedback.subject_type=income_stability -> signal -> rule_id -> inputs/condition",
            "guardrails": ["ATTRIBUTION_ONLY", "NO_AUTO_RULE_UPDATE", "ANALYST_REVIEW_REQUIRED"],
        },
        "rule_contract": {
            "allowed_output": ["rule_basis", "signal_values", "source_paths", "uncertainty"],
            "forbidden_output": ["fortune", "yearly_prediction", "good_bad_judgement", "发财/破财断语", "traditional_prediction_text"],
            "time_context_policy": "P4 time structure is context only and does not change income_stability.",
        },
        "evidence_summary": _evidence_summary(income_stability, self_capacity, wealth_presence_value, wealth_accessibility, volatility, structure_binding),
        "branch_relations": branch_relations,
        "guardrails": ["WEALTH_DOMAIN_SIGNAL_NOT_PREDICTION", "NO_FORTUNE", "NO_SCORE", "NO_TRADITIONAL_NARRATIVE"],
    }


def _signal(
    key: str,
    value: str,
    rule_id: str,
    condition: str,
    inputs: List[Dict[str, Any]],
    sources: List[tuple[str, Any]],
    metrics: Dict[str, Any],
    confidence: float,
) -> Dict[str, Any]:
    return {
        "key": key,
        "value": value,
        "rule_id": rule_id,
        "rule_version": RULE_VERSION,
        "condition": condition,
        "inputs": inputs,
        "sources": [{"path": path, "value": source_value} for path, source_value in sources],
        "metrics": metrics,
        "confidence": round(max(0.0, min(1.0, confidence)), 3),
    }


def _signal_evidence(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "signal": row.get("key"),
        "value": row.get("value"),
        "rule_id": row.get("rule_id"),
        "rule_version": row.get("rule_version"),
        "condition": row.get("condition"),
        "inputs": list(row.get("inputs") or []),
        "confidence": row.get("confidence"),
    }


def _confidence_from_signal(value: str) -> float:
    if value in {"stable", "unstable", "clear", "high", "none"}:
        return 0.86
    if value in {"medium", "mixed", "bound", "present"}:
        return 0.74
    if value in {"conflicted", "disrupted"}:
        return 0.7
    return 0.62


def _find_wealth_pillars(pillars: Dict[str, Any], wealth_element: str) -> List[str]:
    touched: List[str] = []
    for name in PILLAR_NAMES:
        pillar = dict(pillars.get(name) or {})
        if pillar.get("stem_element") == wealth_element or pillar.get("branch_element") == wealth_element:
            touched.append(name)
    return touched


def _branch_relations(pillars: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    branches = [(name, dict(pillars.get(name) or {}).get("branch")) for name in PILLAR_NAMES]
    for left_index, (left_name, left) in enumerate(branches):
        if not left:
            continue
        for right_name, right in branches[left_index + 1 :]:
            if not right:
                continue
            if _has_pair(SIX_COMBINATIONS, left, right):
                rows.append({"type": "six_combination", "branches": f"{left}{right}", "pillar_names": [left_name, right_name]})
            if _has_pair(SIX_CLASHES, left, right):
                rows.append({"type": "six_clash", "branches": f"{left}{right}", "pillar_names": [left_name, right_name]})
    present = {branch for _, branch in branches if branch}
    for harmony in THREE_HARMONIES:
        if set(harmony) <= present:
            rows.append({"type": "three_harmony", "branches": "".join(harmony), "pillar_names": [name for name, branch in branches if branch in harmony]})
    return rows


def _count_wealth_relations(relations: List[Dict[str, Any]], touched_wealth_pillars: List[str]) -> Dict[str, int]:
    touched = set(touched_wealth_pillars)
    counts = {"clash": 0, "combination": 0}
    for relation in relations:
        if not any(name in touched for name in relation.get("pillar_names") or []):
            continue
        relation_type = relation.get("type")
        if relation_type == "six_clash":
            counts["clash"] += 1
        if relation_type in {"six_combination", "three_harmony"}:
            counts["combination"] += 1
    return counts


def _wealth_presence(pillars: Dict[str, Any], wealth_element: str) -> Dict[str, Any]:
    hits: List[str] = []
    for name in PILLAR_NAMES:
        pillar = dict(pillars.get(name) or {})
        if pillar.get("stem_element") == wealth_element:
            hits.append(f"{name}.stem")
        if pillar.get("branch_element") == wealth_element:
            hits.append(f"{name}.branch")
    return {"count": len(hits), "hits": hits}


def _self_capacity(pillars: Dict[str, Any], day_element: str) -> Dict[str, Any]:
    support_element = next((source for source, target in GENERATES.items() if target == day_element), "")
    support = 0.0
    pressure = 0.0
    for name in PILLAR_NAMES:
        pillar = dict(pillars.get(name) or {})
        for element in [pillar.get("stem_element"), pillar.get("branch_element")]:
            if element == day_element:
                support += 1.0
            elif element == support_element:
                support += 0.72
            elif element in {CONTROLS.get(day_element), GENERATES.get(day_element)}:
                pressure += 0.76
            elif CONTROLS.get(element) == day_element:
                pressure += 0.86
    denominator = max(0.1, support + pressure)
    support_score = round(support / denominator, 3)
    pressure_score = round(pressure / denominator, 3)
    tendency = "balanced"
    if support_score >= pressure_score + 0.18:
        tendency = "strong"
    elif pressure_score >= support_score + 0.18:
        tendency = "weak"
    return {"support_score": support_score, "pressure_score": pressure_score, "tendency": tendency}


def _map_self_capacity(tendency: str) -> str:
    if tendency == "strong":
        return "high"
    if tendency == "weak":
        return "low"
    return "medium"


def _map_wealth_presence(count: int) -> str:
    if count <= 0:
        return "none"
    if count == 1:
        return "low"
    if count <= 3:
        return "medium"
    return "high"


def _map_wealth_accessibility(wealth_presence: str, clash_count: int, combination_count: int) -> str:
    if wealth_presence == "none":
        return "not_applicable"
    if clash_count > 0 and combination_count > 0:
        return "conflicted"
    if clash_count > 0:
        return "disrupted"
    if combination_count > 0:
        return "bound"
    return "clear"


def _map_volatility(clash_count: int) -> str:
    if clash_count <= 0:
        return "low"
    if clash_count == 1:
        return "medium"
    return "high"


def _map_income_stability(self_capacity: str, wealth_presence: str, wealth_accessibility: str, volatility: str, structure_binding: str) -> str:
    if wealth_presence == "none" or self_capacity == "low" or volatility == "high" or wealth_accessibility == "disrupted":
        return "unstable"
    if wealth_accessibility == "conflicted":
        return "mixed"
    if self_capacity == "high" and volatility == "low":
        return "stable"
    if structure_binding == "present":
        return "mixed"
    return "mixed"


def _evidence_summary(income_stability: str, self_capacity: str, wealth_presence: str, wealth_accessibility: str, volatility: str, structure_binding: str) -> List[str]:
    return [
        f"income_stability={income_stability}",
        f"self_capacity={self_capacity}",
        f"wealth_presence={wealth_presence}",
        f"wealth_accessibility={wealth_accessibility}",
        f"volatility={volatility}",
        f"structure_binding={structure_binding}",
    ]


def _has_pair(pairs: List[tuple[str, str]], left: str, right: str) -> bool:
    return any({left, right} == {a, b} for a, b in pairs)
