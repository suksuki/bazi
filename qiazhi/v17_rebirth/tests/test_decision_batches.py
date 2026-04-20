from __future__ import annotations

from v17_rebirth.backend.services.decision_batches import build_decision_batches


def test_build_decision_batches_merges_same_target_and_direction_across_sources() -> None:
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
                "source": "l1.physics.op_branch_liuhai",
                "label": "六害再次压制食神",
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
    assert batch["direction_key"] == "down"
    assert batch["direction_label"] == "抑制组"
    assert "食神抑制组 聚合 2 条主张" in batch["prompt_line"]
    assert set(batch["source_families"]) == {"l1.physics.op_branch_liuhai", "l1.physics.op_branch_liupo"}


def test_build_decision_batches_splits_opposite_directions() -> None:
    arbitration = {
        "manual_decisions": [
            {
                "id": "m1",
                "source": "l1.physics.op_branch_sanhe",
                "label": "三合增强七杀",
                "target_god": "七杀",
                "priority": 0.9,
                "physical_impact": {"impact_ratio": 0.23, "significance_weight": 1.0},
            },
            {
                "id": "m2",
                "source": "l1.physics.op_branch_liupo",
                "label": "六破压制七杀",
                "target_god": "七杀",
                "priority": 0.6,
                "physical_impact": {"impact_ratio": -0.04, "significance_weight": 1.0},
            },
        ],
        "auto_resolutions": [],
        "llm_arbitration_context": [],
    }

    batches = build_decision_batches(arbitration=arbitration)
    assert len(batches["manual"]) == 2
    direction_keys = {row["direction_key"] for row in batches["manual"]}
    assert direction_keys == {"up", "down"}


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
