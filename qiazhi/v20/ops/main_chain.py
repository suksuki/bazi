from __future__ import annotations

from collections import Counter
from typing import Any

from v20.api.runtime import run_runtime_from_pillars
from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.rule_library import build_knowledge_rule_library, validate_knowledge_rule_library
from v20.learning.training_iteration import run_training_iteration


MAIN_CHAIN_REVIEW_VERSION = "v20.main_chain_review.v1"


def build_main_chain_review(
    *,
    rule_limit: int = 0,
    include_training: bool = False,
    progress=None,
) -> dict[str, object]:
    units = default_knowledge_units()
    reviewed_units = tuple(unit for unit in units if unit.status == "reviewed")
    rule_library = build_knowledge_rule_library(limit=rule_limit)
    rule_validation = validate_knowledge_rule_library(limit=rule_limit)
    sample_runtime = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.main_chain.review",
        user_text="我想看事业、财运和当前大运触发",
        luck_pillar="乙亥",
        flow_year_pillar="庚子",
    )
    runtime_summary = _runtime_summary(sample_runtime)
    arbitration_summary = _arbitration_summary(sample_runtime)
    training_report = (
        run_training_iteration(write=False, include_rule_batch=True, progress=progress)
        if include_training
        else {
            "version": "v20.training_iteration_report.skipped",
            "status": "skipped",
            "reason": "pass --include-training to run dry-run learning iteration",
            "runtime_mutation": False,
        }
    )
    failures = _failures(rule_validation, runtime_summary, training_report, include_training=include_training)
    return {
        "version": MAIN_CHAIN_REVIEW_VERSION,
        "status": "pass" if not failures else "needs_attention",
        "ok": not failures,
        "chain": [
            "KnowledgeUnit",
            "KnowledgeRuleDefinition",
            "RuleRuntimeReport",
            "BaziFeatureContext",
            "DomainDecisionReport",
            "TopicProjection",
            "PortraitSummary",
            "QuestionAgent",
            "EvidencePack",
            "AnswerPlan",
            "LLMPractitionerAdapter",
            "ArbitrationLoop",
            "TrainingIteration",
        ],
        "knowledge": {
            "unit_count": len(units),
            "reviewed_unit_count": len(reviewed_units),
            "domain_count": len({unit.domain for unit in units}),
            "domains": sorted({unit.domain for unit in units}),
        },
        "rule_library": _rule_library_summary(rule_library),
        "rule_validation": {
            "status": rule_validation.get("status", ""),
            "ok": rule_validation.get("ok", False),
            "definition_count": rule_validation.get("definition_count", 0),
            "failure_count": len(rule_validation.get("failures", ())),
            "failures": rule_validation.get("failures", ()),
        },
        "runtime_sample": runtime_summary,
        "arbitration_loop": arbitration_summary,
        "training_iteration": _training_summary(training_report),
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "MAIN_CHAIN_REVIEW_IS_READ_ONLY",
            "KNOWLEDGE_RULE_FEATURE_PORTRAIT_QUESTION_CHAIN_IS_SINGLE_SPINE",
            "FEATURE_CONTEXT_IS_COMPUTATION_BUS",
            "QUESTION_AGENT_MUST_SUPPRESS_ANSWERED_QUESTIONS",
            "LEARNING_OPTIMIZES_RANKING_AND_WEIGHTS_NOT_CHART_FACTS",
        ],
    }


def _runtime_summary(runtime: dict[str, object]) -> dict[str, object]:
    feature_layer = _dict(runtime.get("feature_layer"))
    decision_report = _dict(runtime.get("decision_report"))
    portrait = _dict(decision_report.get("portrait_projection") or runtime.get("portrait_graph_summary"))
    questions = [row for row in runtime.get("questions", ()) if isinstance(row, dict)]
    question_titles = [str(row.get("title", "")) for row in questions if str(row.get("title", ""))]
    question_domains = Counter(str(row.get("domain", "")) for row in questions if str(row.get("domain", "")))
    question_strategies = Counter(str(row.get("question_strategy", "")) for row in questions if str(row.get("question_strategy", "")))
    return {
        "version": "v20.main_chain_runtime_sample.v1",
        "input_id": runtime.get("input_id", ""),
        "feature_count": feature_layer.get("feature_count", 0),
        "feature_context_count": feature_layer.get("feature_context_count", 0),
        "decision_count": decision_report.get("decision_count", 0),
        "mainline_count": decision_report.get("mainline_count", 0),
        "rule_runtime_count": _dict(decision_report.get("rule_runtime_report")).get("rule_count", 0),
        "portrait_axis_count": portrait.get("axis_count", len(portrait.get("axes", ()) if isinstance(portrait.get("axes", ()), (list, tuple)) else ())),
        "question_count": len(questions),
        "question_unique_title_count": len(set(question_titles)),
        "question_domain_mix": dict(sorted(question_domains.items())),
        "question_strategy_mix": dict(sorted(question_strategies.items())),
        "selected_question": _dict(runtime.get("selected_question")).get("title", ""),
        "question_agent_status": _dict(runtime.get("question_agent_state")).get("status", ""),
        "answer_plan_focus": _dict(runtime.get("answer_plan")).get("focus", ""),
        "answer_text_present": bool(str(runtime.get("answer_text", "")).strip()),
        "core_seed_decision_status": decision_report.get("core_seed_decision_status", ""),
        "runtime_mutation": False,
    }


def _arbitration_summary(runtime: dict[str, object]) -> dict[str, object]:
    decision_report = _dict(runtime.get("decision_report"))
    model = _dict(decision_report.get("defeasible_decision_model"))
    states = {"mixed", "countered", "requires_review", "blocked", "weak_candidate"}
    rows = [
        row
        for row in model.get("argument_nodes", ())
        if isinstance(row, dict) and str(row.get("state", "")) in states
    ]
    by_state: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    for row in rows:
        state = str(row.get("state", ""))
        domain = str(row.get("domain", ""))
        by_state[state] = by_state.get(state, 0) + 1
        by_domain[domain] = by_domain.get(domain, 0) + 1
    return {
        "version": "v20.main_chain_arbitration_summary.v1",
        "status": "needs_review" if rows else "clean",
        "snapshot_count": len(rows),
        "state_counts": dict(sorted(by_state.items())),
        "domain_counts": dict(sorted(by_domain.items())),
        "training_target": "counter_evidence_weight_and_practitioner_calibration",
        "runtime_mutation": False,
    }


def _rule_library_summary(library: dict[str, object]) -> dict[str, object]:
    definitions = [row for row in library.get("definitions", ()) if isinstance(row, dict)]
    by_domain = Counter(str(row.get("domain", "")) for row in definitions if str(row.get("domain", "")))
    return {
        "status": library.get("status", ""),
        "definition_count": library.get("definition_count", 0),
        "atom_count": library.get("atom_count", 0),
        "portrait_output_count": library.get("portrait_output_count", 0),
        "question_output_count": library.get("question_output_count", 0),
        "runtime_allowed_count": library.get("runtime_allowed_count", 0),
        "domain_mix": dict(sorted(by_domain.items())),
    }


def _training_summary(report: dict[str, object]) -> dict[str, object]:
    return {
        "version": report.get("version", ""),
        "status": report.get("status", ""),
        "ok": report.get("ok", report.get("status") in {"pass", "skipped"}),
        "phase_count": report.get("phase_count", 0),
        "failure_count": report.get("failure_count", 0),
        "quality_finding_count": report.get("quality_finding_count", 0),
        "runtime_mutation": False,
    }


def _failures(
    rule_validation: dict[str, object],
    runtime_summary: dict[str, object],
    training_report: dict[str, object],
    *,
    include_training: bool,
) -> list[str]:
    failures: list[str] = []
    if rule_validation.get("ok") is not True:
        failures.append("knowledge_rule_validation_not_pass")
    if int(runtime_summary.get("feature_context_count", 0) or 0) <= 0:
        failures.append("feature_context_missing")
    if int(runtime_summary.get("decision_count", 0) or 0) <= 0:
        failures.append("decision_report_missing")
    if int(runtime_summary.get("portrait_axis_count", 0) or 0) <= 0:
        failures.append("portrait_projection_missing")
    if int(runtime_summary.get("question_count", 0) or 0) < 6:
        failures.append("question_agent_too_few_questions")
    if int(runtime_summary.get("question_unique_title_count", 0) or 0) < 6:
        failures.append("question_agent_titles_too_repetitive")
    if not runtime_summary.get("answer_text_present"):
        failures.append("answer_text_missing")
    if include_training and training_report.get("ok") is False:
        failures.append("training_iteration_failed")
    return failures


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
