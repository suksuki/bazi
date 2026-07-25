from __future__ import annotations

import sys
from pathlib import Path


V50_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = V50_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from core.timing import TimingLayer, build_timing_model_candidates_v1
from v50_validate_timing_model_candidates import validate_candidates


def test_v50_timing_model_candidates_keep_competing_models_not_runtime_truth() -> None:
    candidates = build_timing_model_candidates_v1()

    assert len(candidates) == 12
    assert {candidate.timing_layer for candidate in candidates} == {
        TimingLayer.LUCK,
        TimingLayer.YEAR,
        TimingLayer.MONTH,
    }
    assert sum(1 for candidate in candidates if candidate.timing_layer == TimingLayer.LUCK) == 4
    assert sum(1 for candidate in candidates if candidate.timing_layer == TimingLayer.YEAR) == 4
    assert sum(1 for candidate in candidates if candidate.timing_layer == TimingLayer.MONTH) == 4
    assert all(not candidate.runtime_active for candidate in candidates)
    assert all(not candidate.creates_judgment for candidate in candidates)
    assert all(not candidate.calls_brain for candidate in candidates)
    assert all(not candidate.calls_llm for candidate in candidates)
    assert all(not candidate.mutates_natal_structure for candidate in candidates)
    assert all("natal_immutable_facts" in candidate.does_not_change for candidate in candidates)


def test_v50_timing_model_candidates_validation_report_is_green() -> None:
    summary = validate_candidates()

    assert summary["passed"] is True
    assert summary["total"] == 12
    assert summary["layer_counts"] == {"luck": 4, "month": 4, "year": 4}
    assert summary["runtime_active"] is False
    assert summary["llm_used"] is False
    assert summary["brain_used"] is False
    assert summary["training_performed"] is False
    assert summary["highest_confidence_by_layer"]["luck"]["model_id"] == "timing.luck.perturbation_source.v1"
    assert summary["highest_confidence_by_layer"]["year"]["model_id"] == "timing.year.activation_event.v1"
    assert summary["highest_confidence_by_layer"]["month"]["model_id"] == "timing.month.event_window.v1"
