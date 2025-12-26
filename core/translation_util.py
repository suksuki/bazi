"""
[V1.0] 翻译工具类 (Translation Utility)
统一管理所有英文到中文的翻译映射
"""

from typing import Optional, Dict

class TranslationUtil:
    """
    🌐 翻译工具类
    
    统一管理系统中所有英文术语的中文翻译
    使用方法: 
        from core.utils.translation import T
        T.get("SHANG_GUAN_JIAN_GUAN")  # 返回 "伤官见官"
    """
    
    # ========== 物理格局名称 ==========
    PATTERN_NAMES = {
        "SHANG_GUAN_JIAN_GUAN": "伤官见官",
        "SHANG_GUAN_SHANG_JIN": "伤官伤尽",
        "SHANG_GUAN_PEI_YIN": "伤官配印",
        "YANG_REN_JIA_SHA": "羊刃架杀",
        "XIAO_SHEN_DUO_SHI": "枭神夺食",
        "SHI_SHEN_ZHI_SHA": "食神制杀",
        "CAI_GUAN_XIANG_SHENG": "财官相生",
        "CAI_GUAN_XIANG_SHENG_V4": "财官相生",
        "CYGS_COLLAPSE": "从格坍缩",
        "HGFG_TRANSMUTATION": "化气格重构",
        "SSSC_AMPLIFIER": "食伤生财",
        "JLTG_CORE_ENERGY": "建禄月劫",
        "PGB_SUPER_FLUID_LOCK": "排骨帮超流锁定格",
        "PGB_BRITTLE_TITAN": "排骨帮脆性巨人格",
        "SELECT_ALL": "全选所有格局",
    }
    
    # ========== 状态分类 ==========
    CATEGORIES = {
        # SGJG
        "GATE_VAPORIZED": "栅极气化/毁灭击穿",
        "LOGIC_CIRCUIT_FAIL": "逻辑失效/重度击穿",
        "GATE_LEAKAGE": "栅极漏电/中度干扰",
        "STABLE_CONTROL": "控制稳态",
        
        # SGPY
        "REVERSE_COLLAPSE": "反向坍缩/气化",
        "CONSTRAINT_BOUND": "约束缠绕/失效",
        "SUPER_STABLE": "备用电源/稳态",
        "BAND_STOP_OK": "带阻滤波/稳态",
        "CHARGE_OVERFLOW": "电荷过载/狂暴",
        "UNSTABLE_CONSTRAINT": "非稳态约束",
        
        # SGSJ V4.2 等离子气化场
        "VACUUM_SUPERCONDUCTOR": "真空超导/纯净气化场",
        "PLASMA_SHIELD_ACTIVE": "等离子护盾激活/气化成功",
        "VAPORIZATION_OVERLOAD": "气化过载/拦截失败",
        "SOURCE_BURNOUT": "电源枯竭/自燃",
        "PARTIAL_VAPORIZATION": "部分气化/亚临界态",
        "UNSTABLE_FIELD": "不稳定场态",
        
        # SSZS
        "KINETIC_OVERLOAD": "殉爆/拦截崩溃",
        "GUIDANCE_LOST": "拦截致盲/失控",
        "RADAR_OFFLINE": "绝缘崩溃/雷达离线",
        "PRECISE_INTERCEPT": "定点拦截/完美制导",
        "INTERCEPT_FAILURE": "拦截动能不足",
        "SATURATED_DEFENSE": "饱和防御态",
        
        # YRJS
        "MAGNETIC_BREAKDOWN": "磁场击穿",
        "SUPERCONDUCTING_FUSION": "超导核聚变",
        "STABLE_FUSION": "稳态聚变",
        "THERMAL_TURBULENCE": "热扰动状态",
        "CONTAINMENT_FAIL": "约束失效",
        
        # XSDS
        "PHASE_ANNIHILATION": "彻底断路",
        "QUANTUM_WELL_OVERFLOW": "溢出干扰",
        "STEADY_SIGNAL": "信号稳态",
        "SIGNAL_INTERFERENCE": "信号遮蔽",
        
        # 通用
        "MATCH": "匹配",
        "NO_MATCH": "未匹配",
        "DANGER": "危险",
        "WARNING": "警告",
        "SAFE": "安全",
        "CRITICAL": "临界",
        "NORMAL": "正常",
        "UNSTABLE": "不稳定",
        "STABLE": "稳定",
    }
    
    # ========== 十神 ==========
    TEN_GODS = {
        "正官": "正官",
        "七杀": "七杀",
        "正印": "正印",
        "偏印": "偏印",
        "正财": "正财",
        "偏财": "偏财",
        "食神": "食神",
        "伤官": "伤官",
        "比肩": "比肩",
        "劫财": "劫财",
        "Officer": "正官",
        "Seven Killings": "七杀",
        "Direct Resource": "正印",
        "Indirect Resource": "偏印",
        "Direct Wealth": "正财",
        "Indirect Wealth": "偏财",
        "Eating God": "食神",
        "Hurting Officer": "伤官",
        "Friend": "比肩",
        "Rob Wealth": "劫财",
    }
    
    # ========== 五行 ==========
    ELEMENTS = {
        "Wood": "木",
        "Fire": "火",
        "Earth": "土",
        "Metal": "金",
        "Water": "水",
        "Neutral": "中性",
    }
    
    # ========== 十二长生 ==========
    LIFE_STAGES = {
        "长生": "长生",
        "沐浴": "沐浴",
        "冠带": "冠带",
        "临官": "临官",
        "帝旺": "帝旺",
        "衰": "衰",
        "病": "病",
        "死": "死",
        "墓": "墓",
        "绝": "绝",
        "胎": "胎",
        "养": "养",
    }
    
    # ========== 物理术语 ==========
    PHYSICS_TERMS = {
        "SAI": "应力指数",
        "Stress": "应力",
        "Stress Index": "应力指数",
        "Reynolds": "雷诺数",
        "Entropy": "熵",
        "Resonance": "共振",
        "Kinetic": "动能",
        "Field": "场",
        "Threshold": "阈值",
        "Breakdown": "击穿",
        "Superconductor": "超导",
        "Waveguide": "波导",
        "Tokamak": "托卡马克",
        "Fusion": "聚变",
        "Collapse": "坍缩",
        "Vault": "墓库",
        "Clash": "冲",
        "Combine": "合",
        "Phase": "相位",
        "Interference": "干扰",
        "Impedance": "阻抗",
        "Amplifier": "放大器",
        "Damping": "阻尼",
        "Stability": "稳定性",
        "Constraint": "约束",
        "Buffer": "缓冲",
        "Intercept": "拦截",
        "Overflow": "溢出",
        "Leakage": "泄漏",
    }
    
    # ========== UI 文本 ==========
    UI_TEXT = {
        "Choose options": "请选择选项",
        "Select All": "全选",
        "Clear All": "清空",
        "Submit": "提交",
        "Cancel": "取消",
        "Loading": "加载中",
        "Processing": "处理中",
        "Complete": "完成",
        "Error": "错误",
        "Warning": "警告",
        "Info": "信息",
        "Success": "成功",
        "Failed": "失败",
        "Age": "年龄",
        "Year": "年份",
        "Luck Pillar": "大运",
        "Annual Pillar": "流年",
        "Day Master": "日主",
        "Birth Year": "出生年",
        "Profile": "档案",
        "Scan": "扫描",
        "Audit": "审计",
        "Result": "结果",
        "Detail": "详情",
        "Summary": "摘要",
        "Timeline": "时间线",
        "Chart": "图表",
        "Total": "总计",
        "Count": "数量",
        "Rate": "比率",
        "Peak": "峰值",
        "Danger Zone": "危险区",
        "Safe Zone": "安全区",
        "Warning Zone": "警戒区",
    }
    
    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> str:
        """
        获取翻译文本
        
        Args:
            key: 英文键名
            default: 如果找不到翻译，返回的默认值（如果为None则返回原key）
            
        Returns:
            中文翻译
        """
        # 优先在各个分类中查找
        for category in [cls.PATTERN_NAMES, cls.CATEGORIES, cls.TEN_GODS, 
                        cls.ELEMENTS, cls.LIFE_STAGES, cls.PHYSICS_TERMS, cls.UI_TEXT]:
            if key in category:
                return category[key]
        
        # 尝试提取括号中的内容（如 "GATE_VAPORIZED (栅极气化/毁灭击穿)"）
        if "(" in str(key) and ")" in str(key):
            start = key.find("(")
            end = key.find(")")
            if start < end:
                return key[start+1:end]
        
        return default if default is not None else key
    
    @classmethod
    def translate_category(cls, category: str) -> str:
        """
        翻译状态分类字符串
        
        Args:
            category: 原始分类字符串，可能包含英文和中文
            
        Returns:
            纯中文翻译
        """
        # 如果已经是中文，直接返回
        if category and all('\u4e00' <= c <= '\u9fff' or c in '（）()/' for c in category.replace(" ", "")):
            return category
        
        # 尝试提取英文键名并翻译
        for en_key, cn_val in cls.CATEGORIES.items():
            if en_key in category:
                return cn_val
        
        return cls.get(category, category)
    
    @classmethod
    def translate_pattern(cls, pattern_id: str) -> str:
        """翻译物理格局ID"""
        return cls.PATTERN_NAMES.get(pattern_id, pattern_id)
    
    @classmethod
    def translate_element(cls, element: str) -> str:
        """翻译五行"""
        return cls.ELEMENTS.get(element, element)
    
    @classmethod
    def translate_god(cls, god: str) -> str:
        """翻译十神"""
        return cls.TEN_GODS.get(god, god)


# 快捷别名
T = TranslationUtil
