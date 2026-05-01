from __future__ import annotations

from v20.features.schema import FeatureLayer
from v20.learning.proposal import LearningProposal


def propose_missing_case(feature_layer: FeatureLayer) -> LearningProposal:
    domains = sorted({feature.domain for feature in feature_layer.features})
    return LearningProposal(
        proposal_id="v20.active_learning.synthetic_gap_review",
        proposal_type="synthetic_case_needed",
        summary=f"Review synthetic coverage for domains: {', '.join(domains)}.",
        risk="low",
    )
