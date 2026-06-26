from __future__ import annotations

from pathlib import Path

from v20.role_view.completion import build_role_view_completion_report
from v20.storage.local_jsonl import LocalJsonlStore
from v20.tests.support_paths import read_v20_text


def test_v20_role_view_completion_report_marks_mainline_complete(tmp_path: Path) -> None:
    report = build_role_view_completion_report(store=LocalJsonlStore(runtime_dir=tmp_path))

    assert report["version"] == "v20.role_view_mainline_completion.v1"
    assert report["status"] == "complete"
    assert report["completion_percent"] == 100
    assert report["phase_count"] == 7
    assert report["complete_phase_count"] == 7
    assert report["data_state"]["seed_count"] >= 20
    assert "role_seed_question_priority" in report["runtime_scope"]
    assert "no_core_inference_mutation" in report["non_goals"]
    assert "ROLE_VIEW_RUNTIME_POLICY_ONLY_REORDERS_VIEW_QUESTIONS" in report["guardrails"]


def test_v20_role_view_completion_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/role-view/completion" in server_text
    assert "build_role_view_completion_report" in server_text
