from __future__ import annotations

from v30.contracts import V30Model
from v30.core.constants import element_of_stem
from v30.core.pillars import Pillar, parse_pillar
from v30.core.relations import RelationHit, branch_relation_hits
from v30.core.ten_gods import TenGodPosition, ten_god


class TimeLayerFact(V30Model):
    layer_key: str
    pillar: Pillar
    ten_god: TenGodPosition
    relation_hits: tuple[RelationHit, ...] = ()
    source: str = "explicit_pillar"
    confidence: float = 1.0


class TimeContext(V30Model):
    version: str = "v30.time_context.v1"
    status: str = "not_provided"
    note: str = "Time layer is background only until explicit luck/flow facts are supplied."
    layers: tuple[TimeLayerFact, ...] = ()
    relation_hits: tuple[RelationHit, ...] = ()
    missing_requirements: tuple[str, ...] = ("explicit_luck_or_flow_pillar",)
    guardrails: tuple[str, ...] = (
        "TIME_LAYER_REQUIRES_EXPLICIT_PILLAR",
        "NO_TIMING_PREDICTION_WITHOUT_EVIDENCE",
    )


def empty_time_context() -> TimeContext:
    return TimeContext()


def build_time_context(
    natal_pillars: dict[str, Pillar],
    *,
    day_master: str,
    luck_pillar: str = "",
    flow_year_pillar: str = "",
    flow_month_pillar: str = "",
) -> TimeContext:
    requested = (
        ("luck", luck_pillar),
        ("flow_year", flow_year_pillar),
        ("flow_month", flow_month_pillar),
    )
    layers = tuple(
        _build_layer(natal_pillars, day_master=day_master, layer_key=layer_key, display=display)
        for layer_key, display in requested
        if display.strip()
    )
    if not layers:
        return empty_time_context()
    relation_hits = tuple(hit for layer in layers for hit in layer.relation_hits)
    return TimeContext(
        status="ready",
        note="Explicit time pillars supplied; timing remains evidence-bounded and cannot produce fixed events.",
        layers=layers,
        relation_hits=relation_hits,
        missing_requirements=(),
    )


def _build_layer(
    natal_pillars: dict[str, Pillar],
    *,
    day_master: str,
    layer_key: str,
    display: str,
) -> TimeLayerFact:
    pillar = parse_pillar(display, layer_key)
    time_ten_god = TenGodPosition(
        label=ten_god(day_master, pillar.stem),
        stem=pillar.stem,
        pillar=layer_key,
        layer="time",
        element=element_of_stem(pillar.stem),
        weight=1.0,
    )
    combined = {**natal_pillars, layer_key: pillar}
    hits = tuple(hit for hit in branch_relation_hits(combined, layer="time") if layer_key in hit.positions)
    return TimeLayerFact(layer_key=layer_key, pillar=pillar, ten_god=time_ten_god, relation_hits=hits)
