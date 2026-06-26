from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.storage.m3 import query_m3_source_backlog_from_postgres, select_m3_source_backlog_sql
from v30.validation import (
    build_m3_core_spine_snapshot,
    build_m3_source_backlog_review_surface,
    build_m3_source_extraction_backlog,
    run_m3_source_backlog_review_surface,
)


class FakeCursor:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self.rows = rows
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql: str, params: tuple[object, ...]) -> None:
        self.executed.append((sql, params))

    def fetchall(self) -> list[tuple[object, ...]]:
        return self.rows


class FakeConnection:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self.cursor_instance = FakeCursor(rows)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self) -> FakeCursor:
        return self.cursor_instance


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


def _backlog_rows() -> list[dict[str, object]]:
    snapshot = build_m3_core_spine_snapshot()
    backlog = build_m3_source_extraction_backlog(m3_snapshot=snapshot)
    return list(backlog["backlog_rows"])


def test_m3_source_backlog_review_surface_is_ready_and_read_only(tmp_path: Path) -> None:
    surface = build_m3_source_backlog_review_surface(
        rows=_backlog_rows(),
        query_backend="unit_test",
        artifact_dir=tmp_path,
    )
    decision = surface["decision"]

    assert surface["version"] == "v30.m3_source_backlog_review_surface.v1"
    assert surface["status"] == "completed"
    assert decision["decision_status"] == "m3_g5_backlog_review_surface_ready"
    assert decision["ready_for_admin_review_surface"] is True
    assert decision["ready_for_pointer_promotion"] is False
    assert decision["chart_fact_mutation_allowed"] is False
    assert surface["policy_boundary"]["admin_surface_read_only"] is True
    assert Path(str(surface["artifact_uri"])).exists()


def test_m3_source_backlog_review_surface_filters_generated_fallback(tmp_path: Path) -> None:
    surface = run_m3_source_backlog_review_surface(
        target_domain="useful_god",
        limit=3,
        artifact_dir=tmp_path,
        settings=_settings(tmp_path),
    )

    assert surface["decision"]["ready_for_admin_review_surface"] is True
    assert surface["query_summary"]["backend"].endswith("generated_backlog")
    assert 1 <= surface["decision"]["row_count"] <= 3
    for row in surface["rows"]:
        assert "useful_god" in row["target_domains"]
        assert row["runtime_v20_import_allowed"] is False
        assert row["policy_pointer_promotion_allowed"] is False


def test_m3_source_backlog_postgres_query_maps_rows_and_filters(tmp_path: Path) -> None:
    row_payload = _backlog_rows()[0]
    connection = FakeConnection([
        (
            row_payload["backlog_item_id"],
            row_payload["source_family_id"],
            row_payload["queue_state"],
            row_payload["priority"],
            row_payload["review_status"],
            row_payload["target_domains"],
            row_payload,
        )
    ])
    result = query_m3_source_backlog_from_postgres(
        priority=str(row_payload["priority"]),
        target_domain=str(row_payload["target_domains"][0]),
        limit=10,
        settings=_settings(tmp_path, database_url="postgresql://user:pass@localhost:5432/qiazhi_v30"),
        connect=lambda _url: connection,
    )
    sql = "\n".join(item[0] for item in connection.cursor_instance.executed)

    assert result["backend"] == "postgres"
    assert result["searchable"] is True
    assert result["row_count"] == 1
    assert result["rows"][0]["source_family_id"] == row_payload["source_family_id"]
    assert "v30_m3_source_backlog" in sql
    assert "v20_" not in sql


def test_m3_source_backlog_select_sql_is_v30_only() -> None:
    sql = select_m3_source_backlog_sql()

    assert "v30_m3_source_backlog" in sql
    assert "target_domains ? %s" in sql
    assert "v20_" not in sql
