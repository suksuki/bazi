from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.policy import RuntimePointerStore
from v30.validation.targeted_calibration_closeout import build_targeted_calibration_closeout


def _settings(tmp_path: Path) -> V30Settings:
    return V30Settings(
        database_url=None,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="memory",
    )


def _deferred_decision() -> dict[str, object]:
    return {
        "version": "v30.targeted_calibration_pointer_decision.v1",
        "decision_id": "unit-f6",
        "operator_decision": "defer",
        "decision": {
            "pointer_decision_recorded": True,
            "operator_deferred_promotion": True,
            "decision_status": "pointer_promotion_deferred",
        },
        "pointer_write_summary": {
            "pointer_write_performed": False,
            "changed_pointer_count": 0,
        },
    }


def test_targeted_calibration_closeout_ready(tmp_path: Path) -> None:
    result = build_targeted_calibration_closeout(
        pointer_decision=_deferred_decision(),
        store=RuntimePointerStore(_settings(tmp_path)),
        closeout_id="unit-f6",
    )

    assert result["version"] == "v30.targeted_calibration_closeout.v1"
    assert result["decision"]["closeout_ready"] is True
    assert result["decision"]["targeted_calibration_track_closed"] is True
    assert result["decision"]["policy_pointer_promotion_allowed"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["core_module_reopen_allowed"] is False
    assert result["monitoring_baseline"]["check_count"] >= 4
    assert result["next_mainline_selection"]["task_id"] == "M0"


def test_targeted_calibration_closeout_blocks_pointer_write() -> None:
    result = build_targeted_calibration_closeout(
        pointer_decision={
            **_deferred_decision(),
            "pointer_write_summary": {
                "pointer_write_performed": True,
                "changed_pointer_count": 1,
            },
        }
    )

    assert result["decision"]["closeout_ready"] is False
    assert "unexpected_pointer_write" in result["decision"]["blockers"]
    assert "active_pointer_changed" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "F6"
