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
    feature_domains = {str(row.get("domain", "")) for row in features if isinstance(row, dict)}
    question_keys = {str(row.get("question_key", "")) for row in questions if isinstance(row, dict)}
    failures: list[str] = []
    for domain in case.expected_feature_domains:
        if domain not in feature_domains:
            failures.append(f"missing_feature_domain:{domain}")
    for key in case.expected_question_keys:
        if key not in question_keys:
            failures.append(f"missing_question:{key}")
    for term in case.forbidden_text:
        if term in answer_text:
            failures.append(f"forbidden_text:{term}")
    if result.get("runtime_mutation") is not False:
        failures.append("runtime_mutation_not_false")
    return {
        "ok": not failures,
        "case_id": case.case_id,
        "feature_domains": sorted(feature_domains),
        "question_keys": sorted(question_keys),
        "failures": failures,
        "mutation_invariants": list(case.mutation_invariants),
        "guardrails": ["SYNTHETIC_RUNTIME_EVAL_ONLY", "NO_RUNTIME_MUTATION"],
    }
