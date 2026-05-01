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
