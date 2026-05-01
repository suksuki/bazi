from __future__ import annotations

from v20.core.constants import BRANCHES, HIDDEN_STEMS, STEMS, VAULT_BRANCHES, element_of_stem
from v20.core.relations import branch_relation_hits
from v20.core.schemas import ChartFacts, ChartInput, Pillar, TenGodPosition
from v20.core.ten_gods import ten_god

CHART_FACTS_VERSION = "v20.chart_facts.v1"


def pillar_from_display(display: str, position: str) -> Pillar:
    value = str(display or "").strip()
    if len(value) != 2:
        raise ValueError(f"{position} pillar must be two characters.")
    stem, branch = value[0], value[1]
    if stem not in STEMS:
        raise ValueError(f"{position} stem is not supported: {stem}")
    if branch not in BRANCHES:
        raise ValueError(f"{position} branch is not supported: {branch}")
    return Pillar(stem=stem, branch=branch, position=position)


def chart_input_from_displays(year: str, month: str, day: str, hour: str, *, input_id: str = "") -> ChartInput:
    return ChartInput(
        pillars=(
            pillar_from_display(year, "year"),
            pillar_from_display(month, "month"),
            pillar_from_display(day, "day"),
            pillar_from_display(hour, "hour"),
        ),
        input_id=input_id,
    )


def build_chart_facts(chart_input: ChartInput) -> ChartFacts:
    pillars = chart_input.pillar_map()
    day_master = pillars["day"].stem
    visible: list[TenGodPosition] = []
    hidden: list[TenGodPosition] = []
    for position, pillar in pillars.items():
        if position != "day":
            label = ten_god(day_master, pillar.stem)
            visible.append(
                TenGodPosition(
                    label=label,
                    stem=pillar.stem,
                    pillar=position,
                    layer="visible",
                    element=element_of_stem(pillar.stem),
                    weight=1.0,
                )
            )
        for stem, weight in HIDDEN_STEMS.get(pillar.branch, []):
            label = ten_god(day_master, stem)
            hidden.append(
                TenGodPosition(
                    label=label,
                    stem=stem,
                    pillar=position,
                    layer="hidden",
                    element=element_of_stem(stem),
                    weight=weight,
                )
            )
    vaults = tuple(position for position, pillar in pillars.items() if pillar.branch in VAULT_BRANCHES)
    return ChartFacts(
        version=CHART_FACTS_VERSION,
        pillars=pillars,
        day_master=day_master,
        day_master_element=element_of_stem(day_master),
        visible_ten_gods=tuple(visible),
        hidden_ten_gods=tuple(hidden),
        relation_hits=branch_relation_hits(pillars),
        vault_branches=vaults,
        calendar_assumption=chart_input.calendar_assumption,
    )
