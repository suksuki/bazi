"""
Antigravity Resonance Booster Logic (Phase B-10)
================================================
Core physics logic for Stem-Branch Resonance & Rooting Gain.
"""

from typing import List, Dict, Any, Optional
from core.trinity.core.nexus.definitions import BaziParticleNexus

class ResonanceBooster:
    
    # Rooting Gain Matrix (G_res)
    GAIN_MATRIX = {
        "MAIN": 2.0,
        "MEDIUM": 1.5,
        "RESIDUAL": 1.2,
        "FLOATING": 0.5
    }

    # Standard Hidden Stems Mapping (Simplified for Logic Lookup)
    # Format: Branch -> {Stem: Type}
    HIDDEN_STEMS = {
        "子": {"癸": "MAIN"},
        "丑": {"己": "MAIN", "癸": "MEDIUM", "辛": "RESIDUAL"},
        "寅": {"甲": "MAIN", "丙": "MEDIUM", "戊": "RESIDUAL"},
        "卯": {"乙": "MAIN"},
        "辰": {"戊": "MAIN", "乙": "MEDIUM", "癸": "RESIDUAL"},
        "巳": {"丙": "MAIN", "戊": "MEDIUM", "庚": "RESIDUAL"},
        "午": {"丁": "MAIN", "己": "MEDIUM"},
        "未": {"己": "MAIN", "丁": "MEDIUM", "乙": "RESIDUAL"},
        "申": {"庚": "MAIN", "壬": "MEDIUM", "戊": "RESIDUAL"},
        "酉": {"辛": "MAIN"},
        "戌": {"戊": "MAIN", "辛": "MEDIUM", "丁": "RESIDUAL"},
        "亥": {"壬": "MAIN", "甲": "MEDIUM"}
    }

    @staticmethod
    def calculate_resonance_gain(stem: str, branches: List[str], influence_bus: Optional[Any] = None) -> Dict[str, Any]:
        """
        [V13.7 物理化升级] 计算通根增益：从固定映射回归到"量子概率分布"
        
        核心公式：G_res = G_base * (1 + ε_geo * K_geo²)
        - G_base: 基础通根增益（Main/Medium/Residual/None）
        - ε_geo: 地理修正系数（二阶项，体现"得地"的物理实感）
        - K_geo: 地理因子（从InfluenceBus获取）
        
        Args:
            stem: The Heavenly Stem (e.g., '甲')
            branches: List of Earthly Branches (e.g., ['寅', '辰'])
            influence_bus: Optional InfluenceBus for dynamic adjustments (包含地理修正).
            
        Returns:
            Dict: { 'gain': float, 'best_root': str, 'root_type': str, 'status': str, 'geo_correction': float }
        """
        all_branches = list(branches)
        
        # [V13.5] Extract branches from Bus if present
        if influence_bus:
            for factor in influence_bus.active_factors:
                if hasattr(factor, 'luck_branch') and factor.luck_branch:
                    all_branches.append(factor.luck_branch)
                if hasattr(factor, 'annual_branch') and factor.annual_branch:
                    all_branches.append(factor.annual_branch)

        max_gain = ResonanceBooster.GAIN_MATRIX["FLOATING"]
        best_root_branch = None
        best_root_type = "NONE"
        
        # [V13.7] 提取地理修正系数 K_geo
        geo_correction = 0.0
        geo_factor = 1.0
        geo_element = None
        if influence_bus:
            for factor in influence_bus.active_factors:
                # 检查 factor.name 或 metadata
                if factor.name == "GeoBias/地域":
                    geo_factor = factor.metadata.get("geo_factor", 1.0)
                    geo_element = factor.metadata.get("geo_element")
                    break
                elif hasattr(factor, 'geo_factor') and factor.geo_factor:
                    # 兼容旧格式
                    geo_factor = factor.geo_factor
                    geo_element = getattr(factor, 'geo_element', None)
                    break
        
        # [V13.7] 应用地理二阶修正：G_res = G_base * (1 + ε_geo * K_geo²)
        # 如果地理元素匹配日主元素，则应用修正
        if geo_element and geo_factor > 1.0:
            # 从 STEMS 字典获取天干元素
            if stem in BaziParticleNexus.STEMS:
                stem_element = BaziParticleNexus.STEMS[stem][0].lower()  # (Element, Polarity, HetuNumber)
                if stem_element == geo_element.lower():
                    # ε_geo: 地理修正系数（根据 REAL_01 案例校准：0.0509）
                    # 目标：2.229 = 2.0 * (1 + ε_geo * K_geo²)
                    # 如果 geo_factor = 1.5，则 K_geo = geo_factor = 1.5
                    # 则：ε_geo = 0.1145 / (1.5²) = 0.0509
                    epsilon_geo = 0.0509  # [V13.7] 校准值，基于 REAL_01 案例
                    # K_geo = geo_factor（地理因子）
                    K_geo = geo_factor
                    # 二阶修正：G_res = G_base * (1 + ε_geo * K_geo²)
                    geo_correction = epsilon_geo * (K_geo ** 2)
        
        for br in all_branches:
            hidden = ResonanceBooster.HIDDEN_STEMS.get(br, {})
            if stem in hidden:
                rtype = hidden[stem]
                base_gain = ResonanceBooster.GAIN_MATRIX.get(rtype, 1.0)
                
                # [V13.7] 应用地理二阶修正
                # G_res = G_base * (1 + ε_geo * K_geo²)
                corrected_gain = base_gain * (1.0 + geo_correction)
                
                # "Strong Connection Priority": Take max gain
                if corrected_gain > max_gain:
                    max_gain = corrected_gain
                    best_root_branch = br
                    best_root_type = rtype
        
        status = "SUPER_STABLE" if max_gain >= 2.0 else "STABLE" if max_gain > 1.0 else "DAMPED" if max_gain > 0.5 else "CRITICAL_VOLATILE"
        
        return {
            "gain": max_gain,
            "best_root": best_root_branch,
            "root_type": best_root_type,
            "status": status,
            "energy_pumping": max_gain >= 2.0,
            "geo_correction": geo_correction,  # [V13.7] 新增：地理修正值
            "base_gain": ResonanceBooster.GAIN_MATRIX.get(best_root_type, 1.0) if best_root_type != "NONE" else 0.5
        }

# Export functional alias
calculate_rooting_gain = ResonanceBooster.calculate_resonance_gain
