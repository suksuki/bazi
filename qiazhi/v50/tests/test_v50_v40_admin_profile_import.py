from scripts.v50_import_v40_admin_profiles import birth_input_from_v40, imported_profile_id


def test_v40_admin_profile_conversion_preserves_birth_facts_and_marks_missing_location() -> None:
    row = {
        "profile_id": "v30-admin:example",
        "display_name": "Imported case",
        "gender": "乾",
        "birth_json": {
            "calendar_type": "solar",
            "birth_date": "1980-01-02",
            "birth_time": "03:00",
            "location": "",
            "timezone": "Asia/Shanghai",
        },
        "chart_json": {
            "year_stem": "庚",
            "year_branch": "申",
            "month_stem": "戊",
            "month_branch": "子",
            "day_stem": "甲",
            "day_branch": "辰",
            "hour_stem": "丙",
            "hour_branch": "寅",
        },
    }

    birth = birth_input_from_v40(row)

    assert birth.gender.value == "male"
    assert birth.birth_location == "未记录（V40 导入）"
    assert birth.year_pillar == "庚申"
    assert birth.month_pillar == "戊子"
    assert birth.day_pillar == "甲辰"
    assert birth.hour_pillar == "丙寅"
    assert birth.input_quality == "v40_admin_profile_import"
    assert "source_birth_location_missing" in birth.warnings
    assert imported_profile_id(row["profile_id"]) == imported_profile_id(row["profile_id"])
