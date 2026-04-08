from app.core.rules.junction import detect_universal_flags


def test_detect_shangguan_jian_guan_flag_from_l1_tensor():
    flags = detect_universal_flags(
        metadata={},
        physics_tensor={
            "deity_energy_axes": {
                "伤官": {"absolute_energy": 2.4},
                "正官": {"absolute_energy": 1.1},
            }
        },
    )
    assert flags["SHANG_GUAN_JIAN_GUAN"] is True
    assert flags["control_energy"] == 1.1
    assert flags["source"] == "L1_Junction"

