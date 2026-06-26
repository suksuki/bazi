from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.storage.m3 import write_m3_snapshot_to_postgres
from v30.validation import build_m3_core_spine_snapshot, run_m3_core_spine_snapshot


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


def test_m3_core_spine_snapshot_exposes_inventory_and_gaps() -> None:
    snapshot = build_m3_core_spine_snapshot()
    inventory = snapshot["inventory"]

    assert snapshot["version"] == "v30.m3_core_spine_snapshot.v1"
    assert inventory["krp_unit_count"] >= 72
    assert inventory["rule_spec_count"] >= 20
    assert inventory["source_family_count"] >= 6
    assert inventory["macro_dimension_count"] >= 7
    assert snapshot["synthetic_validation"]["passed"] is True
    calibration = snapshot["source_governed_calibration"]
    assert calibration["version"] == "v30.m3_source_governed_calibration.v1"
    assert calibration["status"] == "ready"
    assert calibration["coverage"]["tag_group_count"] == 5
    assert calibration["coverage"]["real_case_tag_count"] >= 8
    assert calibration["coverage"]["domain_depth_tag_count"] >= 8
    assert calibration["coverage"]["training_tag_count"] >= 1
    assert calibration["coverage"]["source_queue_count"] >= 6
    assert calibration["decision_boundary"]["chart_fact_mutation_allowed"] is False
    assert calibration["decision_boundary"]["policy_pointer_promotion_allowed"] is False
    assert calibration["decision_boundary"]["fixed_bazi_verdict_allowed"] is False
    assert set(calibration["tag_groups"]) == {
        "real_case_calibration_tags",
        "domain_rule_depth_expansion",
        "training_synthetic_distribution",
        "source_extraction_queue",
        "distribution_518k_summary",
    }
    assert [
        row
        for row in calibration["tag_groups"]["domain_rule_depth_expansion"]
        if row["depth_state"] == "growth_candidate"
    ] == []
    assert {row["gap_id"] for row in snapshot["missing_gaps"]} >= {
        "m3.real_case_calibration_tags",
        "m3.training_synthetic_distribution",
        "m3.518k_distribution_summary",
    }
    assert snapshot["storage_boundary"] == (
        "m3_snapshot_persists_support_data_without_promoting_policy_or_mutating_chart_facts"
    )


def test_m3_snapshot_can_write_to_dedicated_postgres_tables(tmp_path: Path) -> None:
    snapshot = build_m3_core_spine_snapshot()
    connection = FakeConnection()
    write = write_m3_snapshot_to_postgres(
        snapshot,
        settings=_settings(tmp_path, database_url="postgresql://user:pass@localhost:5432/qiazhi_v30"),
        connect=lambda _url: connection,
    )
    sql = "\n".join(row[0] for row in connection.cursor_instance.executed)

    assert write.backend == "postgres"
    assert write.searchable is True
    assert write.rows["knowledge_units"] >= 54
    assert write.rows["rule_specs"] >= 9
    assert write.rows["portrait_assets"] >= 7
    assert write.rows["validation_snapshots"] == 1
    assert connection.committed is True
    assert "v30_m3_knowledge_units" in sql
    assert "v30_m3_rule_specs" in sql
    assert "v30_m3_portrait_assets" in sql
    assert "v30_m3_validation_snapshots" in sql
    assert "v20_" not in sql


def test_m3_snapshot_script_payload_can_use_json_fallback(tmp_path: Path) -> None:
    snapshot = run_m3_core_spine_snapshot(write_db=False, artifact_dir=tmp_path)

    assert snapshot["artifact_uri"]
    assert Path(str(snapshot["artifact_uri"])).exists()
    assert "db_write" not in snapshot
    assert snapshot["synthetic_validation"]["passed"] is True
    assert snapshot["source_governed_calibration"]["coverage"]["has_518k_distribution"] is False


def test_m3_source_governed_calibration_can_include_518k_distribution(tmp_path: Path) -> None:
    snapshot = run_m3_core_spine_snapshot(
        include_518k_sample=True,
        sample_limit=2,
        write_db=False,
        artifact_dir=tmp_path,
    )
    calibration = snapshot["source_governed_calibration"]
    distribution = calibration["tag_groups"]["distribution_518k_summary"]

    assert snapshot["validation_518k"]["included"] is True
    assert calibration["coverage"]["has_518k_distribution"] is True
    assert distribution["included"] is True
    assert distribution["case_count"] == 2
    assert distribution["promotion_signal"] in {"eligible", "blocked"}
    assert distribution["boundary"] == "518k_distribution_evidence_guides_m3_coverage_without_full_corpus_default"
