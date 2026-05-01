from __future__ import annotations

from fastapi.testclient import TestClient

from v20.server import app
from v20.validation.rule_portrait_batch import (
    read_rule_portrait_batch_artifact,
    run_rule_portrait_batch,
    write_rule_portrait_batch_artifact,
)


def test_v20_rule_portrait_batch_generates_and_validates_main_chain() -> None:
    report = run_rule_portrait_batch()

    assert report["ok"] is True
    assert report["status"] == "pass"
    assert report["domain_count"] >= 8
    assert report["case_count"] >= 6
    assert report["failure_count"] == 0
    assert all(row["ok"] is True for row in report["rule_generation"])
    assert all(row["ok"] is True for row in report["case_results"])
    assert "wealth" in report["coverage_summary"]["rule_domains"]
    assert "time" in report["coverage_summary"]["portrait_domains"]
    assert report["runtime_mutation"] is False


def test_v20_rule_portrait_batch_artifact_write_is_local_only(tmp_path) -> None:
    write = write_rule_portrait_batch_artifact(output_dir=tmp_path)
    status = read_rule_portrait_batch_artifact(output_dir=tmp_path)

    assert write["status"] == "written"
    assert write["report_status"] == "pass"
    assert write["runtime_mutation"] is True
    assert status["status"] == "pass"
    assert status["runtime_mutation"] is False
    assert status["failure_count"] == 0


def test_v20_rule_portrait_batch_endpoints_are_read_only() -> None:
    client = TestClient(app)
    validation = client.get("/api/v20/validation/rule-portrait-batch").json()
    learning = client.get("/api/v20/learning/rule-portrait-batch").json()

    assert validation["status"] == "pass"
    assert validation["runtime_mutation"] is False
    assert learning["status"] == "pass"
    assert learning["runtime_mutation"] is False
