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
    mainlines = [row for row in report.get("mainlines", ()) if isinstance(row, dict)]
    if not mainlines:
        failures.append("missing_mainlines")
    for row in mainlines:
        if not row.get("source_decision_keys"):
            failures.append(f"mainline_without_source_decisions:{row.get('mainline_key', '')}")
        if not row.get("question_seed"):
            failures.append(f"mainline_without_question_seed:{row.get('mainline_key', '')}")
        if str(row.get("domain", "")) not in {str(decision.get("domain", "")) for decision in decisions}:
            failures.append(f"mainline_domain_without_decision:{row.get('mainline_key', '')}")
    for row in decisions:
        if not row.get("rule_key"):
            failures.append("decision_without_rule_key")
        if not row.get("portrait_tags"):
            failures.append(f"decision_without_portrait_tags:{row.get('decision_key', '')}")
        if float(row.get("score", 0.0)) < 0 or float(row.get("score", 0.0)) > 1:
            failures.append(f"decision_score_out_of_range:{row.get('decision_key', '')}")
        for ref in row.get("knowledge_rule_refs", ()):
            if isinstance(ref, dict) and ref.get("runtime_allowed") is True:
                failures.append(f"knowledge_rule_ref_runtime_allowed:{row.get('decision_key', '')}")
            if isinstance(ref, dict) and ref.get("runtime_promotion_candidate") is True:
                failures.append(f"knowledge_rule_ref_runtime_promotion_candidate:{row.get('decision_key', '')}")
            if isinstance(ref, dict) and not ref.get("synthetic_state"):
                failures.append(f"knowledge_rule_ref_missing_synthetic_state:{row.get('decision_key', '')}")
    portrait = report.get("dynamic_portrait", {})
    if not isinstance(portrait, dict) or portrait.get("version") != "v20.dynamic_portrait.v1":
        failures.append("dynamic_portrait_missing")
    if isinstance(portrait, dict) and portrait.get("source") == "full_corpus_static_truth":
        failures.append("static_corpus_portrait_forbidden")
    bridge = report.get("knowledge_rule_bridge", {})
    if not isinstance(bridge, dict) or bridge.get("version") != "v20.decision_knowledge_rule_bridge.v1":
        failures.append("knowledge_rule_bridge_missing")
    if isinstance(bridge, dict) and bridge.get("runtime_mutation") is not False:
        failures.append("knowledge_rule_bridge_runtime_mutation")
    if isinstance(bridge, dict) and not bridge.get("validation_status"):
        failures.append("knowledge_rule_bridge_missing_validation_status")
    return {
        "version": "v20.decision_report_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "decision_count": len(decisions),
        "mainline_count": len(mainlines),
        "portrait_tag_count": int(portrait.get("tag_count", 0)) if isinstance(portrait, dict) else 0,
        "knowledge_rule_bridge_status": bridge.get("status", "") if isinstance(bridge, dict) else "",
        "knowledge_rule_mapped_decision_count": int(bridge.get("mapped_decision_count", 0)) if isinstance(bridge, dict) else 0,
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "VALIDATION_ONLY",
            "DYNAMIC_DECISIONS_REQUIRED",
            "STATIC_518K_PORTRAIT_TRUTH_FORBIDDEN_IN_RUNTIME",
        ],
    }
