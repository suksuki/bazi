from __future__ import annotations

from copy import deepcopy

from scripts.v50_audit_path_qualification_01 import classify_case_payload
from test_v50_mingli_structural_experiment import _case_payload


def test_path_qualification_classifies_natural_language_without_candidate() -> None:
    payload = _case_payload("path-qualification-natural-language")
    work_path = payload["record"]["cognition"]["work_path"]
    work_path["candidate_path_refs"] = []
    work_path["competing_path_refs"] = []
    work_path["structured_candidate"] = None
    payload["life_case"]["path_assertions"] = []

    result = classify_case_payload(payload)

    assert result == {
        "category": "no_candidate",
        "reason_codes": ["work_path.natural_language_without_candidate"],
    }


def test_path_qualification_separates_rejected_validated_and_legacy_states() -> None:
    source = _case_payload("path-qualification-states")
    source["life_case"]["path_assertions"] = []

    validated = classify_case_payload(source)
    assert validated["category"] == "persistence_or_version_failure"

    rejected_payload = deepcopy(source)
    work_path = rejected_payload["record"]["cognition"]["work_path"]
    work_path["structured_candidate"] = None
    work_path["candidate_path_refs"] = ["unknown-candidate-path-ref"]
    rejected = classify_case_payload(rejected_payload)
    assert rejected["category"] == "segment_rejected"
    assert any("unknown_candidate_ref" in item for item in rejected["reason_codes"])

    legacy_payload = deepcopy(source)
    legacy_payload["life_case"]["path_assertions"] = [{
        "status": "legacy_unresolved",
        "unresolved_reason": "candidate_path_ref_not_found",
    }]
    legacy = classify_case_payload(legacy_payload)
    assert legacy == {
        "category": "legacy_unresolved",
        "reason_codes": ["candidate_path_ref_not_found"],
    }
