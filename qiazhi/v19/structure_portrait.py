from __future__ import annotations

from typing import Any, Dict, List, Tuple

from v19.core.chart import BRANCH_HIDDEN_STEMS, VAULT_BRANCHES, element_of_stem, ten_god


STRUCTURE_PORTRAIT_VERSION = "v19.mainline.structure_portrait.v1"
PORTRAIT_LABEL_ONTOLOGY_VERSION = "v19.mainline.structure_portrait_label_ontology.v2"
PORTRAIT_CALIBRATION_VERSION = "v19.mainline.structure_portrait_calibration_hooks.v1"
FORBIDDEN_PORTRAIT_OUTPUTS = ["一定", "必然", "发财", "破财", "应期", "灾祸", "疾病", "喜木火", "忌金水", "改运"]
WEALTH_GODS = {"正财", "偏财"}
OUTPUT_GODS = {"食神", "伤官"}
RESOURCE_GODS = {"正印", "偏印"}
PEER_GODS = {"比肩", "劫财"}
OFFICER_GODS = {"正官", "七杀"}


def structure_portrait_label_ontology() -> Dict[str, Any]:
    labels = list(_LABEL_ONTOLOGY.values())
    return {
        "version": PORTRAIT_LABEL_ONTOLOGY_VERSION,
        "status": "ready",
        "runtime_scope": "label_ontology_contract_only_no_runtime_mutation",
        "label_count": len(labels),
        "labels": labels,
        "scoring_model": {
            "current": "deterministic_evidence_score_plus_internal_bayesian_style_confidence",
            "rule_graph_support": "selected knowledge paths raise confidence but do not create hard verdicts",
            "layer_policy": "natal_structure_before_time_layer; visible_before_hidden; time_triggers_do_not_rewrite_natal",
        },
        "guardrails": [
            "LABEL_ONTOLOGY_IS_CONTRACT",
            "NO_HARD_USEFUL_GOD_VERDICT",
            "NO_DOMAIN_RESULT_PREDICTION",
            "NO_BLACK_BOX_CORE_INFERENCE",
        ],
    }


_LABEL_ONTOLOGY: Dict[str, Dict[str, Any]] = {
    "portrait.strength.capacity_candidate": {
        "label_id": "portrait.strength.capacity_candidate",
        "family": "strength",
        "required_evidence": ["day_stem", "month_branch", "hidden_stems", "same_element_or_resource"],
        "source_layers": ["natal", "hidden"],
        "confidence_rule": "month_command_and_visible_support_before_hidden_background",
        "question_hooks": ["q_strength_assessment", "q_day_master_month_anchor", "q_useful_god_candidates"],
        "user_calibration_hooks": ["过往压力较大的阶段，你更常感觉能承载，还是容易被消耗？"],
        "analyst_confirmation_hooks": ["强弱候选是否同时满足月令、透藏、根气、克泄耗的证据门槛？"],
        "answer_kinds": ["strength_assessment", "useful_god_boundary", "structure_overview"],
        "answer_boundary": "只能回答强弱承载证据和候选方向，不直接断身强身弱结果。",
        "topic_lanes": ["core_strength_foundation"],
        "domains": ["strength", "day_master_element", "five_element"],
        "vector_key": "strength_capacity",
        "prior": 0.48,
    },
    "portrait.useful_god.candidate_boundary": {
        "label_id": "portrait.useful_god.candidate_boundary",
        "family": "useful_god",
        "required_evidence": ["strength_capacity", "five_element_flow", "same_layer_action", "rescue_or_constraint_path"],
        "source_layers": ["natal", "hidden", "time"],
        "confidence_rule": "all_required_axes_before_hard_favorable_unfavorable_claim",
        "question_hooks": ["q_useful_god_candidates", "q_favorable_elements_boundary", "q_unfavorable_god_boundary", "q_strength_assessment"],
        "user_calibration_hooks": ["哪些年份或阶段，你明显感觉状态被某类环境支持或牵制？"],
        "analyst_confirmation_hooks": ["用神忌神候选是否有同层作用路径和救应路径，还是只能保留为候选？"],
        "answer_kinds": ["useful_god_boundary", "strength_assessment"],
        "answer_boundary": "证据不足时只输出用神忌神候选，不输出喜木火、忌金水等硬断。",
        "topic_lanes": ["core_strength_foundation", "ten_god_mechanism", "pattern_structure"],
        "domains": ["useful_god", "strength", "five_element", "ten_god"],
        "vector_key": "useful_god_candidate_confidence",
        "prior": 0.38,
    },
    "portrait.ten_god.activity": {
        "label_id": "portrait.ten_god.activity",
        "family": "ten_god",
        "required_evidence": ["visible_stems", "hidden_stems", "ten_god_mapping"],
        "source_layers": ["natal", "hidden"],
        "confidence_rule": "visible_ten_god_before_hidden_ten_god; mechanism_requires_action_path",
        "question_hooks": ["q_ten_god_focus", "q_ten_god_metadata", "q_hidden_stem_role"],
        "user_calibration_hooks": ["你更常通过表达产出、资源学习、规则压力，还是人际竞争形成关键变化？"],
        "analyst_confirmation_hooks": ["十神机制是否只是同见，还是已经形成同层作用路径？"],
        "answer_kinds": ["metadata_boundary", "pattern_structure", "income_structure"],
        "answer_boundary": "十神标签说明关系来源，不单独构成结果判断。",
        "topic_lanes": ["ten_god_mechanism"],
        "domains": ["ten_god", "ten_god_relation", "interaction"],
        "vector_key": "ten_god_activity",
        "prior": 0.44,
    },
    "portrait.wealth.visibility": {
        "label_id": "portrait.wealth.visibility",
        "family": "wealth",
        "required_evidence": ["wealth_god_visible_or_hidden", "output_god_support", "source_layer"],
        "source_layers": ["natal", "hidden"],
        "confidence_rule": "visible_wealth_before_hidden_wealth; output_can_only_support_access_path",
        "question_hooks": ["q_income_stability", "q_income_factors", "q_income_path_structure"],
        "user_calibration_hooks": ["收入变化更常来自机会变多，还是来自执行承载、合作牵制或波动变化？"],
        "analyst_confirmation_hooks": ["财星可见度是透干、藏干还是时间触发？是否足以进入财富结构画像？"],
        "answer_kinds": ["income_structure", "career_structure"],
        "answer_boundary": "只说明财星结构素材是否容易观察，不断财富事件。",
        "topic_lanes": ["wealth_career_bridge", "ten_god_mechanism"],
        "domains": ["wealth", "income_stability", "ten_god_relation"],
        "vector_key": "wealth_visibility",
        "prior": 0.42,
    },
    "portrait.wealth.stability": {
        "label_id": "portrait.wealth.stability",
        "family": "wealth",
        "required_evidence": ["wealth_visibility", "capacity_strength", "branch_volatility", "peer_competition"],
        "source_layers": ["natal", "hidden", "time"],
        "confidence_rule": "wealth_stability_requires_visibility_plus_capacity_minus_volatility",
        "question_hooks": ["q_income_stability", "q_signal_combination", "q_income_path_structure"],
        "user_calibration_hooks": ["收入稳定性在不同阶段，是更稳定、周期性波动，还是受合作/竞争影响明显？"],
        "analyst_confirmation_hooks": ["财富稳定性是否同时核验了承载、牵制、比劫竞争和地支波动？"],
        "answer_kinds": ["income_structure", "career_structure"],
        "answer_boundary": "只能回答收入结构稳定性候选，不断发财破财。",
        "topic_lanes": ["wealth_career_bridge", "branch_time_activation"],
        "domains": ["wealth", "income_stability", "time_structure"],
        "vector_key": "wealth_stability",
        "prior": 0.4,
    },
    "portrait.branch.volatility": {
        "label_id": "portrait.branch.volatility",
        "family": "branch",
        "required_evidence": ["branch_relation", "relation_layer", "same_layer_or_time_trigger"],
        "source_layers": ["natal", "time"],
        "confidence_rule": "natal_relation_before_time_trigger; relation_name_requires_actual_pair",
        "question_hooks": ["q_branch_relation_detail", "q_time_vs_natal_relation", "q_time_context_boundary"],
        "user_calibration_hooks": ["出现明显转折的年份，更多对应关系、合作、迁动、分离，还是只是背景压力？"],
        "analyst_confirmation_hooks": ["冲合刑害是否发生在本命同层，还是只属于大运流年触发背景？"],
        "answer_kinds": ["branch_relation", "time_boundary", "structure_overview"],
        "answer_boundary": "冲合刑害只说明结构张力和牵动层级，不直接推出吉凶。",
        "topic_lanes": ["branch_time_activation"],
        "domains": ["structural_relation", "time_structure", "luck_flow"],
        "vector_key": "branch_volatility",
        "prior": 0.46,
    },
    "portrait.time.trigger": {
        "label_id": "portrait.time.trigger",
        "family": "time",
        "required_evidence": ["luck_cycle_or_flow_year", "relation_with_natal", "time_layer_boundary"],
        "source_layers": ["time"],
        "confidence_rule": "time_layer_triggers_context_but_never_rewrites_natal_structure",
        "question_hooks": ["q_time_context_boundary", "q_luck_flow_layers", "q_time_not_inference"],
        "user_calibration_hooks": ["某些大运或流年节点，你的状态变化是否明显，还是命盘结构本身更稳定？"],
        "analyst_confirmation_hooks": ["时间层是否只作为触发背景，没有被误读为改写本命结构？"],
        "answer_kinds": ["time_boundary", "branch_relation"],
        "answer_boundary": "大运流年只作为时间背景和触发候选，不改写本命结构。",
        "topic_lanes": ["branch_time_activation"],
        "domains": ["luck_flow", "time_structure", "timing"],
        "vector_key": "time_trigger_activity",
        "prior": 0.36,
    },
    "portrait.pattern.index": {
        "label_id": "portrait.pattern.index",
        "family": "pattern",
        "required_evidence": ["month_branch", "visible_ten_god", "formation_condition", "breaking_condition"],
        "source_layers": ["natal", "hidden"],
        "confidence_rule": "pattern_name_requires_index_then_same_layer_formation_breaking_review",
        "question_hooks": ["q_pattern_structure", "q_ten_god_focus", "q_strength_assessment"],
        "user_calibration_hooks": ["过往关键阶段更像按某个结构路径反复发生，还是不同主题分散出现？"],
        "analyst_confirmation_hooks": ["格局索引是否完成成格、破格和同层条件核验？"],
        "answer_kinds": ["pattern_structure", "career_structure", "structure_overview"],
        "answer_boundary": "格局只作为结构索引，不能把格局名直接翻成命运结论。",
        "topic_lanes": ["pattern_structure", "ten_god_mechanism"],
        "domains": ["pattern", "interaction", "career"],
        "vector_key": "pattern_index_strength",
        "prior": 0.4,
    },
}


def build_structure_portrait(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    chart = dict(agent_data.get("chart") or {})
    time_context = dict(agent_data.get("time_context") or {})
    inference_context = dict(agent_data.get("inference_context") or {})
    rule_graph_runtime_context = dict(agent_data.get("rule_graph_runtime_context") or {})
    facts = _chart_portrait_facts(chart, time_context)
    income = dict(inference_context.get("income_stability") or {})
    vectors = _portrait_vectors(facts, income, rule_graph_runtime_context)
    ontology = structure_portrait_label_ontology()
    labels = _compile_portrait_labels(facts, vectors, rule_graph_runtime_context)
    judgements = _candidate_judgements(labels, vectors)
    question_bias = _question_bias(vectors, labels)
    calibration_plan = _portrait_calibration_plan(labels)
    return {
        "ok": True,
        "version": STRUCTURE_PORTRAIT_VERSION,
        "label_ontology_version": PORTRAIT_LABEL_ONTOLOGY_VERSION,
        "status": "ready" if facts["pillar_count"] else "chart_facts_unavailable",
        "runtime_scope": "structure_portrait_context_only_no_result_mutation",
        "label_count": len(labels),
        "labels": labels,
        "label_ontology": {
            "version": ontology["version"],
            "label_count": ontology["label_count"],
            "scoring_model": ontology["scoring_model"],
        },
        "label_compilation": _label_compilation_summary(labels),
        "calibration_plan": calibration_plan,
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
        "label_ontology_version": portrait.get("label_ontology_version") or PORTRAIT_LABEL_ONTOLOGY_VERSION,
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
                "compiled_score": row.get("compiled_score"),
                "posterior_confidence": row.get("posterior_confidence"),
                "question_hooks": list(row.get("question_hooks") or [])[:4],
                "user_calibration_hooks": list(row.get("user_calibration_hooks") or [])[:2],
                "analyst_confirmation_hooks": list(row.get("analyst_confirmation_hooks") or [])[:2],
                "candidate_statement": row.get("candidate_statement") or "",
                "answer_boundary": row.get("answer_boundary") or "",
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


def _compile_portrait_labels(facts: Dict[str, Any], vectors: Dict[str, float], runtime_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    labels = [_compile_ontology_label(defn, facts, vectors, runtime_context) for defn in _LABEL_ONTOLOGY.values()]
    return sorted(labels, key=lambda row: (float(row.get("compiled_score") or row.get("score") or 0), float(row.get("confidence") or 0), str(row.get("label_id") or "")), reverse=True)


def _compile_ontology_label(defn: Dict[str, Any], facts: Dict[str, Any], vectors: Dict[str, float], runtime_context: Dict[str, Any]) -> Dict[str, Any]:
    label_id = str(defn.get("label_id") or "")
    vector_key = str(defn.get("vector_key") or "")
    vector_score = _clamp(vectors.get(vector_key, 0.0))
    evidence_score, evidence_hits = _evidence_axis_score(defn, facts, vectors)
    route_support, route_paths = _rule_graph_support(defn, runtime_context)
    value = _ontology_label_value(label_id, vectors)
    penalty = _label_penalty(label_id, value, facts, vectors)
    prior = _clamp(defn.get("prior", 0.4))
    compiled_score = _clamp(vector_score * 0.52 + evidence_score * 0.18 + route_support * 0.22 + prior * 0.08 - penalty)
    posterior = _bayesian_style_confidence(prior, vector_score, evidence_score, route_support, penalty)
    confidence = _clamp(vectors.get("evidence_confidence", 0.0) * 0.38 + posterior * 0.46 + route_support * 0.16 - penalty * 0.25)
    row = _label(
        label_id,
        str(defn.get("family") or ""),
        value,
        compiled_score,
        confidence,
        _evidence_refs_for_label(label_id),
        _candidate_statement_for_label(label_id),
    )
    row.update(
        {
            "ontology_version": PORTRAIT_LABEL_ONTOLOGY_VERSION,
            "compiled_score": round(compiled_score, 3),
            "posterior_confidence": round(posterior, 3),
            "score_breakdown": {
                "prior": round(prior, 3),
                "vector_score": round(vector_score, 3),
                "evidence_score": round(evidence_score, 3),
                "rule_graph_support": round(route_support, 3),
                "penalty": round(penalty, 3),
                "model": "deterministic_evidence_plus_internal_bayesian_style_confidence",
            },
            "required_evidence": list(defn.get("required_evidence") or []),
            "evidence_hits": evidence_hits,
            "source_layers": list(defn.get("source_layers") or []),
            "confidence_rule": defn.get("confidence_rule") or "",
            "question_hooks": list(defn.get("question_hooks") or []),
            "user_calibration_hooks": list(defn.get("user_calibration_hooks") or []),
            "analyst_confirmation_hooks": list(defn.get("analyst_confirmation_hooks") or []),
            "answer_kinds": list(defn.get("answer_kinds") or []),
            "answer_boundary": defn.get("answer_boundary") or "",
            "knowledge_evidence_ids": [str(row.get("knowledge_id") or "") for row in route_paths if row.get("knowledge_id")][:6],
            "rule_evidence_ids": [str(row.get("candidate_rule_id") or "") for row in route_paths if row.get("candidate_rule_id")][:6],
            "runtime_scope": "ontology_compiled_structure_label_context_only_no_verdict",
        }
    )
    return row


def _ontology_label_value(label_id: str, vectors: Dict[str, float]) -> str:
    if label_id == "portrait.strength.capacity_candidate":
        return _capacity_value(vectors["strength_capacity"])
    if label_id == "portrait.useful_god.candidate_boundary":
        return "candidate_only" if vectors["useful_god_candidate_confidence"] >= 0.45 else "insufficient_evidence"
    if label_id == "portrait.ten_god.activity":
        return "active" if vectors["ten_god_activity"] >= 0.55 else "limited"
    if label_id == "portrait.wealth.visibility":
        return "visible" if vectors["wealth_visibility"] >= 0.45 else "weak_or_hidden"
    if label_id == "portrait.wealth.stability":
        return "stable_candidate" if vectors["wealth_stability"] >= 0.55 else "stability_needs_review"
    if label_id == "portrait.branch.volatility":
        return "active" if vectors["branch_volatility"] >= 0.4 else "quiet"
    if label_id == "portrait.time.trigger":
        return "trigger_context" if vectors["time_trigger_activity"] >= 0.25 else "background_only"
    if label_id == "portrait.pattern.index":
        return "index_candidate" if vectors["pattern_index_strength"] >= 0.45 else "insufficient_index"
    return "candidate_only"


def _evidence_axis_score(defn: Dict[str, Any], facts: Dict[str, Any], vectors: Dict[str, float]) -> Tuple[float, List[str]]:
    axes = [str(item) for item in defn.get("required_evidence") or [] if str(item)]
    if not axes:
        return 0.0, []
    hits = [axis for axis in axes if _evidence_axis_present(axis, facts, vectors)]
    return _clamp(len(hits) / max(len(axes), 1)), hits


def _evidence_axis_present(axis: str, facts: Dict[str, Any], vectors: Dict[str, float]) -> bool:
    if axis == "day_stem":
        return bool(facts.get("day_stem"))
    if axis == "month_branch":
        return bool(facts.get("month_branch"))
    if axis == "hidden_stems":
        return bool(facts.get("hidden_stems"))
    if axis == "same_element_or_resource":
        return bool(facts.get("resource_count")) or vectors.get("strength_capacity", 0) >= 0.5
    if axis == "strength_capacity":
        return "strength_capacity" in vectors
    if axis == "five_element_flow":
        return bool(facts.get("day_element") and facts.get("stems"))
    if axis == "same_layer_action":
        return bool(facts.get("ten_gods") or facts.get("relation_types"))
    if axis == "rescue_or_constraint_path":
        return bool(facts.get("resource_count") or facts.get("officer_count") or facts.get("relation_types"))
    if axis == "visible_stems":
        return len(facts.get("stems") or []) >= 2
    if axis == "ten_god_mapping":
        return bool(facts.get("ten_gods"))
    if axis == "wealth_god_visible_or_hidden":
        return bool(facts.get("wealth_count"))
    if axis == "output_god_support":
        return bool(facts.get("output_count")) or bool(facts.get("wealth_count"))
    if axis == "source_layer":
        return bool(facts.get("pillar_count"))
    if axis == "wealth_visibility":
        return vectors.get("wealth_visibility", 0) > 0
    if axis == "capacity_strength":
        return "strength_capacity" in vectors
    if axis == "branch_volatility":
        return "branch_volatility" in vectors
    if axis == "peer_competition":
        return facts.get("peer_count", 0) >= 0
    if axis == "branch_relation":
        return bool(facts.get("relation_types") or facts.get("time_relation_count"))
    if axis == "relation_layer":
        return bool(facts.get("relation_types") or facts.get("time_relation_count"))
    if axis == "same_layer_or_time_trigger":
        return bool(facts.get("relation_types") or facts.get("time_relation_count"))
    if axis == "luck_cycle_or_flow_year":
        return bool(facts.get("time_branches"))
    if axis == "relation_with_natal":
        return bool(facts.get("time_relation_count"))
    if axis == "time_layer_boundary":
        return bool(facts.get("time_branches") or facts.get("time_relation_count"))
    if axis == "visible_ten_god":
        return bool(facts.get("ten_gods"))
    if axis == "formation_condition":
        return bool(facts.get("month_branch") and vectors.get("ten_god_activity", 0) > 0)
    if axis == "breaking_condition":
        return "branch_volatility" in vectors
    return False


def _rule_graph_support(defn: Dict[str, Any], runtime_context: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
    topic_lanes = {str(item) for item in defn.get("topic_lanes") or [] if str(item)}
    domains = {str(item) for item in defn.get("domains") or [] if str(item)}
    selected = [dict(row) for row in runtime_context.get("selected_paths") or [] if isinstance(row, dict)]
    relevant = [
        row
        for row in selected
        if str(row.get("topic_lane") or "") in topic_lanes or str(row.get("domain") or "") in domains
    ]
    if not relevant:
        return 0.0, []
    scores = [_clamp(float(row.get("score") or 0) / 100.0) for row in relevant[:6]]
    support = _clamp((sum(scores[:3]) / max(min(len(scores), 3), 1)) * min(len(relevant), 4) / 4 + 0.12)
    return support, relevant[:6]


def _label_penalty(label_id: str, value: str, facts: Dict[str, Any], vectors: Dict[str, float]) -> float:
    penalty = 0.0
    if value in {"insufficient_evidence", "insufficient_index", "background_only", "weak_or_hidden", "limited"}:
        penalty += 0.08
    if label_id == "portrait.useful_god.candidate_boundary" and vectors.get("useful_god_candidate_confidence", 0) < 0.65:
        penalty += 0.05
    if label_id == "portrait.time.trigger" and not facts.get("time_relation_count"):
        penalty += 0.04
    return _clamp(penalty)


def _bayesian_style_confidence(prior: float, vector_score: float, evidence_score: float, route_support: float, penalty: float) -> float:
    likelihood = _clamp(vector_score * 0.45 + evidence_score * 0.35 + route_support * 0.2)
    prior = _clamp(prior)
    numerator = prior * max(likelihood, 0.01)
    denominator = numerator + (1 - prior) * max(1 - likelihood, 0.01)
    if denominator <= 0:
        return 0.0
    return _clamp((numerator / denominator) - penalty)


def _evidence_refs_for_label(label_id: str) -> List[str]:
    return {
        "portrait.strength.capacity_candidate": ["chart.day_stem", "chart.month_branch", "chart.hidden_stems", "rule_graph.core_strength_foundation"],
        "portrait.useful_god.candidate_boundary": ["portrait.strength_capacity", "chart.elements", "chart.relations", "rule_graph.core_strength_foundation"],
        "portrait.ten_god.activity": ["chart.visible_stems", "chart.hidden_stems", "ten_god.mapping", "rule_graph.ten_god_mechanism"],
        "portrait.wealth.visibility": ["ten_god.wealth", "ten_god.output", "rule_graph.wealth_career_bridge"],
        "portrait.wealth.stability": ["inference_context.income_stability", "chart.branch_relations", "rule_graph.wealth_career_bridge"],
        "portrait.branch.volatility": ["chart.relations", "time_context.relations_with_natal", "rule_graph.branch_time_activation"],
        "portrait.time.trigger": ["time_context.luck_cycle", "time_context.flow_year", "rule_graph.branch_time_activation"],
        "portrait.pattern.index": ["chart.month_branch", "ten_god.mapping", "chart.relations", "rule_graph.pattern_structure"],
    }.get(label_id, ["structure_portrait.ontology"])


def _candidate_statement_for_label(label_id: str) -> str:
    return {
        "portrait.strength.capacity_candidate": "日主强弱先作为承载证据候选，需要月令、透藏、根气和克泄耗共同验证。",
        "portrait.useful_god.candidate_boundary": "用神忌神只进入候选路径，不直接给喜忌硬结论。",
        "portrait.ten_god.activity": "十神活跃度用于选择财官印食伤等观察入口。",
        "portrait.wealth.visibility": "财星可见度只说明财富结构素材是否容易被观察，不是财富结论。",
        "portrait.wealth.stability": "收入稳定性只能作为结构归因候选，需要看承载、牵制和波动。",
        "portrait.branch.volatility": "冲合刑害破和时间触发用于提示结构张力，不直接推出结果。",
        "portrait.time.trigger": "大运流年只作为时间背景和触发候选，不改写本命结构。",
        "portrait.pattern.index": "格局先作为结构索引，不把格局名直接翻成命运判断。",
    }.get(label_id, "结构画像标签只用于证据排序和问题路径选择，不直接生成结果断语。")


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
    bucket_for_family = {
        "strength": "strength_useful_god",
        "useful_god": "strength_useful_god",
        "wealth": "income_stability",
        "branch": "branch_relation",
        "time": "time_context",
        "pattern": "pattern_structure",
        "ten_god": "metadata",
    }
    for label in labels:
        family = str(label.get("family") or "")
        bucket = bucket_for_family.get(family)
        label_weight = float(label.get("compiled_score") or label.get("score") or 0) * 12 + float(label.get("posterior_confidence") or label.get("confidence") or 0) * 5
        if bucket:
            bucket_boosts[bucket] = round(max(float(bucket_boosts.get(bucket) or 0), float(bucket_boosts.get(bucket) or 0) + label_weight * 0.12), 3)
        for key in label.get("question_hooks") or []:
            if not str(key):
                continue
            question_boosts[str(key)] = round(max(float(question_boosts.get(str(key)) or 0), label_weight + float(bucket_boosts.get(bucket or "") or 0) * 0.2), 3)
    ordered_questions = [key for key, _value in sorted(question_boosts.items(), key=lambda row: row[1], reverse=True)]
    return {
        "runtime_scope": "question_ranking_bias_only_no_result_mutation",
        "label_ontology_version": PORTRAIT_LABEL_ONTOLOGY_VERSION,
        "bucket_boosts": bucket_boosts,
        "question_boosts": {key: round(value, 3) for key, value in question_boosts.items()},
        "recommended_question_keys": ordered_questions[:6],
        "dominant_label_ids": [str(row.get("label_id") or "") for row in labels[:5]],
        "label_driven": True,
    }


def _label_compilation_summary(labels: List[Dict[str, Any]]) -> Dict[str, Any]:
    knowledge_ids = []
    for label in labels:
        for knowledge_id in label.get("knowledge_evidence_ids") or []:
            if knowledge_id and knowledge_id not in knowledge_ids:
                knowledge_ids.append(str(knowledge_id))
    return {
        "version": PORTRAIT_LABEL_ONTOLOGY_VERSION,
        "status": "compiled",
        "runtime_scope": "label_compilation_audit_only_no_result_mutation",
        "label_count": len(labels),
        "families": sorted({str(row.get("family") or "") for row in labels if row.get("family")}),
        "knowledge_evidence_count": len(knowledge_ids),
        "knowledge_evidence_ids": knowledge_ids[:12],
        "min_compiled_score": round(min([float(row.get("compiled_score") or 0) for row in labels] or [0]), 3),
        "max_compiled_score": round(max([float(row.get("compiled_score") or 0) for row in labels] or [0]), 3),
        "engine_enabled_count": 0,
        "runtime_mutation": False,
    }


def _portrait_calibration_plan(labels: List[Dict[str, Any]]) -> Dict[str, Any]:
    ranked = sorted(
        [dict(row) for row in labels if isinstance(row, dict)],
        key=lambda row: (float(row.get("compiled_score") or 0), float(row.get("posterior_confidence") or 0)),
        reverse=True,
    )
    user_hooks: List[Dict[str, Any]] = []
    analyst_hooks: List[Dict[str, Any]] = []
    for row in ranked:
        for text in row.get("user_calibration_hooks") or []:
            if text and len(user_hooks) < 5:
                user_hooks.append(_calibration_hook(row, str(text), "user_event_feedback"))
        for text in row.get("analyst_confirmation_hooks") or []:
            if text and len(analyst_hooks) < 5:
                analyst_hooks.append(_calibration_hook(row, str(text), "analyst_confirmation"))
        if len(user_hooks) >= 5 and len(analyst_hooks) >= 5:
            break
    return {
        "version": PORTRAIT_CALIBRATION_VERSION,
        "status": "ready" if ranked else "no_labels",
        "runtime_scope": "portrait_calibration_hooks_only_no_rule_mutation",
        "user_hooks": user_hooks,
        "analyst_hooks": analyst_hooks,
        "hidden_factor_slots": [
            "baseline_amplifier",
            "action_efficiency",
            "event_sensitivity",
            "domain_activation_bias",
        ],
        "feedback_update_policy": "feedback_may_adjust_portrait_confidence_and_question_order_only; rule_updates_require_synthetic_validation",
        "guardrails": [
            "INTERACTIVE_CALIBRATION_CONTEXT_ONLY",
            "USER_FEEDBACK_DOES_NOT_MUTATE_RULES",
            "ANALYST_CONFIRMATION_IS_AUDIT_SIGNAL",
            "NO_PREDICTION_FROM_EVENT_FEEDBACK",
        ],
    }


def _calibration_hook(label: Dict[str, Any], text: str, hook_type: str) -> Dict[str, Any]:
    return {
        "hook_id": f"{hook_type}.{label.get('label_id')}",
        "label_id": label.get("label_id") or "",
        "family": label.get("family") or "",
        "question": text,
        "hook_type": hook_type,
        "compiled_score": label.get("compiled_score"),
        "posterior_confidence": label.get("posterior_confidence"),
        "update_target": "structure_portrait_confidence_only",
        "runtime_mutation": False,
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
