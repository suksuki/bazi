from __future__ import annotations

import importlib.util
from pathlib import Path

from v30.api.app import M3_BACKGROUND_STEP_TIMEOUTS


def test_m3_background_step_timeouts_are_background_sized() -> None:
    assert M3_BACKGROUND_STEP_TIMEOUTS["m3_snapshot"] >= 180
    assert M3_BACKGROUND_STEP_TIMEOUTS["training_pipeline"] >= 900
    assert M3_BACKGROUND_STEP_TIMEOUTS["518k_sample"] >= 900
    assert M3_BACKGROUND_STEP_TIMEOUTS["518k_readiness_matrix"] >= 1200


def test_m3_background_script_uses_same_timeout_policy() -> None:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "run_m3_background_training_job.py"
    spec = importlib.util.spec_from_file_location("run_m3_background_training_job", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.M3_BACKGROUND_STEP_TIMEOUTS == M3_BACKGROUND_STEP_TIMEOUTS
