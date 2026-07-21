from __future__ import annotations

import json
import sys
from pathlib import Path


V50_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = V50_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from v50_run_synthetic_work_system_fixtures import run_group


FIXTURE_FILE = V50_ROOT / "data" / "validation" / "fixtures" / "synthetic_work_system_v1.json"


def test_v50_synthetic_work_system_fixture_group_has_ten_golden_samples() -> None:
    payload = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))

    assert payload["group"] == "synthetic_work_system_v1"
    assert len(payload["cases"]) == 10
    for case in payload["cases"]:
        assert case["structural_variable"]
        assert case["expected_roles"]
        assert "expected_critical_nodes" in case
        assert "expected_ablation_prefix" in case
        assert "must_not_roles" in case


def test_v50_synthetic_work_system_runner_validates_path_role_importance_ablation_chain() -> None:
    summary = run_group("synthetic_work_system_v1")

    assert summary["total"] == 10
    assert summary["passed"] == 10
    assert summary["failed"] == 0
    assert summary["llm_used"] is False
    assert summary["brain_used"] is False
    assert summary["ui_used"] is False
    assert summary["training_performed"] is False
    assert summary["node_importance_policy_version"] == "node_importance_policy_v2"
    assert summary["legacy_unvalidated_path_score_policy_version"] == "path_score_policy_v2"
    assert all(result["checks"]["paths_explored"] > 0 for result in summary["results"])
    assert all(result["checks"]["roles_assigned"] > 0 for result in summary["results"])
