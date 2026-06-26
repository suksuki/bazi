from __future__ import annotations

from v30.core.pillars import pillar_set_from_displays
from v30.core.time_context import build_time_context, empty_time_context


def test_empty_time_context_is_explicit() -> None:
    context = empty_time_context()
    assert context.status == "not_provided"
    assert context.missing_requirements == ("explicit_luck_or_flow_pillar",)


def test_build_explicit_time_context() -> None:
    pillars = pillar_set_from_displays("甲子", "乙丑", "丙寅", "丁卯").as_map()
    context = build_time_context(pillars, day_master="丙", luck_pillar="庚午", flow_year_pillar="辛未")
    assert context.status == "ready"
    assert [layer.layer_key for layer in context.layers] == ["luck", "flow_year"]
    assert context.layers[0].pillar.display == "庚午"
    assert context.missing_requirements == ()
