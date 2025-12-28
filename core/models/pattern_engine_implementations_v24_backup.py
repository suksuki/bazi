"""
[QGA V25.0] 格局引擎具体实现（逻辑真空化）
移除硬编码判定逻辑，改为从PatternDefinitionRegistry读取物理特性描述
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from core.models.pattern_engine import (
    PatternEngine, PatternMatchResult, VectorBias
)
from core.models.pattern_definition_registry import get_pattern_definition_registry

logger = logging.getLogger(__name__)


class ShangGuanJianGuanEngine(PatternEngine):
    """
    伤官见官引擎 (Structural Failure Engine)
    
    语义定义：旧秩序晶格崩塌，产生高频剪切力，系统稳定性急剧下降
    物理修正：大幅扣减官星五行权重，增加财/印的救应权重
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="SHANG_GUAN_JIAN_GUAN",
            pattern_name="伤官见官",
            pattern_type="Conflict"
        )
        self.priority_rank = 2  # 冲突格局，次高优先级
        self.base_strength = 0.75
    
    def matching_logic(self, chart: List[Tuple[str, str]], 
                      day_master: str,
                      luck_pillar: Optional[Tuple[str, str]] = None,
                      year_pillar: Optional[Tuple[str, str]] = None,
                      synthesized_field: Optional[Dict] = None) -> PatternMatchResult:
        """
        [QGA V25.0] 逻辑真空化：移除硬编码判定逻辑
        判定逻辑将由Phase 2的特征向量提取器负责
        """
        # 返回未匹配状态，等待特征向量注入
        return PatternMatchResult(matched=False, confidence=0.0, match_data={})
    
    def semantic_definition(self, match_result: PatternMatchResult,
                           geo_context: Optional[str] = None) -> str:
        """
        [QGA V25.0] 从PatternDefinitionRegistry读取物理判词
        """
        registry = get_pattern_definition_registry()
        definition = registry.get_by_id(self.pattern_id)
        
        if definition:
            base_text = definition.core_conflict
            # 根据地理环境微调（保留原有逻辑）
            if geo_context:
                if geo_context in ["北方/北京", "近水环境"]:
                    return f"{base_text}，在寒性环境下，冲突进一步激化，导致规则挑战与名誉损耗加剧"
                elif geo_context in ["南方/火地"]:
                    return f"{base_text}，在火环境中得到一定缓解，但仍需财星通关或印星制伤"
            return base_text
        
        # 如果注册表中没有，返回默认文本
        return "格局物理特性待定义"
    
    def vector_bias(self, match_result: PatternMatchResult,
                   geo_context: Optional[str] = None) -> VectorBias:
        """
        [QGA V25.0] 从PatternDefinitionRegistry读取五行偏移
        """
        registry = get_pattern_definition_registry()
        definition = registry.get_by_id(self.pattern_id)
        
        if definition:
            # 从定义中读取受力特征
            force_chars = definition.force_characteristics
            bias = VectorBias(
                metal=force_chars.get("metal", 0.0),
                wood=force_chars.get("wood", 0.0),
                water=force_chars.get("water", 0.0),
                fire=force_chars.get("fire", 0.0),
                earth=force_chars.get("earth", 0.0)
            )
            
            # 根据地理环境微调（保留原有逻辑）
            if geo_context in ["北方/北京", "近水环境"]:
                bias.metal -= 5.0
                bias.water += 5.0
            elif geo_context in ["南方/火地"]:
                bias.fire += 5.0
            
            return bias
        
        # 如果注册表中没有，返回零偏移
        return VectorBias()


class HuaHuoGeEngine(PatternEngine):
    """
    化火格引擎 (Phase Transition Engine)
    
    语义定义：分子级化学相变因环境干预而被迫中断，导致能量淤积
    物理修正：根据合化引信的强弱，决定合化后五行的转化率
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="HUA_HUO_GE",
            pattern_name="化火格",
            pattern_type="Special"
        )
        self.priority_rank = 1  # 特殊格局，高优先级
        self.base_strength = 0.85
    
    def matching_logic(self, chart: List[Tuple[str, str]], 
                      day_master: str,
                      luck_pillar: Optional[Tuple[str, str]] = None,
                      year_pillar: Optional[Tuple[str, str]] = None,
                      synthesized_field: Optional[Dict] = None) -> PatternMatchResult:
        """
        化火格判定：天干五合成功化为火
        
        简化实现：检查是否有戊癸合化火、丙辛合化火等
        """
        try:
            # 提取天干
            stems = [p[0] for p in chart]
            if luck_pillar:
                stems.append(luck_pillar[0])
            if year_pillar:
                stems.append(year_pillar[0])
            
            # 检查五合
            # 戊癸合化火、丙辛合化水（这里我们关注化火）
            hua_combinations = [
                ('戊', '癸'),  # 戊癸合化火
            ]
            
            has_hua = False
            hua_stems = []
            
            for combo in hua_combinations:
                if combo[0] in stems and combo[1] in stems:
                    has_hua = True
                    hua_stems = [combo[0], combo[1]]
                    break
            
            if has_hua:
                # 检查是否有火来引化（简化处理）
                # 如果有月令是火，或者地支有火，则合化成功
                branches = [p[1] for p in chart]
                fire_branches = ['巳', '午', '未']  # 火局
                has_fire_support = any(b in fire_branches for b in branches)
                
                hua_strength = 0.85 if has_fire_support else 0.6
                
                return PatternMatchResult(
                    matched=True,
                    confidence=hua_strength,
                    match_data={
                        'hua_stems': hua_stems,
                        'has_fire_support': has_fire_support
                    },
                    sai=hua_strength * 100,
                    stress=0.3 if has_fire_support else 0.6  # 如果无火引化，压力较大
                )
            
            return PatternMatchResult(matched=False, confidence=0.0, match_data={})
        except Exception as e:
            logger.warning(f"化火格判定失败: {e}")
            return PatternMatchResult(matched=False, confidence=0.0, match_data={})
    
    def semantic_definition(self, match_result: PatternMatchResult,
                           geo_context: Optional[str] = None) -> str:
        """
        化火格的物理判词（考虑化火受阻的情况）
        """
        has_fire_support = match_result.match_data.get('has_fire_support', False)
        
        if has_fire_support:
            base_text = "分子级化学相变成功，能量完全转化为火元素，形成单一能量场，性格和命运发生转化"
        else:
            base_text = "分子级化学相变因环境干预而被迫中断，导致能量淤积，合化不彻底"
        
        if geo_context:
            if geo_context in ["北方/北京", "近水环境"]:
                if has_fire_support:
                    return f"{base_text}，但在寒性环境下，化火受阻，能量无法有效释放"
                else:
                    return f"{base_text}，在寒性环境下进一步受阻，形成火水既济或化火受阻的冲突状态"
            elif geo_context in ["南方/火地"]:
                return f"{base_text}，在火环境中得到充分激活，合化成功率大幅提升"
        
        return base_text
    
    def vector_bias(self, match_result: PatternMatchResult,
                   geo_context: Optional[str] = None) -> VectorBias:
        """
        化火格的五行偏移
        
        物理修正：
        - 如果合化成功，火元素大幅增加，原始元素（如戊癸）的能量清零
        - 如果合化受阻，能量淤积，需要根据环境调整
        """
        has_fire_support = match_result.match_data.get('has_fire_support', False)
        hua_strength = match_result.confidence
        
        if has_fire_support:
            # 合化成功：火大幅增加，土（戊）和水（癸）的能量转化为火
            bias = VectorBias(
                fire=+30.0,   # 火大幅增加
                earth=-15.0,  # 戊的能量转化为火
                water=-15.0   # 癸的能量转化为火
            )
        else:
            # 合化受阻：能量淤积，转化不完全
            bias = VectorBias(
                fire=+15.0,   # 部分转化为火
                earth=-8.0,   # 部分转化
                water=-8.0    # 部分转化
            )
        
        # 根据地理环境调整
        if geo_context in ["北方/北京", "近水环境"]:
            # 水环境抑制化火
            if has_fire_support:
                # 原本成功，但现在受阻
                bias.fire -= 10.0
                bias.water += 10.0
            else:
                # 进一步受阻
                bias.fire -= 5.0
                bias.water += 5.0
        elif geo_context in ["南方/火地"]:
            # 火环境促进化火
            bias.fire += 5.0
        
        return bias


class XiaoShenDuoShiEngine(PatternEngine):
    """
    枭神夺食引擎 (Biological Energy Supply Interruption Engine)
    
    语义定义：生物能供给截断，偏印（枭）对食神的相位干涉，导致系统输入中断
    物理修正：增加财星通关或比劫制印的权重
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="XIAO_SHEN_DUO_SHI",
            pattern_name="枭神夺食",
            pattern_type="Conflict"
        )
        self.priority_rank = 2  # 冲突格局，次高优先级
        self.base_strength = 0.7
    
    def matching_logic(self, chart: List[Tuple[str, str]], 
                      day_master: str,
                      luck_pillar: Optional[Tuple[str, str]] = None,
                      year_pillar: Optional[Tuple[str, str]] = None,
                      synthesized_field: Optional[Dict] = None) -> PatternMatchResult:
        """
        枭神夺食判定：偏印（枭）和食神同时出现且形成冲突
        
        简化实现：检查天干中是否有偏印和食神
        """
        try:
            from core.trinity.core.nexus.definitions import BaziParticleNexus
            
            # 提取所有天干
            stems = [p[0] for p in chart]
            if luck_pillar:
                stems.append(luck_pillar[0])
            if year_pillar:
                stems.append(year_pillar[0])
            
            # 获取十神关系
            has_pian_yin = False  # 偏印（枭）
            has_shi_shen = False  # 食神
            
            for stem in stems:
                shi_shen = BaziParticleNexus.get_shi_shen(stem, day_master)
                if shi_shen == '偏印':
                    has_pian_yin = True
                elif shi_shen == '食神':
                    has_shi_shen = True
            
            if has_pian_yin and has_shi_shen:
                # 计算冲突强度
                conflict_strength = 0.7
                return PatternMatchResult(
                    matched=True,
                    confidence=conflict_strength,
                    match_data={
                        'has_pian_yin': has_pian_yin,
                        'has_shi_shen': has_shi_shen
                    },
                    sai=conflict_strength * 100,
                    stress=0.75  # 高压力（精神内耗）
                )
            
            return PatternMatchResult(matched=False, confidence=0.0, match_data={})
        except Exception as e:
            logger.warning(f"枭神夺食判定失败: {e}")
            return PatternMatchResult(matched=False, confidence=0.0, match_data={})
    
    def semantic_definition(self, match_result: PatternMatchResult,
                           geo_context: Optional[str] = None) -> str:
        """
        枭神夺食的物理判词
        """
        base_text = "生物能供给截断，偏印（枭）对食神的相位干涉，导致系统输入中断，表现为生机受损、抑郁或项目停滞"
        
        if geo_context:
            if geo_context in ["北方/北京", "近水环境"]:
                return f"{base_text}，在寒性环境下，能量截断进一步加剧，精神内耗达到峰值，需要通过财星通关或比劫制印来化解"
            elif geo_context in ["南方/火地"]:
                return f"{base_text}，在火环境中得到一定缓解，但核心矛盾依然存在，需要主动寻找资源通道"
        
        return base_text
    
    def vector_bias(self, match_result: PatternMatchResult,
                   geo_context: Optional[str] = None) -> VectorBias:
        """
        枭神夺食的五行偏移
        
        物理修正：
        - 偏印（枭）吸收食神能量，导致输出通道阻塞
        - 增加财星（通关）或比劫（制印）的权重
        """
        # 枭神夺食：偏印（枭）吸收食神能量
        # 需要财星通关，或比劫制印
        bias = VectorBias(
            # 偏印通常对应水或木，食神对应火或土
            # 简化处理：增加财星（土/金）通关，增加比劫（木/火）制印
            earth=+12.0,  # 财星通关
            metal=+8.0,   # 财星通关
            wood=+5.0,    # 比劫制印（部分）
            fire=-10.0,   # 食神被夺，火能量减少
            water=-5.0    # 偏印（枭）可能对应水，但需要制衡
        )
        
        # 根据地理环境微调
        if geo_context in ["北方/北京", "近水环境"]:
            # [QGA V24.7 修复] 水环境增强偏印，进一步夺食
            # 水不应该被抵消，它是枭神（拦截器）的能量来源
            # 强制设定为+10.0，代表"拦截能量的持续注入"
            bias.water = max(0, bias.water) + 10.0  # 确保水元素正向膨胀
            bias.fire -= 5.0
        elif geo_context in ["南方/火地"]:
            # 火环境可以缓解，但需要平衡
            bias.fire += 5.0
        
        return bias


class JianLuYueJieEngine(PatternEngine):
    """
    建禄月劫引擎 (Thermodynamic Positive Feedback Explosion Engine)
    
    语义定义：热力学正反馈爆炸，能量密度过载，缺乏疏导
    物理修正：提升能量阈值，需要财星疏导
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="JIAN_LU_YUE_JIE",
            pattern_name="建禄月劫",
            pattern_type="Special"
        )
        self.priority_rank = 1  # 特殊格局，高优先级
        self.base_strength = 0.8
    
    def matching_logic(self, chart: List[Tuple[str, str]], 
                      day_master: str,
                      luck_pillar: Optional[Tuple[str, str]] = None,
                      year_pillar: Optional[Tuple[str, str]] = None,
                      synthesized_field: Optional[Dict] = None) -> PatternMatchResult:
        """
        建禄月劫判定：日主在月令得禄，且比劫众多
        
        简化实现：检查月令是否为日主的临官位，且比劫多
        """
        try:
            from core.trinity.core.nexus.definitions import BaziParticleNexus
            
            # 检查月令
            month_branch = chart[1][1] if len(chart) > 1 else None
            
            # 建禄：月令为日主的临官位
            jian_lu_map = {
                '甲': '寅', '乙': '卯',
                '丙': '午', '丁': '巳',
                '戊': '午', '己': '巳',
                '庚': '申', '辛': '酉',
                '壬': '子', '癸': '亥'
            }
            
            is_jian_lu = jian_lu_map.get(day_master) == month_branch
            
            # 检查比劫数量
            stems = [p[0] for p in chart]
            if luck_pillar:
                stems.append(luck_pillar[0])
            if year_pillar:
                stems.append(year_pillar[0])
            
            bi_jie_count = 0
            for stem in stems:
                shi_shen = BaziParticleNexus.get_shi_shen(stem, day_master)
                if shi_shen in ['比肩', '劫财']:
                    bi_jie_count += 1
            
            if is_jian_lu and bi_jie_count >= 2:
                strength = min(0.9, 0.6 + bi_jie_count * 0.1)
                return PatternMatchResult(
                    matched=True,
                    confidence=strength,
                    match_data={
                        'is_jian_lu': is_jian_lu,
                        'bi_jie_count': bi_jie_count
                    },
                    sai=strength * 100,
                    stress=0.6  # 能量过载压力
                )
            
            return PatternMatchResult(matched=False, confidence=0.0, match_data={})
        except Exception as e:
            logger.warning(f"建禄月劫判定失败: {e}")
            return PatternMatchResult(matched=False, confidence=0.0, match_data={})
    
    def semantic_definition(self, match_result: PatternMatchResult,
                           geo_context: Optional[str] = None) -> str:
        """
        建禄月劫的物理判词
        """
        base_text = "热力学正反馈爆炸，能量密度过载，缺乏疏导，表现为财星晶格被瞬间气化（破财），需要财星疏导能量"
        
        if geo_context:
            if geo_context in ["北方/北京", "近水环境"]:
                return f"{base_text}，在寒性环境下，能量过载可能转化为极端行为，需要及时疏导"
            elif geo_context in ["南方/火地"]:
                return f"{base_text}，在火环境中能量进一步爆发，需要更强的财星疏导"
        
        return base_text
    
    def vector_bias(self, match_result: PatternMatchResult,
                   geo_context: Optional[str] = None) -> VectorBias:
        """
        建禄月劫的五行偏移
        
        物理修正：
        - 比劫过旺，需要财星疏导
        - 能量密度过高，需要释放
        """
        bi_jie_count = match_result.match_data.get('bi_jie_count', 2)
        
        # 建禄月劫：比劫过旺，需要财星疏导
        # 根据日主确定比劫元素（简化处理）
        bias = VectorBias(
            earth=+15.0,  # 财星疏导（土）
            metal=+10.0,  # 财星疏导（金）
            # 比劫对应的元素需要根据日主确定，这里简化
        )
        
        # 根据地理环境微调
        if geo_context in ["北方/北京", "近水环境"]:
            # 水环境可能抑制能量爆发
            bias.water += 5.0
        elif geo_context in ["南方/火地"]:
            # 火环境增强能量爆发
            bias.fire += 10.0
        
        return bias


class GuanYinXiangShengEngine(PatternEngine):
    """
    官印相生引擎 (Steady-State Laminar Flow Engine)
    
    语义定义：稳态层流模型，能量流不存在紊流和对撞
    物理修正：官星压力通过印星介质平滑吸收，转化为日主动能
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="GUAN_YIN_XIANG_SHENG",
            pattern_name="官印相生",
            pattern_type="Normal"
        )
        self.priority_rank = 3  # 正常格局，较低优先级
        self.base_strength = 0.65
    
    def matching_logic(self, chart: List[Tuple[str, str]], 
                      day_master: str,
                      luck_pillar: Optional[Tuple[str, str]] = None,
                      year_pillar: Optional[Tuple[str, str]] = None,
                      synthesized_field: Optional[Dict] = None) -> PatternMatchResult:
        """
        官印相生判定：正官和正印同时出现，且形成相生关系
        
        简化实现：检查天干中是否有正官和正印
        """
        try:
            from core.trinity.core.nexus.definitions import BaziParticleNexus
            
            # 提取所有天干
            stems = [p[0] for p in chart]
            if luck_pillar:
                stems.append(luck_pillar[0])
            if year_pillar:
                stems.append(year_pillar[0])
            
            # 获取十神关系
            has_zheng_guan = False  # 正官
            has_zheng_yin = False  # 正印
            
            for stem in stems:
                shi_shen = BaziParticleNexus.get_shi_shen(stem, day_master)
                if shi_shen == '正官':
                    has_zheng_guan = True
                elif shi_shen == '正印':
                    has_zheng_yin = True
            
            if has_zheng_guan and has_zheng_yin:
                # 计算相生强度
                strength = 0.65
                return PatternMatchResult(
                    matched=True,
                    confidence=strength,
                    match_data={
                        'has_zheng_guan': has_zheng_guan,
                        'has_zheng_yin': has_zheng_yin
                    },
                    sai=strength * 100,
                    stress=0.2  # 低压力（稳态）
                )
            
            return PatternMatchResult(matched=False, confidence=0.0, match_data={})
        except Exception as e:
            logger.warning(f"官印相生判定失败: {e}")
            return PatternMatchResult(matched=False, confidence=0.0, match_data={})
    
    def semantic_definition(self, match_result: PatternMatchResult,
                           geo_context: Optional[str] = None) -> str:
        """
        官印相生的物理判词
        """
        base_text = "稳态层流模型，能量流不存在紊流和对撞，官星的压力通过印星的介质，被平滑吸收并转化为日主的动能，表现为社会声望与资源位阶的无阻力跃迁"
        
        if geo_context:
            if geo_context in ["北方/北京", "近水环境"]:
                return f"{base_text}，在寒性环境下，印星得到增强，能量传导更加顺畅"
            elif geo_context in ["南方/火地"]:
                return f"{base_text}，在火环境中，能量流动加速，但需要保持平衡"
        
        return base_text
    
    def vector_bias(self, match_result: PatternMatchResult,
                   geo_context: Optional[str] = None) -> VectorBias:
        """
        官印相生的五行偏移
        
        物理修正：
        - 官星（金）和印星（水/木）形成相生
        - 能量平滑传导，系统熵值极低
        """
        # 官印相生：官星（金）生印星（水），印星（水）生日主
        # 简化处理：增强金和水/木的能量
        bias = VectorBias(
            metal=+8.0,   # 正官（金）
            water=+10.0,  # 正印（水）
            wood=+5.0     # 正印（木，部分情况）
        )
        
        # 根据地理环境微调
        if geo_context in ["北方/北京", "近水环境"]:
            # 水环境增强印星
            bias.water += 5.0
        elif geo_context in ["南方/火地"]:
            # 火环境需要平衡
            bias.fire += 3.0
        
        return bias


class YangRenJiaShaEngine(PatternEngine):
    """
    羊刃架杀引擎 (High-Pressure Fusion Engine)
    
    语义定义：极端高压下的动态平衡，系统承载能力达到峰值
    物理修正：提升SAI爆发阈值，画像锁定为"在危机中极度扩张"
    """
    
    def __init__(self):
        super().__init__(
            pattern_id="YANG_REN_JIA_SHA",
            pattern_name="羊刃架杀",
            pattern_type="Special"
        )
        self.priority_rank = 1  # 特殊格局，高优先级
        self.base_strength = 0.9
    
    def matching_logic(self, chart: List[Tuple[str, str]], 
                      day_master: str,
                      luck_pillar: Optional[Tuple[str, str]] = None,
                      year_pillar: Optional[Tuple[str, str]] = None,
                      synthesized_field: Optional[Dict] = None) -> PatternMatchResult:
        """
        羊刃架杀判定：羊刃和七杀同时出现
        
        简化实现：检查是否有羊刃和七杀
        """
        try:
            from core.trinity.core.nexus.definitions import BaziParticleNexus
            
            # 提取地支（羊刃在地支）
            branches = [p[1] for p in chart]
            if luck_pillar:
                branches.append(luck_pillar[1])
            if year_pillar:
                branches.append(year_pillar[1])
            
            # 提取天干（七杀在天干）
            stems = [p[0] for p in chart]
            if luck_pillar:
                stems.append(luck_pillar[0])
            if year_pillar:
                stems.append(year_pillar[0])
            
            # 检查羊刃（简化：检查日主的临官位）
            has_yang_ren = False  # 羊刃
            
            # 检查七杀
            has_qi_sha = False  # 七杀
            
            for stem in stems:
                shi_shen = BaziParticleNexus.get_shi_shen(stem, day_master)
                if shi_shen == '七杀':
                    has_qi_sha = True
            
            # 羊刃判断（简化处理）
            # 实际应该检查日主的临官位是否在地支中出现
            # 这里简化为检查是否有特定组合
            yang_ren_branches = {
                '甲': '卯', '乙': '寅',
                '丙': '午', '丁': '巳',
                '戊': '午', '己': '巳',
                '庚': '酉', '辛': '申',
                '壬': '子', '癸': '亥'
            }
            
            yang_ren_branch = yang_ren_branches.get(day_master)
            if yang_ren_branch and yang_ren_branch in branches:
                has_yang_ren = True
            
            if has_yang_ren and has_qi_sha:
                return PatternMatchResult(
                    matched=True,
                    confidence=0.9,
                    match_data={
                        'has_yang_ren': has_yang_ren,
                        'has_qi_sha': has_qi_sha
                    },
                    sai=0.9 * 100,  # 高SAI
                    stress=0.7  # 高压
                )
            
            return PatternMatchResult(matched=False, confidence=0.0, match_data={})
        except Exception as e:
            logger.warning(f"羊刃架杀判定失败: {e}")
            return PatternMatchResult(matched=False, confidence=0.0, match_data={})
    
    def semantic_definition(self, match_result: PatternMatchResult,
                           geo_context: Optional[str] = None) -> str:
        """
        羊刃架杀的物理判词
        """
        base_text = "极端高压下的动态平衡，系统承载能力达到峰值，在危机中极度扩张，具有强烈的竞争和征服欲"
        
        if geo_context:
            if geo_context in ["北方/北京", "近水环境"]:
                return f"{base_text}，但在寒性环境下，高压状态可能转化为极端行为，需要适当降温"
            elif geo_context in ["南方/火地"]:
                return f"{base_text}，在火环境中得到充分激活，高压转化为强大的执行力"
        
        return base_text
    
    def vector_bias(self, match_result: PatternMatchResult,
                   geo_context: Optional[str] = None) -> VectorBias:
        """
        羊刃架杀的五行偏移
        
        物理修正：
        - 提升SAI爆发阈值（体现在Strength值中）
        - 羊刃（日主同五行）和七杀（克日主）形成高压平衡
        """
        # 羊刃架杀：羊刃（日主同五行）和七杀（克日主）的平衡
        # 通用规则：羊刃（增强日主）和七杀（克日主）的平衡
        # 注意：实际应该根据日主确定具体元素，这里使用通用规则
        # 系统处于高压状态，能量高度集中
        bias = VectorBias(
            # 根据具体日主调整（这里使用通用规则）
            fire=+10.0,  # 高压状态，能量集中
            metal=+5.0   # 七杀（金）的力量
        )
        
        # 根据地理环境调整
        if geo_context in ["北方/北京", "近水环境"]:
            # 水环境可能削弱高压
            bias.water += 5.0
            bias.fire -= 5.0
        elif geo_context in ["南方/火地"]:
            # 火环境增强高压
            bias.fire += 5.0
        
        return bias


# 注册所有格局引擎的函数
def register_all_pattern_engines():
    """注册所有格局引擎到全局注册表"""
    from core.models.pattern_engine import get_pattern_registry
    
    registry = get_pattern_registry()
    
    # 注册伤官见官引擎
    if not registry.get_by_id("SHANG_GUAN_JIAN_GUAN"):
        registry.register(ShangGuanJianGuanEngine())
        logger.info("✅ 已注册伤官见官引擎")
    
    # 注册化火格引擎
    if not registry.get_by_id("HUA_HUO_GE"):
        registry.register(HuaHuoGeEngine())
        logger.info("✅ 已注册化火格引擎")
    
    # 注册羊刃架杀引擎
    if not registry.get_by_id("YANG_REN_JIA_SHA"):
        registry.register(YangRenJiaShaEngine())
        logger.info("✅ 已注册羊刃架杀引擎")
    
    # 注册枭神夺食引擎
    if not registry.get_by_id("XIAO_SHEN_DUO_SHI"):
        registry.register(XiaoShenDuoShiEngine())
        logger.info("✅ 已注册枭神夺食引擎")
    
    # 注册建禄月劫引擎
    if not registry.get_by_id("JIAN_LU_YUE_JIE"):
        registry.register(JianLuYueJieEngine())
        logger.info("✅ 已注册建禄月劫引擎")
    
    # 注册官印相生引擎
    if not registry.get_by_id("GUAN_YIN_XIANG_SHENG"):
        registry.register(GuanYinXiangShengEngine())
        logger.info("✅ 已注册官印相生引擎")


# 自动注册（模块导入时）
register_all_pattern_engines()

