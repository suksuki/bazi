from __future__ import annotations

from v17_rebirth.backend.services.decision_batches import build_decision_batches


def test_build_decision_batches_merges_same_target_and_source_family() -> None:
    arbitration = {
        "manual_decisions": [
            {
                "id": "m1",
                "source": "l1.physics.op_branch_liupo",
                "label": "子卯刑压制食神",
                "target_god": "食神",
                "priority": 0.9,
                "physical_impact": {"impact_ratio": -0.08, "significance_weight": 1.0},
            },
            {
                "id": "m2",
                "source": "l1.physics.op_branch_liupo",
                "label": "子卯刑再次压制食神",
                "target_god": "食神",
                "priority": 0.8,
                "physical_impact": {"impact_ratio": -0.06, "significance_weight": 1.0},
            },
        ],
        "auto_resolutions": [],
        "llm_arbitration_context": [],
    }

    batches = build_decision_batches(arbitration=arbitration)
    assert len(batches["manual"]) == 1
    batch = batches["manual"][0]
    assert batch["decision_count"] == 2
    assert batch["target_god"] == "食神"
    assert batch["net_impact_ratio"] == -0.14
    assert "围绕 食神 聚合 2 条主张" in batch["prompt_line"]


def test_build_decision_batches_generates_prompt_lines_for_llm() -> None:
    arbitration = {
        "manual_decisions": [],
        "auto_resolutions": [],
        "llm_arbitration_context": [
            {
                "id": "l1",
                "source": "l2.risk.risk_matrix",
                "label": "风险矩阵提示正财承压",
                "target_god": "正财",
                "priority": 0.7,
                "physical_impact": {"impact_ratio": -0.05, "significance_weight": 1.0},
            }
        ],
    }

    batches = build_decision_batches(arbitration=arbitration)
    assert len(batches["llm"]) == 1
    assert len(batches["prompt_lines"]) == 1
    assert "决策批次[LLM]" in batches["prompt_lines"][0]
