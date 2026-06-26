from __future__ import annotations

import subprocess
import sys


def test_synthetic_validation_script_smoke() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_synthetic_validation.py", "--tier", "smoke"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "v30.synthetic.smoke: passed" in result.stdout


def test_synthetic_validation_script_gradient() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_synthetic_validation.py", "--tier", "gradient"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "v30.synthetic.gradient: passed" in result.stdout
