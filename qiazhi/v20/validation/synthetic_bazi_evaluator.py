from __future__ import annotations

from typing import Any

from v20.validation.answer_safety_evaluator import evaluate_answer_safety
from v20.validation.synthetic_schema import RoleViewExpectation, SyntheticBaziCase


def evaluate_synthetic_bazi_actual(case: SyntheticBaziCase, actual: dict[str, Any]) -> dict[str, Any]:
    evaluator_results = (
        evaluate_rule_domains(case, actual),
        evaluate_portrait_labels(case, actual),
        evaluate_questions(case, actual),
        evaluate_role_views(case, actual),
        evaluate_role_answer_governance(case, actual),
        evaluate_answer_safety(case, actual),
    )
    failures = tuple(
        failure
        for result in evaluator_results
        for failure in result.get("failures", ())
    )
    return {
        "version": "v20.synthetic_bazi_evaluation.v1",
        "case_id": case.case_id,
        "ok": not failures,
        "evaluator_results": evaluator_results,
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_EVALUATION_ONLY",
            "NO_RUNTIME_RULE_MUTATION",
            "NO_POLICY_POINTER_MUTATION",
        ],
    }


def evaluate_synthetic_bazi_replay(case: SyntheticBaziCase, replay: dict[str, Any]) -> dict[str, Any]:
    actual = replay.get("actual", {}) if isinstance(replay, dict) else {}
    return evaluate_synthetic_bazi_actual(case, actual if isinstance(actual, dict) else {})


def evaluate_rule_domains(case: SyntheticBaziCase, actual: dict[str, Any]) -> dict[str, Any]:
    expected = set(case.expected.rule_domains)
    observed = set(_tuple(actual.get("decision_domains"))) | set(_tuple(actual.get("question_domains")))
    failures = tuple(f"missing_rule_domain:{domain}" for domain in sorted(expected - observed))
    return _result("rule_domains", not failures, failures, expected=expected, observed=observed)


def evaluate_portrait_labels(case: SyntheticBaziCase, actual: dict[str, Any]) -> dict[str, Any]:
    expected = set(case.expected.portrait_labels)
    observed = set(_tuple(actual.get("portrait_labels")))
    missing = [
        label for label in sorted(expected)
        if not _contains_label(label, observed)
    ]
    forbidden = [
        label for label in case.negative.forbidden_portrait_labels
        if _contains_label(label, observed)
    ]
    failures = tuple(
        [f"missing_portrait_label:{label}" for label in missing]
        + [f"forbidden_portrait_label:{label}" for label in forbidden]
    )
    return _result("portrait_labels", not failures, failures, expected=expected, observed=observed)


def evaluate_questions(case: SyntheticBaziCase, actual: dict[str, Any]) -> dict[str, Any]:
    expected_keys = set(case.expected.question_keys)
    observed_keys = set(_tuple(actual.get("question_keys")))
    observed_stages = _stage_set(_tuple(actual.get("question_stages")))
    missing_keys = sorted(expected_keys - observed_keys)
    forbidden_stages = sorted(_stage_set(case.negative.forbidden_question_stages) & observed_stages)
    failures = tuple(
        [f"missing_question_key:{key}" for key in missing_keys]
        + [f"forbidden_question_stage:{stage}" for stage in forbidden_stages]
    )
    return _result(
        "questions",
        not failures,
        failures,
        expected=expected_keys,
        observed=observed_keys,
        observed_stages=observed_stages,
    )


def evaluate_role_views(case: SyntheticBaziCase, actual: dict[str, Any]) -> dict[str, Any]:
    role_views = actual.get("role_views", {})
    if not isinstance(role_views, dict):
        role_views = {}
    failures: list[str] = []
    observed: dict[str, dict[str, Any]] = {}
    for expectation in case.role_expectations:
        view = role_views.get(expectation.role_key)
        if not isinstance(view, dict):
            failures.append(f"missing_role_view:{expectation.role_key}")
            continue
        observed[expectation.role_key] = view
        failures.extend(_evaluate_role_view(expectation, view))
    return {
        "evaluator": "role_views",
        "ok": not failures,
        "failures": tuple(failures),
        "observed_roles": tuple(sorted(observed)),
        "runtime_mutation": False,
    }


def evaluate_role_answer_governance(case: SyntheticBaziCase, actual: dict[str, Any]) -> dict[str, Any]:
    role_views = actual.get("role_views", {})
    if not isinstance(role_views, dict):
        role_views = {}
    failures: list[str] = []
    observed: dict[str, dict[str, Any]] = {}
    for expectation in case.role_expectations:
        role_key = expectation.role_key
        view = role_views.get(role_key)
        if not isinstance(view, dict):
            continue
        boundary_density = str(view.get("answer_boundary_density", ""))
        style_policy = str(view.get("answer_style_policy", ""))
        quality_band = str(view.get("answer_governance_quality_band", ""))
        observed[role_key] = {
            "answer_boundary_density": boundary_density,
            "answer_style_policy": style_policy,
            "answer_governance_quality_band": quality_band,
        }
        if not boundary_density:
            failures.append(f"missing_role_answer_boundary_density:{role_key}")
        if not style_policy:
            failures.append(f"missing_role_answer_style_policy:{role_key}")
        if role_key == "guest" and boundary_density not in {"plain_boundary"}:
            failures.append(f"role_answer_boundary_density_mismatch:{role_key}:{boundary_density}")
        if role_key == "analyst" and boundary_density not in {"technical_boundary_review"}:
            failures.append(f"role_answer_boundary_density_mismatch:{role_key}:{boundary_density}")
        if role_key in {"admin", "lab"} and boundary_density not in {"full_boundary_observation"}:
            failures.append(f"role_answer_boundary_density_mismatch:{role_key}:{boundary_density}")
    return {
        "evaluator": "role_answer_governance",
        "ok": not failures,
        "failures": tuple(failures),
        "observed_roles": tuple(sorted(observed)),
        "observed": observed,
        "runtime_mutation": False,
    }


def _evaluate_role_view(expectation: RoleViewExpectation, view: dict[str, Any]) -> tuple[str, ...]:
    failures: list[str] = []
    role_key = expectation.role_key
    observed_stages = _stage_set(_tuple(view.get("question_stages"))) | _stage_set(_tuple(view.get("question_style")))
    observed_stages -= _internal_stage_set()
    required = _stage_set(expectation.required_stages)
    forbidden = _stage_set(expectation.forbidden_stages)
    missing_required = sorted(stage for stage in required if not _stage_matches(stage, observed_stages))
    observed_forbidden = sorted(stage for stage in forbidden if _stage_matches(stage, observed_stages))
    if expectation.max_question_count and int(view.get("question_count") or 0) > expectation.max_question_count:
        failures.append(f"role_question_count_exceeded:{role_key}")
    if expectation.required_visibility:
        visibility = str(view.get("visibility_level") or "")
        if visibility != expectation.required_visibility:
            failures.append(f"role_visibility_mismatch:{role_key}:{visibility}")
    failures.extend(f"role_missing_stage:{role_key}:{stage}" for stage in missing_required)
    failures.extend(f"role_forbidden_stage:{role_key}:{stage}" for stage in observed_forbidden)
    return tuple(failures)


def _result(
    evaluator: str,
    ok: bool,
    failures: tuple[str, ...],
    *,
    expected: set[str],
    observed: set[str],
    observed_stages: set[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "evaluator": evaluator,
        "ok": ok,
        "failures": failures,
        "expected": tuple(sorted(expected)),
        "observed": tuple(sorted(observed)),
        "runtime_mutation": False,
    }
    if observed_stages is not None:
        payload["observed_stages"] = tuple(sorted(observed_stages))
    return payload


def _contains_label(expected: str, observed: set[str]) -> bool:
    aliases = _label_aliases(expected)
    return any(
        expected == label
        or expected in label
        or label in expected
        or bool(aliases & _label_aliases(label))
        for label in observed
    )


def _stage_matches(expected: str, observed_stages: set[str]) -> bool:
    aliases = _stage_aliases(expected)
    return bool(aliases & observed_stages)


def _stage_set(values: tuple[str, ...]) -> set[str]:
    stages: set[str] = set()
    for value in values:
        stages.update(_stage_aliases(value))
    return stages


def _stage_aliases(stage: str) -> set[str]:
    value = str(stage or "").strip()
    aliases = {
        "entry": {"entry", "starter", "starter_questions"},
        "focus": {"focus", "guided", "guided_questions", "domain_reading"},
        "review": {"review", "technical_review", "review_questions", "practitioner_review_question"},
        "observe": {"observe", "full_observation", "observation_questions", "full_observation_questions"},
        "advice": {"advice"},
        "structure": {"structure", "foundation"},
        "timing": {"timing", "time", "time_context"},
        "closure": {"closure"},
    }
    for key, row in aliases.items():
        if value == key or value in row:
            return set(row) | {key}
    return {value} if value else set()


def _internal_stage_set() -> set[str]:
    return {"arbitration"}


def _label_aliases(label: str) -> set[str]:
    value = str(label or "").strip()
    if not value:
        return set()
    aliases = {
        "wealth_capacity": {"财星压力", "财富承接", "财富承接画像", "财星通道", "输出变现"},
        "strength_capacity": {"资源承接", "日主承载", "日主承载画像", "结构扶抑", "结构压力边界"},
        "career_role": {"事业压力", "事业角色画像", "事业角色"},
        "relationship": {"关系互动", "关系互动画像", "关系牵动"},
        "branch": {"地支互动", "地支互动画像", "地支牵动"},
        "element": {"五行平衡", "五行气势画像", "调候取向画像"},
        "ten_god": {"十神角色", "十神角色画像", "印星缓冲"},
        "useful_god": {"用神候选", "调候取向画像"},
        "pattern": {"格局复核", "格局结构画像", "结构候选"},
        "time": {"时间触发", "时运触发画像", "岁运引动"},
        "system": {"系统观测", "策略来源"},
    }
    matched = {value}
    for group_key, names in aliases.items():
        if value == group_key or value in names or any(value in name or name in value for name in names):
            matched.add(group_key)
            matched.update(names)
    return matched


def _tuple(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple, set)):
        return tuple(str(row) for row in value if str(row))
    return (str(value),)
