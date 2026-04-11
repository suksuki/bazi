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


def test_visibility_filter_minor_when_only_residual_shangguan():
    """余气-only 伤官 + 干上正官 → MINOR_INTERFERENCE，control_energy 受 2% cap。"""
    trace = {
        "伤官": {
            "base_energy": {
                "contribution_sources": [
                    {
                        "source": "year.branch:丑.hidden:辛",
                        "contribution_energy": 2.0,
                    }
                ]
            }
        },
        "正官": {
            "base_energy": {
                "contribution_sources": [
                    {
                        "source": "month.stem:庚",
                        "contribution_energy": 1.5,
                    }
                ]
            }
        },
    }
    flags = detect_universal_flags(
        metadata={"pillars": {"year": {"branch": "丑"}, "month": {"stem": "庚", "branch": "申"}}},
        physics_tensor={
            "deity_energy_axes": {
                "伤官": {"absolute_energy": 2.4},
                "正官": {"absolute_energy": 1.1},
            },
            "deity_trace_details": trace,
        },
    )
    assert flags["SHANG_GUAN_JIAN_GUAN"] is True
    assert flags["sgjg_severity"] == "MINOR_INTERFERENCE"
    assert flags["sgjg_level_label"] == "Level: Deep (藏)"
    assert flags["control_energy"] <= 0.02 * 2.4 + 1e-6


def test_coordinate_distortion_decays_without_tong_gen_or_banhe():
    """天干伤官主导 + 地支正官主导且无通根/半合 → 坐标畸变系数 0.3。"""
    # 甲木日主 → 食伤为火，通根查丙：巳午寅未；四柱地支避开且不含半合对
    md = {
        "pillars": {
            "year": {"stem": "庚", "branch": "戌"},
            "month": {"stem": "丁", "branch": "亥"},
            "day": {"stem": "甲", "branch": "子"},
            "hour": {"stem": "乙", "branch": "酉"},
        }
    }
    trace = {
        "伤官": {
            "base_energy": {
                "contribution_sources": [
                    {"source": "month.stem:丁", "contribution_energy": 5.0},
                    {"source": "day.branch:子.hidden:癸", "contribution_energy": 0.01},
                ]
            }
        },
        "正官": {
            "base_energy": {
                "contribution_sources": [
                    {"source": "hour.branch:酉.hidden:辛", "contribution_energy": 4.0},
                ]
            }
        },
    }
    flags = detect_universal_flags(
        metadata=md,
        physics_tensor={
            "deity_energy_axes": {
                "伤官": {"absolute_energy": 6.0},
                "正官": {"absolute_energy": 5.0},
            },
            "deity_trace_details": trace,
        },
    )
    assert flags["sgjg_coordinate_distortion_applied"] is True
    assert flags["sgjg_coordinate_distortion_factor"] == 0.3
    assert flags["control_energy"] == round(min(6.0, 5.0) * 0.3, 4)

