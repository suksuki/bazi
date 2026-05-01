from __future__ import annotations


def validate_rule_candidate_support(report: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    warnings: list[str] = []
    candidates = [row for row in report.get("candidates", ()) if isinstance(row, dict)]
    if report.get("runtime_mutation") is not False:
        failures.append("runtime_mutation_not_false")
    if not candidates:
        warnings.append("no_rule_candidates_available")
    for candidate in candidates:
        rule_id = str(candidate.get("rule_id", ""))
        if candidate.get("runtime_allowed") is not False:
            failures.append(f"runtime_allowed_before_promotion:{rule_id}")
        if "shadow" not in str(candidate.get("activation_scope", "")):
            failures.append(f"activation_scope_not_shadow:{rule_id}")
        if not candidate.get("condition_summary"):
            failures.append(f"missing_condition_summary:{rule_id}")
        if "验证" not in str(candidate.get("validation_summary", "")):
            failures.append(f"missing_validation_summary:{rule_id}")
    return {
        "version": "v20.rule_candidate_support_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "candidate_count": len(candidates),
        "failures": failures,
        "warnings": warnings,
        "runtime_mutation": False,
        "guardrails": [
            "RULE_CANDIDATE_VALIDATION_ONLY",
            "SHADOW_SCOPE_REQUIRED",
            "PROMOTION_REQUIRED_BEFORE_RUNTIME_ACTIVATION",
        ],
    }


def validate_rule_candidate_question_ranking(report: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    policy = report.get("policy", {})
    if report.get("runtime_mutation") is not False:
        failures.append("runtime_mutation_not_false")
    if isinstance(policy, dict):
        if policy.get("status") != "active_shadow":
            failures.append("ranking_policy_not_shadow")
        if float(policy.get("max_adjustment", 1.0)) > 0.06:
            failures.append("ranking_adjustment_too_large")
    else:
        failures.append("missing_policy")
    for row in report.get("domain_signals", ()):
        if not isinstance(row, dict):
            continue
        if float(row.get("ranking_weight", 0.0)) > 0.06:
            failures.append(f"domain_weight_too_large:{row.get('domain', '')}")
    return {
        "version": "v20.rule_candidate_question_ranking_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "domain_count": int(report.get("domain_count", 0)),
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_RANKING_VALIDATION_ONLY",
            "REORDER_ONLY",
            "NO_RULE_ACTIVATION",
        ],
    }
