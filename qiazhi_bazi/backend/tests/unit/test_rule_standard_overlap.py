from app.plugins.blind_school.rules.rule_standard_overlap import standard_overlap_chip_logs


def test_standard_overlap_emits_chip_when_junction_flag():
    physics = {
        "meta": {
            "l1_junction_flags": {
                "SHANG_GUAN_JIAN_GUAN": True,
            }
        }
    }
    lines = standard_overlap_chip_logs(physics_tensor=physics)
    assert len(lines) == 1
    assert "伤官见官" in lines[0]
    assert "1.5x" in lines[0]


def test_standard_overlap_silent_when_no_flag():
    assert standard_overlap_chip_logs(physics_tensor={"meta": {}}) == []


def test_standard_overlap_skips_minor_interference():
    physics = {
        "meta": {
            "l1_junction_flags": {
                "SHANG_GUAN_JIAN_GUAN": True,
                "sgjg_severity": "MINOR_INTERFERENCE",
            }
        }
    }
    assert standard_overlap_chip_logs(physics_tensor=physics) == []
