from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from v30.config import V30Settings
from v30.storage.production_replay_store import ProductionReplayIntakeStore
from v30.validation import build_production_replay_intake_batch, run_synthetic_tier


def _settings(tmp_path: Path) -> V30Settings:
    return V30Settings(
        database_url=None,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="local_json",
    )


def _batch() -> dict[str, object]:
    synthetic = run_synthetic_tier("real_case_calibration_pack")
    metadata_rows = [
        row.observed["production_replay_metadata"]
        for row in synthetic.results
        if row.observed.get("production_replay_metadata")
    ]
    return build_production_replay_intake_batch(metadata_rows)


def test_production_replay_store_persists_and_searches_metadata_only(tmp_path: Path) -> None:
    store = ProductionReplayIntakeStore(settings=_settings(tmp_path))
    write = store.upsert_batch(_batch())

    assert write["version"] == "v30.production_replay_store_write.v1"
    assert write["stored_count"] == 30
    assert write["total_count"] == 30
    assert write["summary"]["calibration_ready_count"] == 25

    ready = store.search(selection_status="calibration_ready", module_ready="m4")
    assert ready["version"] == "v30.production_replay_search.v1"
    assert ready["count"] == 25
    assert ready["summary"]["calibration_ready_count"] == 25
    assert all(row["selection_status"] == "calibration_ready" for row in ready["rows"])
    assert all(row["module_readiness"]["m4"] is True for row in ready["rows"])
    assert all("birth_date" not in row and "raw_payload" not in row for row in ready["rows"])
    assert ready["boundary"] == "production_replay_search_returns_metadata_only_rows_not_chart_facts"

    lunar = store.search(calendar_type="lunar")
    assert lunar["count"] >= 1
    unknown_hour = store.search(boundary_tag="unknown_hour")
    assert unknown_hour["count"] >= 1


def test_production_replay_store_rejects_private_content(tmp_path: Path) -> None:
    store = ProductionReplayIntakeStore(settings=_settings(tmp_path))
    batch = _batch()
    row = dict(batch["rows"][0])
    row["birth_date"] = "1990-01-01"
    write = store.upsert_batch({"rows": [row]})

    assert write["stored_count"] == 0
    assert write["total_count"] == 0
    assert store.search()["count"] == 0


def test_production_replay_intake_script_can_persist_and_search(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_production_replay_intake.py",
            "--persist",
            "--selection-status",
            "calibration_ready",
            "--module-ready",
            "m4",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "stored=30 total=30" in result.stdout
    assert "search_count=25" in result.stdout
