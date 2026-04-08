from app.skills.energy_topology_skill import EnergyTopologySkill


def test_energy_topology_skill_emits_resonance_fields():
    out = EnergyTopologySkill().produce(
        {
            "metadata": {
                "pillars": {
                    "year": {"stem": "甲", "branch": "子"},
                    "month": {"stem": "丙", "branch": "寅"},
                    "day": {"stem": "庚", "branch": "午"},
                    "hour": {"stem": "壬", "branch": "酉"},
                },
                "conflict_matrix": {"points": [{"detail": "寅午冲"}]},
            },
            "physics_tensor": {
                "deity_energy_axes": {"比肩": {"absolute_energy": 2.0}, "正财": {"absolute_energy": 4.0}},
                "meta": {"runtime_physics_config": {"STEM_RESONANCE_BOOST": 1.6, "WORK_MIN_THRESHOLD": 0.1}},
                "audit_log": {"param_version_id": "p-x"},
            },
        }
    )
    assert len(out["edges"]) >= 1
    assert "stem_resonance" in out["edges"][0]
    assert "resonance_multiplier" in out["edges"][0]
    assert "efficiency_score" in out["edges"][0]
    assert "flow_direction" in out["edges"][0]
