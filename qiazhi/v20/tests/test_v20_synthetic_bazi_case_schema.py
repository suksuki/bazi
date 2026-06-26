from __future__ import annotations

import json

from v20.validation.synthetic_schema import (
    MINIMAL_SYNTHETIC_BAZI_CASES,
    SyntheticBaziCase,
    minimal_synthetic_bazi_cases,
    synthetic_bazi_coverage_report,
    synthetic_bazi_case_manifest,
    validate_synthetic_bazi_case_schema,
)


def test_v20_synthetic_bazi_case_minimal_set_covers_mainline_training_targets() -> None:
    cases = minimal_synthetic_bazi_cases()
    manifest = synthetic_bazi_case_manifest(cases)
    case_types = set(manifest["case_types"])
    stages = set(manifest["dag_stages"])
    roles = set(manifest["role_keys"])

    assert cases == MINIMAL_SYNTHETIC_BAZI_CASES
    assert manifest["case_count"] >= 14
    assert {
        "rule_case",
        "portrait_question_case",
        "question_dag_case",
        "interaction_case",
        "extreme_structure_case",
        "time_layer_case",
        "role_leakage_case",
    }.issubset(case_types)
    assert {"entry", "focus", "structure", "review", "observe", "advice", "timing", "closure"}.issubset(stages)
    assert {"guest", "user", "analyst", "admin"}.issubset(roles)
    assert manifest["runtime_mutation"] is False


def test_v20_synthetic_bazi_case_schema_round_trips_without_private_text_or_runtime_mutation() -> None:
    case = minimal_synthetic_bazi_cases()[0]
    payload = case.to_dict()
    restored = SyntheticBaziCase.from_dict(json.loads(json.dumps(payload, ensure_ascii=False)))

    assert restored.case_id == case.case_id
    assert restored.pillar_displays == case.pillar_displays
    assert restored.expected.rule_domains == case.expected.rule_domains
    assert restored.role_expectations[0].role_key == "guest"
    assert "NO_USER_PRIVATE_TEXT" in restored.guardrails
    assert "NO_RUNTIME_RULE_MUTATION" in restored.guardrails
    assert "review" in restored.negative.forbidden_role_stages["guest"]
    assert "observe" in restored.negative.forbidden_role_stages["guest"]


def test_v20_synthetic_bazi_case_schema_validation_accepts_minimal_cases() -> None:
    failures = {
        case.case_id: validate_synthetic_bazi_case_schema(case)
        for case in minimal_synthetic_bazi_cases()
    }

    assert all(not row for row in failures.values())


def test_v20_question_review_expectation_is_part_of_mainline_schema() -> None:
    case = minimal_synthetic_bazi_cases()[0]
    review = case.question_review_expectation

    assert {"approve", "rewrite", "downrank", "merge", "delete"}.issubset(set(review.required_actions))
    assert {"role_mismatch", "mainline_mismatch", "too_technical", "duplicate", "unfocused"}.issubset(
        set(review.required_reasons)
    )
    assert "rule_truth_mutation" in review.forbidden_runtime_mutations


def test_v20_synthetic_bazi_cases_cover_boundary_and_leakage_guards() -> None:
    cases = minimal_synthetic_bazi_cases()
    by_id = {case.case_id: case for case in cases}

    assert "v20.synthetic.bazi.extreme_same_element_001" in by_id
    assert "v20.synthetic.bazi.full_collision_boundary_001" in by_id
    assert "v20.synthetic.bazi.multi_time_layer_001" in by_id
    assert "v20.synthetic.bazi.role_leakage_guardrail_001" in by_id
    assert "technical_review" in by_id[
        "v20.synthetic.bazi.role_leakage_guardrail_001"
    ].negative.forbidden_role_stages["guest"]


def test_v20_synthetic_bazi_coverage_report_is_machine_readable() -> None:
    report = synthetic_bazi_coverage_report()

    assert report["version"] == "v20.synthetic_bazi_coverage_report.v1"
    assert report["status"] == "pass"
    assert report["case_count"] >= 14
    assert report["gap_count"] == 0
    assert {"strength", "ten_god", "branch", "element", "wealth", "health"}.issubset(report["feature_domains"])
    assert {"entry", "focus", "structure", "timing", "review", "observe", "advice", "closure"}.issubset(
        report["dag_stages"]
    )
    assert {
        "extreme_structure",
        "negative_boundary",
        "multi_time_layer",
        "role_leakage_guardrail",
    }.issubset(report["boundary_capabilities"])
    assert report["runtime_mutation"] is False
