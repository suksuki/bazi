from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from v20.answer.measurement_policy import domain_label, feature_domains_for_applied_domain
from v20.features.schema import FeatureLayer

DOMAIN_BOUNDARIES = {
    "wealth": {
        "allowed_claim_types": ("wealth_material_visibility", "income_structure_context", "constraint_and_support_path"),
        "blocked_claim_types": ("guaranteed_event", "guaranteed_income", "profit_amount", "specific_gain_or_loss_event"),
    },
    "relationship": {
        "allowed_claim_types": ("relationship_structure_context", "interaction_pattern", "candidate_tension_or_support"),
        "blocked_claim_types": ("guaranteed_event", "guaranteed_marriage", "divorce_prediction", "private_partner_inference"),
    },
    "career": {
        "allowed_claim_types": ("role_structure_context", "authority_output_relation", "candidate_work_axis"),
        "blocked_claim_types": ("guaranteed_event", "guaranteed_promotion", "job_loss_prediction", "salary_prediction"),
    },
    "health": {
        "allowed_claim_types": ("five_element_balance_context", "stress_signal_boundary"),
        "blocked_claim_types": ("guaranteed_event", "diagnosis", "disease_prediction", "treatment_advice"),
    },
}


@dataclass(frozen=True)
class DomainProjection:
    version: str
    requested_domain: str
    measurement_topic: str
    source_feature_ids: tuple[str, ...]
    allowed_claim_types: tuple[str, ...]
    blocked_claim_types: tuple[str, ...]
    status: str
    boundary: str
    guardrails: tuple[str, ...] = (
        "DOMAIN_PROJECTION_IS_ANTI_CORRUPTION_LAYER",
        "FEATURES_REMAIN_SOURCE_OF_TRUTH",
        "NO_DIRECT_DOMAIN_VERDICT",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_domain_projection(feature_layer: FeatureLayer, requested_domain: str) -> DomainProjection:
    relevant_domains = feature_domains_for_applied_domain(requested_domain)
    features = [feature for feature in feature_layer.features if feature.domain in relevant_domains]
    policy = DOMAIN_BOUNDARIES.get(
        requested_domain,
        {
            "allowed_claim_types": ("structure_context", "evidence_boundary"),
            "blocked_claim_types": ("guaranteed_event", "fixed_fortune_verdict"),
        },
    )
    return DomainProjection(
        version="v20.domain_projection.v1",
        requested_domain=requested_domain,
        measurement_topic=domain_label(requested_domain),
        source_feature_ids=tuple(feature.feature_id for feature in features[:8]),
        allowed_claim_types=tuple(policy["allowed_claim_types"]),
        blocked_claim_types=tuple(policy["blocked_claim_types"]),
        status="ready" if features else "needs_feature_support",
        boundary=f"{domain_label(requested_domain)}只能由已编译特征投影，不从领域问题直接生成断语。",
    )
