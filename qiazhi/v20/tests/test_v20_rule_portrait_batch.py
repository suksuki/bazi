from __future__ import annotations

import v20.server as server_module
import v20.validation.rule_portrait_batch as rule_portrait_batch
from v20.server import app
from v20.validation.rule_portrait_batch import (
    read_rule_portrait_batch_artifact,
    write_rule_portrait_batch_artifact,
)


def _endpoint(path: str, method: str = "GET"):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", "") == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def test_v20_rule_portrait_batch_generates_and_validates_main_chain() -> None:
    report = _rule_portrait_batch_report()

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


def test_v20_rule_portrait_batch_artifact_write_is_local_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(rule_portrait_batch, "run_rule_portrait_batch", lambda **_: _rule_portrait_batch_report())

    write = write_rule_portrait_batch_artifact(output_dir=tmp_path)
    status = read_rule_portrait_batch_artifact(output_dir=tmp_path)

    assert write["status"] == "written"
    assert write["report_status"] == "pass"
    assert write["runtime_mutation"] is True
    assert status["status"] == "pass"
    assert status["runtime_mutation"] is False
    assert status["failure_count"] == 0


def test_v20_rule_portrait_batch_endpoints_are_read_only(monkeypatch) -> None:
    monkeypatch.setattr(server_module, "run_rule_portrait_batch", lambda **_: _rule_portrait_batch_report())
    validation = _endpoint("/api/v20/validation/rule-portrait-batch")()
    learning = _endpoint("/api/v20/learning/rule-portrait-batch")()

    assert validation["status"] == "pass"
    assert validation["runtime_mutation"] is False
    assert learning["status"] == "pass"
    assert learning["runtime_mutation"] is False


def _rule_portrait_batch_report() -> dict[str, object]:
    return {
        "ok": True,
        "status": "pass",
        "domain_count": 8,
        "case_count": 6,
        "failure_count": 0,
        "rule_generation": tuple({"ok": True} for _ in range(8)),
        "case_results": tuple({"ok": True} for _ in range(6)),
        "coverage_summary": {
            "rule_domains": ("wealth", "career", "strength"),
            "portrait_domains": ("time", "wealth", "career"),
        },
        "runtime_mutation": False,
    }
