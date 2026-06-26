from __future__ import annotations

import subprocess
import sys

from v30.validation.productization_closeout import run_productization_closeout


def test_u5_productization_closeout_accepts_u1_u4_evidence() -> None:
    result = run_productization_closeout("unit-u5-productization")

    assert result["version"] == "v30.productization_closeout.v1"
    assert result["decision"]["decision_status"] == "u5_productization_steady_state_ready"
    assert result["decision"]["productization_steady_state"] is True
    assert result["completion_summary"]["role_session_client_locale_productization"] == 100
    assert result["completion_summary"]["multi_user_projection_completion"] == 100
    assert result["completion_summary"]["multi_terminal_projection_completion"] == 100
    assert result["completion_summary"]["multi_language_projection_completion"] == 100
    assert result["completion_summary"]["durable_auth_session_productization"] == 80
    assert result["completion_summary"]["productized_terminal_ui_completion"] == 80
    assert result["completion_summary"]["deep_locale_content_completion"] == 85
    assert result["decision"]["full_login_required"] is False
    assert result["decision"]["ui_redesign_required"] is False
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "U-S1"
    assert all(row["ready"] for row in result["accepted_evidence"].values())
    assert all(row["passed"] for row in result["checks"])


def test_u5_productization_closeout_script_runs() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_productization_closeout.py",
            "--reading-id",
            "unit-u5-script",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "v30.productization_closeout.v1: passed" in result.stdout
    assert "u5_productization_steady_state_ready" in result.stdout
