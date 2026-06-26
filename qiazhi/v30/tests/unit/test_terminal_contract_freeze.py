from __future__ import annotations

import subprocess
import sys

from v30.validation.terminal_contract_freeze import run_terminal_contract_freeze


def test_u4_terminal_contract_freezes_supported_terminals() -> None:
    result = run_terminal_contract_freeze("unit-u4-terminal")

    assert result["version"] == "v30.terminal_contract_freeze.v1"
    assert result["decision"]["decision_status"] == "u4_terminal_contract_frozen"
    assert result["completion_summary"]["multi_terminal_projection_completion"] == 92
    assert result["completion_summary"]["productized_terminal_ui_completion"] == 65
    assert result["completion_summary"]["role_session_client_locale_productization"] == 95
    assert result["decision"]["ui_redesign_required"] is False
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "U5"
    assert all(row["passed"] for row in result["checks"])


def test_u4_terminal_contract_script_runs() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_terminal_contract_freeze.py",
            "--reading-id",
            "unit-u4-script",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "v30.terminal_contract_freeze.v1: passed" in result.stdout
    assert "u4_terminal_contract_frozen" in result.stdout
