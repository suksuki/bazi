from __future__ import annotations

from typing import Any, Dict, List

from v19.core.chart import BRANCH_HIDDEN_STEMS, VAULT_BRANCHES, element_of_stem, ten_god


STRUCTURE_PORTRAIT_VERSION = "v19.mainline.structure_portrait.v1"
FORBIDDEN_PORTRAIT_OUTPUTS = ["一定", "必然", "发财", "破财", "应期", "灾祸", "疾病", "喜木火", "忌金水", "改运"]
WEALTH_GODS = {"正财", "偏财"}
OUTPUT_GODS = {"食神", "伤官"}
RESOURCE_GODS = {"正印", "偏印"}
PEER_GODS = {"比肩", "劫财"}
OFFICER_GODS = {"正官", "七杀"}


def build_structure_portrait(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    chart = dict(agent_data.get("chart") or {})
    time_context = dict(agent_data.get("time_context") or {})
    inference_context = dict(agent_data.get("inference_context") or {})
    rule_graph_runtime_context = dict(agent_data.get("rule_graph_runtime_context") or {})
    facts = _chart_portrait_facts(chart, time_context)
    income = dict(inference_context.get("income_stability") or {})
    vectors = _portrait_vectors(facts, income, rule_graph_runtime_context)
    labels = _portrait_labels(facts, vectors)
    judgements = _candidate_judgements(labels, vectors)
    question_bias = _question_bias(vectors, labels)
    return {
        "ok": True,
        "version": STRUCTURE_PORTRAIT_VERSION,
        "status": "ready" if facts["pillar_count"] else "chart_facts_unavailable",
        "runtime_scope": "structure_portrait_context_only_no_result_mutation",
        "label_count": len(labels),
        "labels": labels,
        "vectors": vectors,
        "candidate_judgements": judgements,
        "question_bias": question_bias,
        "evidence_summary": {
            "pillar_count": facts["pillar_count"],
            "stem_count": len(facts["stems"]),
            "branch_count": len(facts["branches"]),
            "hidden_stem_count": len(facts["hidden_stems"]),
            "ten_god_count": len(facts["ten_gods"]),
            "relation_count": len(facts["relation_types"]),
            "time_relation_count": facts["time_relation_count"],
            "runtime_route_count": len(rule_graph_runtime_context.get("selected_paths") or []),
        },
        "guardrails": [
            "STRUCTURE_PORTRAIT_CONTEXT_ONLY",
            "CANDIDATE_JUDGEMENT_ONLY",
            "NO_RESULT_MUTATION",
            "NO_RULE_ACTIVATION",
            "NO_HARD_USEFUL_GOD_VERDICT",
            "NO_DOMAIN_RESULT_PREDICTION",
        ],
    }


def structure_portrait_to_prompt_context(portrait: Dict[str, Any], *, limit: int = 8) -> Dict[str, Any]:
    labels = [dict(row) for row in portrait.get("labels") or [] if isinstance(row, dict)]
    judgements = [dict(row) for row in portrait.get("candidate_judgements") or [] if isinstance(row, dict)]
    return {
        "version": STRUCTURE_PORTRAIT_VERSION,
        "status": portrait.get("status") or "",
        "runtime_scope": "llm_prompt_structure_portrait_context_only",
        "vectors": dict(portrait.get("vectors") or {}),
        "labels": [
            {
                "label_id": row.get("label_id") or "",
                "family": row.get("family") or "",
                "value": row.get("value") or "",
                "score": row.get("score"),
                "confidence": row.get("confidence"),
                "candidate_statement": row.get("candidate_statement") or "",
            }
            for row in labels[:limit]
        ],
        "candidate_judgements": judgements[:limit],
        "guardrails": [
            "USE_AS_STRUCTURE_PORTRAIT_ONLY",
            "NO_HARD_VERDICT",
            "NO_DOMAIN_RESULT_PREDICTION",
        ],
    }


def _chart_portrait_facts(chart: Dict[str, Any], time_context: Dict[str, Any]) -> Dict[str, Any]:
    pillars = dict(chart.get("pillars") or {})
    stems: List[str] = []
    branches: List[str] = []
    hidden_stems: List[str] = []
    ten_gods: List[str] = []
    day_stem = str((pillars.get("day") or {}).get("stem") or "")
    month_branch = str((pillars.get("month") or {}).get("branch") or "")
    month_hidden = [stem for stem, _weight in BRANCH_HIDDEN_STEMS.get(month_branch, [])]
    for position in ["year", "month", "day", "hour"]:
        pillar = dict(pillars.get(position) or {})
        stem = str(pillar.get("stem") or "")
        branch = str(pillar.get("branch") or "")
        if stem:
            stems.append(stem)
            if day_stem and position != "day":
                tg = ten_god(day_stem, stem)
                if tg:
                    ten_gods.append(tg)
        if branch:
            branches.append(branch)
            for hidden_stem, _weight in BRANCH_HIDDEN_STEMS.get(branch, []):
                hidden_stems.append(hidden_stem)
                if day_stem:
                    tg = ten_god(day_stem, hidden_stem)
                    if tg:
                        ten_gods.append(tg)
    relation_types = _relation_types(chart)
    time_relation_count = 0
    time_branches: List[str] = []
    for layer_name in ["luck_cycle", "flow_year"]:
        layer = dict(time_context.get(layer_name) or {})
        pillar = dict(layer.get("pillar") or {})
        branch = str(pillar.get("branch") or "")
        if branch:
            time_branches.append(branch)
        rel = layer.get("relations_with_natal") or {}
        if isinstance(rel, dict):
            time_relation_count += sum(len(value) if isinstance(value, list) else 1 for value in rel.values())
    wealth_count = sum(1 for item in ten_gods if item in WEALTH_GODS)
    output_count = sum(1 for item in ten_gods if item in OUTPUT_GODS)
    resource_count = sum(1 for item in ten_gods if item in RESOURCE_GODS)
    peer_count = sum(1 for item in ten_gods if item in PEER_GODS)
    officer_count = sum(1 for item in ten_gods if item in OFFICER_GODS)
    return {
        "pillar_count": sum(1 for value in pillars.values() if isinstance(value, dict) and value.get("display")),
        "day_stem": day_stem,
        "day_element": element_of_stem(day_stem) if day_stem else "",
        "month_branch": month_branch,
        "month_hidden": month_hidden,
        "stems": stems,
        "branches": branches,
        "hidden_stems": hidden_stems,
        "ten_gods": ten_gods,
        "wealth_count": wealth_count,
        "output_count": output_count,
        "resource_count": resource_count,
        "peer_count": peer_count,
        "officer_count": officer_count,
        "relation_types": relation_types,
        "vault_count": sum(1 for branch in branches if branch in VAULT_BRANCHES),
        "time_relation_count": time_relation_count,
        "time_branches": time_branches,
    }


def _relation_types(chart: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for row in (chart.get("relations") or {}).get("items") or []:
        if not isinstance(row, dict):
            continue
        relation_type = str(row.get("type") or row.get("relation_type") or "")
        if relation_type:
            out.append(relation_type)
    return out


def _portrait_vectors(facts: Dict[str, Any], income: Dict[str, Any], runtime_context: Dict[str, Any]) -> Dict[str, float]:
    pillar_factor = min(facts["pillar_count"] / 4, 1.0)
    month_support = 1.0 if facts["day_stem"] and facts["day_stem"] in facts["month_hidden"] else 0.0
    same_element = 0
    if facts["day_element"]:
        same_element = sum(1 for stem in facts["stems"] if element_of_stem(stem) == facts["day_element"])
    relation_count = len(facts["relation_types"])
    branch_volatility = _clamp((relation_count + facts["time_relation_count"] * 0.75) / 6)
    wealth_visibility = _clamp((facts["wealth_count"] * 0.18) + (facts["output_count"] * 0.06))
    income_volatility = _map_level((income.get("volatility") or "unknown"), {"low": 0.15, "medium": 0.45, "high": 0.8, "unknown": 0.35})
    wealth_stability = _clamp(wealth_visibility + 0.25 - branch_volatility * 0.35 - min(facts["peer_count"], 3) * 0.08 - income_volatility * 0.12)
    strength_capacity = _clamp(0.36 + month_support * 0.24 + min(same_element, 4) * 0.07 + facts["resource_count"] * 0.04 - facts["wealth_count"] * 0.025 - branch_volatility * 0.05)
    useful_confidence = _clamp((abs(strength_capacity - 0.5) * 0.8) + min(facts["ten_gods"].__len__(), 8) * 0.035 + pillar_factor * 0.18)
    ten_god_activity = _clamp(len(set(facts["ten_gods"])) / 8)
    time_trigger_activity = _clamp(facts["time_relation_count"] / 5)
    pattern_index_strength = _clamp((1.0 if facts["month_branch"] else 0) * 0.25 + ten_god_activity * 0.35 + (1.0 if facts["relation_types"] else 0) * 0.15 + pillar_factor * 0.2)
    route_count = len(runtime_context.get("selected_paths") or [])
    evidence_confidence = _clamp(pillar_factor * 0.35 + min(len(facts["hidden_stems"]), 8) * 0.035 + min(route_count, 8) * 0.035 + ten_god_activity * 0.2)
    return {
        "strength_capacity": round(strength_capacity, 3),
        "useful_god_candidate_confidence": round(useful_confidence, 3),
        "wealth_visibility": round(wealth_visibility, 3),
        "wealth_stability": round(wealth_stability, 3),
        "ten_god_activity": round(ten_god_activity, 3),
        "branch_volatility": round(branch_volatility, 3),
        "time_trigger_activity": round(time_trigger_activity, 3),
        "pattern_index_strength": round(pattern_index_strength, 3),
        "evidence_confidence": round(evidence_confidence, 3),
    }


def _portrait_labels(facts: Dict[str, Any], vectors: Dict[str, float]) -> List[Dict[str, Any]]:
    labels = [
        _label(
            "portrait.strength.capacity_candidate",
            "strength",
            _capacity_value(vectors["strength_capacity"]),
            vectors["strength_capacity"],
            vectors["evidence_confidence"],
            ["chart.day_stem", "chart.month_branch", "chart.hidden_stems"],
            "日主强弱先作为承载证据候选，需要月令、透藏、根气和克泄耗共同验证。",
        ),
        _label(
            "portrait.useful_god.candidate_boundary",
            "useful_god",
            "candidate_only" if vectors["useful_god_candidate_confidence"] >= 0.45 else "insufficient_evidence",
            vectors["useful_god_candidate_confidence"],
            vectors["evidence_confidence"],
            ["portrait.strength_capacity", "chart.elements", "chart.relations"],
            "用神忌神只进入候选路径，不直接给喜忌硬结论。",
        ),
        _label(
            "portrait.ten_god.activity",
            "ten_god",
            "active" if vectors["ten_god_activity"] >= 0.55 else "limited",
            vectors["ten_god_activity"],
            vectors["evidence_confidence"],
            ["chart.visible_stems", "chart.hidden_stems", "ten_god.mapping"],
            "十神活跃度用于选择财官印食伤等观察入口。",
        ),
        _label(
            "portrait.wealth.visibility",
            "wealth",
            "visible" if vectors["wealth_visibility"] >= 0.45 else "weak_or_hidden",
            vectors["wealth_visibility"],
            vectors["evidence_confidence"],
            ["ten_god.wealth", "ten_god.output"],
            "财星可见度只说明财富结构素材是否容易被观察，不是财富结论。",
        ),
        _label(
            "portrait.wealth.stability",
            "wealth",
            "stable_candidate" if vectors["wealth_stability"] >= 0.55 else "stability_needs_review",
            vectors["wealth_stability"],
            vectors["evidence_confidence"],
            ["inference_context.income_stability", "chart.branch_relations"],
            "收入稳定性只能作为结构归因候选，需要看承载、牵制和波动。",
        ),
        _label(
            "portrait.branch.volatility",
            "branch",
            "active" if vectors["branch_volatility"] >= 0.4 else "quiet",
            vectors["branch_volatility"],
            vectors["evidence_confidence"],
            ["chart.relations", "time_context.relations_with_natal"],
            "冲合刑害破和时间触发用于提示结构张力，不直接推出结果。",
        ),
        _label(
            "portrait.time.trigger",
            "time",
            "trigger_context" if vectors["time_trigger_activity"] >= 0.25 else "background_only",
            vectors["time_trigger_activity"],
            vectors["evidence_confidence"],
            ["time_context.luck_cycle", "time_context.flow_year"],
            "大运流年只作为时间背景和触发候选，不改写本命结构。",
        ),
        _label(
            "portrait.pattern.index",
            "pattern",
            "index_candidate" if vectors["pattern_index_strength"] >= 0.45 else "insufficient_index",
            vectors["pattern_index_strength"],
            vectors["evidence_confidence"],
            ["chart.month_branch", "ten_god.mapping", "chart.relations"],
            "格局先作为结构索引，不把格局名直接翻成命运判断。",
        ),
    ]
    return sorted(labels, key=lambda row: (float(row["score"]), float(row["confidence"]), row["label_id"]), reverse=True)


def _candidate_judgements(labels: List[Dict[str, Any]], vectors: Dict[str, float]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if vectors["useful_god_candidate_confidence"] < 0.65:
        out.append(_judgement("portrait.judgement.useful_god_candidate_only", "useful_god", "用神忌神证据门槛未完全满足，只能保留为候选路径。", vectors["useful_god_candidate_confidence"]))
    if vectors["branch_volatility"] >= 0.4:
        out.append(_judgement("portrait.judgement.branch_volatility_review", "branch", "当前结构张力较明显，推荐先分清冲合刑害发生在本命还是时间背景。", vectors["branch_volatility"]))
    if vectors["wealth_visibility"] >= 0.35 and vectors["wealth_stability"] < 0.55:
        out.append(_judgement("portrait.judgement.wealth_visible_stability_review", "wealth", "财星素材可见，但稳定性仍需看承载和牵制，不形成财富断语。", vectors["wealth_stability"]))
    if vectors["pattern_index_strength"] >= 0.45:
        out.append(_judgement("portrait.judgement.pattern_index_candidate", "pattern", "格局已有结构索引入口，但仍需同层验证成格和破格条件。", vectors["pattern_index_strength"]))
    if not out:
        out.append(_judgement("portrait.judgement.structure_evidence_first", "structure", "当前先以结构证据和候选判断为主，不输出硬结论。", vectors["evidence_confidence"]))
    return out


def _question_bias(vectors: Dict[str, float], labels: List[Dict[str, Any]]) -> Dict[str, Any]:
    bucket_boosts = {
        "strength_useful_god": round(8 + vectors["useful_god_candidate_confidence"] * 12 + (1 - abs(vectors["strength_capacity"] - 0.5)) * 6, 3),
        "income_stability": round(4 + vectors["wealth_visibility"] * 14 + max(0.0, vectors["wealth_visibility"] - vectors["wealth_stability"]) * 10, 3),
        "branch_relation": round(4 + vectors["branch_volatility"] * 18, 3),
        "time_context": round(3 + vectors["time_trigger_activity"] * 18, 3),
        "pattern_structure": round(4 + vectors["pattern_index_strength"] * 14, 3),
        "metadata": round(4 + vectors["ten_god_activity"] * 12, 3),
    }
    question_boosts = {
        "q_strength_assessment": bucket_boosts["strength_useful_god"],
        "q_useful_god_candidates": bucket_boosts["strength_useful_god"] + 2,
        "q_income_stability": bucket_boosts["income_stability"],
        "q_branch_relation_detail": bucket_boosts["branch_relation"],
        "q_time_context_boundary": bucket_boosts["time_context"],
        "q_pattern_structure": bucket_boosts["pattern_structure"],
        "q_ten_god_focus": bucket_boosts["metadata"],
    }
    ordered_questions = [key for key, _value in sorted(question_boosts.items(), key=lambda row: row[1], reverse=True)]
    return {
        "runtime_scope": "question_ranking_bias_only_no_result_mutation",
        "bucket_boosts": bucket_boosts,
        "question_boosts": {key: round(value, 3) for key, value in question_boosts.items()},
        "recommended_question_keys": ordered_questions[:6],
        "dominant_label_ids": [str(row.get("label_id") or "") for row in labels[:5]],
    }


def _label(label_id: str, family: str, value: str, score: float, confidence: float, evidence_refs: List[str], statement: str) -> Dict[str, Any]:
    return {
        "label_id": label_id,
        "family": family,
        "value": value,
        "score": round(_clamp(score), 3),
        "confidence": round(_clamp(confidence), 3),
        "evidence_refs": evidence_refs,
        "candidate_statement": statement,
        "forbidden_outputs": FORBIDDEN_PORTRAIT_OUTPUTS,
        "runtime_scope": "structure_label_context_only_no_verdict",
    }


def _judgement(judgement_id: str, family: str, text: str, confidence: float) -> Dict[str, Any]:
    return {
        "judgement_id": judgement_id,
        "family": family,
        "text": text,
        "confidence": round(_clamp(confidence), 3),
        "verdict": "candidate_only",
        "forbidden_outputs": FORBIDDEN_PORTRAIT_OUTPUTS,
    }


def _capacity_value(score: float) -> str:
    if score >= 0.64:
        return "stronger_capacity_candidate"
    if score <= 0.38:
        return "weaker_capacity_candidate"
    return "balanced_or_uncertain_candidate"


def _map_level(value: Any, mapping: Dict[str, float]) -> float:
    return mapping.get(str(value or "").lower(), mapping.get("unknown", 0.0))


def _clamp(value: float) -> float:
    try:
        number = float(value)
    except Exception:
        return 0.0
    if number < 0:
        return 0.0
    if number > 1:
        return 1.0
    return number
