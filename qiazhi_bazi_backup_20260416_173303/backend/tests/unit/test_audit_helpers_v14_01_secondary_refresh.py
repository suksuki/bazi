from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.helpers import audit_helpers as ah


def test_parse_interaction_sql_patch_kv() -> None:
    sql = "UPDATE physics_interaction_params SET param_value=0.42 WHERE param_key='CF_FLOATING_DECAY';"
    p = ah.parse_interaction_sql_patch_kv(sql)
    assert p is not None
    assert p[0] == "CF_FLOATING_DECAY"
    assert abs(p[1] - 0.42) < 1e-6


def test_secondary_refresh_merges_and_calls_evaluate(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict = {}

    def fake_evaluate(*, physics_tensor, metadata, interaction_params, physics_config=None):
        called["params"] = dict(interaction_params)
        return {"ok": True}

    monkeypatch.setattr(
        "app.services.helpers.interaction_pipeline.evaluate_interactions",
        fake_evaluate,
    )

    class FakeSkill:
        @staticmethod
        def instance():
            m = MagicMock()
            m.get_interaction_params = lambda: {"CF_FLOATING_DECAY": 0.1, "conflict_penalty_gamma": 0.12}
            return m

    monkeypatch.setattr("app.skills.physics_engine.PhysicsInferenceSkill", FakeSkill)

    md = {
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day": {"stem": "戊", "branch": "午"},
            "hour": {"stem": "庚", "branch": "申"},
        },
        "decision_impact_registry_v14_01": {
            "pending_sql_patches": [
                "UPDATE physics_interaction_params SET param_value=0.55 WHERE param_key='CF_FLOATING_DECAY';",
            ],
            "events": [],
        },
    }
    pt: dict = {"meta": {}, "by_pillar": {}, "deity_scores": {}, "deity_energy_axes": {}}

    out = ah.secondary_refresh_physics_tensor_before_final_verdict_v14_01(md, pt)
    assert out.get("applied") is True
    assert "CF_FLOATING_DECAY" in (out.get("applied_param_keys") or [])
    assert md["decision_impact_registry_v14_01"].get("pending_sql_patches") == []
    assert called.get("params", {}).get("CF_FLOATING_DECAY") == 0.55
