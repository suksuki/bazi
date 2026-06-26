from __future__ import annotations

from v30.core.ten_gods import ten_god


def test_ten_god_same_element() -> None:
    assert ten_god("甲", "甲") == "比肩"
    assert ten_god("甲", "乙") == "劫财"


def test_ten_god_generation_and_control() -> None:
    assert ten_god("甲", "丙") == "食神"
    assert ten_god("甲", "丁") == "伤官"
    assert ten_god("甲", "戊") == "偏财"
    assert ten_god("甲", "己") == "正财"
    assert ten_god("甲", "庚") == "七杀"
    assert ten_god("甲", "辛") == "正官"
    assert ten_god("甲", "壬") == "偏印"
    assert ten_god("甲", "癸") == "正印"
