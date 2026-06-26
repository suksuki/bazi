from __future__ import annotations

from v30.diagnosis import (
    CLAIM_GENERATOR_VERSION,
    extract_diagnosis_features,
    extract_diagnosis_portraits,
    generate_diagnosis_claims,
    match_real_bazi_rules,
    summarize_diagnosis_claims,
    translate_dynamic_paths,
)
from v30.runtime import create_smoke_runtime


def _claims():
    runtime = create_smoke_runtime(
        "rbd-claim-generator-runtime",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    paths = translate_dynamic_paths(
        runtime.structure_state,
        timing_context=runtime.chart_context.time_layers,
    )
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
    return claims


def test_claim_generator_produces_concrete_bazi_claims() -> None:
    claims = _claims()
    summary = summarize_diagnosis_claims(claims)
    text = "\n".join(claim.claim_text for claim in claims)

    assert len(claims) >= 35
    assert summary["version"] == CLAIM_GENERATOR_VERSION
    assert summary["claim_count"] == len(claims)
    assert summary["domain_counts"]["wealth"] >= 3
    assert summary["domain_counts"]["career"] >= 3
    assert summary["level_counts"]["domain"] >= 5
    assert "财运沿" in text
    assert "事业落在" in text
    assert "关系受" in text
    assert "命局结构以" in text


def test_claims_are_traceable_and_not_llm_generated() -> None:
    claims = _claims()

    assert all(claim.evidence_ids or claim.rule_ids or claim.path_ids or claim.portrait_ids for claim in claims)
    assert all(not claim.llm_generated for claim in claims)
    assert all(not claim.chart_fact_mutation_allowed for claim in claims)
    assert all(not claim.fixed_event_prediction for claim in claims)
    assert any(claim.claim_level == "fact" and "不可改写" in claim.claim_text for claim in claims)
    assert any(claim.claim_level == "path" and claim.path_ids for claim in claims)
    assert any(claim.claim_level == "portrait" and claim.portrait_ids for claim in claims)


def test_claim_generator_keeps_health_hidden_and_timing_boundaries() -> None:
    claims = _claims()
    health = [claim for claim in claims if claim.domain == "health"]
    hidden = [claim for claim in claims if claim.domain == "hidden_factor"]
    timing = [claim for claim in claims if claim.domain == "timing"]

    assert health
    assert hidden
    assert timing
    assert any("不做疾病" in claim.claim_text or "medical_diagnosis" in claim.blocked_overclaim for claim in health)
    assert any(claim.needs_user_calibration for claim in hidden)
    assert any("不能单独生成具体年份事件" in claim.claim_text for claim in timing)
    assert any("fixed_event_prediction" in claim.blocked_overclaim for claim in timing)


def test_claim_generator_can_limit_sorted_claims() -> None:
    claims = _claims()
    limited = generate_diagnosis_claims(
        matched_rules=[],
        features=[],
        paths=[],
        portraits=[],
        limit=5,
    )

    assert limited == []
    assert claims == sorted(
        claims,
        key=lambda row: (
            ["overview", "structure", "useful_god", "timing", "wealth", "career", "relationship", "health", "hidden_factor"].index(row.domain),
            ["fact", "feature", "path", "portrait", "domain", "timing", "question"].index(row.claim_level),
            {"high": 0, "medium": 1, "low": 2}[row.confidence_band],
            row.claim_id,
        ),
    )
