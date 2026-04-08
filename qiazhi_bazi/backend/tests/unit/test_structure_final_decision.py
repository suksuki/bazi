from app.skills.structure_final_decision import build_structure_final_decision_v0


def test_build_structure_final_decision_includes_strategic_advice():
    out = build_structure_final_decision_v0(
        structure_candidates_v0={
            "self_abs": 0.7,
            "candidates": [
                {"name": "FOLLOW_WEALTH_POWER", "state": "CollapsedState", "match_score": 0.82},
            ],
        },
        work_vector={
            "net_effect": "gain",
            "work_expectation": 3.2,
            "released_energy": 4.1,
            "work_vectors": [
                {"expected_work": 2.1, "contributors": ["偏财", "正官"]},
            ],
        },
    )
    assert out["primary_structure"] == "FOLLOW_WEALTH_POWER"
    assert "primary_structure_humanized" in out
    assert "balance_verdict" in out
    assert "work_verdict" in out
    assert "strategic_advice" in out
    assert "recommendation" in out["strategic_advice"]
    assert "utility_god" in out
    assert "obstacle_god" in out
    assert "climate_adjustment" in out
