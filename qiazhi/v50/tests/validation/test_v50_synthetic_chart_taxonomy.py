from __future__ import annotations

import sys
from pathlib import Path


V50_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = V50_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from v50_validate_synthetic_chart_taxonomy import EXPECTED_CASE_TYPES, validate_taxonomy


def test_v50_synthetic_chart_taxonomy_defines_required_structural_families() -> None:
    summary = validate_taxonomy()

    assert summary["passed"] is True
    assert summary["total_case_types"] == len(EXPECTED_CASE_TYPES)
    assert summary["total_cases"] == 17
    assert set(summary["case_type_counts"]) == EXPECTED_CASE_TYPES
    assert all(count == 1 for count in summary["case_type_counts"].values())


def test_v50_synthetic_chart_taxonomy_is_not_runtime_training_or_fortune_validation() -> None:
    summary = validate_taxonomy()

    assert summary["runtime_active"] is False
    assert summary["llm_used"] is False
    assert summary["brain_used"] is False
    assert summary["training_performed"] is False
    assert summary["errors"] == []
    assert set(summary["timing_overlay_cases"]) == {"luck_changes_main_path", "year_activates_key_node"}
