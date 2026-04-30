from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Set, Tuple

from v19.core.chart import BRANCH_HIDDEN_STEMS, element_of_stem, ten_god


RULE_GRAPH_ORCHESTRATOR_VERSION = "v19.p46.rule_graph_orchestrator.v1"
CANARY_RUNTIME_KNOWLEDGE_IDS = {
    "core.five_element_relations.v1",
    "core.stem_attributes.v1",
}
FORBIDDEN_ANSWER_TEXT = ["发财", "破财", "官非", "灾祸", "疾病", "应期", "必然", "一定", "改运"]


def orchestrate_rule_graph_paths(
    agent_data: Dict[str, Any],
    *,
    question_key: str = "",
    message: str = "",
    answer_kind: str = "",
    limit: int = 8,
) -> Dict[str, Any]:
    chart = dict(agent_data.get("chart") or {})
    time_context = dict(agent_data.get("time_context") or {})
    graph = build_chart_rule_graph(chart, time_context)
    intent = infer_question_intent(question_key, message, answer_kind)
    candidates = _load_rule_candidates()
    scored = [_score_candidate(candidate, graph, intent) for candidate in candidates]
    retrieved = [row for row in scored if row["score"] > 0]
    retrieved.sort(key=lambda row: (row["score"], row["risk_rank"] * -1, row["knowledge_id"]), reverse=True)
    selected = arbitrate_rule_paths(retrieved, limit=limit)
    audit = audit_selected_paths_for_answer(selected)
    return {
        "ok": True,
        "version": RULE_GRAPH_ORCHESTRATOR_VERSION,
        "status": "rule_graph_paths_ready",
        "runtime_scope": "chart_specific_rule_path_selection_no_answer_mutation",
        "question_intent": intent,
        "chart_graph": graph,
        "summary": {
            "candidate_count": len(candidates),
            "retrieved_count": len(retrieved),
            "selected_count": len(selected),
            "canary_selected_count": sum(1 for row in selected if row.get("framework_state") == "canary_isolated_passed"),
            "runtime_allowed_count": sum(1 for row in selected if row.get("runtime_allowed") is True),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "by_topic_lane": _count_by(selected, "topic_lane"),
        },
        "selected_paths": selected,
        "answer_audit": audit,
        "arbitration": {
            "policy": "select_highest_scoring_paths_by_intent_and_chart_features",
            "rules": [
                "natal_structure_before_time_layer",
                "visible_layer_before_hidden_stem_layer",
                "canary_paths_may_emit_internal_signal_only",
                "r2_paths_remain_shadow_scoring_only",
                "no_domain_prediction_output",
            ],
        },
        "future_model_slots": {
            "gnn": "reserved_for_path_embedding_or_rerank_after_labeled_eval_dataset_exists",
            "rl": "reserved_for_question_ordering_and_dialog_policy_not_core_rule_truth",
            "current": "deterministic_rule_graph_path_scoring",
        },
        "guardrails": [
            "RULE_GRAPH_ORCHESTRATION",
            "DETERMINISTIC_PATH_SCORING",
            "NO_BLACK_BOX_CORE_INFERENCE",
            "NO_RUNTIME_RULE_ACTIVATION",
            "NO_ANSWER_MUTATION",
            "NO_DOMAIN_RESULT_PREDICTION",
        ],
    }


def build_chart_rule_graph(chart: Dict[str, Any], time_context: Dict[str, Any]) -> Dict[str, Any]:
    pillars = dict(chart.get("pillars") or {})
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    feature_tags: Set[str] = set()
    day_stem = str((pillars.get("day") or {}).get("stem") or "")

    for position in ["year", "month", "day", "hour"]:
        pillar = dict(pillars.get(position) or {})
        stem = str(pillar.get("stem") or "")
        branch = str(pillar.get("branch") or "")
        display = str(pillar.get("display") or "")
        if display:
            nodes.append(_node(f"pillar:{position}", "pillar", display, layer="natal", position=position))
        if stem:
            nodes.append(_node(f"stem:{stem}:{position}", "stem", stem, layer="natal", position=position, element=element_of_stem(stem)))
            edges.append(_edge(f"pillar:{position}", f"stem:{stem}:{position}", "has_stem", layer="natal"))
            feature_tags.update({"stem", f"stem:{stem}", f"element:{element_of_stem(stem)}", "visible_stem"})
            if day_stem and position != "day":
                tg = ten_god(day_stem, stem)
                if tg:
                    nodes.append(_node(f"ten_god:{tg}:{position}", "ten_god", tg, layer="natal", position=position))
                    edges.append(_edge(f"stem:{stem}:{position}", f"ten_god:{tg}:{position}", "maps_to_ten_god", layer="natal"))
                    feature_tags.update({"ten_god", f"ten_god:{tg}", "visible_ten_god"})
        if branch:
            nodes.append(_node(f"branch:{branch}:{position}", "branch", branch, layer="natal", position=position))
            edges.append(_edge(f"pillar:{position}", f"branch:{branch}:{position}", "has_branch", layer="natal"))
            feature_tags.update({"branch", f"branch:{branch}"})
            for hidden_stem, _weight in BRANCH_HIDDEN_STEMS.get(branch, []):
                nodes.append(_node(f"hidden_stem:{hidden_stem}:{branch}", "hidden_stem", hidden_stem, layer="hidden", branch=branch, element=element_of_stem(hidden_stem)))
                edges.append(_edge(f"branch:{branch}:{position}", f"hidden_stem:{hidden_stem}:{branch}", "contains_hidden_stem", layer="hidden"))
                feature_tags.update({"hidden_stem", f"hidden_stem:{hidden_stem}", f"element:{element_of_stem(hidden_stem)}"})

    for relation in (chart.get("relations") or {}).get("items") or []:
        if not isinstance(relation, dict):
            continue
        relation_type = str(relation.get("type") or relation.get("relation_type") or "")
        pair = _relation_pair(relation)
        if relation_type:
            feature_tags.update({"branch_relation", f"relation:{relation_type}"})
            nodes.append(_node(f"relation:{relation_type}:{pair}", "relation", relation_type, layer="natal", pair=pair))
            if pair:
                edges.append(_edge(f"relation:{relation_type}:{pair}", f"feature:branch_relation", "emits_feature", layer="natal"))

    for layer_name in ["luck_cycle", "flow_year"]:
        layer = dict(time_context.get(layer_name) or {})
        pillar = dict(layer.get("pillar") or {})
        if not layer:
            continue
        nodes.append(_node(f"time_layer:{layer_name}", "time_layer", layer_name, layer="time"))
        stem = str(pillar.get("stem") or "")
        branch = str(pillar.get("branch") or "")
        if stem:
            nodes.append(_node(f"time_stem:{stem}:{layer_name}", "stem", stem, layer="time", element=element_of_stem(stem)))
            edges.append(_edge(f"time_layer:{layer_name}", f"time_stem:{stem}:{layer_name}", "has_time_stem", layer="time"))
        if branch:
            nodes.append(_node(f"time_branch:{branch}:{layer_name}", "branch", branch, layer="time"))
            edges.append(_edge(f"time_layer:{layer_name}", f"time_branch:{branch}:{layer_name}", "has_time_branch", layer="time"))
        if layer.get("relations_with_natal"):
            feature_tags.update({"time_layer", "time_relation"})

    return {
        "version": RULE_GRAPH_ORCHESTRATOR_VERSION,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": _dedupe_by_id(nodes)[:96],
        "edges": edges[:128],
        "feature_tags": sorted(tag for tag in feature_tags if tag and not tag.endswith(":")),
        "layer_policy": {
            "natal": "base structure",
            "hidden": "background only unless action path is explicit",
            "time": "trigger context only and cannot rewrite natal structure",
        },
    }


def infer_question_intent(question_key: str = "", message: str = "", answer_kind: str = "") -> Dict[str, Any]:
    key = str(question_key or "")
    text = str(message or "")
    seed = f"{key} {text} {answer_kind}"
    lowered = seed.lower()
    if answer_kind:
        route = answer_kind
    elif any(token in lowered for token in ["pattern"]) or any(token in seed for token in ["格局", "成格", "破格", "从格", "化格", "羊刃"]):
        route = "pattern_structure"
    elif any(token in lowered for token in ["blind", "source target", "work efficiency"]) or any(token in seed for token in ["盲派", "做功", "原神", "目标神", "换象", "带象"]):
        route = "blind_lifa_boundary"
    elif any(token in lowered for token in ["auxiliary", "nayin", "shen sha"]) or any(token in seed for token in ["神煞", "纳音", "命宫", "身宫", "胎元", "空亡", "地理", "地域"]):
        route = "auxiliary_evidence"
    elif any(token in lowered for token in ["wealth", "income"]) or any(token in seed for token in ["收入", "财", "소득", "수입", "재물"]):
        route = "income_structure"
    elif any(token in lowered for token in ["career", "work", "job"]) or any(token in seed for token in ["事业", "官", "杀", "직업", "커리어"]):
        route = "career_structure"
    elif any(token in lowered for token in ["relationship", "partner", "marriage"]) or any(token in seed for token in ["感情", "关系", "婚", "伴侣", "配偶", "관계", "연애", "배우자", "결혼"]):
        route = "relationship_structure"
    elif any(token in lowered for token in ["health", "body", "safety"]) or any(token in seed for token in ["健康", "身体", "安全", "건강", "몸"]):
        route = "health_structure"
    elif any(token in lowered for token in ["time", "luck", "flow year", "luck cycle"]) or any(token in seed for token in ["流年", "大运", "时间", "대운", "세운"]):
        route = "time_boundary"
    elif any(token in lowered for token in ["relation", "clash", "combination"]) or any(token in seed for token in ["冲", "合", "刑", "害", "破", "地支", "충", "합"]):
        route = "branch_relation"
    elif any(token in lowered for token in ["metadata", "ten god", "day master", "month branch", "hidden stem"]) or any(token in seed for token in ["十神", "日主", "月令", "藏干", "五行", "십성", "일간", "월지", "지장간"]):
        route = "metadata_boundary"
    else:
        route = "structure_overview"
    return {
        "intent": route,
        "question_key": key,
        "message_present": bool(text.strip()),
        "preferred_lanes": _preferred_lanes_for_intent(route),
        "preferred_domains": _preferred_domains_for_intent(route),
    }


def arbitrate_rule_paths(scored: List[Dict[str, Any]], *, limit: int = 8) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    used_lanes: Dict[str, int] = {}
    for row in scored:
        lane = str(row.get("topic_lane") or "unknown")
        max_per_lane = 3 if lane in {"core_strength_foundation", "branch_time_activation", "ten_god_mechanism"} else 2
        if used_lanes.get(lane, 0) >= max_per_lane:
            continue
        selected.append(row)
        used_lanes[lane] = used_lanes.get(lane, 0) + 1
        if len(selected) >= limit:
            break
    return selected


def audit_selected_paths_for_answer(paths: List[Dict[str, Any]]) -> Dict[str, Any]:
    forbidden_failures = []
    for path in paths:
        for token in path.get("forbidden_outputs") or []:
            if str(token) in FORBIDDEN_ANSWER_TEXT:
                continue
        if path.get("runtime_allowed") is True and path.get("framework_state") != "canary_isolated_passed":
            forbidden_failures.append({"knowledge_id": path.get("knowledge_id"), "failure_type": "runtime_allowed_without_canary"})
    return {
        "status": "pass" if not forbidden_failures else "fail",
        "selected_path_count": len(paths),
        "runtime_allowed_count": sum(1 for path in paths if path.get("runtime_allowed") is True),
        "answer_mutation_count": 0,
        "forbidden_failures": forbidden_failures,
        "guardrails": ["ANSWER_AUDIT_BEFORE_RENDER", "NO_PREDICTION_TEXT", "NO_INTERNAL_DEBUG_DUMP"],
    }


def rule_graph_paths_to_signals(report: Dict[str, Any], *, limit: int = 6) -> List[Dict[str, Any]]:
    signals = []
    for path in (report.get("selected_paths") or [])[:limit]:
        category = _signal_category_for_path(path)
        signals.append(
            {
                "signal_id": f"rule_graph.{path.get('knowledge_id')}",
                "source": "rule_graph_orchestrator",
                "version": RULE_GRAPH_ORCHESTRATOR_VERSION,
                "domain": path.get("domain") or "structure",
                "category": category,
                "title": path.get("title") or path.get("knowledge_id") or "",
                "knowledge_id": path.get("knowledge_id") or "",
                "rule_id": path.get("candidate_rule_id") or "",
                "risk_level": path.get("risk_level") or "",
                "observed": path.get("matched_features") or [],
                "reason": path.get("reason") or "",
                "score": int(path.get("score") or 0),
                "runtime_allowed": path.get("runtime_allowed") is True,
                "mutates_result": False,
            }
        )
    return signals


def _load_rule_candidates() -> List[Dict[str, Any]]:
    return [dict(row) for row in _cached_rule_candidates()]


@lru_cache(maxsize=1)
def _cached_rule_candidates() -> Tuple[Dict[str, Any], ...]:
    from v19.synthetic_validation.domain_route_backfill import build_p61_domain_route_backfill_candidates
    from v19.synthetic_validation.mainline_p1_safe_wrappers import build_p69_mainline_p1_safe_wrappers
    from v19.synthetic_validation.rule_conversion_validation import build_p39_rule_conversion_candidates

    candidates = [dict(row) for row in build_p39_rule_conversion_candidates().get("candidates") or []]
    candidates.extend(dict(row) for row in build_p61_domain_route_backfill_candidates().get("candidates") or [])
    candidates.extend(dict(row) for row in build_p69_mainline_p1_safe_wrappers().get("candidates") or [])
    return tuple(candidates)


def _score_candidate(candidate: Dict[str, Any], graph: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    feature_tags = set(str(tag) for tag in graph.get("feature_tags") or [])
    domain = str(candidate.get("domain") or "")
    title = str(candidate.get("title") or "")
    knowledge_id = str(candidate.get("knowledge_id") or "")
    topic_lane = _topic_lane(candidate)
    matched = _matched_features(candidate, feature_tags)
    base = 0
    if topic_lane in set(intent.get("preferred_lanes") or []):
        base += 32
    if domain in set(intent.get("preferred_domains") or []):
        base += 24
    if topic_lane == "domain_safety_bridge" and domain in set(intent.get("preferred_domains") or []):
        base += 26
    base += min(len(matched) * 7, 28)
    if knowledge_id in CANARY_RUNTIME_KNOWLEDGE_IDS:
        base += 16
    if str(candidate.get("risk_level") or "") == "R0":
        base += 10
    elif str(candidate.get("risk_level") or "") == "R1":
        base += 6
    elif str(candidate.get("risk_level") or "") == "R2":
        base += 2
    if str(candidate.get("conversion_mode") or "") in {"route_only_safe_wrapper", "boundary_only_safe_wrapper", "evidence_only_label"} and (
        domain in set(intent.get("preferred_domains") or []) or topic_lane in set(intent.get("preferred_lanes") or [])
    ):
        base += 30
    if _title_matches_intent(title, intent):
        base += 10
    if not matched and topic_lane not in set(intent.get("preferred_lanes") or []) and domain not in set(intent.get("preferred_domains") or []):
        base = 0
    risk_rank = {"R0": 0, "R1": 1, "R2": 2}.get(str(candidate.get("risk_level") or ""), 3)
    framework_state = _framework_state(candidate)
    return {
        "path_id": f"p46.path.{knowledge_id}",
        "candidate_rule_id": candidate.get("candidate_rule_id") or "",
        "knowledge_id": knowledge_id,
        "title": title,
        "domain": domain,
        "topic_lane": topic_lane,
        "risk_level": candidate.get("risk_level") or "",
        "risk_rank": risk_rank,
        "score": base,
        "matched_features": matched,
        "condition_axes_required": candidate.get("condition_axes_required") or [],
        "expected_question_keys": candidate.get("expected_question_keys") or [],
        "forbidden_outputs": candidate.get("forbidden_outputs") or [],
        "conversion_mode": candidate.get("conversion_mode") or "",
        "audit_tags": candidate.get("audit_tags") or [],
        "framework_state": framework_state,
        "runtime_allowed": framework_state == "canary_isolated_passed",
        "reason": _path_reason(candidate, matched, intent, framework_state),
    }


def _matched_features(candidate: Dict[str, Any], feature_tags: Set[str]) -> List[str]:
    text = " ".join(
        [
            str(candidate.get("knowledge_id") or ""),
            str(candidate.get("title") or ""),
            str(candidate.get("domain") or ""),
            str(candidate.get("category") or ""),
            " ".join(str(axis) for axis in candidate.get("condition_axes_required") or []),
        ]
    )
    matches = set()
    feature_map = {
        "five_element": {"element:", "五行", "生克", "element"},
        "stem": {"stem", "天干"},
        "branch": {"branch", "地支"},
        "hidden_stem": {"hidden_stem", "藏干"},
        "ten_god": {"ten_god", "十神", "财", "官", "杀", "印", "食", "伤", "比劫"},
        "branch_relation": {"branch_relation", "冲", "合", "刑", "害", "破", "relation"},
        "time_relation": {"time_relation", "time_layer", "流年", "大运", "引动"},
        "domain_safety": {"relationship", "health", "关系", "感情", "健康", "安全", "降级", "domain_answer_boundary"},
    }
    for label, tokens in feature_map.items():
        if any(tag.startswith(label) or tag == label for tag in feature_tags) and any(token in text for token in tokens):
            matches.add(label)
    if "element:" in " ".join(feature_tags) and any(token in text for token in ["五行", "element", "生克"]):
        matches.add("five_element")
    return sorted(matches)


def _topic_lane(candidate: Dict[str, Any]) -> str:
    domain = str(candidate.get("domain") or "")
    knowledge_id = str(candidate.get("knowledge_id") or "")
    if domain in {"interaction", "ten_god"}:
        return "ten_god_mechanism"
    if domain == "pattern":
        return "pattern_structure"
    if domain in {"wealth", "career"}:
        return "wealth_career_bridge"
    if domain in {"relationship", "health", "family", "children", "personality"}:
        return "domain_safety_bridge"
    if domain in {"blind", "palace"}:
        return "blind_lifa_palace"
    if domain in {"auxiliary_pillars", "auxiliary_symbols", "geo_context", "nayin", "shensha"}:
        return "auxiliary_evidence"
    if domain == "luck_flow" or any(token in knowledge_id for token in ["branch", "time", "luck", "stem_combination", "vault", "month_command", "hidden_stem"]):
        return "branch_time_activation"
    return "core_strength_foundation"


def _signal_category_for_path(path: Dict[str, Any]) -> str:
    knowledge_id = str(path.get("knowledge_id") or "")
    topic_lane = str(path.get("topic_lane") or "")
    domain = str(path.get("domain") or "")
    if "five_element" in knowledge_id:
        return "five_element_relation"
    if "stem_attributes" in knowledge_id or "stem" in knowledge_id:
        return "stem_branch_attribute"
    if topic_lane == "branch_time_activation":
        return "timing_context" if domain == "luck_flow" else "branch_relation"
    if topic_lane == "ten_god_mechanism":
        return "ten_god_interaction"
    if topic_lane == "wealth_career_bridge":
        return "wealth_boundary" if domain == "wealth" else "pattern_structure"
    if topic_lane == "domain_safety_bridge":
        return f"{domain}_boundary" if domain else "domain_safety_boundary"
    if topic_lane == "pattern_structure":
        return "pattern_structure"
    if topic_lane == "blind_lifa_palace":
        return "blind_lifa_boundary"
    if topic_lane == "auxiliary_evidence":
        return "auxiliary_evidence_label"
    if topic_lane == "core_strength_foundation":
        return "strength_model"
    return "core_symbol"


def _framework_state(candidate: Dict[str, Any]) -> str:
    if str(candidate.get("knowledge_id") or "") in CANARY_RUNTIME_KNOWLEDGE_IDS:
        return "canary_isolated_passed"
    if str(candidate.get("risk_level") or "") in {"R0", "R1"}:
        return "dry_run_passed_candidate"
    if str(candidate.get("risk_level") or "") == "R2":
        return "shadow_scoring_candidate"
    return "candidate_only"


def _preferred_lanes_for_intent(route: str) -> List[str]:
    return {
        "income_structure": ["wealth_career_bridge", "ten_god_mechanism", "branch_time_activation"],
        "career_structure": ["wealth_career_bridge", "ten_god_mechanism", "pattern_structure"],
        "pattern_structure": ["pattern_structure", "ten_god_mechanism", "core_strength_foundation"],
        "blind_lifa_boundary": ["blind_lifa_palace", "branch_time_activation", "core_strength_foundation"],
        "auxiliary_evidence": ["auxiliary_evidence", "core_strength_foundation"],
        "relationship_structure": ["domain_safety_bridge", "core_strength_foundation", "ten_god_mechanism", "branch_time_activation", "blind_lifa_palace"],
        "health_structure": ["domain_safety_bridge", "core_strength_foundation", "branch_time_activation", "ten_god_mechanism"],
        "time_boundary": ["branch_time_activation", "core_strength_foundation"],
        "branch_relation": ["branch_time_activation", "core_strength_foundation"],
        "metadata_boundary": ["core_strength_foundation", "ten_god_mechanism", "branch_time_activation"],
        "structure_overview": ["core_strength_foundation", "branch_time_activation", "ten_god_mechanism"],
    }.get(route, ["core_strength_foundation", "branch_time_activation"])


def _preferred_domains_for_intent(route: str) -> List[str]:
    return {
        "income_structure": ["wealth", "interaction", "ten_god", "luck_flow"],
        "career_structure": ["career", "interaction", "pattern"],
        "pattern_structure": ["pattern", "career", "interaction"],
        "blind_lifa_boundary": ["blind", "palace", "core_structure"],
        "auxiliary_evidence": ["auxiliary_pillars", "auxiliary_symbols", "geo_context", "nayin", "shensha"],
        "relationship_structure": ["relationship", "ten_god", "interaction", "palace", "luck_flow"],
        "health_structure": ["health", "strength", "core_structure", "luck_flow", "ten_god"],
        "time_boundary": ["luck_flow", "timing", "core_structure"],
        "branch_relation": ["core_structure", "luck_flow", "branch_advanced"],
        "metadata_boundary": ["core_structure", "five_element", "ten_god", "strength"],
        "structure_overview": ["core_structure", "five_element", "strength", "luck_flow"],
    }.get(route, ["core_structure", "strength"])


def _title_matches_intent(title: str, intent: Dict[str, Any]) -> bool:
    route = str(intent.get("intent") or "")
    route_tokens = {
        "income_structure": ["财", "收入", "财富"],
        "career_structure": ["事业", "官", "杀"],
        "pattern_structure": ["格局", "成格", "破格", "从格", "化格", "羊刃"],
        "blind_lifa_boundary": ["盲派", "做功", "原神", "目标神", "换象", "带象"],
        "auxiliary_evidence": ["神煞", "纳音", "命宫", "身宫", "胎元", "空亡", "地理", "地域"],
        "relationship_structure": ["感情", "关系", "婚", "伴侣", "配偶"],
        "health_structure": ["健康", "身体", "安全"],
        "time_boundary": ["流年", "大运", "引动", "时间"],
        "branch_relation": ["冲", "合", "刑", "害", "破", "地支"],
        "metadata_boundary": ["五行", "天干", "藏干", "十神", "日主", "月令"],
        "structure_overview": ["结构", "五行", "天干", "地支"],
    }.get(route, [])
    return any(token in title for token in route_tokens)


def _path_reason(candidate: Dict[str, Any], matched: List[str], intent: Dict[str, Any], framework_state: str) -> str:
    title = str(candidate.get("title") or candidate.get("knowledge_id") or "")
    match_text = "、".join(matched) if matched else "问题意图"
    return f"{title}匹配{match_text}，当前状态为{framework_state}；只用于结构路径选择。"


def _node(node_id: str, kind: str, label: str, **extra: Any) -> Dict[str, Any]:
    return {"id": node_id, "kind": kind, "label": label, **extra}


def _edge(source: str, target: str, relation: str, **extra: Any) -> Dict[str, Any]:
    return {"source": source, "target": target, "relation": relation, **extra}


def _relation_pair(relation: Dict[str, Any]) -> str:
    branches = relation.get("branches") or relation.get("pair") or []
    if isinstance(branches, list):
        return "-".join(str(item) for item in branches if str(item))
    return str(branches or "")


def _dedupe_by_id(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for row in rows:
        row_id = str(row.get("id") or "")
        if not row_id or row_id in seen:
            continue
        seen.add(row_id)
        out.append(row)
    return out


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
