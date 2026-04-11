"""Strategy Pattern implementation for Bazi relationship physics (刑冲合害)."""
from __future__ import annotations

import abc
from typing import Any, Dict, List, Tuple

class BaseRelationRule(abc.ABC):
    """Abstract base class for relationship rules."""

    @property
    @abc.abstractmethod
    def relation_key(self) -> str:
        """The identifier string, e.g., '冲', '合', '刑'"""
        pass

    @property
    def relation_type(self) -> str:
        """English translation for the relation type."""
        return "unknown"

    def apply_topology(
        self,
        *,
        raw_energy: float,
        boost_setting: float,
        decay_setting: float,
        distance: float,
    ) -> Dict[str, Any]:
        """
        Calculate topology-level physics (energy propagation and resonance).
        Returns a dictionary overriding default properties.
        """
        return {}

    def apply_evaluator(
        self,
        *,
        detail: str,
        base_eta: float,
        settings: Dict[str, Any],
        tomb_branches: List[str],
    ) -> Dict[str, Any]:
        """
        Calculate evaluator-level semantics (unlocks, efficiency, risks).
        Returns a dictionary overriding default properties.
        """
        return {}


class ClashRule(BaseRelationRule):
    """冲 (Clash) - High kinetic energy, unlocks tombs, creates resonance."""

    @property
    def relation_key(self) -> str:
        return "冲"

    @property
    def relation_type(self) -> str:
        return "clash"

    def apply_topology(
            self, *, raw_energy: float, boost_setting: float, decay_setting: float, distance: float
    ) -> Dict[str, Any]:
        resonance_boost = boost_setting
        distance_decay = max(0.1, 1.0 - decay_setting * distance)
        final_work = raw_energy * resonance_boost * distance_decay
        return {
            "resonance_boost": round(resonance_boost, 4),
            "distance_decay": round(distance_decay, 4),
            "final_work": round(final_work, 4),
            "stem_resonance": True,
            "clash_vibration_flag": True,
        }

    def apply_evaluator(
            self, *, detail: str, base_eta: float, settings: Dict[str, Any], tomb_branches: List[str]
    ) -> Dict[str, Any]:
        # '冲' dynamically unlocks tombs if tomb branches are involved
        unlock_source = detail if tomb_branches else ""
        return {
            "eta": base_eta,
            "unlock_source": unlock_source,
        }


class CombineRule(BaseRelationRule):
    """合 (Combine) - Restraints and harmonizes energy."""

    @property
    def relation_key(self) -> str:
        return "合"

    @property
    def relation_type(self) -> str:
        return "combination"

    def apply_topology(
            self, *, raw_energy: float, boost_setting: float, decay_setting: float, distance: float
    ) -> Dict[str, Any]:
        resonance_boost = 1.0
        distance_decay = max(0.1, 1.0 - decay_setting * distance)
        final_work = raw_energy * resonance_boost * distance_decay
        return {
            "resonance_boost": round(resonance_boost, 4),
            "distance_decay": round(distance_decay, 4),
            "final_work": round(final_work, 4),
            "stem_resonance": False,
            "clash_vibration_flag": False,
        }

    def apply_evaluator(
            self, *, detail: str, base_eta: float, settings: Dict[str, Any], tomb_branches: List[str]
    ) -> Dict[str, Any]:
        return {"eta": base_eta, "unlock_source": ""}


class PierceRule(BaseRelationRule):
    """穿 (Pierce/Harm) - Sharp piercing damage."""

    @property
    def relation_key(self) -> str:
        return "穿"

    @property
    def relation_type(self) -> str:
        return "pierce"

    def apply_topology(
            self, *, raw_energy: float, boost_setting: float, decay_setting: float, distance: float
    ) -> Dict[str, Any]:
        resonance_boost = boost_setting
        distance_decay = max(0.1, 1.0 - decay_setting * distance)
        final_work = raw_energy * resonance_boost * distance_decay
        return {
            "resonance_boost": round(resonance_boost, 4),
            "distance_decay": round(distance_decay, 4),
            "final_work": round(final_work, 4),
            "stem_resonance": True,
            "clash_vibration_flag": False,
        }

    def apply_evaluator(
            self, *, detail: str, base_eta: float, settings: Dict[str, Any], tomb_branches: List[str]
    ) -> Dict[str, Any]:
        pierce_floor = float(settings.get("MANGPAI_ETA_PIERCE", settings.get("MANGPAI_SIX_HARM_ETA", 0.99)))
        eta = min(1.0, max(base_eta, pierce_floor))
        return {"eta": eta, "unlock_source": ""}


class PunishmentRule(BaseRelationRule):
    """刑 (Punish) - Hidden friction and internal consumption."""

    @property
    def relation_key(self) -> str:
        return "刑"

    @property
    def relation_type(self) -> str:
        return "punishment"

    def apply_topology(
            self, *, raw_energy: float, boost_setting: float, decay_setting: float, distance: float
    ) -> Dict[str, Any]:
        resonance_boost = 1.0
        # Punishment applies additional distance friction decay (-0.1)
        distance_decay = max(0.1, (1.0 - decay_setting * distance) - 0.1)
        final_work = raw_energy * resonance_boost * distance_decay
        return {
            "resonance_boost": round(resonance_boost, 4),
            "distance_decay": round(distance_decay, 4),
            "final_work": round(final_work, 4),
            "stem_resonance": False,
            "clash_vibration_flag": False,
        }

    def apply_evaluator(
            self, *, detail: str, base_eta: float, settings: Dict[str, Any], tomb_branches: List[str]
    ) -> Dict[str, Any]:
        return {"eta": base_eta, "unlock_source": ""}


class HarmRule(PunishmentRule):
    """害 (Harm) - Similar friction mechanics to Punish at topology level."""

    @property
    def relation_key(self) -> str:
        return "害"

    @property
    def relation_type(self) -> str:
        return "harm"


class BreakRule(PunishmentRule):
    """破 (Break) - Similar friction mechanics to Punish at topology level."""

    @property
    def relation_key(self) -> str:
        return "破"

    @property
    def relation_type(self) -> str:
        return "break"


class GenerateRule(BaseRelationRule):
    """生 (Generate) - Mutual reinforcement."""

    @property
    def relation_key(self) -> str:
        return "生"

    @property
    def relation_type(self) -> str:
        return "generate"

    def apply_topology(
            self, *, raw_energy: float, boost_setting: float, decay_setting: float, distance: float
    ) -> Dict[str, Any]:
        resonance_boost = 1.0
        distance_decay = max(0.1, 1.0 - decay_setting * distance)
        final_work = raw_energy * resonance_boost * distance_decay
        return {
            "resonance_boost": round(resonance_boost, 4),
            "distance_decay": round(distance_decay, 4),
            "final_work": round(final_work, 4),
            "stem_resonance": False,
            "clash_vibration_flag": False,
        }


class ControlRule(GenerateRule):
    """克 (Control) - Dominance and restriction."""

    @property
    def relation_key(self) -> str:
        return "克"

    @property
    def relation_type(self) -> str:
        return "control"


class FallbackRule(BaseRelationRule):
    """Fallback rule to act as '冲' default if not matched."""

    @property
    def relation_key(self) -> str:
        return "unknown"

    @property
    def relation_type(self) -> str:
        return "clash"

    def apply_topology(
            self, *, raw_energy: float, boost_setting: float, decay_setting: float, distance: float
    ) -> Dict[str, Any]:
        return ClashRule().apply_topology(
            raw_energy=raw_energy, boost_setting=boost_setting, decay_setting=decay_setting, distance=distance
        )

    def apply_evaluator(
            self, *, detail: str, base_eta: float, settings: Dict[str, Any], tomb_branches: List[str]
    ) -> Dict[str, Any]:
        return ClashRule().apply_evaluator(
            detail=detail, base_eta=base_eta, settings=settings, tomb_branches=tomb_branches
        )


class RelationNodeFactory:
    """Registry for looking up the appropriate Relationship physics rule node."""

    _registry = {
        cls().relation_key: cls() for cls in [
            ClashRule,
            CombineRule,
            PierceRule,
            PunishmentRule,
            HarmRule,
            BreakRule,
            GenerateRule,
            ControlRule
        ]
    }

    @classmethod
    def get_rule_from_detail(cls, detail: str) -> BaseRelationRule:
        """Parse detail string to find the correct relationship type (e.g. 穿, 冲)."""
        valid_keys = ("穿", "冲", "刑", "害", "破", "合", "生", "克")
        for k in valid_keys:
            if k in (detail or ""):
                return cls._registry.get(k, FallbackRule())
        return FallbackRule()

