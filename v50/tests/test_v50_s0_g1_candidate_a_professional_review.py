from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
G1 = ROOT / "reports" / "abu-says-mingli-s0" / "g1"
SOURCE = ROOT / "packages" / "experience" / "fixtures" / "temporal_sandbox_c0_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _temporal_layer(source: dict, layer_id: str) -> dict:
    return next(layer for layer in source["temporal_layers"] if layer["layer_id"] == layer_id)


def test_intermediate_reject_all_decision_is_preserved_as_audit_history() -> None:
    decision = _load(G1 / "S0_G1_ANALYST_DECISION_LOCK_V2.json")
    manifest = _load(G1 / "s0_source_manifest_blocked_after_rejection_v2.json")

    assert decision["decision"] == "REJECT_ALL"
    assert decision["selected_fixture_id"] is None
    assert decision["professional_content_approved"] is False
    assert decision["approved_committed_path_ref"] is None
    assert decision["approved_temporal_ref"] is None
    assert decision["approved_discrete_change"] is None
    assert decision["audit_history"]["preselection_lock_preserved"] is True
    assert decision["audit_history"]["preselection_artifacts_modified"] is False
    assert decision["gate"] == {
        "s0_g1_complete": False,
        "s0_g2_authorized": False,
        "production_authorized": False,
    }

    assert manifest["manifest_status"] == "BLOCKED_PENDING_CANDIDATE_A_PROFESSIONAL_REVIEW"
    assert manifest["selected_fixture_id"] is None
    assert manifest["source_scene_state"] is None
    assert manifest["content_hash"] is None
    assert manifest["professional_content_approved"] is False
    assert manifest["s0_g2_authorized"] is False
    assert manifest["internal_animatic_authorized"] is False
    assert manifest["production_authorized"] is False


def test_candidate_a_review_evidence_is_an_exact_extraction_not_a_new_judgment() -> None:
    source = _load(SOURCE)
    evidence = _load(G1 / "s0_candidate_a_professional_evidence_v1.json")

    assert evidence["source_fixture"]["sha256"] == _sha256(SOURCE)
    assert evidence["candidate_snapshot"]["sha256"] == _sha256(
        G1 / "sources" / "s0-fixture-candidate-a.json"
    )
    assert evidence["evidence_class"] == "contract_fixture_semantics_not_professionally_approved"

    source_paths = {path["path_ref"]: path for path in source["life_case"]["paths"]}
    review_path = evidence["natal_path_claim"]
    source_path = source_paths[review_path["path_ref"]]
    assert review_path["ordered_node_refs"] == source_path["node_refs"]
    assert [segment["relation_ref"] for segment in review_path["segments"]] == source_path[
        "relation_refs"
    ]
    assert review_path["trace"] == {
        "source_mode": source_path["trace"]["source_mode"],
        "epistemic_status": source_path["trace"]["epistemic_status"],
        "source_refs": source_path["trace"]["source_refs"],
        "commitment_refs": source_path["trace"]["commitment_refs"],
    }

    chart_relations = {relation["relation_ref"]: relation for relation in source["chart"]["relations"]}
    for segment in review_path["segments"]:
        relation = chart_relations[segment["relation_ref"]]
        assert segment["from_node_ref"] == relation["from_node_ref"]
        assert segment["to_node_ref"] == relation["to_node_ref"]
        assert segment["relation_type"] == relation["relation_type"]
        assert segment["trace"]["source_refs"] == relation["trace"]["source_refs"]
        assert segment["trace"]["epistemic_status"] == relation["trace"]["epistemic_status"]


def test_temporal_claims_preserve_fixture_semantics_and_missing_evidence() -> None:
    source = _load(SOURCE)
    evidence = _load(G1 / "s0_candidate_a_professional_evidence_v1.json")

    for evidence_key, layer_id, expected_state in (
        ("luck_claim_under_review", "luck-gengzi-official", "weakened"),
        ("year_claim_under_review", "year-bingwu-official", "reinforced"),
    ):
        review = evidence[evidence_key]
        layer = _temporal_layer(source, layer_id)
        relation = layer["relations"][0]
        update = layer["path_updates"][0]

        assert review["stage_ref"] == layer["temporal_snapshot_id"]
        assert review["introduced_relation"]["relation_ref"] == relation["relation_ref"]
        assert review["introduced_relation"]["from_node_ref"] == relation["from_node_ref"]
        assert review["introduced_relation"]["to_node_ref"] == relation["to_node_ref"]
        assert review["introduced_relation"]["source_refs"] == relation["trace"]["source_refs"]
        assert review["path_update"]["semantic_state"] == expected_state
        assert review["path_update"]["source_refs"] == update["state_trace"]["source_refs"]
        assert review["path_update"]["reason_refs"] == update["change_reason_refs"]
        assert review["not_established_by_source"]

    classification = evidence["epistemic_classification"]
    assert classification["deterministic_relation_engine_result_proven"] is False
    assert classification["formal_reasoner_cognition_proven"] is False
    assert classification["professional_analyst_approval_proven"] is False
    assert "C0 fixture-authored derived Diff semantic" in classification["weakened"]
    assert "C0 fixture-authored derived Diff semantic" in classification["reinforced"]


def test_three_professional_approvals_are_independent_and_all_pending() -> None:
    evidence = _load(G1 / "s0_candidate_a_professional_evidence_v1.json")
    approvals = evidence["required_independent_approvals"]

    assert {approval["approval_id"] for approval in approvals} == {
        "natal_path",
        "luck_stage_weakening",
        "year_stage_renewed_support",
    }
    assert all(approval["decision"] == "PENDING" for approval in approvals)
    assert all(approval["required"] is True for approval in approvals)
    assert evidence["promotion_rule"]["all_three_approvals_required"] is True
    assert evidence["promotion_rule"]["approved_source_mode"] == (
        "approved_anonymous_teaching_fixture"
    )

    review = (G1 / "S0_G1_CANDIDATE_A_PROFESSIONAL_REVIEW_PACK.md").read_text(
        encoding="utf-8"
    )
    assert "三项必须分别批准" in review
    assert "C0 Diff 覆盖语义" in review
    assert "candidate_a_status: PENDING_THREE_PART_PROFESSIONAL_APPROVAL" in review
    assert "A. 原局路径" in review
    assert "B. 庚子大运削弱" in review
    assert "C. 丙午流年重新支持" in review


def test_post_decision_lock_matches_review_artifacts() -> None:
    lock_lines = (G1 / "S0_G1_POST_DECISION_LOCK.sha256").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(lock_lines) == 4

    for line in lock_lines:
        expected, relative_path = line.split("  ", 1)
        artifact = ROOT / relative_path
        assert artifact.is_file()
        assert _sha256(artifact) == expected
