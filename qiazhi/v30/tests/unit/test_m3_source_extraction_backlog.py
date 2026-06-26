from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.storage.m3 import write_m3_source_backlog_to_postgres
from v30.validation import build_m3_core_spine_snapshot, build_m3_source_extraction_backlog


class FakeCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql: str, params: tuple[object, ...]) -> None:
        self.executed.append((sql, params))


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.committed = True


def _settings(tmp_path: Path, database_url: str | None = None) -> V30Settings:
    return V30Settings(
        database_url=database_url,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="memory",
    )


def test_m3_source_extraction_backlog_is_ready_and_review_only(tmp_path: Path) -> None:
    snapshot = build_m3_core_spine_snapshot()
    backlog = build_m3_source_extraction_backlog(
        m3_snapshot=snapshot,
        artifact_dir=tmp_path,
    )
    decision = backlog["decision"]
    summary = backlog["backlog_summary"]

    assert backlog["version"] == "v30.m3_source_extraction_backlog.v1"
    assert backlog["status"] == "completed"
    assert decision["decision_status"] == "m3_g4_source_extraction_backlog_ready"
    assert decision["ready_for_source_backlog_review"] is True
    assert decision["ready_for_pointer_promotion"] is False
    assert decision["runtime_v20_import_allowed"] is False
    assert decision["chart_fact_mutation_allowed"] is False
    assert summary["backlog_row_count"] >= 6
    assert Path(str(backlog["artifact_uri"])).exists()
    assert backlog["next_mainline_selection"]["next_task"] == "M3-G5 Backlog Persistence And Admin Review Surface"


def test_m3_source_extraction_backlog_rows_have_operational_fields_and_boundaries() -> None:
    snapshot = build_m3_core_spine_snapshot()
    backlog = build_m3_source_extraction_backlog(m3_snapshot=snapshot)

    assert {row["check_id"]: row["passed"] for row in backlog["checks"]} == {
        "source_governed_calibration_ready": True,
        "all_source_families_have_backlog_rows": True,
        "backlog_rows_are_reviewable": True,
        "evidence_links_present": True,
        "operational_fields_present": True,
        "no_runtime_import_or_mutation_allowed": True,
    }
    for row in backlog["backlog_rows"]:
        assert row["source_family_id"].startswith("v30.source.")
        assert row["priority"] in {"P0", "P1", "P2"}
        assert row["review_status"] == "review_ready"
        assert row["target_domains"]
        assert row["extraction_targets"]
        assert row["validation_requirements"]
        assert row["linked_knowledge_unit_ids"]
        assert row["runtime_v20_import_allowed"] is False
        assert row["chart_fact_mutation_allowed"] is False
        assert row["policy_pointer_promotion_allowed"] is False
        assert row["fixed_bazi_verdict_allowed"] is False


def test_m3_source_backlog_can_write_to_dedicated_postgres_table(tmp_path: Path) -> None:
    snapshot = build_m3_core_spine_snapshot()
    backlog = build_m3_source_extraction_backlog(m3_snapshot=snapshot)
    connection = FakeConnection()
    write = write_m3_source_backlog_to_postgres(
        backlog,
        settings=_settings(tmp_path, database_url="postgresql://user:pass@localhost:5432/qiazhi_v30"),
        connect=lambda _url: connection,
    )
    sql = "\n".join(row[0] for row in connection.cursor_instance.executed)

    assert write.backend == "postgres"
    assert write.searchable is True
    assert write.rows["source_backlog"] >= 6
    assert write.rows["validation_snapshots"] == 1
    assert connection.committed is True
    assert "v30_m3_source_backlog" in sql
    assert "v30_m3_validation_snapshots" in sql
    assert "v20_" not in sql
