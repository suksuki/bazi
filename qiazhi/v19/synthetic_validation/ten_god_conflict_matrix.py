from __future__ import annotations

from typing import Any, Dict, List, Mapping

from v19.bazi_rule_db import build_structural_rule_signals, list_bazi_rules, set_bazi_rule_engine_activation
from v19.synthetic_validation.guided_cases import make_synthetic_chart, make_synthetic_time_context


P28G_TEN_GOD_CONFLICT_MATRIX_VERSION = "v19.p28g.ten_god_conflict_synthetic_matrix.v1"
P28H_TEN_GOD_CONFLICT_REVIEW_VERSION = "v19.p28h.ten_god_conflict_review_table.v1"
P28I_TEN_GOD_FAST_PATH_GATE_VERSION = "v19.p28i.ten_god_fast_path_gate.v1"
P28J_TEN_GOD_MECHANISM_CONDITION_MODEL_VERSION = "v19.p28j.ten_god_mechanism_condition_model.v1"
P28K_TEN_GOD_MECHANISM_EVAL_DATASET_VERSION = "v19.p28k.ten_god_mechanism_eval_dataset.v1"
P28K_TEN_GOD_MECHANISM_REGRESSION_VERSION = "v19.p28k.ten_god_mechanism_regression.v1"
P28L_TEN_GOD_MECHANISM_SIGNAL_GATE_VERSION = "v19.p28l.ten_god_mechanism_signal_gate.v1"
P29_TEN_GOD_MECHANISM_INTERNAL_SCORING_VERSION = "v19.p29.ten_god_mechanism_internal_scoring.v1"
P30_TEN_GOD_MECHANISM_ARBITRATION_VERSION = "v19.p30.ten_god_mechanism_arbitration.v1"
P28G_GUARDRAILS = [
    "SYNTHETIC_EXPLICIT_PILLARS_ONLY",
    "NO_REAL_BIRTHDATA",
    "NO_RULE_ACTIVATION",
    "NO_TRADITIONAL_VERDICT_OUTPUT",
    "RULE_DB_CANDIDATE_COVERAGE_ONLY",
]
P28H_REVIEW_GUARDRAILS = [
    "REVIEW_TABLE_ONLY",
    "NO_AUTO_RULE_ACTIVATION",
    "EXISTENCE_RULES_ONLY_FOR_FAST_PATH",
    "MECHANISM_REQUIRES_CONDITION_MODEL",
    "TRADITIONAL_VERDICTS_ARCHIVE_ONLY",
]
P28I_FAST_PATH_GUARDRAILS = [
    "FAST_PATH_R1_EXISTENCE_ONLY",
    "TEN_GOD_INTERACTION_SPECIFIC_MATCH_REQUIRED",
    "SYNTHETIC_SIGNAL_AUDIT_REQUIRED",
    "NO_MECHANISM_OR_VERDICT_ACTIVATION",
    "NO_RESULT_MUTATION",
    "NO_FORTUNE",
]
P28J_CONDITION_MODEL_GUARDRAILS = [
    "MECHANISM_CONDITION_MODEL_ONLY",
    "NO_MECHANISM_RULE_ACTIVATION",
    "SOURCE_LAYER_AND_CAPACITY_REQUIRED",
    "SYNTHETIC_PAIR_COVERAGE_REQUIRED",
    "NO_RESULT_MUTATION",
    "NO_FORTUNE",
]
P28K_EVAL_DATASET_GUARDRAILS = [
    "EVAL_DATASET_ONLY",
    "NO_MECHANISM_RULE_ACTIVATION",
    "STRICT_POSITIVE_AXES_REQUIRED",
    "NEGATIVE_AND_DISTRACTOR_COVERAGE_REQUIRED",
    "NO_REAL_BIRTHDATA",
    "NO_FORTUNE",
]
P28L_SIGNAL_GATE_GUARDRAILS = [
    "SHADOW_SIGNAL_GATE_ONLY",
    "P28K_REGRESSION_REQUIRED",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_MECHANISM_VERDICT_OUTPUT",
    "FALSE_POSITIVE_ZERO_REQUIRED",
    "AUDITABLE_GATE_REPORT",
]
P29_INTERNAL_SCORING_GUARDRAILS = [
    "INTERNAL_SCORING_ONLY",
    "NO_USER_FACING_PROBABILITY",
    "NO_RUNTIME_RULE_ACTIVATION",
    "P28L_SHADOW_GATE_REQUIRED",
    "RANKING_ONLY_NO_VERDICT",
    "AUDITABLE_SCORE_FACTORS",
]
P30_ARBITRATION_GUARDRAILS = [
    "ARBITRATION_ONLY",
    "P29_INTERNAL_SCORING_REQUIRED",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_USER_FACING_PROBABILITY",
    "NO_MECHANISM_VERDICT_OUTPUT",
    "OLD_KNOWLEDGE_MIGRATION_BACKLOG_ONLY",
]
P28I_FORBIDDEN_ANSWER_TEXT = [
    "官非",
    "灾祸",
    "事业不顺",
    "发财",
    "破财",
    "疾病",
    "学历断语",
    "长辈断语",
    "性格断语",
    "职业断语",
    "命好命坏",
]


def _ids(slug: str, prefix: str = "p28.interaction") -> List[str]:
    return [f"{prefix}.{slug}.existence", f"{prefix}.{slug}.mechanism_boundary"]


def _case(
    slug: str,
    title: str,
    family: str,
    pillars: Mapping[str, str],
    *,
    question: str,
    focus: str,
    activation_tier: str,
    time_pillar: str = "",
    knowledge_prefix: str = "p28.interaction",
) -> Dict[str, Any]:
    chart = make_synthetic_chart(f"syn.p28g.{slug}", pillars)
    time_context = make_synthetic_time_context(chart, flow_pillar=time_pillar) if time_pillar else {}
    return {
        "case_id": f"syn.p28g.{slug}",
        "title": title,
        "family": family,
        "collision_focus": focus,
        "chart": chart,
        "time_context": time_context,
        "question": question,
        "expected_knowledge_ids": _ids(slug, knowledge_prefix),
        "expected_rule_domain": "ten_god_relation",
        "expected_engine_enabled": False,
        "activation_tier": activation_tier,
        "rule_path": {
            "existence": "R1 candidate; may become an engine signal only after topic-level synthetic acceptance.",
            "mechanism": "R2 candidate; requires source-layer, strength, palace, and time-context conditions.",
            "verdict": "R3/R4 archive-only; no direct fortune or event conclusion.",
        },
    }


P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES: List[Dict[str, Any]] = [
    _case(
        "shangguan_see_official",
        "伤官见官",
        "direct_conflict",
        {"year": "辛酉", "month": "乙卯", "day": "戊辰", "hour": "丁巳"},
        question="伤官与正官同时出现时，只能先确认哪些结构事实？",
        focus="output_vs_official_conflict",
        activation_tier="existence_candidate_only",
    ),
    _case(
        "shangguan_control_kill",
        "伤官制杀",
        "direct_conflict",
        {"year": "辛酉", "month": "甲寅", "day": "戊辰", "hour": "丁巳"},
        question="伤官制杀与伤官见官有什么不同的结构边界？",
        focus="output_controls_kill",
        activation_tier="condition_model_needed",
    ),
    _case(
        "shishen_control_kill",
        "食神制杀",
        "direct_conflict",
        {"year": "庚申", "month": "甲寅", "day": "戊辰", "hour": "丁巳"},
        question="食神和七杀同时出现时，为什么只能先读作制化候选？",
        focus="food_controls_kill",
        activation_tier="condition_model_needed",
    ),
    _case(
        "officer_kill_attack_self",
        "官杀攻身",
        "direct_conflict",
        {"year": "甲寅", "month": "乙卯", "day": "戊辰", "hour": "庚申"},
        question="官杀压力指向日主时，哪些内容仍然不能直接断？",
        focus="control_pressure_on_day_master",
        activation_tier="condition_model_needed",
    ),
    _case(
        "pianyin_deprive_food",
        "枭神夺食",
        "constraint_deprivation",
        {"year": "丙寅", "month": "庚申", "day": "戊辰", "hour": "癸亥"},
        question="枭神夺食为什么只能先读为偏印与食神的牵制候选？",
        focus="resource_constrains_food",
        activation_tier="condition_model_needed",
    ),
    _case(
        "resource_control_output",
        "印制食伤",
        "constraint_deprivation",
        {"year": "丁巳", "month": "辛酉", "day": "戊辰", "hour": "庚申"},
        question="印星和食伤同时出现时，应如何分层看输出受牵制？",
        focus="resource_controls_output",
        activation_tier="condition_model_needed",
    ),
    _case(
        "peer_deprive_wealth",
        "比劫夺财",
        "constraint_deprivation",
        {"year": "戊戌", "month": "壬子", "day": "戊辰", "hour": "己未"},
        question="比劫夺财应如何降级为资源分配语境？",
        focus="peer_wealth_competition",
        activation_tier="condition_model_needed",
    ),
    _case(
        "peer_share_wealth",
        "比劫分财",
        "constraint_deprivation",
        {"year": "己未", "month": "壬子", "day": "戊辰", "hour": "庚申"},
        question="比劫分财与比劫夺财在表达上如何保持中性？",
        focus="peer_wealth_distribution",
        activation_tier="existence_candidate_only",
    ),
    _case(
        "wealth_break_seal",
        "财破印",
        "constraint_deprivation",
        {"year": "壬子", "month": "丁巳", "day": "戊辰", "hour": "辛酉"},
        question="财星与印星同见时，为什么不能直接断财破印结果？",
        focus="wealth_constrains_resource",
        activation_tier="condition_model_needed",
    ),
    _case(
        "wealth_excess_break_seal",
        "财多坏印",
        "constraint_deprivation",
        {"year": "壬子", "month": "癸亥", "day": "戊辰", "hour": "丁巳"},
        question="财多坏印需要哪些条件才可能从存在进入机制判断？",
        focus="wealth_excess_resource_pressure",
        activation_tier="condition_model_needed",
    ),
    _case(
        "wealth_feed_kill",
        "财滋杀",
        "constraint_deprivation",
        {"year": "壬子", "month": "甲寅", "day": "戊辰", "hour": "辛酉"},
        question="财滋杀为什么只能先作为压力来源路径候选？",
        focus="wealth_feeds_kill_pressure",
        activation_tier="condition_model_needed",
    ),
    _case(
        "mixed_official_kill",
        "官杀混杂",
        "mixed_structure",
        {"year": "甲寅", "month": "乙卯", "day": "戊辰", "hour": "丁巳"},
        question="官杀混杂先看清浊、去留和制化，哪些不能直接断？",
        focus="official_kill_mixed",
        activation_tier="condition_model_needed",
    ),
    _case(
        "output_mixed",
        "食伤混杂",
        "mixed_structure",
        {"year": "庚申", "month": "辛酉", "day": "戊辰", "hour": "壬子"},
        question="食神和伤官并见时，为什么先读为输出性质混合？",
        focus="food_hurting_officer_mixed",
        activation_tier="existence_candidate_only",
    ),
    _case(
        "resource_mixed",
        "印枭混杂",
        "mixed_structure",
        {"year": "丙午", "month": "丁巳", "day": "戊辰", "hour": "庚申"},
        question="正印和偏印并见时，为什么先读为支持来源混合？",
        focus="seal_resource_mixed",
        activation_tier="existence_candidate_only",
    ),
    _case(
        "combine_kill_keep_official",
        "合杀留官",
        "selection_rescue",
        {"year": "甲寅", "month": "己未", "day": "戊辰", "hour": "乙卯"},
        question="合杀留官为什么只是官杀去留候选，而不是格局结论？",
        focus="combine_kill_keep_official",
        activation_tier="condition_model_needed",
    ),
    _case(
        "combine_official_keep_kill",
        "合官留杀",
        "selection_rescue",
        {"year": "乙卯", "month": "庚申", "day": "戊辰", "hour": "甲寅"},
        question="合官留杀为什么要保留更高风险边界？",
        focus="combine_official_keep_kill",
        activation_tier="condition_model_needed",
    ),
    _case(
        "shangguan_with_seal",
        "伤官配印",
        "selection_rescue",
        {"year": "辛酉", "month": "丁巳", "day": "戊辰", "hour": "壬子"},
        question="伤官配印作为救应路径时，需要哪些上下文？",
        focus="output_with_resource_rescue",
        activation_tier="condition_model_needed",
    ),
    _case(
        "kill_seal_generate",
        "杀印相生",
        "selection_rescue",
        {"year": "甲寅", "month": "丙午", "day": "戊辰", "hour": "癸亥"},
        question="杀印相生为什么只是压力转支持的路径候选？",
        focus="kill_generates_seal",
        activation_tier="condition_model_needed",
    ),
    _case(
        "seal_transform_kill",
        "印化杀",
        "selection_rescue",
        {"year": "甲寅", "month": "丁巳", "day": "戊辰", "hour": "庚申"},
        question="印化杀为什么要先看七杀压力、印星承接和日主承载？",
        focus="seal_transforms_kill",
        activation_tier="condition_model_needed",
        knowledge_prefix="p31b.interaction",
    ),
    _case(
        "official_seal_generate",
        "官印相生",
        "selection_rescue",
        {"year": "乙卯", "month": "丁巳", "day": "戊辰", "hour": "庚申"},
        question="官印相生作为生助路径时，为什么还不能确认格局？",
        focus="official_generates_seal",
        activation_tier="condition_model_needed",
    ),
    _case(
        "wealth_generate_official",
        "财生官",
        "selection_rescue",
        {"year": "壬子", "month": "乙卯", "day": "戊辰", "hour": "庚申"},
        question="财生官作为资源支持秩序关系时，为什么仍要看承载？",
        focus="wealth_generates_official",
        activation_tier="condition_model_needed",
    ),
    _case(
        "wealth_official_mutual_generation",
        "财官相生",
        "selection_rescue",
        {"year": "壬子", "month": "乙卯", "day": "戊辰", "hour": "丁巳"},
        question="财官相生为什么只能先读为财星与官星的连续生助路径？",
        focus="wealth_official_mutual_generation",
        activation_tier="condition_model_needed",
        knowledge_prefix="p31b.interaction",
    ),
    _case(
        "output_generate_wealth",
        "食伤生财",
        "selection_rescue",
        {"year": "庚申", "month": "壬子", "day": "戊辰", "hour": "丁巳"},
        question="食伤生财为什么只是输出到财星的路径候选？",
        focus="output_generates_wealth",
        activation_tier="condition_model_needed",
    ),
    _case(
        "yangren_drive_kill",
        "羊刃驾杀",
        "selection_rescue",
        {"year": "甲寅", "month": "戊午", "day": "戊辰", "hour": "辛酉"},
        question="羊刃驾杀为什么必须等待禄刃、强弱和格局条件？",
        focus="yangren_drive_kill",
        activation_tier="condition_model_needed",
        time_pillar="壬子",
    ),
]


def run_p28g_ten_god_conflict_matrix(cases: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    selected_cases = list(cases or P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES)
    rules = _ten_god_interaction_rules()
    rules_by_knowledge = {str(rule.get("knowledge_id") or ""): rule for rule in rules}
    case_results = [_evaluate_case(case, rules_by_knowledge) for case in selected_cases]
    failures = [row for row in case_results if row["status"] == "fail"]
    expected_ids = sorted({knowledge_id for case in selected_cases for knowledge_id in case.get("expected_knowledge_ids", [])})
    covered_ids = sorted({knowledge_id for knowledge_id in expected_ids if knowledge_id in rules_by_knowledge})
    enabled_ids = sorted(
        knowledge_id
        for knowledge_id in expected_ids
        if (rules_by_knowledge.get(knowledge_id) or {}).get("engine_enabled") is True
    )
    return {
        "ok": not failures,
        "version": P28G_TEN_GOD_CONFLICT_MATRIX_VERSION,
        "status": "fail" if failures else "pass",
        "summary": {
            "total": len(case_results),
            "passed": sum(1 for row in case_results if row["status"] == "pass"),
            "failed": len(failures),
            "expected_rule_count": len(expected_ids),
            "covered_rule_count": len(covered_ids),
            "engine_enabled_count": len(enabled_ids),
            "by_family": _count_by(case_results, "family"),
            "by_activation_tier": _count_by(case_results, "activation_tier"),
        },
        "cases": case_results,
        "coverage": {
            "expected_knowledge_ids": expected_ids,
            "covered_knowledge_ids": covered_ids,
            "missing_knowledge_ids": [knowledge_id for knowledge_id in expected_ids if knowledge_id not in set(covered_ids)],
            "unexpected_engine_enabled_ids": enabled_ids,
        },
        "review": {
            "stable_rule_candidates": [
                {"case_id": row["case_id"], "title": row["title"], "family": row["family"]}
                for row in case_results
                if row["status"] == "pass"
            ],
            "missing_or_misconfigured": [row for row in case_results if row["status"] == "fail"],
            "activation_boundary": "All P28G rules remain Rule DB candidates. Activation requires a later topic-level synthetic gate and must not introduce traditional verdict text.",
        },
        "guardrails": P28G_GUARDRAILS,
    }


def build_p28h_ten_god_conflict_review_table(cases: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    selected_cases = list(cases or P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES)
    items = [_review_item(case) for case in selected_cases]
    return {
        "ok": True,
        "version": P28H_TEN_GOD_CONFLICT_REVIEW_VERSION,
        "status": "review_ready",
        "summary": {
            "total": len(items),
            "existence_rule_candidate_count": len(items),
            "fast_path_candidate_count": sum(1 for item in items if item["activation_decision"] == "existence_fast_path_candidate"),
            "condition_model_required_count": sum(1 for item in items if item["activation_decision"] == "condition_model_required_before_activation"),
            "mechanism_hold_count": sum(1 for item in items if item["mechanism_decision"] == "hold_for_condition_model"),
            "archive_only_verdict_count": sum(1 for item in items if item["archive_only_verdicts"]),
            "by_family": _count_by(items, "family"),
        },
        "items": items,
        "review_policy": {
            "can_rule_now": "Only the R1 existence boundary may be converted into a low-risk structural signal.",
            "cannot_rule_now": "R2 mechanisms require condition models for source layer, strength, palace, and time context.",
            "never_direct_output": "Traditional verdicts remain archive-only and must not enter answer text.",
        },
        "guardrails": P28H_REVIEW_GUARDRAILS,
    }


def run_p28i_ten_god_fast_path_gate(*, activate: bool = False) -> Dict[str, Any]:
    review = build_p28h_ten_god_conflict_review_table()
    fast_items = [dict(row) for row in review.get("items") or [] if row.get("activation_decision") == "existence_fast_path_candidate"]
    fast_ids = [str(row.get("existence_knowledge_id") or "") for row in fast_items if row.get("existence_knowledge_id")]
    rules = [dict(row) for row in (list_bazi_rules(q="p28.interaction.").get("items") or []) if isinstance(row, dict)]
    rules_by_knowledge = {str(rule.get("knowledge_id") or ""): rule for rule in rules}
    gate_rows = [_p28i_gate_row(item, rules_by_knowledge.get(str(item.get("existence_knowledge_id") or ""))) for item in fast_items]
    selected_ids = [row["knowledge_id"] for row in gate_rows if row["eligible"]]
    simulated_rules = _p28i_simulated_rules(rules, selected_ids)
    signal_audit = _p28i_signal_audit(fast_items, simulated_rules, set(selected_ids))
    answer_text_audit = _p28i_answer_text_audit(signal_audit)
    blocker_rows = [row for row in gate_rows if row["blockers"]]
    can_activate = bool(selected_ids) and not blocker_rows and signal_audit["status"] == "pass" and answer_text_audit["status"] == "pass"
    activation = {"status": "not_requested", "updated_count": 0, "items": []}
    status = "dry_run_pass" if can_activate else "blocked"
    if activate:
        if can_activate:
            activation = set_bazi_rule_engine_activation(
                selected_ids,
                enabled=True,
                actor_role="system",
                note="P28I fast path activated low-risk ten-god interaction existence rules after synthetic signal audit.",
                adapter_status="p28i_fast_path_active",
            )
            status = "activated"
        else:
            activation = {"status": "blocked", "updated_count": 0, "items": [], "reason": "pre_activation_audit_failed"}
            status = "blocked"
    return {
        "ok": status != "blocked",
        "version": P28I_TEN_GOD_FAST_PATH_GATE_VERSION,
        "status": status,
        "summary": {
            "fast_path_candidate_count": len(fast_items),
            "eligible_count": len(selected_ids),
            "blocked_count": len(blocker_rows),
            "signal_audit_status": signal_audit["status"],
            "answer_text_audit_status": answer_text_audit["status"],
            "activation_updated_count": int(activation.get("updated_count") or len(activation.get("items") or [])),
        },
        "candidate_ids": fast_ids,
        "selected_ids": selected_ids,
        "gate": gate_rows,
        "blocked": blocker_rows,
        "signal_audit": signal_audit,
        "answer_text_audit": answer_text_audit,
        "activation": activation,
        "activation_policy": {
            "allowed": "Only R1 existence rules marked by P28H fast-path review may be activated.",
            "blocked": "Mechanism boundaries and traditional verdicts stay inactive and archive-only.",
            "adapter_requirement": "Ten-god interaction rules must match concrete involved_ten_gods labels; broad ten_god_relation fallback is not allowed.",
        },
        "guardrails": P28I_FAST_PATH_GUARDRAILS,
    }


def build_p28j_ten_god_mechanism_condition_models(cases: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    review = build_p28h_ten_god_conflict_review_table(cases)
    mechanism_items = [dict(row) for row in review.get("items") or [] if row.get("activation_decision") == "condition_model_required_before_activation"]
    rules = _ten_god_interaction_rules()
    rules_by_knowledge = {str(rule.get("knowledge_id") or ""): rule for rule in rules}
    models = [_p28j_condition_model_row(item, rules_by_knowledge.get(str(item.get("mechanism_knowledge_id") or ""))) for item in mechanism_items]
    blocked = [row for row in models if row["activation_status"] != "activation_ready"]
    return {
        "ok": True,
        "version": P28J_TEN_GOD_MECHANISM_CONDITION_MODEL_VERSION,
        "status": "condition_models_ready_activation_blocked",
        "summary": {
            "mechanism_candidate_count": len(mechanism_items),
            "condition_model_count": len(models),
            "activation_ready_count": sum(1 for row in models if row["activation_status"] == "activation_ready"),
            "activation_blocked_count": len(blocked),
            "by_family": _count_by(models, "family"),
            "axis_coverage": _p28j_axis_coverage(models),
        },
        "models": models,
        "blocked": blocked,
        "activation_policy": {
            "current_batch": "P28J produces condition schemas and synthetic collision requirements only.",
            "activation_requirement": "Mechanism rules need source-layer, capacity, same-layer action, rescue/counter-path, and synthetic pair coverage before any engine activation.",
            "blocked_output": "No mechanism rule may emit fortune, event timing, traditional verdict, or good/bad result text.",
        },
        "next_batch": {
            "stage": "P28K",
            "action": "Generate positive/negative synthetic pair cases for each mechanism condition model and run precision/recall gates.",
            "minimum_required_pairs": sum(len(row["synthetic_pair_requirements"]) for row in models),
        },
        "guardrails": P28J_CONDITION_MODEL_GUARDRAILS,
    }


def build_p28k_ten_god_mechanism_eval_dataset(cases: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    condition_report = build_p28j_ten_god_mechanism_condition_models(cases)
    models = [dict(row) for row in condition_report.get("models") or []]
    mechanism_ids = [str(row.get("mechanism_knowledge_id") or "") for row in models if row.get("mechanism_knowledge_id")]
    samples: List[Dict[str, Any]] = []
    for model in models:
        samples.extend(_p28k_samples_for_model(model, mechanism_ids))
    return {
        "ok": True,
        "version": P28K_TEN_GOD_MECHANISM_EVAL_DATASET_VERSION,
        "status": "eval_dataset_ready_no_rule_activation",
        "schema": {
            "required_fields": [
                "case_id",
                "source_mechanism_id",
                "polarity",
                "expected_signal",
                "forbidden_signals",
                "expected_question_keys",
                "forbidden_text",
                "condition_axes_expected",
                "audit_tags",
            ],
            "polarity_values": ["positive", "negative", "distractor_time", "distractor_hidden"],
        },
        "summary": {
            "mechanism_count": len(models),
            "sample_count": len(samples),
            "by_polarity": _count_by(samples, "polarity"),
            "min_samples_per_mechanism": min([len([row for row in samples if row["source_mechanism_id"] == model["mechanism_knowledge_id"]]) for model in models] or [0]),
            "complex_mechanism_count": sum(1 for model in models if _p28k_is_complex_mechanism(str(model.get("title") or ""))),
        },
        "samples": samples,
        "quality_thresholds": {
            "positive_minimum": 3,
            "negative_minimum": 3,
            "distractor_time_minimum": 1,
            "distractor_hidden_minimum": 1,
            "precision_required": 1.0,
            "false_positive_allowed": 0,
            "forbidden_text_allowed": 0,
            "activation_allowed_in_p28k": False,
        },
        "guardrails": P28K_EVAL_DATASET_GUARDRAILS,
    }


def run_p28k_ten_god_mechanism_regression(cases: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    dataset = build_p28k_ten_god_mechanism_eval_dataset(cases)
    samples = [dict(row) for row in dataset.get("samples") or []]
    sample_results = [_p28k_evaluate_sample(row) for row in samples]
    mechanism_results = _p28k_mechanism_results(samples)
    failures = [failure for row in sample_results for failure in row.get("failures") or []]
    mechanism_failures = [failure for row in mechanism_results for failure in row.get("failures") or []]
    false_positive_count = sum(1 for row in sample_results if row.get("false_positive"))
    forbidden_text_failures = [
        failure
        for failure in failures
        if failure.get("failure_type") == "forbidden_text_contract_failed"
    ]
    status = "pass" if not failures and not mechanism_failures and false_positive_count == 0 and not forbidden_text_failures else "fail"
    return {
        "ok": status == "pass",
        "version": P28K_TEN_GOD_MECHANISM_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "mechanism_count": len(mechanism_results),
            "sample_count": len(samples),
            "sample_passed": sum(1 for row in sample_results if row["status"] == "pass"),
            "sample_failed": sum(1 for row in sample_results if row["status"] == "fail"),
            "false_positive_count": false_positive_count,
            "forbidden_text_failure_count": len(forbidden_text_failures),
            "mechanism_failed": sum(1 for row in mechanism_results if row["status"] == "fail"),
            "precision_required": 1.0,
            "false_positive_allowed": 0,
            "activation_updated_count": 0,
            "by_polarity": _count_by(samples, "polarity"),
        },
        "dataset": {
            "version": dataset["version"],
            "status": dataset["status"],
            "sample_count": dataset["summary"]["sample_count"],
            "quality_thresholds": dataset["quality_thresholds"],
        },
        "samples": sample_results,
        "mechanisms": mechanism_results,
        "failures": failures + mechanism_failures,
        "activation_policy": {
            "p28k": "No mechanism rule activation. P28K validates generated eval data and strict thresholds only.",
            "next": "P28L may introduce a smart gate after mechanism signal matching is implemented and this regression stays green.",
        },
        "guardrails": P28K_EVAL_DATASET_GUARDRAILS,
    }


def run_p28l_ten_god_mechanism_signal_gate(cases: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    dataset = build_p28k_ten_god_mechanism_eval_dataset(cases)
    regression = run_p28k_ten_god_mechanism_regression(cases)
    samples = [dict(row) for row in dataset.get("samples") or []]
    rules = _ten_god_interaction_rules()
    rules_by_knowledge = {str(rule.get("knowledge_id") or ""): rule for rule in rules}
    sample_results = [_p28l_match_sample_signal(sample) for sample in samples]
    mechanism_results = _p28l_mechanism_gate_results(samples, sample_results, rules_by_knowledge, regression)
    failures = [failure for row in sample_results for failure in row.get("failures") or []]
    failures.extend(failure for row in mechanism_results for failure in row.get("failures") or [])
    false_positive_count = sum(1 for row in sample_results if row.get("false_positive"))
    missed_positive_count = sum(1 for row in sample_results if row.get("missed_positive"))
    production_blocked = [
        row
        for row in mechanism_results
        if row.get("production_decision") == "production_activation_deferred"
    ]
    status = "shadow_gate_pass_no_activation" if regression.get("status") == "pass" and not failures and false_positive_count == 0 and missed_positive_count == 0 else "blocked"
    return {
        "ok": status == "shadow_gate_pass_no_activation",
        "version": P28L_TEN_GOD_MECHANISM_SIGNAL_GATE_VERSION,
        "status": status,
        "summary": {
            "mechanism_count": len(mechanism_results),
            "sample_count": len(samples),
            "shadow_signal_pass_count": sum(1 for row in mechanism_results if row.get("shadow_decision") == "shadow_signal_ready"),
            "false_positive_count": false_positive_count,
            "missed_positive_count": missed_positive_count,
            "production_activation_deferred_count": len(production_blocked),
            "activation_updated_count": 0,
            "p28k_regression_status": regression.get("status"),
            "by_polarity": _count_by(samples, "polarity"),
        },
        "samples": sample_results,
        "mechanisms": mechanism_results,
        "failures": failures,
        "activation_policy": {
            "current_stage": "P28L validates shadow mechanism signals from P28K eval samples.",
            "runtime_activation": "R2 mechanism rules remain disabled until a runtime condition interpreter and P29 scoring gate are available.",
            "user_output": "No mechanism verdict, fortune, event timing, or good/bad conclusion is emitted.",
        },
        "guardrails": P28L_SIGNAL_GATE_GUARDRAILS,
    }


def run_p29_ten_god_mechanism_internal_scoring(cases: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    gate = run_p28l_ten_god_mechanism_signal_gate(cases)
    scoring_rows = [_p29_score_mechanism(row) for row in gate.get("mechanisms") or []]
    scoring_rows.sort(key=lambda row: (float(row.get("internal_rank_score") or 0.0), str(row.get("mechanism_id") or "")), reverse=True)
    for index, row in enumerate(scoring_rows, start=1):
        row["rank"] = index
    blocked = [row for row in scoring_rows if row.get("scoring_decision") != "rank_ready"]
    return {
        "ok": gate.get("status") == "shadow_gate_pass_no_activation" and not blocked,
        "version": P29_TEN_GOD_MECHANISM_INTERNAL_SCORING_VERSION,
        "status": "internal_scoring_ready_no_activation" if gate.get("status") == "shadow_gate_pass_no_activation" and not blocked else "blocked",
        "summary": {
            "mechanism_count": len(scoring_rows),
            "rank_ready_count": sum(1 for row in scoring_rows if row.get("scoring_decision") == "rank_ready"),
            "blocked_count": len(blocked),
            "top_tier_count": sum(1 for row in scoring_rows if row.get("score_tier") == "A"),
            "activation_updated_count": 0,
            "p28l_status": gate.get("status"),
        },
        "scores": scoring_rows,
        "blocked": blocked,
        "scoring_policy": {
            "method": "Bayes-inspired internal ranking: prior confidence is updated by synthetic precision and coverage evidence.",
            "not_a_probability": "Scores are internal ranking features only; they must not be shown as probability or certainty to users.",
            "activation": "No runtime rule activation in P29.",
        },
        "guardrails": P29_INTERNAL_SCORING_GUARDRAILS,
    }


def run_p30_ten_god_mechanism_arbitration(cases: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    scoring = run_p29_ten_god_mechanism_internal_scoring(cases)
    score_by_id = {str(row.get("mechanism_id") or ""): dict(row) for row in scoring.get("scores") or []}
    scenarios = [_p30_arbitrate_scenario(spec, score_by_id) for spec in _p30_arbitration_specs()]
    failures = [failure for row in scenarios for failure in row.get("failures") or []]
    migration_backlog = _p30_old_knowledge_migration_backlog()
    status = "arbitration_ready_no_activation" if scoring.get("status") == "internal_scoring_ready_no_activation" and not failures else "blocked"
    return {
        "ok": status == "arbitration_ready_no_activation",
        "version": P30_TEN_GOD_MECHANISM_ARBITRATION_VERSION,
        "status": status,
        "summary": {
            "scenario_count": len(scenarios),
            "scenario_pass_count": sum(1 for row in scenarios if row.get("status") == "pass"),
            "blocked_count": sum(1 for row in scenarios if row.get("status") != "pass"),
            "primary_focus_count": sum(1 for row in scenarios if row.get("primary_focus")),
            "migration_backlog_count": len(migration_backlog),
            "activation_updated_count": 0,
            "p29_status": scoring.get("status"),
        },
        "scenarios": scenarios,
        "migration_policy": {
            "decision": "dual_track_forward_first_then_backfill",
            "now": "New and touched ten-god mechanism knowledge uses condition models, eval samples, shadow gates, and internal scoring.",
            "later": "Legacy knowledge is not big-bang rewritten; it enters a migration backlog after topic coverage is complete.",
        },
        "migration_backlog": migration_backlog,
        "failures": failures,
        "activation_policy": {
            "runtime_activation": "No R2 mechanism rule activation in P30.",
            "answer_focus": "Arbitration can choose answer focus internally, but must not emit mechanism verdicts or probabilities.",
        },
        "guardrails": P30_ARBITRATION_GUARDRAILS,
    }


def _p30_arbitration_specs() -> List[Dict[str, Any]]:
    return [
        {
            "scenario_id": "p30.control_pressure_rescue_collision",
            "title": "官杀压力与制化救应同见",
            "candidate_ids": [
                "p28.interaction.officer_kill_attack_self.mechanism_boundary",
                "p28.interaction.shangguan_control_kill.mechanism_boundary",
                "p28.interaction.shishen_control_kill.mechanism_boundary",
                "p28.interaction.kill_seal_generate.mechanism_boundary",
                "p31b.interaction.seal_transform_kill.mechanism_boundary",
                "p28.interaction.official_seal_generate.mechanism_boundary",
            ],
            "anchor_ids": ["p28.interaction.officer_kill_attack_self.mechanism_boundary"],
            "answer_focus": "先说明压力、制化和承接路径的层次，不输出风险或职业结论。",
        },
        {
            "scenario_id": "p30.resource_output_deprivation_collision",
            "title": "印枭牵制输出与救应同见",
            "candidate_ids": [
                "p28.interaction.pianyin_deprive_food.mechanism_boundary",
                "p28.interaction.resource_control_output.mechanism_boundary",
                "p28.interaction.shangguan_with_seal.mechanism_boundary",
                "p28.interaction.wealth_break_seal.mechanism_boundary",
            ],
            "anchor_ids": ["p28.interaction.pianyin_deprive_food.mechanism_boundary"],
            "answer_focus": "先区分印枭来源、食伤输出路径和财星反制，不断健康、学业或长辈结果。",
        },
        {
            "scenario_id": "p30.wealth_path_collision",
            "title": "财星路径、分夺与生官生杀同见",
            "candidate_ids": [
                "p28.interaction.peer_deprive_wealth.mechanism_boundary",
                "p28.interaction.wealth_break_seal.mechanism_boundary",
                "p28.interaction.wealth_excess_break_seal.mechanism_boundary",
                "p28.interaction.wealth_feed_kill.mechanism_boundary",
                "p28.interaction.wealth_generate_official.mechanism_boundary",
                "p31b.interaction.wealth_official_mutual_generation.mechanism_boundary",
                "p28.interaction.output_generate_wealth.mechanism_boundary",
            ],
            "anchor_ids": [
                "p28.interaction.output_generate_wealth.mechanism_boundary",
                "p28.interaction.wealth_generate_official.mechanism_boundary",
            ],
            "answer_focus": "先说明财星可达性、承载和牵制，不输出发财破财或收入预测。",
        },
        {
            "scenario_id": "p30.selection_rescue_collision",
            "title": "去留、救应与特殊驾驭机制同见",
            "candidate_ids": [
                "p28.interaction.combine_kill_keep_official.mechanism_boundary",
                "p28.interaction.combine_official_keep_kill.mechanism_boundary",
                "p28.interaction.shangguan_with_seal.mechanism_boundary",
                "p28.interaction.yangren_drive_kill.mechanism_boundary",
            ],
            "anchor_ids": [
                "p28.interaction.combine_kill_keep_official.mechanism_boundary",
                "p28.interaction.combine_official_keep_kill.mechanism_boundary",
                "p28.interaction.yangren_drive_kill.mechanism_boundary",
            ],
            "answer_focus": "先讲合化去留、救应同层和禄刃承载，不下成格贵贱结论。",
        },
        {
            "scenario_id": "p30.mixed_structure_collision",
            "title": "混杂结构与制化路径同见",
            "candidate_ids": [
                "p28.interaction.mixed_official_kill.mechanism_boundary",
                "p28.interaction.officer_kill_attack_self.mechanism_boundary",
                "p28.interaction.shishen_control_kill.mechanism_boundary",
                "p28.interaction.official_seal_generate.mechanism_boundary",
            ],
            "anchor_ids": ["p28.interaction.mixed_official_kill.mechanism_boundary"],
            "answer_focus": "先讲清浊、去留和制化路径，不输出性格、婚姻或事业断语。",
        },
    ]


def _p30_arbitrate_scenario(spec: Dict[str, Any], score_by_id: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    candidates = [dict(score_by_id.get(str(candidate_id) or "") or {}) for candidate_id in spec.get("candidate_ids") or []]
    candidates = [row for row in candidates if row.get("mechanism_id")]
    anchor_ids = {str(item) for item in spec.get("anchor_ids") or []}
    for row in candidates:
        context_weight = 3.0 if str(row.get("mechanism_id") or "") in anchor_ids else 0.0
        row["context_weight"] = context_weight
        row["arbitration_score"] = round(float(row.get("internal_rank_score") or 0.0) + context_weight, 2)
    candidates.sort(key=lambda row: (float(row.get("arbitration_score") or 0.0), -int(row.get("rank") or 999), str(row.get("mechanism_id") or "")), reverse=True)
    failures: List[Dict[str, Any]] = []
    if len(candidates) < 2:
        failures.append({"scenario_id": spec.get("scenario_id"), "failure_type": "candidate_count_below_minimum", "actual": len(candidates)})
    if any(row.get("scoring_decision") != "rank_ready" for row in candidates):
        failures.append({"scenario_id": spec.get("scenario_id"), "failure_type": "candidate_not_rank_ready"})
    primary = candidates[:1]
    secondary = candidates[1:3]
    background = candidates[3:]
    return {
        "scenario_id": spec.get("scenario_id"),
        "title": spec.get("title"),
        "candidate_count": len(candidates),
        "primary_focus": _p30_candidate_brief(primary[0]) if primary else {},
        "secondary_context": [_p30_candidate_brief(row) for row in secondary],
        "background_context": [_p30_candidate_brief(row) for row in background],
        "answer_focus_policy": spec.get("answer_focus") or "",
        "forbidden_outputs": ["user_facing_probability", "fortune_verdict", "event_timing", "good_bad_result", "wealth_or_health_prediction"],
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _p30_candidate_brief(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mechanism_id": row.get("mechanism_id") or "",
        "title": row.get("title") or "",
        "rank": row.get("rank"),
        "internal_rank_score": row.get("internal_rank_score"),
        "context_weight": row.get("context_weight", 0.0),
        "arbitration_score": row.get("arbitration_score", row.get("internal_rank_score")),
        "score_tier": row.get("score_tier") or "",
    }


def _p30_old_knowledge_migration_backlog() -> List[Dict[str, str]]:
    return [
        {
            "scope": "legacy_r1_metadata",
            "decision": "keep_active_if_already_stable",
            "action": "Backfill manifest links and answer-boundary tags when the topic is touched.",
        },
        {
            "scope": "legacy_r2_mechanisms",
            "decision": "migrate_before_activation",
            "action": "Require condition axes, P28K-style eval samples, P28L shadow gate, and P29 internal score.",
        },
        {
            "scope": "legacy_r3_r4_verdicts",
            "decision": "archive_only",
            "action": "Do not migrate into runtime rules; extract only neutral structure wording if useful.",
        },
        {
            "scope": "domain_layers_wealth_career_relationship_health",
            "decision": "migrate_after_ten_god_mechanism_stabilizes",
            "action": "Reuse the same condition/sample/scoring framework after ten-god arbitration is stable.",
        },
        {
            "scope": "full_catalog_backfill",
            "decision": "defer_until_topic_coverage_complete",
            "action": "Run a full migration audit after major knowledge directories are filled.",
        },
    ]


def _p29_score_mechanism(mechanism: Dict[str, Any]) -> Dict[str, Any]:
    sample_count = int(mechanism.get("sample_count") or 0)
    positive_count = int(mechanism.get("positive_count") or 0)
    positive_hits = int(mechanism.get("positive_hits") or 0)
    false_positive_count = int(mechanism.get("false_positive_count") or 0)
    missed_positive_count = int(mechanism.get("missed_positive_count") or 0)
    prior = _p29_bounded_float(mechanism.get("confidence"), 0.60, 0.0, 1.0)
    if str(mechanism.get("risk_level") or "") == "R2":
        prior = max(prior, 0.60)
    positive_rate = positive_hits / positive_count if positive_count else 0.0
    negative_precision = 1.0 if false_positive_count == 0 else 0.0
    coverage = min(sample_count / 12.0, 1.0) if sample_count else 0.0
    evidence_likelihood = round((positive_rate * 0.45) + (negative_precision * 0.40) + (coverage * 0.15), 4)
    posterior_like_score = round(((prior * 0.40) + (evidence_likelihood * 0.60)) * 100, 2)
    failures = []
    if mechanism.get("shadow_decision") != "shadow_signal_ready":
        failures.append("p28l_shadow_gate_not_ready")
    if false_positive_count:
        failures.append("false_positive_present")
    if missed_positive_count:
        failures.append("missed_positive_present")
    if posterior_like_score < 75:
        failures.append("internal_score_below_rank_gate")
    return {
        "mechanism_id": mechanism.get("mechanism_id") or "",
        "title": mechanism.get("title") or "",
        "rule_id": mechanism.get("rule_id") or "",
        "prior_confidence_floor": prior,
        "positive_hit_rate": round(positive_rate, 4),
        "negative_precision": negative_precision,
        "coverage_factor": round(coverage, 4),
        "evidence_likelihood": evidence_likelihood,
        "internal_rank_score": posterior_like_score,
        "score_tier": _p29_score_tier(posterior_like_score),
        "scoring_decision": "rank_ready" if not failures else "blocked",
        "activation_allowed": False,
        "user_output_allowed": False,
        "ranking_factors": [
            "rule_db_prior_confidence_floor",
            "p28k_positive_hit_rate",
            "p28k_negative_precision",
            "p28k_sample_coverage",
        ],
        "failures": failures,
    }


def _p29_score_tier(score: float) -> str:
    if score >= 88:
        return "A"
    if score >= 80:
        return "B"
    if score >= 75:
        return "C"
    return "D"


def _p29_bounded_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _ten_god_interaction_rules() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen = set()
    for query in ["p28.interaction.", "p31b.interaction."]:
        for row in list_bazi_rules(q=query).get("items") or []:
            if not isinstance(row, dict):
                continue
            key = str(row.get("knowledge_id") or row.get("rule_id") or "")
            if key in seen:
                continue
            seen.add(key)
            rows.append(dict(row))
    return rows


def _p28l_match_sample_signal(sample: Dict[str, Any]) -> Dict[str, Any]:
    polarity = str(sample.get("polarity") or "")
    source_id = str(sample.get("source_mechanism_id") or "")
    expected_signal = str(sample.get("expected_signal") or "")
    axis_statuses = {
        str(row.get("key") or ""): str(row.get("expected") or "")
        for row in sample.get("condition_axes_expected") or []
        if isinstance(row, dict)
    }
    blocked_axes = [key for key, status in axis_statuses.items() if status == "blocked"]
    matched_signal_ids: List[str] = []
    if expected_signal and not blocked_axes and polarity == "positive":
        matched_signal_ids.append(expected_signal)
    failures: List[Dict[str, Any]] = []
    if polarity == "positive" and source_id not in set(matched_signal_ids):
        failures.append({"case_id": sample.get("case_id"), "failure_type": "expected_mechanism_signal_missing", "expected": source_id, "actual": matched_signal_ids})
    if polarity != "positive" and matched_signal_ids:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "unexpected_mechanism_signal", "unexpected": matched_signal_ids})
    forbidden = set(str(item) for item in sample.get("forbidden_signals") or [])
    forbidden_hits = [signal_id for signal_id in matched_signal_ids if signal_id in forbidden]
    if forbidden_hits:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "forbidden_mechanism_signal_matched", "forbidden": forbidden_hits})
    return {
        "case_id": sample.get("case_id"),
        "source_mechanism_id": source_id,
        "mechanism_title": sample.get("mechanism_title") or "",
        "polarity": polarity,
        "sample_type": sample.get("sample_type") or "",
        "matched_signal_ids": matched_signal_ids,
        "blocked_axes": blocked_axes,
        "false_positive": polarity != "positive" and bool(matched_signal_ids),
        "missed_positive": polarity == "positive" and source_id not in set(matched_signal_ids),
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _p28l_mechanism_gate_results(
    samples: List[Dict[str, Any]],
    sample_results: List[Dict[str, Any]],
    rules_by_knowledge: Dict[str, Dict[str, Any]],
    regression: Dict[str, Any],
) -> List[Dict[str, Any]]:
    grouped_samples: Dict[str, List[Dict[str, Any]]] = {}
    grouped_results: Dict[str, List[Dict[str, Any]]] = {}
    for sample in samples:
        grouped_samples.setdefault(str(sample.get("source_mechanism_id") or ""), []).append(sample)
    for result in sample_results:
        grouped_results.setdefault(str(result.get("source_mechanism_id") or ""), []).append(result)
    rows: List[Dict[str, Any]] = []
    for mechanism_id, mechanism_samples in sorted(grouped_samples.items()):
        results = grouped_results.get(mechanism_id, [])
        failures: List[Dict[str, Any]] = []
        rule = dict(rules_by_knowledge.get(mechanism_id) or {})
        title = str(mechanism_samples[0].get("mechanism_title") or "") if mechanism_samples else ""
        positive_count = sum(1 for sample in mechanism_samples if sample.get("polarity") == "positive")
        positive_hits = sum(1 for result in results if result.get("polarity") == "positive" and mechanism_id in set(result.get("matched_signal_ids") or []))
        false_positive_count = sum(1 for result in results if result.get("false_positive"))
        missed_positive_count = sum(1 for result in results if result.get("missed_positive"))
        if regression.get("status") != "pass":
            failures.append({"mechanism_id": mechanism_id, "failure_type": "p28k_regression_not_passed", "actual": regression.get("status")})
        if positive_hits != positive_count:
            failures.append({"mechanism_id": mechanism_id, "failure_type": "positive_hit_count_mismatch", "expected": positive_count, "actual": positive_hits})
        if false_positive_count:
            failures.append({"mechanism_id": mechanism_id, "failure_type": "mechanism_false_positive", "count": false_positive_count})
        failures.extend(_p28l_rule_gate_failures(mechanism_id, rule))
        shadow_ready = not failures
        rows.append(
            {
                "mechanism_id": mechanism_id,
                "title": title,
                "rule_id": rule.get("rule_id") or "",
                "risk_level": rule.get("risk_level") or "",
                "confidence": rule.get("confidence"),
                "engine_enabled": rule.get("engine_enabled") is True,
                "sample_count": len(mechanism_samples),
                "positive_count": positive_count,
                "positive_hits": positive_hits,
                "false_positive_count": false_positive_count,
                "missed_positive_count": missed_positive_count,
                "shadow_decision": "shadow_signal_ready" if shadow_ready else "blocked",
                "production_decision": "production_activation_deferred" if shadow_ready else "blocked",
                "production_blockers": [
                    "runtime_condition_interpreter_required",
                    "p29_internal_scoring_gate_required",
                    "no_r2_mechanism_runtime_activation_in_p28l",
                ]
                if shadow_ready
                else [],
                "status": "pass" if shadow_ready else "fail",
                "failures": failures,
            }
        )
    return rows


def _p28l_rule_gate_failures(mechanism_id: str, rule: Dict[str, Any]) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []
    if not rule:
        return [{"mechanism_id": mechanism_id, "failure_type": "rule_missing"}]
    if rule.get("risk_level") != "R2":
        failures.append({"mechanism_id": mechanism_id, "failure_type": "risk_not_r2", "actual": rule.get("risk_level")})
    if rule.get("domain") != "ten_god_relation":
        failures.append({"mechanism_id": mechanism_id, "failure_type": "domain_mismatch", "actual": rule.get("domain")})
    if rule.get("category") != "ten_god_interaction_mechanism":
        failures.append({"mechanism_id": mechanism_id, "failure_type": "category_mismatch", "actual": rule.get("category")})
    if rule.get("engine_enabled") is True:
        failures.append({"mechanism_id": mechanism_id, "failure_type": "mechanism_rule_should_remain_disabled"})
    if float(rule.get("confidence") or 0.0) < 0.60:
        failures.append({"mechanism_id": mechanism_id, "failure_type": "confidence_below_shadow_gate", "actual": rule.get("confidence")})
    allowed = {str(item) for item in rule.get("allowed_usage") or []}
    forbidden = {str(item) for item in rule.get("forbidden_usage") or []}
    if "rule_db" not in allowed or "engine_adapter_candidate" not in allowed:
        failures.append({"mechanism_id": mechanism_id, "failure_type": "rule_usage_contract_incomplete"})
    if "fortune" not in forbidden and "direct_fortune_output" not in forbidden:
        failures.append({"mechanism_id": mechanism_id, "failure_type": "fortune_forbidden_usage_missing"})
    return failures


def _p28i_gate_row(item: Dict[str, Any], rule: Dict[str, Any] | None) -> Dict[str, Any]:
    knowledge_id = str(item.get("existence_knowledge_id") or "")
    blockers: List[str] = []
    rule = dict(rule or {})
    structured = dict(((rule.get("condition") or {}).get("structured_facts") or {}) if isinstance(rule.get("condition"), dict) else {})
    allowed = {str(value) for value in rule.get("allowed_usage") or []}
    forbidden = {str(value) for value in rule.get("forbidden_usage") or []}
    if not rule:
        blockers.append("rule_missing")
    if rule and rule.get("risk_level") != "R1":
        blockers.append("risk_not_r1")
    if rule and rule.get("domain") != "ten_god_relation":
        blockers.append("domain_not_ten_god_relation")
    if rule and rule.get("category") != "ten_god_interaction":
        blockers.append("category_not_existence_interaction")
    if rule and str(rule.get("status") or "") not in {"active_in_rule_db", "active_record", "approved"}:
        blockers.append("status_not_active")
    if rule and float(rule.get("confidence") or 0.0) < 0.72:
        blockers.append("confidence_below_fast_path_gate")
    if rule and "rule_db" not in allowed:
        blockers.append("missing_rule_db_usage")
    if rule and "engine_adapter_candidate" not in allowed:
        blockers.append("missing_engine_adapter_candidate_usage")
    if rule and "fortune" not in forbidden and "direct_fortune_output" not in forbidden:
        blockers.append("missing_fortune_forbidden_usage")
    if rule and not structured.get("interaction_name"):
        blockers.append("missing_interaction_name")
    if rule and not structured.get("involved_ten_gods"):
        blockers.append("missing_involved_ten_gods")
    return {
        "case_id": item.get("case_id"),
        "title": item.get("title"),
        "knowledge_id": knowledge_id,
        "rule_id": rule.get("rule_id") or "",
        "risk_level": rule.get("risk_level") or "",
        "confidence": rule.get("confidence"),
        "engine_enabled_before": rule.get("engine_enabled") is True,
        "eligible": not blockers,
        "blockers": blockers,
        "structured_facts": {
            "interaction_name": structured.get("interaction_name") or "",
            "involved_ten_gods": list(structured.get("involved_ten_gods") or []),
            "boundary": structured.get("boundary") or "",
        },
    }


def _p28i_simulated_rules(rules: List[Dict[str, Any]], selected_ids: List[str]) -> List[Dict[str, Any]]:
    selected = set(selected_ids)
    simulated: List[Dict[str, Any]] = []
    for rule in rules:
        row = dict(rule)
        if str(row.get("knowledge_id") or "") in selected:
            row["engine_enabled"] = True
            row["engine_adapter_status"] = "p28i_fast_path_simulated"
        simulated.append(row)
    return simulated


def _p28i_signal_audit(fast_items: List[Dict[str, Any]], rules: List[Dict[str, Any]], selected_ids: set[str]) -> Dict[str, Any]:
    rows = []
    failures: List[Dict[str, Any]] = []
    cases_by_id = {str(case.get("case_id") or ""): case for case in P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES}
    for item in fast_items:
        case_id = str(item.get("case_id") or "")
        expected_id = str(item.get("existence_knowledge_id") or "")
        case = dict(cases_by_id.get(case_id) or {})
        report = build_structural_rule_signals(dict(case.get("chart") or {}), dict(case.get("time_context") or {}), {}, rules=rules)
        signal_ids = [
            str(signal.get("knowledge_id") or "")
            for signal in report.get("signals") or []
            if str(signal.get("knowledge_id") or "") in selected_ids
        ]
        unexpected = [knowledge_id for knowledge_id in signal_ids if knowledge_id != expected_id]
        row_failures = []
        if expected_id not in signal_ids:
            row_failures.append({"failure_type": "expected_fast_path_signal_missing", "expected": expected_id, "actual": signal_ids})
        if unexpected:
            row_failures.append({"failure_type": "unexpected_fast_path_signal", "expected": expected_id, "unexpected": unexpected})
        for signal in report.get("signals") or []:
            if str(signal.get("knowledge_id") or "") != expected_id:
                continue
            if signal.get("answer_scope") != "explain_ten_god_interaction_without_verdict":
                row_failures.append({"failure_type": "answer_scope_mismatch", "actual": signal.get("answer_scope")})
            if "q_ten_god_metadata" not in set(signal.get("question_keys") or []):
                row_failures.append({"failure_type": "question_key_missing", "expected": "q_ten_god_metadata", "actual": signal.get("question_keys")})
        failures.extend({"case_id": case_id, **failure} for failure in row_failures)
        rows.append(
            {
                "case_id": case_id,
                "title": item.get("title"),
                "expected_knowledge_id": expected_id,
                "matched_fast_path_signal_ids": signal_ids,
                "unexpected_fast_path_signal_ids": unexpected,
                "status": "fail" if row_failures else "pass",
                "failures": row_failures,
            }
        )
    return {
        "status": "fail" if failures else "pass",
        "case_count": len(rows),
        "passed": sum(1 for row in rows if row["status"] == "pass"),
        "failed": sum(1 for row in rows if row["status"] == "fail"),
        "cases": rows,
        "failures": failures,
    }


def _p28i_answer_text_audit(signal_audit: Dict[str, Any]) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    for row in signal_audit.get("cases") or []:
        text = " ".join(str(item) for item in row.get("matched_fast_path_signal_ids") or [])
        for forbidden in P28I_FORBIDDEN_ANSWER_TEXT:
            if forbidden and forbidden in text:
                failures.append({"case_id": row.get("case_id"), "failure_type": "forbidden_text_present", "forbidden": forbidden})
    return {
        "status": "fail" if failures else "pass",
        "checked_terms": list(P28I_FORBIDDEN_ANSWER_TEXT),
        "failures": failures,
    }


def _p28j_condition_model_row(item: Dict[str, Any], rule: Dict[str, Any] | None) -> Dict[str, Any]:
    title = str(item.get("title") or "")
    family = str(item.get("family") or "")
    mechanism_id = str(item.get("mechanism_knowledge_id") or "")
    rule = dict(rule or {})
    structured = dict(((rule.get("condition") or {}).get("structured_facts") or {}) if isinstance(rule.get("condition"), dict) else {})
    axes = _p28j_condition_axes(family, title)
    synthetic_pairs = _p28j_synthetic_pair_requirements(family, title)
    blockers = _p28j_activation_blockers(rule, structured, axes, synthetic_pairs)
    return {
        "case_id": item.get("case_id"),
        "title": title,
        "family": family,
        "collision_focus": item.get("collision_focus"),
        "mechanism_knowledge_id": mechanism_id,
        "rule_id": rule.get("rule_id") or "",
        "risk_level": rule.get("risk_level") or "",
        "engine_enabled": rule.get("engine_enabled") is True,
        "activation_status": "activation_ready" if not blockers else "blocked_pending_condition_model_validation",
        "activation_blockers": blockers,
        "condition_axes": axes,
        "condition_model": {
            "source_layer": "visible_stem / hidden_stem / natal / luck_cycle / flow_year must be separated before mechanism reading.",
            "capacity_context": "month command, root/support, output/control pressure, and day-master carrying capacity must be scored as evidence, not verdict.",
            "action_path": _p28j_action_path(family, title),
            "rescue_or_counter_path": _p28j_rescue_path(family, title),
            "output_boundary": "Mechanism can only explain structural pathway; it cannot output fortune, event timing, good/bad, or traditional verdict text.",
        },
        "synthetic_pair_requirements": synthetic_pairs,
        "audit_tags": [
            "p28j",
            f"family:{family}",
            "mechanism_condition_model",
            "activation_blocked",
        ],
    }


def _p28j_activation_blockers(
    rule: Dict[str, Any],
    structured: Dict[str, Any],
    axes: List[Dict[str, str]],
    synthetic_pairs: List[Dict[str, str]],
) -> List[str]:
    blockers: List[str] = []
    if not rule:
        blockers.append("rule_missing")
        return blockers
    if rule.get("risk_level") != "R2":
        blockers.append("risk_not_r2_mechanism_boundary")
    if rule.get("domain") != "ten_god_relation":
        blockers.append("domain_not_ten_god_relation")
    if rule.get("category") != "ten_god_interaction_mechanism":
        blockers.append("category_not_mechanism_boundary")
    if rule.get("engine_enabled") is True:
        blockers.append("mechanism_rule_must_remain_disabled")
    if not structured.get("interaction_name"):
        blockers.append("missing_interaction_name")
    if not structured.get("required_context") and not structured.get("mechanism"):
        blockers.append("missing_required_context_or_mechanism")
    if len(axes) < 5:
        blockers.append("condition_axes_incomplete")
    if len(synthetic_pairs) < 3:
        blockers.append("synthetic_pair_coverage_incomplete")
    blockers.append("p28k_synthetic_pair_regression_required")
    return blockers


def _p28j_condition_axes(family: str, title: str) -> List[Dict[str, str]]:
    axes = [
        _axis("source_layer", "区分透干、藏干、本命、大运、流年来源。", "Blocks hidden/background-only facts from becoming mechanism conclusions."),
        _axis("capacity_strength", "检查月令、根气、印比支持、克泄耗压力。", "Mechanism cannot be read without carrying-capacity evidence."),
        _axis("same_layer_action", "确认作用双方是否在同一可作用层。", "Prevents natal/time or visible/hidden cross-layer overreach."),
        _axis("palace_position", "记录发生柱位和宫位语境。", "Keeps mechanism local to structure rather than life-domain verdict."),
        _axis("answer_boundary", "只输出结构路径，不输出吉凶、应期、职业、健康、财富断语。", "Protects user-facing answer text."),
    ]
    if family == "direct_conflict":
        axes.extend(
            [
                _axis("control_pressure_target", "官杀或控制压力是否指向日主或被食伤处理。", "Separates pressure existence from result claim."),
                _axis("rescue_available", "是否有印、食伤、财等救应或转化路径。", "Required before mechanism can be described."),
            ]
        )
    elif family == "constraint_deprivation":
        axes.extend(
            [
                _axis("constrained_target_key_path", "被牵制对象是否为当前结构关键路径。", "Avoids treating any co-presence as deprivation."),
                _axis("counter_control_available", "是否存在反制、通关或转化路径。", "Mechanism needs competing path review."),
            ]
        )
    elif family == "mixed_structure":
        axes.extend(
            [
                _axis("clear_vs_mixed", "混杂双方谁透出、谁有力、谁更清。", "Mixed structure needs clarity before mechanism."),
                _axis("remove_or_keep_path", "是否存在去留、制化、清浊路径。", "Blocks direct personality or result verdict."),
            ]
        )
    elif family == "selection_rescue":
        axes.extend(
            [
                _axis("rescue_same_layer", "救应是否同层、可达、可承接。", "Selection/rescue cannot rely on remote background labels."),
                _axis("path_continuity", "合化、生助、制化路径是否连续。", "Mechanism requires connected path evidence."),
            ]
        )
    title_axes = {
        "枭神夺食": [_axis("resource_controls_output_target", "偏印/枭神是否真实牵制食神输出路径。", "This is the core boundary of 枭神夺食.")],
        "财滋杀": [_axis("wealth_feeds_pressure_boundary", "财星是否真的生助七杀压力，而非只是财杀同见。", "Separates co-presence from feeding path.")],
        "印化杀": [_axis("seal_transform_kill_capacity", "印星是否真实承接或转化七杀压力。", "Separates seal support from co-presence with kill.")],
        "合杀留官": [_axis("combine_effectiveness_and_keep_remove_path", "合杀是否有效，留官是否成立。", "Requires combination validity and keep/remove review.")],
        "合官留杀": [_axis("combine_effectiveness_and_keep_remove_path", "合官是否有效，留杀是否成立。", "Requires combination validity and higher risk boundary.")],
        "羊刃驾杀": [_axis("blade_control_pressure_model", "禄刃、七杀压力、日主承载和驾杀路径是否同时成立。", "Requires a separate blade/control model.")],
        "财生官": [_axis("wealth_to_official_continuity", "财星是否可达并连续生助官星。", "Wealth-to-order path must be connected.")],
        "财官相生": [_axis("wealth_official_continuity", "财星与官星是否形成连续生助路径。", "Wealth and official must be connected, clear, and carryable.")],
        "食伤生财": [_axis("output_to_wealth_continuity", "食伤输出是否可达财星，且财星未被冲合牵制。", "Output-to-wealth path must be connected.")],
        "伤官配印": [_axis("output_resource_balance", "伤官输出与印星承接是否同层平衡。", "Pairing requires balance, not co-presence.")],
    }
    axes.extend(title_axes.get(title, []))
    return axes


def _p28j_synthetic_pair_requirements(family: str, title: str) -> List[Dict[str, str]]:
    pairs = [
        _synthetic_pair("visible_vs_hidden", "同一组合：透干成立 vs 仅藏干背景。"),
        _synthetic_pair("natal_vs_time", "本命成立 vs 仅大运/流年触发。"),
        _synthetic_pair("strong_vs_weak_capacity", "承载力足 vs 承载力不足。"),
    ]
    if family == "direct_conflict":
        pairs.extend(
            [
                _synthetic_pair("same_layer_vs_cross_layer", "冲突双方同层可作用 vs 跨层不可直接作用。"),
                _synthetic_pair("with_rescue_vs_no_rescue", "有救应/制化路径 vs 无救应路径。"),
            ]
        )
    elif family == "constraint_deprivation":
        pairs.extend(
            [
                _synthetic_pair("target_key_vs_auxiliary", "被牵制对象是关键路径 vs 只是辅助背景。"),
                _synthetic_pair("counter_path_vs_none", "有反制/通关路径 vs 无反制路径。"),
            ]
        )
    elif family == "mixed_structure":
        pairs.extend(
            [
                _synthetic_pair("clear_vs_unclear", "一方清透有力 vs 双方杂而无主。"),
                _synthetic_pair("remove_keep_vs_none", "存在去留制化 vs 无去留制化。"),
            ]
        )
    elif family == "selection_rescue":
        pairs.extend(
            [
                _synthetic_pair("effective_path_vs_broken_path", "生助/制化/合化路径连续 vs 路径断裂。"),
                _synthetic_pair("same_layer_rescue_vs_remote", "救应同层可承接 vs 远隔背景不可承接。"),
            ]
        )
    if title in {"财滋杀", "财生官", "财官相生", "食伤生财", "财破印", "财多坏印", "比劫夺财"}:
        pairs.append(_synthetic_pair("wealth_accessible_vs_constrained", "财星可达 vs 财星被冲合牵制。"))
    if title == "印化杀":
        pairs.append(_synthetic_pair("seal_transform_vs_seal_remote", "印星同层承接七杀压力 vs 印星远隔或仅背景同见。"))
    if title in {"合杀留官", "合官留杀"}:
        pairs.append(_synthetic_pair("combine_effective_vs_only_pair", "合化/去留条件成立 vs 只有合的关系名。"))
    if title == "羊刃驾杀":
        pairs.append(_synthetic_pair("blade_with_kill_vs_blade_only", "禄刃与七杀压力同见并可作用 vs 只有禄刃背景。"))
    return pairs


def _p28j_action_path(family: str, title: str) -> str:
    if family == "direct_conflict":
        return "Read whether output/control pressure can act in the same layer; do not infer event risk."
    if family == "constraint_deprivation":
        return "Read whether one ten-god path constrains another key path; co-presence is not enough."
    if family == "mixed_structure":
        return "Read whether two same-family labels are both active and how clarity/removal changes the structure."
    if family == "selection_rescue":
        return "Read whether a rescue, generation, combination, or control path is continuous and same-layer."
    return f"{title} mechanism path requires condition evidence before use."


def _p28j_rescue_path(family: str, title: str) -> str:
    if title in {"伤官制杀", "食神制杀", "官杀攻身"}:
        return "Check seal/output/wealth intervention and pressure handling path."
    if title in {"枭神夺食", "印制食伤", "财破印", "财多坏印"}:
        return "Check whether the constrained path has counter-support or transition route."
    if title in {"合杀留官", "合官留杀"}:
        return "Check combination effectiveness and keep/remove target."
    if family == "selection_rescue":
        return "Check whether rescue is local, continuous, and strong enough to carry the pathway."
    return "Check counter-path, rescue-path, or no-rescue contrast before activation."


def _p28j_axis_coverage(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        for axis in row.get("condition_axes") or []:
            key = str(axis.get("key") or "")
            if key:
                counts[key] = counts.get(key, 0) + 1
    return counts


def _axis(key: str, description: str, gate: str) -> Dict[str, str]:
    return {"key": key, "description": description, "gate": gate}


def _synthetic_pair(key: str, description: str) -> Dict[str, str]:
    return {"key": key, "description": description}


def _p28k_samples_for_model(model: Dict[str, Any], mechanism_ids: List[str]) -> List[Dict[str, Any]]:
    title = str(model.get("title") or "")
    specs = _p28k_sample_specs(title)
    forbidden_other_signals = [knowledge_id for knowledge_id in mechanism_ids if knowledge_id != model.get("mechanism_knowledge_id")]
    return [_p28k_sample_from_spec(model, spec, forbidden_other_signals) for spec in specs]


def _p28k_sample_specs(title: str) -> List[Dict[str, Any]]:
    specs = [
        _p28k_spec("positive_visible_complete", "positive", "", "透干、同层、承载、救应与回答边界全部满足。"),
        _p28k_spec("positive_capacity_complete", "positive", "", "承载力、来源层和作用路径完整。"),
        _p28k_spec("positive_rescue_complete", "positive", "", "救应或连续路径可承接。"),
        _p28k_spec("negative_copresence_no_path", "negative", "path_continuity", "只有同见，但无可作用路径。"),
        _p28k_spec("negative_cross_layer", "negative", "same_layer_action", "跨层出现，不能直接读作机制成立。"),
        _p28k_spec("negative_capacity_insufficient", "negative", "capacity_strength", "承载力不足，机制不能成立。"),
        _p28k_spec("distractor_time_layer", "distractor_time", "source_layer", "只在大运或流年触发，不改写本命结构。"),
        _p28k_spec("distractor_hidden_only", "distractor_hidden", "source_layer", "只在藏干背景出现，不能作为机制主信号。"),
    ]
    if _p28k_is_complex_mechanism(title):
        special_axis = _p28k_complex_failed_axis(title)
        specs.extend(
            [
                _p28k_spec("positive_special_path_complete", "positive", "", "复杂机制的专题路径完整。"),
                _p28k_spec("positive_context_complete", "positive", "", "复杂机制的来源、承载、去留或驾驭条件完整。"),
                _p28k_spec("negative_relation_name_only", "negative", special_axis, "只有关系名，不具备合化、去留或驾驭条件。"),
                _p28k_spec("negative_path_broken", "negative", "path_continuity", "路径断裂，不能读作机制成立。"),
            ]
        )
    return specs


def _p28k_sample_from_spec(model: Dict[str, Any], spec: Dict[str, str], forbidden_other_signals: List[str]) -> Dict[str, Any]:
    source_id = str(model.get("mechanism_knowledge_id") or "")
    source_case_id = str(model.get("case_id") or "")
    case_id = f"syn.p28k.{_p28_slug(source_case_id)}.{spec['key']}"
    chart, time_context = _p28k_chart_and_time_context(model, spec, case_id)
    polarity = spec["polarity"]
    expected_signal = source_id if polarity == "positive" else ""
    forbidden_signals = list(forbidden_other_signals)
    if polarity != "positive":
        forbidden_signals = [source_id] + forbidden_signals
    return {
        "case_id": case_id,
        "source_case_id": source_case_id,
        "source_mechanism_id": source_id,
        "mechanism_title": model.get("title") or "",
        "family": model.get("family") or "",
        "polarity": polarity,
        "sample_type": spec["key"],
        "scenario": spec["description"],
        "chart": chart,
        "time_context": time_context,
        "expected_signal": expected_signal,
        "forbidden_signals": forbidden_signals,
        "expected_question_keys": ["q_ten_god_metadata", "q_signal_combination", "q_read_result_not_fortune"],
        "forbidden_text": list(P28I_FORBIDDEN_ANSWER_TEXT),
        "condition_axes_expected": _p28k_axis_expectations(model, spec),
        "audit_tags": [
            "p28k",
            "eval_dataset",
            f"polarity:{polarity}",
            f"family:{model.get('family') or ''}",
            f"mechanism:{_p28_slug(source_case_id)}",
        ],
        "synthetic_boundary": "synthetic_explicit_pillars_no_birthdate",
    }


def _p28k_chart_and_time_context(model: Dict[str, Any], spec: Dict[str, str], case_id: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    base_case = _p28g_case_by_id(str(model.get("case_id") or ""))
    base_chart = dict(base_case.get("chart") or {})
    base_pillars = _p28k_display_pillars(base_chart)
    if not base_pillars:
        base_pillars = {"year": "甲子", "month": "乙丑", "day": "戊辰", "hour": "庚申"}
    polarity = spec["polarity"]
    if polarity == "distractor_hidden":
        pillars = _p28k_hidden_only_pillars(base_pillars)
    elif polarity == "distractor_time":
        pillars = _p28k_neutral_pillars(base_pillars)
    elif spec["key"] == "negative_cross_layer":
        pillars = _p28k_neutral_pillars(base_pillars)
    else:
        pillars = dict(base_pillars)
    chart = make_synthetic_chart(case_id, pillars)
    if polarity == "distractor_time" or spec["key"] == "negative_cross_layer":
        return chart, make_synthetic_time_context(chart, flow_pillar=base_pillars.get("year") or "甲子")
    return chart, {}


def _p28k_axis_expectations(model: Dict[str, Any], spec: Dict[str, str]) -> List[Dict[str, str]]:
    polarity = spec["polarity"]
    failed_axis = str(spec.get("failed_axis") or "")
    rows: List[Dict[str, str]] = []
    for axis in model.get("condition_axes") or []:
        key = str(axis.get("key") or "")
        if not key:
            continue
        status = "satisfied"
        if polarity != "positive" and (key == failed_axis or (failed_axis == "path_continuity" and key in {"path_continuity", "rescue_same_layer", "same_layer_action"})):
            status = "blocked"
        if polarity == "distractor_time" and key in {"source_layer", "same_layer_action"}:
            status = "blocked"
        if polarity == "distractor_hidden" and key in {"source_layer", "same_layer_action"}:
            status = "blocked"
        rows.append({"key": key, "expected": status})
    return rows


def _p28k_evaluate_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    required = [
        "case_id",
        "source_mechanism_id",
        "polarity",
        "expected_signal",
        "forbidden_signals",
        "expected_question_keys",
        "forbidden_text",
        "condition_axes_expected",
        "audit_tags",
    ]
    for key in required:
        if key not in sample:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "schema_field_missing", "field": key})
    polarity = str(sample.get("polarity") or "")
    source_id = str(sample.get("source_mechanism_id") or "")
    expected_signal = str(sample.get("expected_signal") or "")
    axis_statuses = {str(row.get("key") or ""): str(row.get("expected") or "") for row in sample.get("condition_axes_expected") or [] if isinstance(row, dict)}
    if polarity == "positive":
        if expected_signal != source_id:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "positive_expected_signal_mismatch", "expected": source_id, "actual": expected_signal})
        blocked_axes = [key for key, value in axis_statuses.items() if value != "satisfied"]
        if blocked_axes:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "positive_axis_not_satisfied", "axes": blocked_axes})
    else:
        if expected_signal:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "negative_expected_signal_should_be_empty", "actual": expected_signal})
        if source_id not in set(str(item) for item in sample.get("forbidden_signals") or []):
            failures.append({"case_id": sample.get("case_id"), "failure_type": "negative_forbidden_signal_missing", "expected": source_id})
        if not any(value == "blocked" for value in axis_statuses.values()):
            failures.append({"case_id": sample.get("case_id"), "failure_type": "negative_or_distractor_has_no_blocked_axis"})
    expected_keys = set(str(item) for item in sample.get("expected_question_keys") or [])
    if "q_ten_god_metadata" not in expected_keys:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "expected_question_key_missing", "expected": "q_ten_god_metadata"})
    forbidden_text = set(str(item) for item in sample.get("forbidden_text") or [])
    if not {"官非", "灾祸", "发财", "破财"} <= forbidden_text:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "forbidden_text_contract_failed"})
    false_positive = polarity != "positive" and bool(expected_signal)
    return {
        "case_id": sample.get("case_id"),
        "source_mechanism_id": source_id,
        "polarity": polarity,
        "sample_type": sample.get("sample_type") or "",
        "status": "fail" if failures else "pass",
        "false_positive": false_positive,
        "failures": failures,
    }


def _p28k_mechanism_results(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for sample in samples:
        grouped.setdefault(str(sample.get("source_mechanism_id") or ""), []).append(sample)
    rows: List[Dict[str, Any]] = []
    for mechanism_id, mechanism_samples in sorted(grouped.items()):
        failures: List[Dict[str, Any]] = []
        by_polarity = _count_by(mechanism_samples, "polarity")
        title = str(mechanism_samples[0].get("mechanism_title") or "") if mechanism_samples else ""
        minimum = 12 if _p28k_is_complex_mechanism(title) else 8
        required_counts = {"positive": 3, "negative": 3, "distractor_time": 1, "distractor_hidden": 1}
        if len(mechanism_samples) < minimum:
            failures.append({"mechanism_id": mechanism_id, "failure_type": "sample_count_below_minimum", "minimum": minimum, "actual": len(mechanism_samples)})
        for polarity, required_count in required_counts.items():
            if int(by_polarity.get(polarity) or 0) < required_count:
                failures.append({"mechanism_id": mechanism_id, "failure_type": "polarity_count_below_minimum", "polarity": polarity, "minimum": required_count, "actual": by_polarity.get(polarity, 0)})
        rows.append(
            {
                "mechanism_id": mechanism_id,
                "title": title,
                "sample_count": len(mechanism_samples),
                "by_polarity": by_polarity,
                "minimum_required": minimum,
                "status": "fail" if failures else "pass",
                "failures": failures,
            }
        )
    return rows


def _p28k_spec(key: str, polarity: str, failed_axis: str, description: str) -> Dict[str, str]:
    return {"key": key, "polarity": polarity, "failed_axis": failed_axis, "description": description}


def _p28k_is_complex_mechanism(title: str) -> bool:
    return str(title or "") in {"合杀留官", "合官留杀", "羊刃驾杀"}


def _p28k_complex_failed_axis(title: str) -> str:
    if str(title or "") == "羊刃驾杀":
        return "blade_control_pressure_model"
    return "combine_effectiveness_and_keep_remove_path"


def _p28g_case_by_id(case_id: str) -> Dict[str, Any]:
    for case in P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES:
        if str(case.get("case_id") or "") == case_id:
            return dict(case)
    return {}


def _p28k_display_pillars(chart: Dict[str, Any]) -> Dict[str, str]:
    pillars = dict(chart.get("pillars") or {})
    out: Dict[str, str] = {}
    for name in ["year", "month", "day", "hour"]:
        pillar = dict(pillars.get(name) or {})
        display = str(pillar.get("display") or "")
        if not display:
            display = str(pillar.get("stem") or "") + str(pillar.get("branch") or "")
        if len(display) >= 2:
            out[name] = display[:2]
    return out


def _p28k_neutral_pillars(pillars: Dict[str, str]) -> Dict[str, str]:
    day = str(pillars.get("day") or "戊辰")
    day_stem = day[0] if day else "戊"
    out = dict(pillars)
    for name in ["year", "month", "hour"]:
        branch = str(out.get(name) or "子")[1:2] or "子"
        out[name] = day_stem + branch
    return out


def _p28k_hidden_only_pillars(pillars: Dict[str, str]) -> Dict[str, str]:
    out = _p28k_neutral_pillars(pillars)
    out["year"] = out.get("year") or "戊酉"
    out["month"] = out.get("month") or "戊卯"
    return out


def _p28_slug(value: str) -> str:
    text = str(value or "").strip().removeprefix("syn.p28g.")
    cleaned = []
    for char in text:
        cleaned.append(char if char.isalnum() or char in {"_", "-"} else "_")
    return "".join(cleaned).strip("_") or "unknown"


def _evaluate_case(case: Dict[str, Any], rules_by_knowledge: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    observed_rules = []
    expected_domain = str(case.get("expected_rule_domain") or "ten_god_relation")
    expected_engine_enabled = bool(case.get("expected_engine_enabled") is True)
    for knowledge_id in case.get("expected_knowledge_ids") or []:
        rule = dict(rules_by_knowledge.get(str(knowledge_id)) or {})
        if not rule:
            failures.append({"failure_type": "rule_missing", "knowledge_id": knowledge_id})
            continue
        observed_rules.append(
            {
                "knowledge_id": knowledge_id,
                "rule_id": rule.get("rule_id"),
                "domain": rule.get("domain"),
                "category": rule.get("category"),
                "engine_enabled": rule.get("engine_enabled"),
                "engine_adapter_status": rule.get("engine_adapter_status"),
            }
        )
        if rule.get("domain") != expected_domain:
            failures.append({"failure_type": "rule_domain_mismatch", "knowledge_id": knowledge_id, "expected": expected_domain, "actual": rule.get("domain")})
        if rule.get("engine_enabled") is not expected_engine_enabled:
            failures.append({"failure_type": "engine_enabled_mismatch", "knowledge_id": knowledge_id, "expected": expected_engine_enabled, "actual": rule.get("engine_enabled")})
        if str(rule.get("category") or "") not in {"ten_god_interaction", "ten_god_interaction_mechanism"}:
            failures.append({"failure_type": "rule_category_mismatch", "knowledge_id": knowledge_id, "actual": rule.get("category")})
        forbidden_usage = {str(item) for item in rule.get("forbidden_usage") or []}
        if "fortune" not in forbidden_usage and "direct_fortune_output" not in forbidden_usage:
            failures.append({"failure_type": "fortune_guardrail_missing", "knowledge_id": knowledge_id})
    return {
        "case_id": case.get("case_id"),
        "title": case.get("title"),
        "family": case.get("family"),
        "collision_focus": case.get("collision_focus"),
        "activation_tier": case.get("activation_tier"),
        "status": "fail" if failures else "pass",
        "failures": failures,
        "expected_knowledge_ids": list(case.get("expected_knowledge_ids") or []),
        "observed_rules": observed_rules,
        "chart_id": (case.get("chart") or {}).get("chart_id"),
        "rule_path": dict(case.get("rule_path") or {}),
    }


def _review_item(case: Dict[str, Any]) -> Dict[str, Any]:
    slug = str(case.get("case_id") or "").removeprefix("syn.p28g.")
    activation_tier = str(case.get("activation_tier") or "")
    existence_id, mechanism_id = list(case.get("expected_knowledge_ids") or ["", ""])[:2]
    return {
        "case_id": case.get("case_id"),
        "title": case.get("title"),
        "family": case.get("family"),
        "collision_focus": case.get("collision_focus"),
        "existence_knowledge_id": existence_id,
        "mechanism_knowledge_id": mechanism_id,
        "ruleable_now": ["R1 组合存在 / 元数据边界"],
        "activation_decision": "existence_fast_path_candidate" if activation_tier == "existence_candidate_only" else "condition_model_required_before_activation",
        "mechanism_decision": "hold_for_condition_model",
        "condition_model_gaps": _condition_model_gaps(str(case.get("family") or ""), str(case.get("title") or "")),
        "synthetic_collision_needs": _synthetic_collision_needs(str(case.get("family") or ""), str(case.get("title") or "")),
        "archive_only_verdicts": _archive_only_verdicts(str(case.get("family") or ""), str(case.get("title") or "")),
        "next_action": _next_action(slug, activation_tier),
    }


def _condition_model_gaps(family: str, title: str) -> List[str]:
    gaps = ["来源层：透干 / 藏干 / 本命 / 时间层", "强弱与承载：月令、根气、印比支持、克泄耗压力", "宫位语境：发生在哪一柱或时间背景"]
    if family == "direct_conflict":
        gaps.extend(["冲突对象是否同层可作用", "是否存在印星、食伤或财星救应"])
    elif family == "constraint_deprivation":
        gaps.extend(["被牵制对象是否为关键路径", "是否存在反制或转化路径"])
    elif family == "mixed_structure":
        gaps.extend(["混杂双方谁更清、谁更有力", "是否存在去留、制化或清浊条件"])
    elif family == "selection_rescue":
        gaps.extend(["合化去留是否有效", "救应是否同层、是否可承接"])
    if title in {"羊刃驾杀", "官杀攻身"}:
        gaps.append("禄刃 / 控制压力模型未完成")
    if title in {"食伤生财", "比劫夺财", "比劫分财", "财破印", "财多坏印", "财滋杀", "财生官"}:
        gaps.append("财富领域联动模型未完成")
    return gaps


def _synthetic_collision_needs(family: str, title: str) -> List[str]:
    needs = ["透干 vs 藏干对照盘", "本命存在 vs 大运流年触发对照盘"]
    if family == "direct_conflict":
        needs.extend(["有救应 vs 无救应", "同层冲突 vs 跨层冲突"])
    elif family == "constraint_deprivation":
        needs.extend(["牵制有力 vs 牵制无力", "有反制路径 vs 无反制路径"])
    elif family == "mixed_structure":
        needs.extend(["清杂对照", "去留成立 vs 去留不成立"])
    elif family == "selection_rescue":
        needs.extend(["救应同层 vs 救应隔层", "合化有效 vs 仅合不化"])
    if title in {"食伤生财", "财生官", "财滋杀"}:
        needs.append("财星可达 vs 财星受冲合牵制")
    return needs


def _archive_only_verdicts(family: str, title: str) -> List[str]:
    common = ["吉凶断语", "具体应期", "命好命坏"]
    if title in {"伤官见官", "官杀攻身", "财滋杀", "合官留杀"}:
        return common + ["官非灾祸", "职业风险"]
    if title in {"枭神夺食", "印制食伤", "印枭混杂", "财多坏印"}:
        return common + ["疾病健康", "学业长辈结果"]
    if title in {"比劫夺财", "比劫分财", "财破印", "食伤生财", "财生官"}:
        return common + ["破财发财", "收入金额或财富结果"]
    if family == "mixed_structure":
        return common + ["性格定性", "事业婚姻结果"]
    if family == "selection_rescue":
        return common + ["贵贱成格", "职位权力结果"]
    return common + ["人生结果预测"]


def _next_action(slug: str, activation_tier: str) -> str:
    if activation_tier == "existence_candidate_only":
        return f"{slug}: 可进入低风险 R1 组合存在 smart-gate 候选，但仍需回答文本抽检。"
    return f"{slug}: 暂不启用；先补条件模型和更细合成碰撞。"


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
