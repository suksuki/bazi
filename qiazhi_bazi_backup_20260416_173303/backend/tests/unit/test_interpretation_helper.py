from app.services.helpers.interpretation_helper import build_shensha_tag_metadata, merge_interpretation_metadata_for_llm


def test_build_shensha_wenchang_hit() -> None:
    md = {
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day": {"stem": "甲", "branch": "午"},
            "hour": {"stem": "甲", "branch": "巳"},
        }
    }
    out = build_shensha_tag_metadata(md)
    names = {t["name"] for t in out["active_tags"]}
    assert "文昌贵人" in names


def test_merge_interpretation_adds_shensha() -> None:
    md = {"pillars": {"year": {"stem": "甲", "branch": "子"}, "month": {"stem": "丙", "branch": "寅"}, "day": {"stem": "甲", "branch": "午"}, "hour": {"stem": "甲", "branch": "巳"}}}
    merged = merge_interpretation_metadata_for_llm(md)
    assert "interpretation" in merged
    assert merged["interpretation"]["shensha"]["version"] == "shensha_tags.v1"
