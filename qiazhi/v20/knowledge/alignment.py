from __future__ import annotations

from v20.features.schema import FeatureLayer
from v20.knowledge.retrieval import retrieve_knowledge


def knowledge_feature_alignment(feature_layer: FeatureLayer) -> dict[str, object]:
    report = retrieve_knowledge(feature_layer)
    covered_domains = {ref.domain for ref in report.refs}
    feature_domains = {feature.domain for feature in feature_layer.features}
    missing = sorted(feature_domains - covered_domains)
    return {
        "version": "v20.knowledge_feature_alignment.v1",
        "status": "pass" if not missing else "needs_review",
        "feature_domains": sorted(feature_domains),
        "covered_domains": sorted(covered_domains),
        "missing_domains": missing,
        "retrieval_report": report.to_dict(),
        "guardrails": ["ALIGNMENT_AUDIT_ONLY", "NO_RUNTIME_MUTATION"],
    }
