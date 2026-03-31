
from typing import Dict, Any
from core.trinity.core.middleware.influence_bus import InfluenceFactor, NonlinearType, ExpectationVector

class TemporalInjectionFactor(InfluenceFactor):
    """
    [V1.4] 时序注入因子
    将原本硬编码在 RegistryLoader 中的流年/大运能量注入逻辑解耦到此因子中。
    """
    def __init__(self, name: str = "TemporalInjection/时序注入"):
        super().__init__(name, NonlinearType.LINEAR_SHIFT)
        # 注入映射表（未来可由 config_schema 管理）
        self.injection_map = {
            '七杀': {'power': 0.5},
            '正官': {'power': 0.5},
            '正印': {'resource': 0.3},
            '偏印': {'resource': 0.3},
            '比肩': {'parallel': 0.3},
            '劫财': {'parallel': 0.3},
            '伤官': {'output': 0.2},
            '食神': {'output': 0.2},
            '正财': {'wealth': 0.4},
            '偏财': {'wealth': 0.4}
        }

    def apply_nonlinear_correction(self, base_e: ExpectationVector, context: Dict[str, Any] = None) -> ExpectationVector:
        if not context:
            return base_e
            
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        day_master = context.get('day_master')
        if not day_master:
            return base_e

        # 1. 处理流年 (Annual Pillar)
        year_pillar = context.get('annual_pillar')
        if year_pillar and len(year_pillar) >= 1:
            year_stem = year_pillar[0]
            year_ten_god = BaziParticleNexus.get_shi_shen(year_stem, day_master)
            
            adjustments = self.injection_map.get(year_ten_god, {})
            for key, val in adjustments.items():
                if key in base_e.elements:
                    base_e.elements[key] += val
                    self.log(f"流年 [{year_ten_god}] 对 [{key}] 注入能量: +{val}")

        # 2. 处理大运 (Luck Pillar)
        luck_pillar = context.get('luck_pillar')
        if luck_pillar and len(luck_pillar) >= 1:
            luck_stem = luck_pillar[0]
            luck_ten_god = BaziParticleNexus.get_shi_shen(luck_stem, day_master)
            
            # 大运注入系数通常减半，因为它是背景场
            adjustments = self.injection_map.get(luck_ten_god, {})
            for key, val in adjustments.items():
                if key in base_e.elements:
                    luck_val = val * 0.5
                    base_e.elements[key] += luck_val
                    self.log(f"大运 [{luck_ten_god}] 对 [{key}] 注入背景能量: +{luck_val}")

        return base_e
