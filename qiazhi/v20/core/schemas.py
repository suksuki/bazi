from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Pillar:
    stem: str
    branch: str
    position: str

    @property
    def display(self) -> str:
        return f"{self.stem}{self.branch}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChartInput:
    pillars: tuple[Pillar, Pillar, Pillar, Pillar]
    calendar_assumption: str = "explicit_pillars_no_calendar_conversion"
    input_id: str = ""

    def pillar_map(self) -> dict[str, Pillar]:
        return {pillar.position: pillar for pillar in self.pillars}


@dataclass(frozen=True)
class TenGodPosition:
    label: str
    stem: str
    pillar: str
    layer: str
    element: str
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RelationHit:
    relation_type: str
    branches: tuple[str, ...]
    positions: tuple[str, ...]
    layer: str = "natal"
    element: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimeLayerFact:
    layer_key: str
    pillar: Pillar
    ten_god: TenGodPosition
    relation_hits: tuple[RelationHit, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_key": self.layer_key,
            "pillar": self.pillar.to_dict(),
            "ten_god": self.ten_god.to_dict(),
            "relation_hits": [row.to_dict() for row in self.relation_hits],
        }


@dataclass(frozen=True)
class ChartFacts:
    version: str
    pillars: dict[str, Pillar]
    day_master: str
    day_master_element: str
    visible_ten_gods: tuple[TenGodPosition, ...]
    hidden_ten_gods: tuple[TenGodPosition, ...]
    relation_hits: tuple[RelationHit, ...]
    vault_branches: tuple[str, ...]
    calendar_assumption: str
    guardrails: tuple[str, ...] = (
        "CHART_FACTS_DETERMINISTIC",
        "NO_LLM_FACT_GENERATION",
        "NO_FORTUNE_CONCLUSION",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "pillars": {key: value.to_dict() for key, value in self.pillars.items()},
            "day_master": self.day_master,
            "day_master_element": self.day_master_element,
            "visible_ten_gods": [row.to_dict() for row in self.visible_ten_gods],
            "hidden_ten_gods": [row.to_dict() for row in self.hidden_ten_gods],
            "relation_hits": [row.to_dict() for row in self.relation_hits],
            "vault_branches": list(self.vault_branches),
            "calendar_assumption": self.calendar_assumption,
            "guardrails": list(self.guardrails),
        }


@dataclass(frozen=True)
class TimeContext:
    version: str = "v20.time_context.v1"
    status: str = "not_provided"
    note: str = "Time layer is background only until explicit luck/flow facts are supplied."
    layers: tuple[TimeLayerFact, ...] = field(default_factory=tuple)
    relation_hits: tuple[RelationHit, ...] = field(default_factory=tuple)
    guardrails: tuple[str, ...] = (
        "TIME_LAYER_REQUIRES_EXPLICIT_PILLAR",
        "NO_CALENDAR_INFERENCE_FROM_TEXT",
        "NO_TIMING_PREDICTION_WITHOUT_EVIDENCE",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "note": self.note,
            "layers": [row.to_dict() for row in self.layers],
            "relation_hits": [row.to_dict() for row in self.relation_hits],
            "guardrails": list(self.guardrails),
        }


@dataclass(frozen=True)
class CoreInference:
    version: str
    day_master_capacity: str
    support_score: float
    pressure_score: float
    visible_ten_god_count: int
    hidden_ten_god_count: int
    relation_count: int
    uncertainty_sources: tuple[str, ...] = field(default_factory=tuple)
    guardrails: tuple[str, ...] = (
        "CORE_INFERENCE_STRUCTURAL_ONLY",
        "NO_USEFUL_GOD_VERDICT",
        "NO_DOMAIN_RESULT",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
