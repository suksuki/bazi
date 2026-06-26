from __future__ import annotations

import subprocess
import sys

from v30.validation.multi_user_terminal_locale_readiness import run_multi_user_terminal_locale_readiness


def test_u1_readiness_accepts_full_role_locale_client_matrix() -> None:
    result = run_multi_user_terminal_locale_readiness("unit-u1-readiness")

    assert result["version"] == "v30.multi_user_terminal_locale_readiness.v1"
    assert result["matrix_summary"]["combination_count"] == 72
    assert result["matrix_summary"]["customer_roles"] == ["guest", "user"]
    assert set(result["matrix_summary"]["diagnostic_roles"]) >= {"practitioner", "admin", "analyst", "lab"}
    assert result["completion_summary"]["multi_user_projection_completion"] == 80
    assert result["completion_summary"]["multi_terminal_projection_completion"] == 78
    assert result["completion_summary"]["multi_locale_projection_completion"] == 76
    assert result["decision"]["decision_status"] == "u1_projection_readiness_ready"
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["decision"]["full_pytest_required"] is False
    assert result["next_mainline_selection"]["task_id"] == "U2"


def test_u1_readiness_script_runs_projection_gate() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_multi_user_terminal_locale_readiness.py",
            "--reading-id",
            "unit-u1-script",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "v30.multi_user_terminal_locale_readiness.v1: passed" in result.stdout
    assert "u1_projection_readiness_ready" in result.stdout
