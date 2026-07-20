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


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def test_candidate_a_has_three_explicit_medium_confidence_approvals() -> None:
    decision = _load(G1 / "S0_G1_CANDIDATE_A_PROFESSIONAL_DECISION_LOCK_V1.json")

    assert decision["decision"] == "SELECT"
    assert decision["selected_fixture_id"] == "s0-fixture-candidate-a"
    assert decision["professional_content_approved"] is True
    assert decision["approval_scope"] == "internal_teaching_projection"
    assert decision["confidence"] == "medium"
    assert decision["source_mode"] == "approved_anonymous_teaching_fixture"
    assert decision["real_user_life_case"] is False
    assert decision["deterministic_algorithm_best_path"] is False
    assert decision["event_prediction_authorized"] is False

    assert decision["natal_path"]["decision"] == "APPROVE"
    assert decision["luck_stage"]["decision"] == "APPROVE"
    assert decision["year_stage"]["decision"] == "APPROVE"
    assert decision["luck_stage"]["approved_discrete_change"] == "weakened"
    assert decision["year_stage"]["approved_discrete_change"] == "reinforced"
    assert decision["year_stage"]["relative_to"] == "luck_stage"
    assert decision["gate"]["three_required_approvals_complete"] is True
    assert decision["gate"]["s0_g2_authorized_after_final_manifest_lock"] is True
    assert decision["gate"]["s0_g3_authorized"] is False


def test_approved_projection_binds_only_analyst_approved_source_objects() -> None:
    source = _load(SOURCE)
    projection = _load(G1 / "s0_candidate_a_approved_teaching_projection_v1.json")

    chart_relation_refs = {item["relation_ref"] for item in source["chart"]["relations"]}
    temporal_relation_refs = {
        item["relation_ref"]
        for layer in source["temporal_layers"]
        for item in layer["relations"]
    }
    source_relation_refs = chart_relation_refs | temporal_relation_refs
    source_path_refs = {item["path_ref"] for item in source["life_case"]["paths"]}
    source_temporal_refs = {
        layer["temporal_snapshot_id"]
        for layer in source["temporal_layers"]
        if layer.get("temporal_snapshot_id") is not None
    }

    assert projection["source_mode"] == "approved_anonymous_teaching_fixture"
    assert projection["approval_scope"] == "internal_teaching_projection"
    assert projection["source_lineage"]["c0_fixture_sha256"] == _sha256(SOURCE)
    assert projection["identity_boundary"]["real_user_life_case"] is False
    assert projection["identity_boundary"]["event_prediction_authorized"] is False

    path = projection["approved_natal_path"]
    assert path["path_ref"] in source_path_refs
    assert set(path["relation_refs"]) <= source_relation_refs
    assert path["terminal_label"] == "金结构"
    assert "无条件完全合化" in path["terminal_uncertainty"]

    approved_relations = set(path["relation_refs"])
    approved_temporal_refs: set[str] = set()
    for stage in projection["approved_temporal_stages"]:
        approved_relations.update(stage["approved_relation_refs"])
        approved_temporal_refs.add(stage["temporal_ref"])
        assert set(stage["approved_relation_refs"]) <= source_relation_refs
        assert stage["temporal_ref"] in source_temporal_refs

    assert approved_relations == {
        "relation-yi-generates-ding",
        "relation-ding-acts-on-metal",
        "relation-luck-geng-controls-yi",
        "relation-year-bing-supports-ding",
    }
    assert approved_temporal_refs == {
        "snapshot-luck-gengzi-v1",
        "snapshot-year-bingwu-v1",
    }

    for cue in projection["approved_animation_cues"]:
        assert set(cue["relation_refs"]) <= approved_relations
        assert cue["path_ref"] == "path-committed-output-pressure"


def test_final_manifest_authorizes_only_internal_g2_and_preserves_effect_limits() -> None:
    manifest = _load(G1 / "s0_source_manifest_final_v1.json")
    projection_path = G1 / "s0_candidate_a_approved_teaching_projection_v1.json"
    decision_path = G1 / "S0_G1_CANDIDATE_A_PROFESSIONAL_DECISION_LOCK_V1.json"

    assert manifest["manifest_status"] == "LOCKED_FOR_INTERNAL_G2"
    assert manifest["content_hash"] == _sha256(projection_path)
    assert manifest["professional_decision_hash"] == _sha256(decision_path)
    assert manifest["source_fixture_hash"] == _sha256(SOURCE)
    assert manifest["onecanvas_snapshot_hash"] == _sha256(
        G1 / "sources" / "s0-fixture-candidate-a.json"
    )
    assert manifest["narration_script_hash"] == _sha256(G1 / "s0_locked_copy_v1.json")
    assert manifest["professional_content_approved"] is True
    assert manifest["source_mode"] == "approved_anonymous_teaching_fixture"
    assert manifest["source_life_case_class"] == "contract_fixture_not_real_user_life_case"

    assert manifest["approved_relation_refs"] == [
        "relation-yi-generates-ding",
        "relation-ding-acts-on-metal",
        "relation-luck-geng-controls-yi",
        "relation-year-bing-supports-ding",
    ]
    assert manifest["approved_committed_path_refs"] == ["path-committed-output-pressure"]
    assert manifest["approved_temporal_refs"] == [
        "snapshot-luck-gengzi-v1",
        "snapshot-year-bingwu-v1",
    ]

    changes = {item["change"]: item for item in manifest["approved_discrete_changes"]}
    assert changes["weakened"]["must_not_render_as"] == "blocked"
    assert changes["reinforced"]["relative_to"] == "luck_stage"
    assert changes["reinforced"]["must_not_render_as"] == (
        "fully_restored_or_above_natal_baseline"
    )
    assert "Zi-to-Ding effect arrow" in manifest["blocked_animation_effects"]
    assert "Wu-to-Ding effect arrow" in manifest["blocked_animation_effects"]

    assert manifest["s0_g1_status"] == "PASS_WITH_CONDITIONS"
    assert manifest["s0_g2_authorized"] is True
    assert manifest["s0_g3_authorized"] is False
    assert manifest["final_master_authorized"] is False
    assert manifest["website_release_authorized"] is False
    assert manifest["public_release_authorized"] is False


def test_approved_projection_contains_no_private_case_identity() -> None:
    projection = _load(G1 / "s0_candidate_a_approved_teaching_projection_v1.json")
    private_keys = {
        "profile_id",
        "user_id",
        "display_name",
        "birth_date",
        "birth_time",
        "birth_location",
        "conversation_history",
        "reality_feedback",
    }

    assert not (_all_keys(projection) & private_keys)
    assert projection["identity_boundary"]["anonymous"] is True
    assert projection["identity_boundary"]["birth_datetime_included"] is False
    assert projection["identity_boundary"]["birth_location_included"] is False
    assert projection["identity_boundary"]["reality_feedback_included"] is False


def test_s0_g1_final_manifest_lock_matches_all_authoritative_inputs() -> None:
    lock_lines = (G1 / "S0_G1_FINAL_MANIFEST_LOCK.sha256").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(lock_lines) == 6

    for line in lock_lines:
        expected, relative_path = line.split("  ", 1)
        artifact = ROOT / relative_path
        assert artifact.is_file()
        assert _sha256(artifact) == expected
