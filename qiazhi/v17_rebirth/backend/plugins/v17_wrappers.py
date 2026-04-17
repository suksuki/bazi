"""兼容层：转发至 `logic.plugin_discovery`（延迟 import，避免与 `plugins` 包 `__init__` 循环）。"""
from __future__ import annotations

from typing import Any, Dict, List

from v17_rebirth.backend.plugins.spec import V17Decision, V17Fact

_pd_mod: Any = None


def _pd() -> Any:
    global _pd_mod
    if _pd_mod is None:
        from v17_rebirth.backend.logic import plugin_discovery as m

        _pd_mod = m
    return _pd_mod


def collect_spec_facts(physics_tensor: Dict[str, Any]) -> List[V17Fact]:
    return _pd().collect_all_spec_facts(physics_tensor)


def collect_spec_facts_and_record(physics_tensor: Dict[str, Any]) -> List[V17Fact]:
    return _pd().collect_all_spec_facts_and_record(physics_tensor)


def collect_pending_decisions_from_specs(facts: List[V17Fact]) -> List[V17Decision]:
    return _pd().collect_pending_decisions_from_specs(facts)


def iter_v17_plugin_specs() -> List[Any]:
    return _pd().iter_all_plugin_specs()


def v17_fact_to_row(f: V17Fact) -> Dict[str, Any]:
    return _pd().v17_fact_to_row(f)


def v17_decision_to_row(d: V17Decision) -> Dict[str, Any]:
    return _pd().v17_decision_to_row(d)


def collect_plugin_facts(deity_scores: Dict[str, float]) -> List[Dict[str, Any]]:
    tensor: Dict[str, Any] = {"deity_scores": deity_scores or {}}
    return [v17_fact_to_row(f) for f in collect_spec_facts(tensor)]


__all__ = [
    "V17Fact",
    "V17Decision",
    "collect_spec_facts",
    "collect_spec_facts_and_record",
    "collect_pending_decisions_from_specs",
    "iter_v17_plugin_specs",
    "v17_fact_to_row",
    "v17_decision_to_row",
    "collect_plugin_facts",
]
