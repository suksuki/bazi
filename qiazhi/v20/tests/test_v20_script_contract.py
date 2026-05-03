from __future__ import annotations

import argparse
import json
import pathlib
import ast

from v20.scripts import contract


def test_run_and_print_emits_contract_metadata_and_ok_status(capsys: object) -> None:
    code = contract.run_and_print(
        lambda: {"ok": True, "status": "PASS"},
        command="contract_test.py",
        args=argparse.Namespace(run_id="r1", token="shh", debug=True),
        runtime_mutation=False,
    )

    output = capsys.readouterr().out
    payload = json.loads(output)

    assert code == 0
    assert payload["status"] == "pass"
    assert payload["contract_command"] == "v20/scripts/contract_test.py"
    assert payload["script_path"] == "v20/scripts/contract_test.py"
    assert payload["runtime_mutation"] is False
    assert isinstance(payload["contract_args_hash"], str) and payload["contract_args_hash"]
    assert payload["contract_args"]["run_id"] == "r1"
    assert payload["contract_args"]["token"] == "REDACTED"
    assert payload["contract_args"]["debug"] is True


def test_run_and_print_unknown_status_defaults_to_non_blocking_zero_exit(capsys: object) -> None:
    code = contract.run_and_print(
        lambda: {"status": "custom_in_progress"},
        command="contract_test.py",
        args=argparse.Namespace(),
    )

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["status"] == "custom_in_progress"


def test_run_and_print_exception_is_encoded_as_error_status(capsys: object) -> None:
    def explode() -> dict[str, object]:
        raise RuntimeError("contract_test_failure")

    code = contract.run_and_print(explode, command="contract_test.py", args=argparse.Namespace())

    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["status"] == "error"
    assert payload["ok"] is False
    assert payload["error"] == "contract_test_failure"
    assert "RuntimeError: contract_test_failure" in payload["traceback"]


def test_all_training_scripts_use_run_and_print_contract_entrypoint() -> None:
    root = pathlib.Path(__file__).resolve().parents[2] / "v20" / "scripts"
    script_paths = sorted(path for path in root.glob("*.py") if path.name not in {"contract.py"})
    assert script_paths, "expected script files under v20/scripts"

    missing: list[str] = []
    for path in script_paths:
        text = path.read_text(encoding="utf-8")
        module = ast.parse(text)
        has_main_call = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "run_and_print"
            for node in ast.walk(module)
        )
        if not has_main_call:
            missing.append(path.name)
    assert not missing, f"scripts missing run_and_print contract path: {missing}"
