from __future__ import annotations


def validate_decision_report(report: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    if report.get("version") != "v20.decision_report.v1":
        failures.append("version_mismatch")
    if report.get("runtime_mutation") is not False:
        failures.append("runtime_mutation_must_be_false")
    decisions = [row for row in report.get("decisions", ()) if isinstance(row, dict)]
    if not decisions:
        failures.append("missing_decisions")
    for row in decisions:
        if not row.get("rule_key"):
            failures.append("decision_without_rule_key")
        if not row.get("portrait_tags"):
            failures.append(f"decision_without_portrait_tags:{row.get('decision_key', '')}")
        if float(row.get("score", 0.0)) < 0 or float(row.get("score", 0.0)) > 1:
            failures.append(f"decision_score_out_of_range:{row.get('decision_key', '')}")
    portrait = report.get("dynamic_portrait", {})
    if not isinstance(portrait, dict) or portrait.get("version") != "v20.dynamic_portrait.v1":
        failures.append("dynamic_portrait_missing")
    if isinstance(portrait, dict) and portrait.get("source") == "full_corpus_static_truth":
        failures.append("static_corpus_portrait_forbidden")
    return {
        "version": "v20.decision_report_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "decision_count": len(decisions),
        "portrait_tag_count": int(portrait.get("tag_count", 0)) if isinstance(portrait, dict) else 0,
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "VALIDATION_ONLY",
            "DYNAMIC_DECISIONS_REQUIRED",
            "STATIC_518K_PORTRAIT_TRUTH_FORBIDDEN_IN_RUNTIME",
        ],
    }
