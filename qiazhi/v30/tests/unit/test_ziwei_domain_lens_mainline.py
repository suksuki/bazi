from __future__ import annotations

from v30.brain.decision_engine import build_decision_result
from v30.production.contracts import (
    BaziDomain,
    BaziTopic,
    SignalSourceType,
    SourceModule,
)
from v30.production.signal_registry import build_signal_registry
from v30.ziwei.adapters import ziwei_signal_from_rule, ziwei_signal_to_bazi_signal
from v30.ziwei.domain_rules import load_ziwei_v1_domain_rules, rule_domain_counts
from v30.ziwei.probe_mapping import ZIWEI_PROBE_MAPPINGS, mapping_for_claim_key, probe_mappings_by_domain
from v30.ziwei.standards import (
    FOURTEEN_MAIN_STARS,
    V1_AUXILIARY_STARS,
    ZIWEI_DECISION_WEIGHT_V1,
    ZIWEI_STANDARD_GUARDRAILS,
    ZIWEI_SYSTEM_STANDARD_VERSION,
)


def test_ziwei_standard_v1_is_observation_only() -> None:
    assert ZIWEI_SYSTEM_STANDARD_VERSION == "v30.ziwei_system_standard.v1"
    assert ZIWEI_DECISION_WEIGHT_V1 == 0.0
    assert len(FOURTEEN_MAIN_STARS) == 14
    assert len(V1_AUXILIARY_STARS) == 14
    assert "ziwei_v1_decision_weight_is_zero" in ZIWEI_STANDARD_GUARDRAILS
    assert "ziwei_must_not_override_bazi_decision_engine_or_reality_probe" in ZIWEI_STANDARD_GUARDRAILS


def test_ziwei_v1_rules_cover_six_domains_and_probe_mapping() -> None:
    rules = load_ziwei_v1_domain_rules()
    counts = rule_domain_counts()

    assert len(rules) == 36
    assert counts == {
        "wealth": 6,
        "career": 6,
        "relationship": 6,
        "mobility": 6,
        "health_pressure": 6,
        "property": 6,
    }
    assert len({rule.rule_id for rule in rules}) == 36
    assert len({rule.claim_key for rule in rules}) == 36
    assert all(rule.decision_weight == 0.0 for rule in rules)
    assert all(rule.probe_trigger for rule in rules)
    assert len(ZIWEI_PROBE_MAPPINGS) == 36
    assert mapping_for_claim_key("ziwei_career_authority_pressure").probe_trigger == "authority_pressure_probe"
    assert len(probe_mappings_by_domain("relationship")) == 6


def test_ziwei_signal_enters_registry_without_user_raw_visibility() -> None:
    rule = next(rule for rule in load_ziwei_v1_domain_rules() if rule.rule_id == "ZW-CAREER-02")
    ziwei_signal = ziwei_signal_from_rule(reading_id="pytest-ziwei", rule=rule)
    bazi_signal = ziwei_signal_to_bazi_signal(ziwei_signal)
    registry = build_signal_registry(reading_id="pytest-ziwei", signals=[bazi_signal])

    assert not registry.validation_issues
    assert bazi_signal.source_module == SourceModule.ZIWEI_DOMAIN_LENS
    assert bazi_signal.source_type == SignalSourceType.ZIWEI_SIGNAL
    assert bazi_signal.domain == BaziDomain.CAREER
    assert bazi_signal.topic == BaziTopic.CAREER
    assert "user" not in bazi_signal.role_visibility
    assert "ziwei_signal_quality" in bazi_signal.training_targets
    assert bazi_signal.boundary == "ziwei_domain_lens_signal_is_observation_only_decision_weight_zero"
    assert registry.by_source_type(SignalSourceType.ZIWEI_SIGNAL)[0].claim_key == "ziwei_career_authority_pressure"


def test_ziwei_registry_does_not_change_decision_verdict() -> None:
    diagnosis = {
        "claims": [
            {
                "claim_id": "claim:career:main",
                "domain": "career",
                "claim_level": "domain",
                "claim_text": "事业压力需要先转成资质、平台和可交付成果。",
                "confidence_band": "high",
                "evidence_ids": ["ev:career"],
                "path_ids": ["path:career"],
                "blocked_overclaim": [],
            }
        ],
        "paths": [
            {
                "path_id": "path:career",
                "family_chain": ["authority", "resource"],
                "mechanism": "官印相生",
                "domain_targets": ["career"],
                "diagnosis_statement": "压力通过印星承接成资质和平台。",
                "score": 0.82,
                "evidence_ids": ["ev:career"],
            }
        ],
        "portraits": [],
        "features": [],
        "matched_rules": [],
    }
    claim_scores = [
        {
            "claim_id": "claim:career:main",
            "domain": "career",
            "claim_level": "domain",
            "score": 0.84,
            "requires_question": False,
            "components": {"path_coherence": 0.72, "counter_evidence": 0.0, "missing_context_penalty": 0.0},
        }
    ]
    rule = next(rule for rule in load_ziwei_v1_domain_rules() if rule.rule_id == "ZW-CAREER-02")
    registry = build_signal_registry(
        reading_id="pytest-ziwei-verdict",
        signals=[ziwei_signal_to_bazi_signal(ziwei_signal_from_rule(reading_id="pytest-ziwei-verdict", rule=rule))],
    )

    baseline = build_decision_result(
        reading_id="pytest-ziwei-verdict",
        active_stage_id="stage:career",
        diagnosis=diagnosis,
        claim_scores=claim_scores,
    )
    with_ziwei = build_decision_result(
        reading_id="pytest-ziwei-verdict",
        active_stage_id="stage:career",
        diagnosis=diagnosis,
        claim_scores=claim_scores,
        signal_registry=registry.model_dump(mode="json"),
    )

    assert [(row["domain"], row["assertion_level"], row["headline"]) for row in with_ziwei["verdicts"]] == [
        (row["domain"], row["assertion_level"], row["headline"]) for row in baseline["verdicts"]
    ]
    assert with_ziwei["candidate_builder_summary"]["score_mutation_allowed"] is False
    assert with_ziwei["engine_version"] == baseline["engine_version"]
