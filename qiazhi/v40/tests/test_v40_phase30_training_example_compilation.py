from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue, LocalOverlay, TrainingLabelEvent
from v40.storage import V40PostgresRepository, resolve_v40_database_config
from v40.training import build_training_example_from_labels


def _label(reading_id: str) -> TrainingLabelEvent:
    return TrainingLabelEvent(
        event_id=f"label:{reading_id}:phase30",
        reading_id=reading_id,
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=LabelTargetType.BRANCH,
        target_ids=["branch:career:phase30"],
        label=LabelValue.SUPPORTS,
        strength=0.78,
        confidence=0.72,
        reason="命理师确认该事业分支贴近当前反馈。",
        created_by_role="practitioner",
        local_only=True,
    )


def test_training_example_builder_keeps_overlay_refs_without_global_update() -> None:
    reading_id = "reading.phase30.builder.001"
    example = build_training_example_from_labels(
        example_id="example.phase30.builder.001",
        reading_id=reading_id,
        label_events=[_label(reading_id)],
        topic=Topic.CAREER,
        input_snapshot_ref="runtime:reading.phase30.builder.001",
        runtime_output_ref="surface:report",
        local_overlay_refs=["overlay:phase30.builder.001"],
    )

    assert example.reading_id == reading_id
    assert example.topic == Topic.CAREER
    assert example.attribution_targets == ["branch:career:phase30"]
    assert example.expected_update["scope"] == "local_overlay_first"
    assert example.expected_update["local_overlay_count"] == 1
    assert example.global_update_allowed is False
    assert example.chart_fact_mutation_allowed is False


def test_training_example_from_reading_api_compiles_persisted_labels_and_overlays() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    reading_id = "reading.phase30.api.001"
    repository = V40PostgresRepository.from_env()
    repository.save_training_label_event(_label(reading_id))
    repository.save_local_overlay(
        LocalOverlay(
            overlay_id="overlay:phase30.api.001",
            reading_id=reading_id,
            label_event_ids=[f"label:{reading_id}:phase30"],
            affected_target_ids=["branch:career:phase30"],
        )
    )
    client = TestClient(create_app())

    response = client.post(
        f"{API_PREFIX}/training/example-from-reading",
        json={
            "example_id": "example.phase30.api.001",
            "reading_id": reading_id,
            "topic": Topic.CAREER.value,
            "input_snapshot_ref": f"runtime:{reading_id}",
            "runtime_output_ref": "surface:report",
            "persist": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    example = body["example"]
    assert body["label_count"] >= 1
    assert body["local_overlay_count"] >= 1
    assert body["persisted"] is True
    assert example["expected_update"]["global_update_requires_release_gate"] is True
    assert "overlay:phase30.api.001" in example["expected_update"]["local_overlay_refs"]
    listed = client.get(f"{API_PREFIX}/training/examples?reading_id={reading_id}&limit=5").json()["examples"]
    assert any(row["example_id"] == "example.phase30.api.001" for row in listed)


def test_phase30_training_example_schema_and_repository_are_v40_only() -> None:
    schema = Path("qiazhi/v40/deploy/postgres_v40_schema.sql").read_text(encoding="utf-8")
    repository = Path("qiazhi/v40/v40/storage/postgres.py").read_text(encoding="utf-8")
    app_source = Path("qiazhi/v40/v40/api/app.py").read_text(encoding="utf-8")

    assert "v40_training_examples" in schema
    assert "idx_v40_training_examples_reading" in schema
    assert "save_training_example" in repository
    assert "list_training_examples" in repository
    assert "/training/example-from-reading" in app_source
    assert "/training/examples" in app_source
    assert "v30_training_examples" not in schema
    assert "v30_training_examples" not in repository
