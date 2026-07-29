from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_TOOL_PATH = Path(__file__).resolve().parents[2] / "tools" / "local_runtime.py"
_SPEC = importlib.util.spec_from_file_location("v60_local_runtime", _TOOL_PATH)
assert _SPEC is not None and _SPEC.loader is not None
local_runtime = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(local_runtime)


def test_runtime_guard_rejects_stale_game_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    engines = dict(local_runtime.EXPECTED_ENGINES)
    engines["game"] = "v60.dream-game-engine.stale"
    monkeypatch.setattr(
        local_runtime,
        "_runtime_probe",
        lambda host, port: {
            "manifest": {
                "product_id": local_runtime.PRODUCT_ID,
                "engines": engines,
            },
            "runtime_status": {"status": "READY"},
        },
    )

    with pytest.raises(local_runtime.LocalRuntimeError, match="version_mismatch"):
        local_runtime._assert_ready("127.0.0.1", 8060)


def test_runtime_guard_rejects_stale_decision_kernel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engines = dict(local_runtime.EXPECTED_ENGINES)
    engines["decision"] = "v60.cognitive-decision-kernel.stale"
    monkeypatch.setattr(
        local_runtime,
        "_runtime_probe",
        lambda host, port: {
            "manifest": {
                "product_id": local_runtime.PRODUCT_ID,
                "engines": engines,
            },
            "runtime_status": {"status": "READY"},
        },
    )

    with pytest.raises(local_runtime.LocalRuntimeError, match="version_mismatch"):
        local_runtime._assert_ready("127.0.0.1", 8060)


def test_runtime_guard_rejects_degraded_integrity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        local_runtime,
        "_runtime_probe",
        lambda host, port: {
            "manifest": {
                "product_id": local_runtime.PRODUCT_ID,
                "engines": dict(local_runtime.EXPECTED_ENGINES),
            },
            "runtime_status": {"status": "DEGRADED"},
        },
    )

    with pytest.raises(local_runtime.LocalRuntimeError, match="integrity_not_ready"):
        local_runtime._assert_ready("127.0.0.1", 8060)


def test_runtime_guard_rejects_stale_database_foundation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        local_runtime,
        "_runtime_probe",
        lambda host, port: {
            "health": {
                "status": "degraded",
                "database": {
                    "status": "incompatible",
                    "foundation_version": "v60.foundation.001",
                },
            },
            "manifest": {
                "product_id": local_runtime.PRODUCT_ID,
                "engines": dict(local_runtime.EXPECTED_ENGINES),
            },
            "runtime_status": {"status": "READY"},
        },
    )

    with pytest.raises(
        local_runtime.LocalRuntimeError,
        match="database_foundation_mismatch",
    ):
        local_runtime._assert_ready("127.0.0.1", 8060)


def test_runtime_guard_only_owns_its_exact_uvicorn_process(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(local_runtime, "RUNTIME_DIR", tmp_path)
    pid_path, _ = local_runtime._paths(8060)
    pid_path.write_text(
        '{"pid":123,"host":"127.0.0.1","port":8060}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        local_runtime,
        "_process_command",
        lambda pid: "python unrelated-service.py",
    )

    assert local_runtime._owned_pid(8060) is None
