from __future__ import annotations


def analyst_api_scope() -> dict[str, object]:
    return {
        "version": "v20.analyst_api_scope.v1",
        "allowed": ["evidence_audit", "synthetic_case_label", "proposal_review"],
        "blocked": ["core_fact_mutation", "direct_runtime_activation"],
    }
