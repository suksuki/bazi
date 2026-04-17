from app.core.plugins.conflict_evaluator import evaluate_plugin_conflict


def test_conflict_evaluator_marks_polarity_reversal():
    report = evaluate_plugin_conflict(
        plugin_outputs={
            "classical.blind_school.v1": {"verdict": "可转化，顺势推进", "confidence_score": 0.9},
            "classical.wangshuai.v1": {"verdict": "闭锁受阻，建议止损", "confidence_score": 0.9},
        },
        plugin_weights={
            "classical.blind_school.v1": 1.0,
            "classical.wangshuai.v1": 1.0,
        },
    )
    assert report["has_polarity_reversal"] is True
    assert report["zone"] in {"RED", "YELLOW"}
