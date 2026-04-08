from __future__ import annotations

from app.skills.blind_work_evaluator import evaluate_blind_work


def test_evaluate_blind_work_builds_vectors():
    metadata = {
        "conflict_matrix": {
            "points": [
                {"detail": "寅申冲"},
                {"detail": "巳申穿"},
            ]
        }
    }
    physics_tensor = {
        "deity_energy_axes": {
            "比肩": {"absolute_energy": 2.0},
            "正印": {"absolute_energy": 1.5},
            "正财": {"absolute_energy": 3.0},
            "正官": {"absolute_energy": 2.0},
        }
    }
    result = evaluate_blind_work(metadata, physics_tensor)
    assert result["work_expectation"] > 0
    assert result["unlock_gain"] > 0
    assert result["backfire_risk"] > 0
    assert result["net_effect"] in {"gain", "neutral", "risk"}
    assert len(result["work_vectors"]) == 2
    assert result["work_vectors"][0]["direction"] in {"Host->Guest", "Guest->Host"}
    assert "unlock_gain" in result["work_vectors"][0]
    assert "backfire_risk" in result["work_vectors"][0]
