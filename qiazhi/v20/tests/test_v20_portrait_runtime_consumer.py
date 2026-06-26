from __future__ import annotations

from v20.features.schema import FeatureLayer
from v20.interaction.portrait_projection import build_portrait_projection


def test_v20_portrait_projection_consumes_active_portrait_policy_pointer() -> None:
    feature_layer = FeatureLayer(version="test", features=())
    decision_model = {
        "version": "test.decision_model",
        "argument_nodes": (
            {
                "argument_id": "argument.strength",
                "domain": "strength",
                "state": "confirmed",
                "score": 0.61,
                "feature_ids": ("feature.strength.capacity",),
                "label": "日主承载",
                "summary": "日主承载结构成立",
                "boundary": "只说明结构边界",
            },
        ),
    }
    decision_report = {
        "version": "test.decision_report",
        "mainlines": (),
    }
    pointer = {
        "version": "v20.portrait_runtime_pointer.v1",
        "status": "candidate_active",
        "active_policy_version": "v20.portrait_policy.candidate.test",
        "candidate_policy_version": "v20.portrait_policy.candidate.test",
        "runtime_applied": True,
        "runtime_allowed": True,
        "policy_payload": {
            "portrait_axis_weight_policy": (
                {
                    "domain": "strength",
                    "axis_weight_delta": 0.04,
                    "confidence_floor_delta": 0.02,
                    "role_depth_hint": "guided_summary",
                    "source": "test",
                },
            )
        },
        "blocking_gate": "",
        "runtime_mutation": False,
    }

    projection = build_portrait_projection(
        feature_layer,
        decision_model,
        decision_report,
        runtime_policy_pointer=pointer,
    )
    axis = projection["axes"][0]
    effect = projection["policy_effect"]["portrait_policy"]

    assert projection["status"] == "ready"
    assert axis["domain"] == "strength"
    assert axis["peak_confidence"] == 0.65
    assert axis["policy_applied"] is True
    assert axis["policy_axis_weight_delta"] == 0.04
    assert axis["policy_role_depth_hint"] == "guided_summary"
    assert effect["status"] == "applied"
    assert effect["active_policy_version"] == "v20.portrait_policy.candidate.test"
    assert effect["policy_count"] == 1
    assert effect["applied_axis_count"] == 1
    assert effect["applied_domains"] == ("strength",)
    assert projection["runtime_policy_effect"] == effect
    assert "PORTRAIT_RUNTIME_CONSUMES_ACTIVE_PORTRAIT_POINTER" in projection["guardrails"]
