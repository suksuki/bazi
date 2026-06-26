from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_promote_policy_candidate_script(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "V30_RUNTIME_DIR": str(tmp_path / ".runtime"),
        "V30_ENV": "test",
    }
    result = subprocess.run(
        [
            sys.executable,
            "scripts/promote_policy_candidate.py",
            "--family",
            "structure_policy",
            "--candidate-id",
            "script-candidate",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    pointer_path = tmp_path / ".runtime" / "policies" / "structure_policy" / "active.json"
    assert result.returncode == 0
    assert "structure_policy:script-candidate: promoted" in result.stdout
    assert pointer_path.exists()
    assert "structure_policy.script-candidate" in pointer_path.read_text(encoding="utf-8")
