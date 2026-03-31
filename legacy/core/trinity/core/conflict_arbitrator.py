import logging
from typing import List, Dict, Any, Set, Optional
from core.trinity.core.arbitrator_global_config import ExecutionTier, ArbitrationPolicy
from core.logic_registry import LogicRegistry
from core.trinity.core.nexus.context import ContextSnapshot, ArbitrationScenario

logger = logging.getLogger(__name__)

class ConflictArbitrator:
    """
    智能冲突仲裁器 (Conflict Arbitrator)
    负责处理规则之间的“贪合忘冲”逻辑及层级调度。
    """
    
    @staticmethod
    def resolve_conflicts(triggered_rules: List[Dict[str, Any]], manifest_registry: Dict[str, Any], context: Optional[ContextSnapshot] = None) -> List[Dict[str, Any]]:
        """
        根据优先级和冲突规则进行仲裁。
        
        Args:
            triggered_rules: 已触发的规则列表，包含 id 和其他参数。
            manifest_registry: 全局规则库，包含元数据 (priority, layer, conflicts)。
            context: 可选的上下文快照 (Luck, Annual, GEO, Scenario)。
        """
        if not triggered_rules:
            return []

        # 1. Enrich rules with metadata from registry
        active_registry = manifest_registry if manifest_registry else LogicRegistry().manifest.get("registry", {})
        
        current_scenario = context.scenario if context else ArbitrationScenario.GENERAL
        
        enriched_rules = []
        for tr in triggered_rules:
            rule_id = tr.get("id")
            meta = active_registry.get(rule_id, {})
            
            # Lifecycle Check: Skip DEPRECATED or inactive rules
            if meta.get("status", "ACTIVE") != "ACTIVE":
                logger.info(f"⏭️ Conflict Arbitrator: Skipping DEPRECATED/INACTIVE rule {rule_id}")
                continue
            
            # Scenario-Based Dynamic Weighting
            base_priority = meta.get("priority", 0)
            bonus = 0
            
            # If the rule has affinity with the current scenario, boost its priority
            scenario_affinity = meta.get("scenario_affinity", [])
            if current_scenario.name in scenario_affinity:
                bonus = 100 # Standard Scenario Boost
                logger.info(f"🚀 Conflict Arbitrator: Boosting {rule_id} (+{bonus}) for scenario {current_scenario.name}")

            # Combine trigger data with metadata
            rule_data = {
                **tr,
                "priority": base_priority + bonus,
                "layer": meta.get("layer", "STRUCTURAL"),
                "conflicts": meta.get("conflicts", []),
                "origin_trace": meta.get("origin_trace", []),
                "fusion_type": meta.get("fusion_type", "LEGACY"),
                "scenario_affinity": scenario_affinity
            }
            enriched_rules.append(rule_data)

        # 2. Sort by Priority (Descending)
        sorted_rules = sorted(enriched_rules, key=lambda x: x.get("priority", 0), reverse=True)

        # 3. Conflict Resolution (Greedy filtering)
        # 如果高优先级规则冲突列表包含低优先级规则，则剔除低优先级规则
        final_rules = []
        suppressed_ids: Set[str] = set()

        for rule in sorted_rules:
            rid = rule.get("id")
            if rid in suppressed_ids:
                logger.info(f"🚫 Conflict Arbitrator: Suppressing {rid} due to higher priority conflict.")
                continue
                
            final_rules.append(rule)
            
            # If "Greedy Fusion" policy is active, add conflicts to suppression list
            if ArbitrationPolicy.OVERRIDE_CLASH_BY_FUSION:
                for conflict_id in rule.get("conflicts", []):
                    suppressed_ids.add(conflict_id)

        return final_rules

    @staticmethod
    def group_by_layer(rules: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按层级分层，供调度总线使用。"""
        layers = {tier.name: [] for tier in ExecutionTier}
        for r in rules:
            layer_name = r.get("layer", "STRUCTURAL")
            if layer_name in layers:
                layers[layer_name].append(r)
            else:
                # Fallback
                layers.setdefault("STRUCTURAL", []).append(r)
        return layers
