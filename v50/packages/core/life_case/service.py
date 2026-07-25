"""Stable LifeCase service API backed by responsibility-specific modules."""

from core.life_case.commit_service import (
    commit_baseline_life_case,
    commit_case_revision,
    commit_domain_insight,
    commit_temporal_prior,
)
from core.life_case.evidence_service import (
    build_reality_evidence,
    complete_monthly_review,
    ensure_temporal_snapshot,
    normalize_period_key,
    record_reality_evidence,
    upsert_reality_evidence,
)
from core.life_case.insight_service import (
    build_baseline_insight,
    build_case_revision_insight,
    build_domain_insight,
    validate_formal_insight,
)
from core.life_case.projection_service import formal_projection_record, project_life_case

__all__ = [
    "build_baseline_insight",
    "build_case_revision_insight",
    "build_domain_insight",
    "build_reality_evidence",
    "commit_baseline_life_case",
    "commit_case_revision",
    "commit_domain_insight",
    "commit_temporal_prior",
    "complete_monthly_review",
    "ensure_temporal_snapshot",
    "formal_projection_record",
    "normalize_period_key",
    "project_life_case",
    "record_reality_evidence",
    "upsert_reality_evidence",
    "validate_formal_insight",
]
