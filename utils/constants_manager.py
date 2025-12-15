"""
utils/constants_manager.py
--------------------------
V14.0 Constants Manager:
- Provide unified, authoritative constants for five elements, ten gods, relations, defaults.
"""

from typing import List, Dict


class ConstantsManager:
    """提供全系统统一的核心常量定义。"""

    FIVE_ELEMENTS: List[str] = ["Wood", "Fire", "Earth", "Metal", "Water"]

    TEN_GODS: List[str] = [
        "ZhengYin", "PianYin",
        "BiJian", "JieCai",
        "ShiShen", "ShangGuan",
        "ZhengCai", "PianCai",
        "ZhengGuan", "QiSha",
    ]

    # 五行相生相克关系（示例，可按需扩展）
    ELEMENT_RELATIONS: Dict[str, Dict[str, str]] = {
        "Wood": {"produces": "Fire", "controls": "Earth"},
        "Fire": {"produces": "Earth", "controls": "Metal"},
        "Earth": {"produces": "Metal", "controls": "Water"},
        "Metal": {"produces": "Water", "controls": "Wood"},
        "Water": {"produces": "Wood", "controls": "Fire"},
    }

    # 默认粒子权重 (1.0 = 100%)
    DEFAULT_PARTICLE_WEIGHTS: Dict[str, float] = {god: 1.0 for god in TEN_GODS}

    # 默认 GEO 修正城市列表（示例，实际应从数据文件加载）
    DEFAULT_GEO_CITIES: List[str] = ["Beijing", "Shanghai", "Shenzhen", "None"]


def get_constants() -> ConstantsManager:
    """
    获取常量管理器实例。当前实现为简单工厂，后续可升级为单例。
    """
    return ConstantsManager()

