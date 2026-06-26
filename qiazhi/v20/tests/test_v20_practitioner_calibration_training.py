from __future__ import annotations

from pathlib import Path

from v20.interaction.practitioner_calibration import PractitionerControlSelection, record_practitioner_calibration
from v20.interaction.latent_event_calibration import LatentCalibrationAnswer, record_latent_event_calibration
from v20.learning.practitioner_calibration_training import (
    build_practitioner_calibration_training_report,
    read_practitioner_calibration_training_artifact,
    write_practitioner_calibration_training_artifact,
)
import v20.learning.training_iteration as training_iteration
from v20.learning.training_iteration import run_training_iteration
from v20.storage.local_jsonl import LocalJsonlStore
from v20.storage.postgres_ledger_import import build_ledger_postgres_import_plan


def test_v20_practitioner_calibration_training_aggregates_structured_choices(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for option in ("中和偏弱", "中和偏弱", "偏弱"):
        record_practitioner_calibration(
            input_id=f"case.{option}",
            source_role="analyst",
            selections=(
                PractitionerControlSelection(
                    control_key="control.day_master_strength",
                    option=option,
                    source_decision_keys=("decision.strength.day_master_capacity",),
                ),
            ),
            store=store,
        )

    report = build_practitioner_calibration_training_report(store=store)
    summary = report["control_summaries"][0]
    proposal = report["training_proposals"][0]

    assert report["runtime_mutation"] is False
    assert report["status"] == "ready"
    assert report["selection_count"] == 3
    assert summary["control_key"] == "control.day_master_strength"
    assert summary["top_option"] == "中和偏弱"
    assert summary["activation_candidate"] is False
    assert proposal["target"] == "decision_parameters.strength_capacity"
    assert proposal["runtime_allowed"] is True


def test_v20_practitioner_calibration_accepts_mainline_arbitration_review(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    result = record_practitioner_calibration(
        input_id="mainline.review.case",
        source_role="analyst",
        selections=(
            PractitionerControlSelection(
                control_key="control.mainline_arbitration",
                option="切换到次级主线",
                source_decision_keys=(),
            ),
        ),
        store=store,
    )

    analysis = result["analysis"]
    signal = analysis["training_signals"][0]
    assert analysis["selection_count"] == 1
    assert signal["control_key"] == "control.mainline_arbitration"
    assert signal["target"] == "decision_parameters.mainline_arbitration"
    assert result["runtime_mutation"] is True


def test_v20_practitioner_calibration_training_write_and_status(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    store = LocalJsonlStore(runtime_dir=tmp_path)
    record_practitioner_calibration(
        input_id="pattern.case",
        source_role="analyst",
        selections=(
            PractitionerControlSelection(
                control_key="control.pattern_status",
                option="候选",
                source_decision_keys=("decision.pattern.status",),
            ),
        ),
        store=store,
    )

    written = write_practitioner_calibration_training_artifact(store=store)
    status = read_practitioner_calibration_training_artifact()

    assert written["status"] == "written"
    assert written["selection_count"] == 1
    assert status["version"] == "v20.practitioner_calibration_training_report.v1"
    assert status["selection_count"] == 1
    assert status["runtime_mutation"] is False


def test_v20_training_iteration_includes_practitioner_calibration_phase(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    _stub_training_iteration(monkeypatch)
    report = run_training_iteration(include_rule_batch=False)

    assert "practitioner_calibration_training" in report["results"]
    assert report["results"]["practitioner_calibration_training"]["status"] == "not_enough_data"
    assert "NO_USER_UI_TRAINING_SURFACE" in report["guardrails"]


def test_v20_practitioner_calibration_postgres_import_is_dry_run_by_default(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    record_practitioner_calibration(
        input_id="postgres.import.case",
        source_role="analyst",
        selections=(
            PractitionerControlSelection(
                control_key="control.wealth_capacity",
                option="看大运",
                source_decision_keys=("decision.wealth.capacity",),
            ),
        ),
        store=store,
    )
    plan = build_ledger_postgres_import_plan(
        ledger_name="practitioner_calibration_ledger",
        store=store,
        database_url="",
    )
    blocked = build_ledger_postgres_import_plan(
        ledger_name="practitioner_calibration_ledger",
        store=store,
        database_url="",
        apply=True,
    )

    assert plan["status"] == "dry_run"
    assert plan["record_count"] == 1
    assert plan["target_table"] == "v20_feedback_ledger"
    assert plan["runtime_mutation"] is False
    assert blocked["status"] == "blocked_missing_V20_DATABASE_URL"
    assert blocked["runtime_mutation"] is True


def test_v20_latent_event_calibration_can_be_imported_to_postgres_ledger(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    record_latent_event_calibration(
        input_id="postgres.latent.case",
        source_role="user",
        answers=(
            LatentCalibrationAnswer(
                scenario_id="latent.wealth_change",
                year_option="25_to_30",
                result_option="income_up",
                intensity="clear",
                confidence="medium",
            ),
        ),
        store=store,
    )
    plan = build_ledger_postgres_import_plan(
        ledger_name="latent_event_calibration_ledger",
        store=store,
        database_url="",
    )

    assert plan["status"] == "dry_run"
    assert plan["record_count"] == 1
    assert plan["target_table"] == "v20_feedback_ledger"
    assert plan["runtime_mutation"] is False


def _stub_training_iteration(monkeypatch) -> None:
    def ready(name: str) -> dict[str, object]:
        return {"version": f"test.{name}.v1", "status": "ready", "runtime_mutation": False}

    monkeypatch.setattr(training_iteration, "run_dynamic_decision_training_batch", lambda **_: ready("dynamic"))
    monkeypatch.setattr(
        training_iteration,
        "build_practitioner_calibration_training_report",
        lambda **_: {"version": "test.practitioner.v1", "status": "not_enough_data", "runtime_mutation": False},
    )
    monkeypatch.setattr(training_iteration, "build_orchestrator_memory_training_report", lambda **_: ready("memory"))
    monkeypatch.setattr(training_iteration, "build_arbitration_loop_report", lambda **_: ready("arbitration"))
    monkeypatch.setattr(training_iteration, "build_question_ranking_learning_report", lambda **_: ready("question"))
    monkeypatch.setattr(training_iteration, "build_rule_synthetic_training_report", lambda *_, **__: ready("synthetic"))
    monkeypatch.setattr(training_iteration, "build_knowledge_rule_review_overlay", lambda *_, **__: ready("overlay"))
    monkeypatch.setattr(training_iteration, "build_rule_subcondition_split_report", lambda **_: ready("subcondition"))
    monkeypatch.setattr(training_iteration, "build_decision_registry_iteration_report", lambda **_: ready("registry"))
    monkeypatch.setattr(training_iteration, "build_decision_training_plan", lambda: ready("plan"))
