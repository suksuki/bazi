from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Iterator

from v17_rebirth.backend.logic.configs import manager as config_manager


PARAMETER_SANDBOX_VERSION = "v17.parameter_sandbox.v1"


@contextmanager
def patched_v17_constants(overrides: dict[str, Any]) -> Iterator[None]:
    """Temporarily override V17 constants in-process.

    This is deliberately test-only. It patches the config manager function, never
    writes `v17_core_constants.json`, and restores the original function on exit.
    """
    original_getter = config_manager.get_v17_constants
    base_constants = deepcopy(original_getter(flatten=False))
    patched_constants = _apply_overrides(base_constants, overrides)

    def _patched_get_v17_constants(flatten: bool = False) -> dict[str, Any]:
        if not flatten:
            return deepcopy(patched_constants)
        flat: dict[str, Any] = {}
        for key, value in patched_constants.items():
            if isinstance(value, dict) and key != "INDUCTION_MAP":
                flat.update(value)
            else:
                flat[key] = value
        return flat

    config_manager.get_v17_constants = _patched_get_v17_constants
    try:
        yield
    finally:
        config_manager.get_v17_constants = original_getter


def build_shadow_override(
    *,
    parameter_path: str,
    multiplier: float,
) -> dict[str, Any]:
    constants = config_manager.get_v17_constants(flatten=False)
    current = _read_path(constants, parameter_path)
    if not isinstance(current, (int, float)):
        return {}
    return {
        parameter_path: round(float(current) * float(multiplier), 6),
    }


def _apply_overrides(constants: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(constants)
    for path, value in (overrides or {}).items():
        parts = [str(part).strip() for part in str(path).split(".") if str(part).strip()]
        if not parts:
            continue
        target = result
        for part in parts[:-1]:
            if not isinstance(target.get(part), dict):
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value
    return result


def _read_path(constants: dict[str, Any], path: str) -> Any:
    cur: Any = constants
    for part in [str(item).strip() for item in str(path).split(".") if str(item).strip()]:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur

