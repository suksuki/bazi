from __future__ import annotations

import sys
from pathlib import Path


V50_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = V50_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from v50_run_policy_anti_overfit_review import run_review


def test_v50_policy_anti_overfit_review_uses_non_base_charts_and_does_not_tune_weights() -> None:
    summary = run_review()

    assert summary["total"] >= 10
    assert summary["non_base_derived_cases"] == summary["total"]
    assert summary["base_chart_family_excluded"] == "丁巳 乙巳 乙丑 乙酉"
    assert summary["llm_used"] is False
    assert summary["brain_used"] is False
    assert summary["training_performed"] is False
    assert summary["weight_adjustment_performed"] is False
    assert summary["overfit_warning"] is False
    assert all(result["chart"] != summary["base_chart_family_excluded"] for result in summary["results"])


def test_v50_policy_anti_overfit_review_requires_principle_reasons_and_category_spread() -> None:
    summary = run_review()
    counts = summary["category_counts_v2"]

    assert all(change["mingli_principle_reason"] for change in summary["node_weight_changes"])
    assert all(
        change["mingli_principle_reason"]
        for change in summary["legacy_unvalidated_path_weight_changes"]
    )
    assert summary["max_category_share_v2"] <= 0.5
    assert summary["converter_bridge_share_v2"] <= 0.55
    assert counts["month_command_first"] >= 3
    assert counts["converter_first"] < summary["total"] / 2
    assert counts["no_obvious_first"] >= 1
