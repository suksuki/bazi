from __future__ import annotations

from v20.corpus.artifacts import read_corpus_training_artifacts
from v20.intelligence.generation import build_intelligence_generation_manifest
from v20.knowledge.rule_extraction import validate_llm_rule_extraction_report, validate_rule_extraction_report
from v20.knowledge.rule_proposal import build_first_wave_rule_proposal_preflight
from v20.validation.rule_synthetic import build_rule_synthetic_training_report, run_rule_synthetic_suite
from v20.validation.suite import run_synthetic_suite


def validate_intelligence_generation() -> dict[str, object]:
    manifest = build_intelligence_generation_manifest()
    synthetic = run_synthetic_suite()
    rule_synthetic = run_rule_synthetic_suite()
    rule_synthetic_training = build_rule_synthetic_training_report()
    rule_preflight = build_first_wave_rule_proposal_preflight(limit_per_domain=1)
    rule_extraction = validate_rule_extraction_report(limit=12)
    llm_rule_extraction = validate_llm_rule_extraction_report(limit=2)
    corpus_training = read_corpus_training_artifacts()
    failures = []
    if synthetic["ok"] is not True:
        failures.append("synthetic_suite_failed")
    if rule_synthetic["ok"] is not True:
        failures.append("rule_synthetic_suite_failed")
    if rule_synthetic_training["status"] != "ready":
        failures.append("rule_synthetic_training_not_ready")
    if manifest["knowledge_generation"]["reviewed_unit_count"] <= 0:
        failures.append("no_reviewed_knowledge_units")
    if manifest["rule_generation"]["proposal_count"] <= 0:
        failures.append("no_rule_proposals")
    if manifest["portrait_generation"]["source_policy"] != "dynamic_rule_decision_supported":
        failures.append("portrait_source_policy_mismatch")
    if manifest.get("bazi_domain_alignment", {}).get("version") != "v20.bazi_domain_alignment_manifest.v1":
        failures.append("bazi_domain_alignment_manifest_missing")
    if rule_preflight["status"] != "ready_for_shadow_training":
        failures.append("rule_proposals_not_ready_for_shadow_training")
    if rule_extraction["status"] != "pass":
        failures.append("rule_extraction_validation_failed")
    if llm_rule_extraction["status"] != "pass":
        failures.append("llm_rule_extraction_validation_failed")
    return {
        "version": "v20.intelligence_generation_validation.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "failures": failures,
        "synthetic": {
            "ok": synthetic["ok"],
            "case_count": synthetic["case_count"],
            "failure_count": len(synthetic["failures"]),
        },
        "rule_synthetic": {
            "ok": rule_synthetic["ok"],
            "case_count": rule_synthetic["case_count"],
            "failure_count": len(rule_synthetic["failures"]),
            "training_status": rule_synthetic_training["status"],
        },
        "bazi_domain_alignment": {
            "status": "ready" if "bazi_domain_alignment_manifest_missing" not in failures else "missing",
            "core_domain_count": len(manifest.get("bazi_domain_alignment", {}).get("core_domains", ())),
            "applied_domain_count": len(manifest.get("bazi_domain_alignment", {}).get("applied_domains", ())),
        },
        "shadow_training": {
            "allowed": rule_preflight["ok"] and rule_synthetic_training["status"] == "ready",
            "rule_preflight_status": rule_preflight["status"],
            "proposal_count": rule_preflight["proposal_count"],
            "rule_extraction_status": rule_extraction["status"],
            "rule_extraction_candidate_count": rule_extraction["candidate_count"],
            "rule_synthetic_training_status": rule_synthetic_training["status"],
            "llm_rule_extraction_status": llm_rule_extraction["status"],
            "llm_rule_extraction_fallback_count": llm_rule_extraction["fallback_count"],
            "corpus_training_artifact_status": corpus_training["status"],
        },
        "promotion": {
            "user_visible_rule_promotion_ready": False,
            "reason": "DecisionRegistry review and broader synthetic coverage are still required before user-visible promotion.",
            "requirement_count": rule_preflight["promotion_requirement_count"],
        },
        "runtime_mutation": False,
        "guardrails": [
            "VALIDATION_REPORT_ONLY",
            "RULE_SHADOW_TRAINING_REQUIRES_SYNTHETIC_GATE",
            "PROMOTION_REQUIRES_SYNTHETIC_AND_DECISION",
            "BAZI_DOMAIN_ALIGNMENT_REQUIRED",
            "NO_RUNTIME_MUTATION",
        ],
    }
