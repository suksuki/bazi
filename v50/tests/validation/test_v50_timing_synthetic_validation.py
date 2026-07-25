from __future__ import annotations

import json
import sys
from pathlib import Path


V50_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = V50_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from v50_run_timing_synthetic_validation import run_group


FIXTURE_FILE = V50_ROOT / "data" / "validation" / "fixtures" / "timing_synthetic_validation_v1.json"


def test_v50_timing_synthetic_validation_fixture_group_shape() -> None:
    payload = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))

    assert payload["group"] == "timing_synthetic_validation_v1"
    assert len(payload["fixtures"]) == 6
    assert {fixture["temporal_state"]["timing_layer"] for fixture in payload["fixtures"]} == {
        "luck",
        "year",
        "month",
    }
    for fixture in payload["fixtures"]:
        assert fixture["candidate_model_id"].startswith("timing.")
        assert fixture["current_flow_state"]["mechanism"]
        assert fixture["temporal_state"]["evidence_refs"]
        assert fixture["expected"]["candidate_outputs"]
        assert fixture["expected"]["delta_keys"]
        assert "birth_input" in fixture["expected"]["must_not_change"]


def test_v50_timing_synthetic_validation_runner_validates_state_delta_without_runtime_activation() -> None:
    summary = run_group("timing_synthetic_validation_v1")

    assert summary["total"] == 6
    assert summary["passed"] == 6
    assert summary["failed"] == 0
    assert summary["llm_used"] is False
    assert summary["brain_used"] is False
    assert summary["training_performed"] is False
    assert summary["runtime_timing_policy_activated"] is False
    assert summary["layer_counts"] == {"luck": 2, "month": 2, "year": 2}
    for result in summary["results"]:
        assert result["passed"] is True
        assert result["errors"] == []
        assert result["checks"]["candidate_not_runtime_active"] is True
        assert result["checks"]["candidate_does_not_mutate_natal"] is True
        assert result["checks"]["evolution_no_judgment"] is True
        assert result["checks"]["evolution_no_brain"] is True
        assert result["checks"]["evolution_no_llm"] is True
        assert result["observed"]["delta_keys"]
        assert result["observed"]["reason_codes"]
