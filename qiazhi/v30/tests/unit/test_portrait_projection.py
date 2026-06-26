from __future__ import annotations

from v30.portrait import (
    build_macro_portrait_projection_views,
    build_macro_portrait_projections,
    summarize_macro_portrait_projection_views,
    summarize_macro_portrait_projections,
)
from v30.runtime import create_smoke_runtime


def test_build_macro_portrait_projections_from_runtime_macro_signals() -> None:
    runtime = create_smoke_runtime("v30-portrait-projection-test")
    signals = runtime.question_plan.policy_effect["macro_dimension_signals"]
    projections = build_macro_portrait_projections(signals)
    domains = {row.domain for row in projections}
    assert domains >= {"wealth", "career", "relationship", "romance", "health", "hidden_factor"}
    assert all(row.evidence_ids for row in projections)
    assert all(row.boundaries for row in projections)
    assert all(row.source_policy == "portrait_is_projection_not_fact_source" for row in projections)


def test_macro_portrait_summary_matches_runtime_projection_payload() -> None:
    runtime = create_smoke_runtime("v30-portrait-summary-test")
    projections = build_macro_portrait_projections(runtime.question_plan.policy_effect["macro_dimension_signals"])
    summary = summarize_macro_portrait_projections(projections)
    assert summary == runtime.question_plan.policy_effect["macro_portrait_summary"]
    assert summary["projection_count"] >= 7
    assert "wealth_channel" in summary["portrait_dimensions"]


def test_macro_portrait_projection_views_are_role_and_client_filtered() -> None:
    runtime = create_smoke_runtime("v30-portrait-view-test")
    projections = runtime.question_plan.policy_effect["macro_portrait_projections"]
    user_views = build_macro_portrait_projection_views(projections, role_key="user", client="web")
    guest_views = build_macro_portrait_projection_views(projections, role_key="guest", client="mobile")
    admin_views = build_macro_portrait_projection_views(projections, role_key="admin", client="admin")
    assert any(row.domain == "hidden_factor" and row.visibility == "boundary_visible" for row in user_views)
    assert not any(row.domain == "hidden_factor" for row in guest_views)
    assert any(row.domain == "hidden_factor" and row.visibility == "diagnostic" for row in admin_views)
    assert all(row.density == "compact" for row in guest_views)
    summary = summarize_macro_portrait_projection_views(admin_views)
    assert summary["roles"] == ["admin"]
    assert summary["hidden_factor_view_count"] >= 1
    assert summary["source_policy"] == "portrait_is_projection_not_fact_source"
