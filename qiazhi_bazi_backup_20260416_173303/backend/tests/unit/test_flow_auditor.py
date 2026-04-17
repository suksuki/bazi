from app.services.helpers.flow_auditor import apply_energy_flow_audit


def test_flow_auditor_detects_broken_segment() -> None:
    tensor: dict = {
        "normalized": {
            "wood": 0.4,
            "fire": 0.01,
            "earth": 0.2,
            "metal": 0.19,
            "water": 0.2,
        },
        "meta": {},
    }
    out = apply_energy_flow_audit(physics_tensor=tensor, physics_config={"FLOW_AUDITOR_ABS_THRESHOLD": 0.06})
    assert out["break_count"] >= 1
    segs = out["segments"]
    wood_fire = next(s for s in segs if s["from"] == "wood" and s["to"] == "fire")
    assert wood_fire["state"] == "BROKEN"
