from __future__ import annotations

import pytest

from v30.core.pillars import parse_pillar, pillar_set_from_displays


def test_parse_valid_pillar() -> None:
    pillar = parse_pillar("甲子", "year")
    assert pillar.stem == "甲"
    assert pillar.branch == "子"
    assert pillar.display == "甲子"


def test_parse_rejects_invalid_stem() -> None:
    with pytest.raises(ValueError, match="stem"):
        parse_pillar("A子", "year")


def test_parse_rejects_invalid_branch() -> None:
    with pytest.raises(ValueError, match="branch"):
        parse_pillar("甲A", "year")


def test_pillar_set_from_displays() -> None:
    pillars = pillar_set_from_displays("甲子", "乙丑", "丙寅", "丁卯")
    assert pillars.day.display == "丙寅"
    assert set(pillars.as_map()) == {"year", "month", "day", "hour"}
