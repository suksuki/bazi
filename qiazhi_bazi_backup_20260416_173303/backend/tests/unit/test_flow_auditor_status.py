from app.services.helpers.flow_auditor import apply_energy_flow_audit


def test_flow_auditor_uses_status_element_efficiency() -> None:
    tensor: dict = {
        "normalized": {"wood": 0.05, "fire": 0.05, "earth": 0.4, "metal": 0.25, "water": 0.25},
        "meta": {
            "l1_status_element_flow_efficiency": {
                "wood": 1.25,
                "fire": 1.25,
                "earth": 1.0,
                "metal": 1.0,
                "water": 1.0,
            }
        },
    }
    out = apply_energy_flow_audit(physics_tensor=tensor, physics_config={"FLOW_AUDITOR_ABS_THRESHOLD": 0.06})
    assert out.get("status_flow_efficiency_applied") is True
    wood_fire = next(s for s in out["segments"] if s["from"] == "wood" and s["to"] == "fire")
    assert wood_fire["from_abs_flow"] > wood_fire["from_abs"]
