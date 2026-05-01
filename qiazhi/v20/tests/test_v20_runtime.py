from __future__ import annotations

import ast
from pathlib import Path

from v20.api.runtime import run_runtime_from_pillars
from v20.corpus.canonical_case import CanonicalCase
from v20.corpus.precompute_runner import precompute_case
from v20.llm.contracts import ANSWER_PLAN_REWRITE
from v20.llm.practitioner import accept_or_fallback_practitioner_answer
from v20.llm.tasks import (
    accept_or_fallback_rewrite,
    draft_rule_extraction_from_knowledge,
    interpret_user_intent,
    propose_feature_candidates,
    review_output_safety,
    suggest_question_candidates,
)
from v20.knowledge.alignment import knowledge_feature_alignment
from v20.knowledge.audit import audit_default_knowledge_units
from v20.knowledge.loader import default_knowledge_units
from v20.validation.evaluator import evaluate_answer_plan, evaluate_runtime_result
from v20.validation.golden import GOLDEN_CASES
from v20.validation.synthetic_schema import SyntheticCase


def test_v20_runtime_builds_dynamic_decision_answer_plan() -> None:
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="v20.test")

    assert result["version"] == "v20.runtime_result.v1"
    assert result["runtime_mutation"] is False
    assert result["locale"] == "zh"
    assert result["chart_facts"]["day_master"] == "甲"
    assert result["time_context"]["status"] == "not_provided"
    assert result["core_inference"]["guardrails"]
    assert result["feature_layer"]["status"] == "ready"
    assert result["feature_layer"]["feature_count"] >= 5
    assert result["feature_layer"]["macro_feature_count"] >= 4
    assert {row["domain"] for row in result["feature_layer"]["macro_features"]} >= {"strength", "branch", "wealth"}
    assert {row["domain"] for row in result["feature_layer"]["features"]} >= {"strength", "useful_god", "element", "branch", "wealth"}
    assert result["questions"]
    assert result["selected_question"]["question_key"]
    assert result["knowledge_alignment"]["status"] == "pass"
    assert result["knowledge_semantic_model"]["status"] == "ready"
    assert result["knowledge_semantic_validation"]["ok"] is True
    assert result["decision_report"]["version"] == "v20.decision_report.v1"
    assert result["decision_report"]["decision_count"] >= 5
    assert result["decision_validation"]["ok"] is True
    assert result["dynamic_portrait"]["version"] == "v20.dynamic_portrait.v1"
    assert result["dynamic_portrait"]["tag_count"] >= 1
    assert "feature_discovery" not in result
    assert "portrait_projection" not in result
    assert "portrait_intelligence" not in result
    assert "rule_candidate_support" not in result
    assert result["knowledge_report"]["count"] >= 6
    assert all(row["reviewed"] and row["evidence_template"] for row in result["knowledge_refs"])
    assert len(result["llm_capabilities"]) >= 6
    assert result["answer_plan"]["sections"]
    assert result["answer_plan"]["measurement_focus"] == "bazi_measurement"
    assert result["answer_plan"]["domain_projection"]["guardrails"]
    assert "guaranteed_event" in result["answer_plan"]["domain_projection"]["blocked_claim_types"]
    assert result["prediction_policy"]["core_focus"] == "bazi_measurement"
    assert result["llm_assist"]["status"] == "idle"
    assert result["llm_assist"]["context_pack"]["publishable"] is False
    assert result["llm_assist"]["context_pack"]["runtime_mutation"] is False
    assert "answer_plan_rewrite" in result["llm_assist"]["context_pack"]["task_contexts"]
    assert "practitioner_answer" in result["llm_assist"]["context_pack"]["task_contexts"]
    assert result["llm_assist"]["answer_safety_review"]["result"]["ok"] is True


def test_v20_dynamic_decisions_drive_questions_portrait_and_interaction() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "丁丑",
        "乙巳",
        input_id="v20.feature.discovery",
        user_text="我想重点看事业和财运",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
    )
    decision_domains = {row["domain"] for row in result["decision_report"]["decisions"]}
    question_domains = {row["domain"] for row in result["questions"]}

    assert result["decision_report"]["status"] == "ready"
    assert result["decision_validation"]["status"] == "pass"
    assert result["dynamic_portrait"]["status"] == "ready"
    assert {"career", "wealth"} & decision_domains
    assert {"career", "wealth"} & question_domains
    assert result["llm_assist"]["status"] == "ready"
    assert result["knowledge_semantic_validation"]["status"] == "pass"
    assert result["runtime_mutation"] is False
    assert "八字测算重点" in result["answer_text"]
    assert "确定事件" in result["answer_text"]
    assert "core." not in result["answer_text"]
    assert "feature." not in result["answer_text"]
    assert result["measurement_report"]["core_focus"] == "bazi_measurement"
    assert result["measurement_report"]["selected_question_key"] == result["selected_question"]["question_key"]
    assert all(row["role"] == "bazi_measurement_entry" for row in result["questions"])
    assert all(row["measurement_topic"] for row in result["questions"])
    assert all(row["alignment_status"] in {"bazi_core_aligned", "bazi_projection_aligned"} for row in result["questions"])
    assert all(row["bazi_focus"] for row in result["questions"])
    assert {"career", "wealth", "element"} & {row["domain"] for row in result["questions"]}


def test_v20_validation_and_llm_fallback_are_guarded(monkeypatch) -> None:
    monkeypatch.setenv("V20_LLM_ENABLED", "0")
    monkeypatch.setenv("V20_LLM_EXECUTE", "0")
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="v20.validation")
    rewritten = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.validation.rewrite",
        user_text="请按命理结构说明一下",
        llm_mode="rewrite",
    )
    practitioner = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.validation.practitioner",
        user_text="请像命理师一样说明主线",
        llm_mode="practitioner",
    )
    case = GOLDEN_CASES[0]
    eval_result = evaluate_answer_plan(
        case,
        _feature_layer_obj(result),
        _question_objs(result),
        _answer_plan_obj(result),
    )

    assert eval_result["ok"] is True
    bad = accept_or_fallback_rewrite(_answer_plan_obj(result), "一定发财，feature.x")
    assert bad["ok"] is False
    assert bad["source"] == "deterministic_fallback"
    hidden_bad = accept_or_fallback_rewrite(_answer_plan_obj(result), "你会在未来发大财")
    assert hidden_bad["ok"] is False
    assert "forbidden_semantic_pattern" in hidden_bad["validation"]["failures"]
    assert ANSWER_PLAN_REWRITE.task_name == "answer_plan_rewrite"
    safe = review_output_safety(result["answer_text"])
    assert safe["result"]["ok"] is True
    assert rewritten["llm_assist"]["answer_rewrite"]["status"] == "fallback"
    assert rewritten["llm_assist"]["answer_rewrite"]["source"] == "deterministic_fallback"
    assert rewritten["llm_assist"]["answer_safety_review"]["result"]["ok"] is True
    assert practitioner["llm_assist"]["practitioner_answer"]["status"] == "fallback"
    assert practitioner["llm_assist"]["practitioner_answer"]["source"] == "deterministic_fallback"
    assert practitioner["llm_assist"]["answer_safety_review"]["result"]["ok"] is True


def test_v20_practitioner_answer_accepts_only_verified_context_text() -> None:
    safe = accept_or_fallback_practitioner_answer(
        {
            "text": "命理主线先看日主承载、十神来源和地支互动，再回答当前问题的结构边界。",
            "mainline": "日主承载、十神来源、地支互动。",
            "question_answer": "只解释已验证结构，不扩展为事件。",
            "evidence_notes": ["已接入特征发现和知识边界。"],
            "next_questions": ["是否继续看用神候选？"],
            "boundary_notes": ["不输出固定吉凶。"],
        },
        "deterministic",
    )
    bad = accept_or_fallback_practitioner_answer(
        {
            "text": "你一定发财。",
            "mainline": "越界",
            "question_answer": "越界",
            "evidence_notes": [],
            "next_questions": [],
            "boundary_notes": [],
        },
        "deterministic",
    )

    assert safe["ok"] is True
    assert safe["source"] == "llm_practitioner_answer"
    assert bad["ok"] is False
    assert bad["source"] == "deterministic_fallback"


def test_v20_explicit_time_layer_routes_to_time_measurement() -> None:
    result = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.time",
        user_text="我想看流年触发",
        flow_year_pillar="庚子",
    )

    assert result["time_context"]["status"] == "ready"
    assert result["time_context"]["layers"][0]["layer_key"] == "flow_year"
    assert result["time_context"]["layers"][0]["ten_god"]["label"] == "七杀"
    assert {row["layer"] for row in result["time_context"]["relation_hits"]} == {"time"}
    assert "time" in {row["domain"] for row in result["feature_layer"]["features"]}
    assert result["selected_question"]["question_key"] == "q_time_layer_context"
    assert result["selected_question"]["domain"] == "time"
    assert {"q_time_layer_context", "q_time_relation_triggers"} <= {
        row["question_key"] for row in result["questions"]
    }
    assert "time" in {row["domain"] for row in result["knowledge_refs"]}
    assert result["llm_assist"]["routed_question_key"] == "q_time_layer_context"
    assert "时间层触发候选" in result["answer_text"]
    assert "庚子=七杀" in result["answer_text"]
    assert "日柱午与流年子冲" in result["answer_text"]
    assert "发财" not in result["answer_text"]


def test_v20_answers_include_verified_hidden_ten_god_material() -> None:
    result = run_runtime_from_pillars(
        "壬寅",
        "甲辰",
        "丙子",
        "甲午",
        input_id="v20.hidden-ten-god",
        question_key="q_hidden_stem_role",
    )

    assert result["selected_question"]["question_key"] == "q_hidden_stem_role"
    assert "十神显隐要分层读取" in result["answer_text"]
    assert "正官" in result["answer_text"]
    assert "七杀" in result["answer_text"]
    assert "feature." not in result["answer_text"]


def test_v20_p85_applied_domain_answers_use_professional_reading_paths() -> None:
    result = run_runtime_from_pillars(
        "壬寅",
        "甲辰",
        "丙子",
        "甲午",
        input_id="v20.p85.wealth",
        question_key="q_income_stability",
        flow_year_pillar="丙午",
        luck_pillar="庚戌",
    )

    assert "q_income_stability" in {row["question_key"] for row in result["questions"]}
    assert result["selected_question"]["question_key"] == "q_income_stability"
    assert result["selected_question"]["domain"] == "wealth"
    assert "动态裁决画像" in result["answer_text"]
    assert "财星" in result["answer_text"]
    assert "知识依据" in result["answer_text"]
    assert "财星材料边界" in result["answer_text"]
    assert "规则候选" not in result["answer_text"]
    assert "影子复核" not in result["answer_text"]
    assert "下一步" in result["answer_text"]
    assert "收益结果" not in result["answer_text"]
    assert "feature." not in result["answer_text"]
    assert "decision_knowledge_support" in {
        row["section_type"] for row in result["answer_plan"]["sections"]
    }
    assert "dynamic_decision_portrait" in {row["section_type"] for row in result["answer_plan"]["sections"]}
    synthetic = SyntheticCase(
        "v20.synthetic.wealth-rule-candidate",
        ("壬寅", "甲辰", "丙子", "甲午"),
        expected_feature_domains=("wealth", "ten_god", "strength"),
        expected_question_keys=("q_income_stability",),
        expected_rule_candidate_domains=("wealth",),
    )
    assert evaluate_runtime_result(synthetic, result)["ok"] is True


def test_v20_p85_time_answer_preserves_trigger_path_section() -> None:
    result = run_runtime_from_pillars(
        "壬寅",
        "甲辰",
        "丙子",
        "甲午",
        input_id="v20.p85.time",
        question_key="q_time_relation_triggers",
        flow_year_pillar="丙午",
        luck_pillar="庚戌",
    )

    assert "时间层触发候选" in result["answer_text"]
    assert "庚戌=偏财" in result["answer_text"]
    assert "丙午=比肩" in result["answer_text"]
    assert "月柱辰与大运戌冲" in result["answer_text"]
    assert "时间层触发边界" in result["answer_text"]
    assert "下一步" in result["answer_text"]
    assert "feature." not in result["answer_text"]


def test_v20_multilingual_answer_rendering_uses_deterministic_terms() -> None:
    en = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.locale.en",
        locale="en",
        user_text="timing",
        flow_year_pillar="庚子",
    )
    ko = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.locale.ko",
        locale="ko",
        user_text="세운",
        flow_year_pillar="庚子",
    )

    assert "time layer and flow triggers" in en["answer_text"]
    assert "命理测算主线" not in en["answer_text"]
    assert "시간층과 세운 촉발" in ko["answer_text"]
    assert "命理测算主线" not in ko["answer_text"]
    assert en["llm_assist"]["answer_safety_review"]["result"]["ok"] is True
    assert ko["llm_assist"]["answer_safety_review"]["result"]["ok"] is True


def test_v20_knowledge_and_llm_are_aligned_but_assistive() -> None:
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="v20.llm")
    routed = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.llm.routed",
        user_text="我想看财和用神",
    )
    feature_layer = _feature_layer_obj(result)
    questions = _question_objs(result)

    audit = audit_default_knowledge_units()
    alignment = knowledge_feature_alignment(feature_layer)
    intent = interpret_user_intent("我想看财和用神，以及有没有地支冲合", feature_layer)
    suggestions = suggest_question_candidates("我想看财和用神", feature_layer, questions)
    proposals = propose_feature_candidates("我想看财和用神", feature_layer)
    rule_draft = draft_rule_extraction_from_knowledge(default_knowledge_units()[0])

    assert audit["status"] == "pass"
    assert alignment["status"] == "pass"
    assert intent["runtime_mutation"] is False
    assert {"wealth", "useful_god", "branch"} <= set(intent["result"]["feature_domains"])
    assert suggestions["runtime_mutation"] is False
    assert proposals["runtime_mutation"] is False
    assert all(row["status"] == "proposal_only" for row in proposals["candidates"])
    assert rule_draft["runtime_mutation"] is False
    assert rule_draft["validation"]["ok"] is True
    assert rule_draft["draft"]["status"] == "draft_only"
    assert routed["llm_assist"]["status"] == "ready"
    assert routed["llm_assist"]["routed_question_key"] == "q_useful_god_candidates"
    assert routed["llm_assist"]["context_pack"]["user_text_present"] is True
    assert routed["llm_assist"]["context_pack"]["knowledge_ref_count"] >= 1
    assert routed["selected_question"]["question_key"] == "q_useful_god_candidates"
    assert routed["llm_assist"]["answer_safety_review"]["result"]["ok"] is True


def test_v20_corpus_precompute_is_dry_run_only() -> None:
    case = CanonicalCase("v20.case.sample", ("甲子", "戊辰", "甲午", "辛酉"))
    snapshot = precompute_case(case)

    assert snapshot["case"]["input_hash"]
    assert snapshot["runtime_mutation"] is False
    assert snapshot["feature_count"] >= 5
    assert "PRECOMPUTE_DRY_RUN_ONLY" in snapshot["guardrails"]


def test_v20_package_does_not_import_v19() -> None:
    root = Path(__file__).resolve().parents[2]
    for path in (root / "v20").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(name == "v19" or name.startswith("v19.") for name in names), path


def _feature_layer_obj(result):
    from v20.features.schema import BaziFeature, EvidenceRef, FeatureLayer

    features = []
    for row in result["feature_layer"]["features"]:
        features.append(
            BaziFeature(
                feature_id=row["feature_id"],
                title=row["title"],
                domain=row["domain"],
                source_layers=tuple(row["source_layers"]),
                evidence_refs=tuple(EvidenceRef(**ref) for ref in row["evidence_refs"]),
                confidence=row["confidence"],
                readiness=row["readiness"],
                boundary=row["boundary"],
                question_hooks=tuple(row["question_hooks"]),
                answer_hooks=tuple(row["answer_hooks"]),
                calibration_state=row["calibration_state"],
            )
        )
    return FeatureLayer(version=result["feature_layer"]["version"], status=result["feature_layer"]["status"], features=tuple(features))


def _question_objs(result):
    from v20.interaction.questions import QuestionCandidate

    return tuple(QuestionCandidate(**row) for row in result["questions"])


def _answer_plan_obj(result):
    from v20.answer.evidence import EvidencePack
    from v20.answer.plan import AnswerPlan, AnswerSection

    pack = result["answer_plan"]["evidence_pack"]
    return AnswerPlan(
        version=result["answer_plan"]["version"],
        question_key=result["answer_plan"]["question_key"],
        sections=tuple(AnswerSection(**row) for row in result["answer_plan"]["sections"]),
        evidence_pack=EvidencePack(
            version=pack["version"],
            feature_ids=tuple(pack["feature_ids"]),
            evidence_refs=tuple(pack["evidence_refs"]),
            boundaries=tuple(pack["boundaries"]),
            measurement_domains=tuple(pack["measurement_domains"]),
            guardrails=tuple(pack["guardrails"]),
        ),
        measurement_focus=result["answer_plan"]["measurement_focus"],
        prediction_policy=result["answer_plan"]["prediction_policy"],
        domain_projection=result["answer_plan"]["domain_projection"],
        guardrails=tuple(result["answer_plan"]["guardrails"]),
    )
