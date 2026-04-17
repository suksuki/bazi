from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class V17PluginFact:
    source: str
    fact: str
    decision_hint: str = ""
    priority: float = 0.0


class V17PluginWrapper:
    name: str = "base"

    def collect_v17_facts(self, deity_scores: Dict[str, float]) -> List[V17PluginFact]:
        return []


class ThreeHarmonyWrapper(V17PluginWrapper):
    name = "three_harmony"

    def collect_v17_facts(self, deity_scores: Dict[str, float]) -> List[V17PluginFact]:
        food = float(deity_scores.get("食神", 0.0))
        wealth = float(deity_scores.get("正财", 0.0) + deity_scores.get("偏财", 0.0))
        if food >= 18 and wealth >= 14:
            return [
                V17PluginFact(
                    source=self.name,
                    fact="食神与财星形成协同，资源流动性正在升温。",
                    decision_hint="将资源投放节奏改为两段式，先小规模验证再加码。",
                    priority=0.84,
                )
            ]
        return []


class SixPierceWrapper(V17PluginWrapper):
    name = "six_pierce"

    def collect_v17_facts(self, deity_scores: Dict[str, float]) -> List[V17PluginFact]:
        peer = float(deity_scores.get("比肩", 0.0))
        officer = float(deity_scores.get("正官", 0.0))
        if abs(peer - officer) <= 4 and (peer > 10 or officer > 10):
            return [
                V17PluginFact(
                    source=self.name,
                    fact="约束力与自驱力形成穿透态，决策窗口偏短。",
                    decision_hint="为关键决策设置二次确认，降低冲动型误判。",
                    priority=0.76,
                )
            ]
        return []


class OfficerConflictWrapper(V17PluginWrapper):
    name = "officer_conflict"

    def collect_v17_facts(self, deity_scores: Dict[str, float]) -> List[V17PluginFact]:
        officer = float(deity_scores.get("正官", 0.0))
        hurting = float(deity_scores.get("伤官", 0.0))
        if officer >= 20 and hurting >= 16:
            return [
                V17PluginFact(
                    source=self.name,
                    fact="伤官见官触发张力，表达与秩序存在摩擦。",
                    decision_hint="先统一沟通口径，再推进外部谈判动作。",
                    priority=0.9,
                )
            ]
        return []


def collect_plugin_facts(deity_scores: Dict[str, float]) -> List[V17PluginFact]:
    wrappers: List[V17PluginWrapper] = [ThreeHarmonyWrapper(), SixPierceWrapper(), OfficerConflictWrapper()]
    rows: List[V17PluginFact] = []
    for wrapper in wrappers:
        rows.extend(wrapper.collect_v17_facts(deity_scores))
    return rows
