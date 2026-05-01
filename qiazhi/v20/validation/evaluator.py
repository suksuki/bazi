from __future__ import annotations

from v20.answer.composer import compose_answer
from v20.answer.plan import AnswerPlan
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.validation.synthetic_schema import SyntheticCase


def evaluate_answer_plan(case: SyntheticCase, feature_layer: FeatureLayer, questions: tuple[QuestionCandidate, ...], plan: AnswerPlan) -> dict[str, object]:
    text = compose_answer(plan)
    feature_domains = {feature.domain for feature in feature_layer.features}
    question_keys = {question.question_key for question in questions}
    failures: list[str] = []
    for domain in case.expected_feature_domains:
        if domain not in feature_domains:
            failures.append(f"missing_feature_domain:{domain}")
    for key in case.expected_question_keys:
        if key not in question_keys:
            failures.append(f"missing_question:{key}")
    for term in case.forbidden_text:
        if term in text:
            failures.append(f"forbidden_text:{term}")
    return {
        "ok": not failures,
        "case_id": case.case_id,
        "failures": failures,
        "mutation_invariants": list(case.mutation_invariants),
        "guardrails": ["SYNTHETIC_EVAL_ONLY", "NO_RUNTIME_MUTATION"],
    }


def evaluate_runtime_result(case: SyntheticCase, result: dict[str, object]) -> dict[str, object]:
    feature_layer = result.get("feature_layer", {})
    features = feature_layer.get("features", []) if isinstance(feature_layer, dict) else []
    questions = result.get("questions", [])
    answer_text = str(result.get("answer_text", ""))
    decision_report = result.get("decision_report", {})
    decisions = decision_report.get("decisions", []) if isinstance(decision_report, dict) else []
    decision_domains = _decision_domains([row for row in decisions if isinstance(row, dict)])
    feature_domains = {str(row.get("domain", "")) for row in features if isinstance(row, dict)}
    question_keys = {str(row.get("question_key", "")) for row in questions if isinstance(row, dict)}
    failures: list[str] = []
    for domain in case.expected_feature_domains:
        if domain not in feature_domains:
            failures.append(f"missing_feature_domain:{domain}")
    for key in case.expected_question_keys:
        if key not in question_keys:
            failures.append(f"missing_question:{key}")
    for domain in case.expected_rule_candidate_domains:
        if domain not in decision_domains:
            failures.append(f"missing_decision_domain:{domain}")
    for term in case.forbidden_text:
        if term in answer_text:
            failures.append(f"forbidden_text:{term}")
    if result.get("runtime_mutation") is not False:
        failures.append("runtime_mutation_not_false")
    decision_validation = result.get("decision_validation", {})
    if isinstance(decision_validation, dict) and decision_validation.get("ok") is not True:
        failures.append("decision_validation_not_ok")
    return {
        "ok": not failures,
        "case_id": case.case_id,
        "feature_domains": sorted(feature_domains),
        "question_keys": sorted(question_keys),
        "decision_domains": sorted(decision_domains),
        "failures": failures,
        "mutation_invariants": list(case.mutation_invariants),
        "guardrails": ["SYNTHETIC_RUNTIME_EVAL_ONLY", "NO_RUNTIME_MUTATION"],
    }


def _decision_domains(rows: list[dict[str, object]]) -> set[str]:
    domains: set[str] = set()
    for row in rows:
        domain = str(row.get("domain", ""))
        if domain:
            domains.add(domain)
        rule_key = str(row.get("rule_key", ""))
        for marker, mapped in (
            (".ten_god.", "ten_god"),
            (".wealth.", "wealth"),
            (".strength.", "strength"),
            (".branch.", "branch"),
            (".time.", "time"),
            (".element.", "element"),
            (".useful_god.", "useful_god"),
            (".pattern.", "pattern"),
        ):
            if marker in rule_key:
                domains.add(mapped)
    return domains
