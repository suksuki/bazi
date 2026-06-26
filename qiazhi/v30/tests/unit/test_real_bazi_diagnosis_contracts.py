from __future__ import annotations

import pytest
from pydantic import ValidationError

from v30.diagnosis import (
    DIAGNOSIS_CONTRACT_VERSION,
    DiagnosisClaim,
    DiagnosisContext,
    DiagnosisFeature,
    DiagnosisGraph,
    DiagnosisGraphEdge,
    DiagnosisGraphNode,
    DiagnosisPath,
    DiagnosisPortrait,
    DiagnosisRouteDecision,
    MatchedRule,
    RealBaziDiagnosis,
)


def _context() -> DiagnosisContext:
    return DiagnosisContext(
        context_id="ctx:diagnosis",
        reading_id="rbd-contract",
        chart_context_id="chart:rbd-contract",
        role_key="user",
        diagnosis_mode="overview",
        active_domains=["career", "wealth"],
        immutable_chart_fact_ids=["pillar:year", "pillar:month", "pillar:day", "pillar:hour"],
        active_time_layers={"luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        strongest_evidence_families=["wealth_authority_resource_path"],
        counter_evidence_families=["single_factor_reading"],
        blocked_claim_types=["fixed_event_prediction", "chart_fact_mutation"],
        evidence_ids=["ev:domain_rule", "ev:path"],
        policy_versions={"rule_policy": "rule.v1"},
    )


def _matched_rule() -> MatchedRule:
    return MatchedRule(
        rule_match_id="match:wealth_authority_resource",
        rule_id="rule:wealth_authority_resource",
        source_family_ids=["v30.source.yuan_hai_zi_ping_pattern_catalog"],
        domain_targets=["career", "wealth"],
        match_strength=0.82,
        required_context_hit=["ten_god_family:wealth", "ten_god_family:authority", "ten_god_family:resource"],
        counter_context_hit=[],
        missing_context=[],
        claim_templates=["财官印路径以资源、责任、规则承接为主。"],
        blocked_claims=["fixed_event_prediction"],
        evidence_ids=["ev:domain_rule"],
        path_ids=["path:wealth_authority_resource"],
    )


def _feature() -> DiagnosisFeature:
    return DiagnosisFeature(
        feature_id="feature:month_command",
        family="month_command",
        domain="structure",
        statement="月令和五行分布提示此局不能只按单一旺衰直断。",
        evidence_ids=["ev:month_command"],
        confidence_band="high",
        supports_claim_types=["feature", "path"],
    )


def _path() -> DiagnosisPath:
    return DiagnosisPath(
        path_id="path:wealth_authority_resource",
        family_chain=["wealth", "authority", "resource", "day_master"],
        mechanism="财官印制化",
        domain_targets=["career", "wealth"],
        diagnosis_statement="财星先牵动官杀压力，再由印星承接回到日主。",
        risk_statement="不能把财星单独断成稳定财源。",
        timing_trigger={"luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        score=0.86,
        evidence_ids=["ev:path", "ev:domain_rule"],
        blocked_overclaim=["fixed_wealth_outcome_claim"],
    )


def _portrait() -> DiagnosisPortrait:
    return DiagnosisPortrait(
        portrait_id="portrait:resource_pressure",
        dimension="resource_pressure_conversion",
        domain="career",
        statement="此类画像更偏向通过规则、资质、平台承接压力，而非单纯凭冲劲取财。",
        evidence_ids=["ev:domain_rule"],
        path_ids=["path:wealth_authority_resource"],
        confidence_band="high",
    )


def _claim() -> DiagnosisClaim:
    return DiagnosisClaim(
        claim_id="claim:career_resource_platform",
        claim_level="domain",
        domain="career",
        claim_text="此局事业不宜单看财，财星容易牵动官杀压力，真正可用处在印星承接。",
        confidence_band="high",
        evidence_ids=["ev:domain_rule"],
        rule_ids=["rule:wealth_authority_resource"],
        path_ids=["path:wealth_authority_resource"],
        portrait_ids=["portrait:resource_pressure"],
        blocked_overclaim=["fixed_promotion_year"],
    )


def _graph() -> DiagnosisGraph:
    return DiagnosisGraph(
        graph_id="graph:rbd-contract",
        reading_id="rbd-contract",
        nodes=[
            DiagnosisGraphNode(node_id="node:rule", node_kind="matched_rule", ref_id="match:wealth_authority_resource", weight=0.82),
            DiagnosisGraphNode(node_id="node:path", node_kind="path", ref_id="path:wealth_authority_resource", weight=0.86),
            DiagnosisGraphNode(node_id="node:claim", node_kind="claim", ref_id="claim:career_resource_platform", weight=0.88),
        ],
        edges=[
            DiagnosisGraphEdge(
                edge_id="edge:rule:path",
                source_node_id="node:rule",
                target_node_id="node:path",
                edge_kind="supports",
                weight=0.8,
                evidence_ids=["ev:domain_rule"],
            ),
            DiagnosisGraphEdge(
                edge_id="edge:path:claim",
                source_node_id="node:path",
                target_node_id="node:claim",
                edge_kind="explains",
                weight=0.85,
                evidence_ids=["ev:path"],
            ),
        ],
        top_claim_ids=["claim:career_resource_platform"],
        top_path_ids=["path:wealth_authority_resource"],
    )


def _route() -> DiagnosisRouteDecision:
    return DiagnosisRouteDecision(
        route_id="route:rbd-contract",
        reading_id="rbd-contract",
        role_key="user",
        diagnosis_mode="career",
        selected_domain="career",
        selected_claim_ids=["claim:career_resource_platform"],
        selected_path_ids=["path:wealth_authority_resource"],
        selected_portrait_ids=["portrait:resource_pressure"],
        expression_density="standard",
        safeguards=["no_chart_fact_mutation", "no_llm_fact_generation"],
        training_routes=["real_bazi_diagnosis", "expression"],
    )


def test_real_bazi_diagnosis_contracts_compose_traceable_diagnosis() -> None:
    diagnosis = RealBaziDiagnosis(
        diagnosis_id="diagnosis:rbd-contract",
        reading_id="rbd-contract",
        context=_context(),
        matched_rules=[_matched_rule()],
        features=[_feature()],
        paths=[_path()],
        portraits=[_portrait()],
        claims=[_claim()],
        graph=_graph(),
        route_decision=_route(),
        storage_policy={"postgres_required": True, "redis_cache_allowed": True},
    )

    assert diagnosis.version == DIAGNOSIS_CONTRACT_VERSION
    assert diagnosis.claims[0].claim_text.startswith("此局事业不宜单看财")
    assert diagnosis.paths[0].mechanism == "财官印制化"
    assert diagnosis.route_decision.boundary == "diagnosis_route_decision_selects_claims_not_facts"
    assert diagnosis.context.chart_fact_mutation_allowed is False


def test_diagnosis_context_rejects_write_or_fact_mutation() -> None:
    with pytest.raises(ValidationError):
        DiagnosisContext(
            context_id="ctx:bad",
            reading_id="rbd-contract",
            chart_context_id="chart:rbd-contract",
            role_key="user",
            runtime_write_allowed=True,
        )

    with pytest.raises(ValidationError):
        DiagnosisContext(
            context_id="ctx:bad",
            reading_id="rbd-contract",
            chart_context_id="chart:rbd-contract",
            role_key="user",
            chart_fact_mutation_allowed=True,
        )


def test_diagnosis_claim_rejects_llm_or_untraceable_claims() -> None:
    with pytest.raises(ValidationError):
        DiagnosisClaim(
            claim_id="claim:llm",
            claim_level="domain",
            domain="career",
            claim_text="LLM 自行生成的断语。",
            evidence_ids=["ev:x"],
            llm_generated=True,
        )

    with pytest.raises(ValidationError):
        DiagnosisClaim(
            claim_id="claim:no-trace",
            claim_level="domain",
            domain="career",
            claim_text="没有证据链的断语。",
        )


def test_diagnosis_graph_rejects_missing_node_edge_reference() -> None:
    with pytest.raises(ValidationError):
        DiagnosisGraph(
            graph_id="graph:bad",
            reading_id="rbd-contract",
            nodes=[
                DiagnosisGraphNode(node_id="node:claim", node_kind="claim", ref_id="claim:career", weight=0.7),
            ],
            edges=[
                DiagnosisGraphEdge(
                    edge_id="edge:bad",
                    source_node_id="node:missing",
                    target_node_id="node:claim",
                    edge_kind="supports",
                    weight=0.5,
                )
            ],
        )


def test_route_decision_rejects_fact_generation_or_empty_action() -> None:
    with pytest.raises(ValidationError):
        DiagnosisRouteDecision(
            route_id="route:bad",
            reading_id="rbd-contract",
            role_key="user",
            diagnosis_mode="career",
            central_brain_generated_facts=True,
            selected_claim_ids=["claim:career"],
        )

    with pytest.raises(ValidationError):
        DiagnosisRouteDecision(
            route_id="route:bad-empty",
            reading_id="rbd-contract",
            role_key="user",
            diagnosis_mode="career",
        )
