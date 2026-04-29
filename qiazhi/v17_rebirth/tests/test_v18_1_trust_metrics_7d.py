from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from v17_rebirth.backend.services import v18_1_predictive_engine as engine


def test_trust_metrics_exposes_7_day_realization_fields(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=2)).replace(microsecond=0).isoformat()
    old = (now - timedelta(days=10)).replace(microsecond=0).isoformat()

    service._ledger = {
        "pred-recent-hit": {
            "prediction_id": "pred-recent-hit",
            "created_at": recent,
            "agent_session_id": "agent-a",
            "contract": {"confidence": 0.82},
            "verifier_status": "pass",
        },
        "pred-recent-miss": {
            "prediction_id": "pred-recent-miss",
            "created_at": recent,
            "agent_session_id": "agent-b",
            "contract": {"confidence": 0.68},
            "verifier_status": "pass_with_warning",
        },
        "pred-old": {
            "prediction_id": "pred-old",
            "created_at": old,
            "agent_session_id": "agent-old",
            "contract": {"confidence": 0.74},
            "verifier_status": "pass",
        },
    }
    service._feedback_events = {
        "pred-recent-hit": [{"feedback_type": "hit", "created_at": recent}],
        "pred-recent-miss": [{"feedback_type": "miss", "observed_at": recent}],
        "pred-old": [{"feedback_type": "partial", "created_at": old}],
    }

    metrics = service.query_trust_metrics()

    assert metrics["last_7d_predictions"] == 2
    assert metrics["last_7d_feedback"] == 2
    assert metrics["last_7d_hit_partial_rate"] == 0.5
    assert metrics["last_7d_active_users"] == 2
    assert metrics["last_7d_metrics"]["predictions"] == 2
    assert metrics["last_7d_metrics"]["feedback"] == 2
    assert metrics["last_7d_metrics"]["hit_partial_rate"] == 0.5
    assert metrics["last_7d_metrics"]["data_sufficient"] is False
