from __future__ import annotations

from pathlib import Path

from v20.validation.next_question_synthetic import (
    build_next_question_synthetic_validation_report,
    read_next_question_synthetic_validation_artifact,
    validate_question_atom_followup_targets,
    write_next_question_synthetic_validation_artifact,
)
from v20.storage.local_jsonl import LocalJsonlStore


def test_v20_next_question_synthetic_validation_passes_core_roles() -> None:
    report = build_next_question_synthetic_validation_report()

    assert report["version"] == "v20.next_question_synthetic_validation_report.v1"
    assert report["status"] == "ready"
    assert report["case_count"] >= 7
    assert report["failure_count"] == 0
    assert report["candidate_policy"]["status"] == "ready"
    assert report["candidate_policy"]["stage_boosts"]["timing"] > 0
    assert report["candidate_policy"]["topic_boosts"]["health_balance"] > 0
    assert report["candidate_policy"]["topic_boosts"]["useful_god"] > 0
    assert report["followup_target_validation"]["status"] == "pass"
    assert report["followup_target_validation"]["edge_count"] >= 20
    assert any("atom.user.timing.trigger" in row["top_atom_ids"] for row in report["case_results"])
    assert any("atom.user.focus.useful_god" in row["top_atom_ids"] for row in report["case_results"])
    assert any("atom.user.timing.relationship_window" in row["active_followup_targets"] for row in report["case_results"])


def test_v20_next_question_synthetic_artifact_write_and_read(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    store = LocalJsonlStore(runtime_dir=tmp_path)

    before = read_next_question_synthetic_validation_artifact()
    written = write_next_question_synthetic_validation_artifact(store=store)
    after = read_next_question_synthetic_validation_artifact()

    assert before["status"] == "not_built"
    assert written["version"] == "v20.next_question_synthetic_validation_artifact_write.v1"
    assert written["status"] == "written"
    assert written["failure_count"] == 0
    assert after["status"] == "ready"
    assert Path(written["latest_path"]).exists()


def test_v20_question_atom_followup_targets_are_validated() -> None:
    validation = validate_question_atom_followup_targets()

    assert validation["version"] == "v20.question_atom_followup_target_validation.v1"
    assert validation["status"] == "pass"
    assert validation["missing_target_count"] == 0
    assert validation["edge_count"] >= 20
