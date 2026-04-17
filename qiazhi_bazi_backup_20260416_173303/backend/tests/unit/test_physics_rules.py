from app.skills.physics_rules import ROOT_MAP, deity_from_self_and_target_stem


def test_deity_mapping_matches_expected_relationships():
    assert deity_from_self_and_target_stem(day_stem="甲", target_stem="甲") == "比肩"
    assert deity_from_self_and_target_stem(day_stem="甲", target_stem="乙") == "劫财"
    assert deity_from_self_and_target_stem(day_stem="甲", target_stem="丙") == "食神"
    assert deity_from_self_and_target_stem(day_stem="甲", target_stem="辛") == "正官"


def test_root_map_keeps_expected_day_master_roots():
    assert {"寅", "卯"}.issubset(ROOT_MAP["甲"])
    assert {"申", "酉"}.issubset(ROOT_MAP["庚"])
