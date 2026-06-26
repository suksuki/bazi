from __future__ import annotations

import subprocess
import sys

from v30.validation.session_owner_boundary_readiness import run_session_owner_boundary_readiness


def test_u2_session_owner_boundary_accepts_strict_customer_history() -> None:
    result = run_session_owner_boundary_readiness()

    assert result["version"] == "v30.session_owner_boundary_readiness.v1"
    assert result["decision"]["decision_status"] == "u2_session_owner_boundary_ready"
    assert result["completion_summary"]["durable_auth_session_productization"] == 60
    assert result["completion_summary"]["multi_user_projection_completion"] == 88
    assert result["decision"]["full_login_introduced"] is False
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["decision"]["full_pytest_required"] is False
    assert result["next_mainline_selection"]["task_id"] == "U3"
    assert all(row["passed"] for row in result["checks"])


def test_u2_session_owner_boundary_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_session_owner_boundary_readiness.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "v30.session_owner_boundary_readiness.v1: passed" in result.stdout
    assert "u2_session_owner_boundary_ready" in result.stdout
