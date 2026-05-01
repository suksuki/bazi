from __future__ import annotations

from v20.knowledge.loader import default_knowledge_units


def audit_default_knowledge_units() -> dict[str, object]:
    units = default_knowledge_units()
    failures: list[str] = []
    for unit in units:
        if unit.status != "reviewed":
            failures.append(f"not_reviewed:{unit.knowledge_id}")
        if "direct_rule_truth" not in unit.forbidden_usage:
            failures.append(f"missing_forbidden_rule_truth:{unit.knowledge_id}")
        if not unit.evidence_template or not unit.boundary:
            failures.append(f"missing_evidence_or_boundary:{unit.knowledge_id}")
    return {
        "version": "v20.knowledge_audit.v1",
        "status": "pass" if not failures else "fail",
        "unit_count": len(units),
        "failures": failures,
        "guardrails": ["KNOWLEDGE_AUDIT_ONLY", "NO_RULE_ACTIVATION"],
    }
