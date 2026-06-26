from __future__ import annotations

from v30.brain import DIAGNOSIS_ROUTER_VERSION, route_real_bazi_diagnosis, summarize_diagnosis_route
from v30.diagnosis import (
    DIAGNOSIS_GRAPH_VERSION,
    build_diagnosis_graph,
    extract_diagnosis_features,
    extract_diagnosis_portraits,
    generate_diagnosis_claims,
    match_real_bazi_rules,
    summarize_diagnosis_graph,
    translate_dynamic_paths,
)
from v30.runtime import create_smoke_runtime


def _rbd_parts(role_key: str = "user"):
    runtime = create_smoke_runtime(
        f"rbd-router-runtime-{role_key}",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    paths = translate_dynamic_paths(runtime.structure_state, timing_context=runtime.chart_context.time_layers)
    matches = match_real_bazi_rules(
        feature_evidence=runtime.feature_evidence,
        structure_state=runtime.structure_state,
        model_signal_summary=runtime.question_plan.policy_effect["model_signal_summary"],
        krp_units=runtime.question_plan.policy_effect["krp_library_units"],
    )
    features = extract_diagnosis_features(
        feature_evidence=runtime.feature_evidence,
        matched_rules=matches,
        diagnosis_paths=paths,
    )
    portraits = extract_diagnosis_portraits(
        matched_rules=matches,
        diagnosis_paths=paths,
        krp_units=runtime.question_plan.policy_effect["krp_library_units"],
    )
    claims = generate_diagnosis_claims(
        matched_rules=matches,
        features=features,
        paths=paths,
        portraits=portraits,
    )
    graph = build_diagnosis_graph(
        reading_id=runtime.reading_id,
        matched_rules=matches,
        features=features,
        paths=paths,
        portraits=portraits,
        claims=claims,
    )
    return runtime, matches, features, paths, portraits, claims, graph


def test_diagnosis_graph_connects_evidence_rules_paths_portraits_and_claims() -> None:
    runtime, matches, features, paths, portraits, claims, graph = _rbd_parts()
    summary = summarize_diagnosis_graph(graph)

    assert summary["version"] == DIAGNOSIS_GRAPH_VERSION
    assert graph.reading_id == runtime.reading_id
    assert summary["node_counts"]["claim"] == len(claims)
    assert summary["node_counts"]["path"] == len(paths)
    assert summary["node_counts"]["matched_rule"] == len(matches)
    assert summary["node_counts"]["portrait"] == len(portraits)
    assert summary["edge_counts"]["supports"] > 0
    assert summary["edge_counts"]["explains"] > 0
    assert summary["edge_counts"]["blocks"] > 0
    assert graph.top_claim_ids
    assert graph.top_path_ids


def test_router_selects_wealth_claims_without_generating_facts() -> None:
    runtime, _, _, paths, portraits, claims, graph = _rbd_parts("user")
    route = route_real_bazi_diagnosis(
        reading_id=runtime.reading_id,
        role_key="user",
        graph=graph,
        claims=claims,
        paths=paths,
        portraits=portraits,
        requested_mode="wealth",
    )
    summary = summarize_diagnosis_route(route)
    selected = [claim for claim in claims if claim.claim_id in route.selected_claim_ids]

    assert summary["version"] == DIAGNOSIS_ROUTER_VERSION
    assert route.selected_domain == "wealth"
    assert route.expression_density == "standard"
    assert route.central_brain_generated_facts is False
    assert selected
    assert selected[0].domain == "wealth"
    assert any("财运沿" in claim.claim_text for claim in selected)
    assert "central_brain_selects_claims_not_facts" in route.safeguards
    assert "domain_claim_quality:wealth" in route.training_routes


def test_router_role_density_and_practitioner_diagnostic_scope() -> None:
    runtime, _, _, paths, portraits, claims, graph = _rbd_parts("practitioner")
    route = route_real_bazi_diagnosis(
        reading_id=runtime.reading_id,
        role_key="practitioner",
        graph=graph,
        claims=claims,
        paths=paths,
        portraits=portraits,
        requested_mode="practitioner_diagnostic",
    )
    selected = [claim for claim in claims if claim.claim_id in route.selected_claim_ids]

    assert route.expression_density == "dense"
    assert route.selected_claim_ids
    assert len(route.selected_claim_ids) >= 6
    assert {claim.domain for claim in selected} <= {"structure", "useful_god", "timing", "wealth", "career"}
    assert route.selected_path_ids
    assert route.selected_portrait_ids


def test_router_routes_hidden_factor_calibration_to_question_loop() -> None:
    runtime, _, _, paths, portraits, claims, graph = _rbd_parts("user")
    route = route_real_bazi_diagnosis(
        reading_id=runtime.reading_id,
        role_key="user",
        graph=graph,
        claims=claims,
        paths=paths,
        portraits=portraits,
        requested_mode="hidden_factor_calibration",
        selected_question_id="q-hidden-factor",
    )

    assert route.selected_domain == "hidden_factor"
    assert route.followup_required is True
    assert "selected_question:q-hidden-factor" in route.followup_reason
    assert "route_calibration_to_question_loop" in route.safeguards
    assert "question_strategy_calibration" in route.training_routes
    assert "hidden_factor_boundary_quality" in route.training_routes
