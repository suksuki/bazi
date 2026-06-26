from __future__ import annotations

from v30.core.pillars import pillar_set_from_displays
from v30.core.relations import branch_relation_hits


def test_branch_clash_detected() -> None:
    pillars = pillar_set_from_displays("甲子", "乙丑", "丙午", "丁卯").as_map()
    hits = branch_relation_hits(pillars)
    assert any(hit.relation_type == "clash" and set(hit.branches) == {"子", "午"} for hit in hits)


def test_three_harmony_detected() -> None:
    pillars = pillar_set_from_displays("甲申", "乙子", "丙辰", "丁卯").as_map()
    hits = branch_relation_hits(pillars)
    assert any(hit.relation_type == "three_harmony" and hit.element == "water" for hit in hits)
