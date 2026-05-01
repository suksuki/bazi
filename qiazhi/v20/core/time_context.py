from __future__ import annotations

from v20.core.chart import pillar_from_display
from v20.core.constants import element_of_stem
from v20.core.relations import branch_relation_hits
from v20.core.schemas import ChartFacts, Pillar, RelationHit, TenGodPosition, TimeContext, TimeLayerFact
from v20.core.ten_gods import ten_god


def empty_time_context() -> TimeContext:
    return TimeContext()


def build_time_context(
    facts: ChartFacts,
    *,
    flow_year_pillar: str = "",
    luck_pillar: str = "",
    flow_month_pillar: str = "",
) -> TimeContext:
    requested = (
        ("luck", luck_pillar),
        ("flow_year", flow_year_pillar),
        ("flow_month", flow_month_pillar),
    )
    layers = tuple(_build_layer(facts, layer_key, display) for layer_key, display in requested if display.strip())
    if not layers:
        return empty_time_context()
    relation_hits = tuple(hit for layer in layers for hit in layer.relation_hits)
    return TimeContext(
        status="ready",
        note="Explicit time pillars supplied; timing remains evidence-bounded and cannot produce fixed events.",
        layers=layers,
        relation_hits=relation_hits,
    )


def _build_layer(facts: ChartFacts, layer_key: str, display: str) -> TimeLayerFact:
    pillar = pillar_from_display(display, layer_key)
    time_ten_god = TenGodPosition(
        label=ten_god(facts.day_master, pillar.stem),
        stem=pillar.stem,
        pillar=layer_key,
        layer="time",
        element=element_of_stem(pillar.stem),
        weight=1.0,
    )
    return TimeLayerFact(
        layer_key=layer_key,
        pillar=pillar,
        ten_god=time_ten_god,
        relation_hits=_time_relation_hits(facts, pillar),
    )


def _time_relation_hits(facts: ChartFacts, time_pillar: Pillar) -> tuple[RelationHit, ...]:
    combined = {**facts.pillars, time_pillar.position: time_pillar}
    hits = branch_relation_hits(combined)
    return tuple(
        RelationHit(
            relation_type=hit.relation_type,
            branches=hit.branches,
            positions=hit.positions,
            layer="time",
            element=hit.element,
        )
        for hit in hits
        if time_pillar.position in hit.positions
    )
