from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
G1 = ROOT / "reports" / "abu-says-mingli-s0" / "g1"


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


def test_s0_g1_has_exactly_three_anonymous_traceable_candidates() -> None:
    registry = _load(G1 / "s0_g1_fixture_candidates_v1.json")
    candidates = registry["candidates"]

    assert registry["status"] == "awaiting_analyst_fixture_selection"
    assert len(candidates) == 3
    assert {item["candidate_alias"] for item in candidates} == {"A", "B", "C"}

    required = {
        "fixture_id",
        "chart_version_hash",
        "scene_state_hash",
        "life_case_projection_source",
        "committed_path_ref",
        "temporal_ref",
        "selected_discrete_change",
        "professional_risk",
        "privacy_status",
        "why_suitable_for_s0",
    }
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

    for candidate in candidates:
        assert required <= set(candidate)
        source_path = ROOT / candidate["source_scene_file"]
        source = _load(source_path)
        assert candidate["scene_state_hash"] == _sha256(source_path)
        assert candidate["chart_version_hash"] == hashlib.sha256(
            source["chart"]["chart_version_ref"].encode("utf-8")
        ).hexdigest()
        assert not (_all_keys(source) & private_keys)
        serialized = json.dumps(source, ensure_ascii=False)
        assert "v50-user-" not in serialized
        assert "王金星" not in serialized
        assert source["privacy_status"].startswith("anonymous_")
        assert source["life_case_projection"]["committed_path"]["epistemic_status"] == "committed"


def test_s0_candidates_do_not_overclaim_current_temporal_evidence() -> None:
    sources = {
        alias: _load(G1 / "sources" / f"s0-fixture-candidate-{alias.lower()}.json")
        for alias in ("A", "B", "C")
    }

    assert sources["A"]["source_contract_status"] == "c0_contract_fixture_only"
    assert sources["A"]["scene_selection"]["selected_discrete_change"] == "reinforced"
    assert "requires_analyst_promotion_to_teaching_fixture" in sources["A"]["professional_risk"]["codes"]

    for alias in ("B", "C"):
        source = sources[alias]
        assert source["temporal_projection"]["typed_path_effects"] == []
        assert source["scene_selection"]["selected_discrete_change"] == "introduced"
        assert source["scene_selection"]["path_state_after_change"] == "unchanged"
        assert "no_typed_temporal_path_effect" in source["professional_risk"]["codes"]


def test_s0_locked_copy_matches_analyst_wording_and_authority() -> None:
    copy = _load(G1 / "s0_locked_copy_v1.json")
    narration = copy["narration_text"]

    assert copy["public_brand"] == "DeepBazi · Life Intelligence"
    assert copy["experience_name"] == "阿布说命"
    assert copy["life_script_term"] == "人生剧本的底稿"
    assert copy["path_public_term"] == "正式主路径"
    assert copy["voice_status"] == "Eric internal audition only"
    assert "命理不该被简化为迷信" in narration
    assert "也不该被用来宣判一个注定的人生" in narration
    assert "我们正在把原局四柱、大运与流年" in narration
    assert "阿布不替你决定命运" in narration
    assert "系统最优路径" in copy["forbidden_claims"]
    assert copy["derivatives"]["thirty_second_version"] == "not_locked_not_authorized"


def test_s0_g2_remains_blocked_until_analyst_selects_and_approves() -> None:
    registry = _load(G1 / "s0_g1_fixture_candidates_v1.json")
    manifest = _load(G1 / "s0_source_manifest_pending_selection_v1.json")

    assert registry["final_selection"] == {
        "status": "PENDING_ANALYST_SELECTION",
        "selected_fixture_id": None,
        "analyst_content_approval": None,
        "decision_rationale": None,
        "locked_at": None,
    }
    assert registry["gate"]["s0_g1_complete"] is False
    assert registry["gate"]["s0_g2_authorized"] is False
    assert registry["gate"]["internal_animatic_authorized"] is False
    assert manifest["manifest_status"] == "PENDING_ANALYST_FIXTURE_SELECTION"
    assert manifest["source_scene_state"] is None
    assert manifest["content_hash"] is None
    assert manifest["s0_g2_authorized"] is False
    assert "analyst_fixture_selection_missing" in manifest["blocked_reasons"]


def test_s0_g1_preselection_lock_matches_all_review_artifacts() -> None:
    lock_lines = (G1 / "S0_G1_PRESELECTION_LOCK.sha256").read_text(encoding="utf-8").splitlines()
    assert len(lock_lines) == 7

    for line in lock_lines:
        expected, relative_path = line.split("  ", 1)
        artifact = ROOT / relative_path
        assert artifact.is_file()
        assert _sha256(artifact) == expected
