from __future__ import annotations

from v40.contracts.base import ReleaseRecommendation
from v40.contracts.evaluation import MetricSummary, ReleaseGateResult


def build_release_gate_from_metrics(
    metrics: MetricSummary,
    *,
    gate_id: str,
    candidate_version: str,
    regression_failures: list[str] | None = None,
) -> ReleaseGateResult:
    failures = regression_failures or []
    fact_gate = True
    golden_gate = metrics.overall_score >= 0.82
    overclaim_gate = metrics.overclaim_rate <= 0.05
    advice_gate = metrics.advice_grounding_rate >= 0.8
    probe_gate = metrics.probe_yield_score >= 0.45
    llm_gate = metrics.llm_boundary_violation_rate == 0
    leakage_gate = metrics.surface_leakage_rate == 0
    all_passed = all([fact_gate, golden_gate, overclaim_gate, advice_gate, probe_gate, llm_gate, leakage_gate]) and not failures
    return ReleaseGateResult(
        gate_id=gate_id,
        candidate_version=candidate_version,
        fact_gate_passed=fact_gate,
        golden_case_gate_passed=golden_gate,
        overclaim_gate_passed=overclaim_gate,
        advice_grounding_gate_passed=advice_gate,
        probe_yield_gate_passed=probe_gate,
        llm_boundary_gate_passed=llm_gate,
        leakage_gate_passed=leakage_gate,
        regression_failures=failures,
        recommendation=ReleaseRecommendation.APPROVE if all_passed else ReleaseRecommendation.NEEDS_REVIEW,
        production_write_allowed=False,
    )
