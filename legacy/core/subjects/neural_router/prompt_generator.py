"""
[QGA V25.0 Phase 3] Prompt生成器（逻辑内联版本）
实现Logic Inlining：将所有格局的公理定义、特征向量数据、权重坍缩指令合并成高密度指令压缩包
"""

import logging
import json
from typing import Dict, List, Optional, Any
from .registry import get_neural_router_registry
from .feature_vectorizer import FeatureVectorizer

logger = logging.getLogger(__name__)


class PromptGenerator:
    """
    Prompt生成器（逻辑内联版本）
    实现Logic Inlining，将所有物理公理、特征向量、权重坍缩指令合并
    """
    
    def __init__(self):
        """初始化Prompt生成器"""
        self.registry = get_neural_router_registry()
        logger.info("✅ Prompt生成器初始化完成（逻辑内联模式）")
    
    def _extract_pattern_axioms(self, active_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取激活格局的物理公理
        
        Args:
            active_patterns: 激活的格局列表
            
        Returns:
            格局公理列表
        """
        axioms = []
        
        for pattern in active_patterns:
            pattern_id = pattern.get("id") or pattern.get("name")
            pattern_def = self.registry.get_pattern_definition(pattern_id)
            
            if pattern_def and pattern_def.get("physical_axiom"):
                axiom = pattern_def["physical_axiom"].copy()
                axiom["pattern_id"] = pattern_id
                axiom["pattern_name"] = pattern_def.get("pattern_name")
                axiom["pattern_type"] = pattern_def.get("pattern_type")
                axiom["priority_rank"] = pattern_def.get("priority_rank", 999)
                axiom["base_strength"] = pattern_def.get("base_strength", 0.5)
                axioms.append(axiom)
        
        # 按优先级排序
        axioms.sort(key=lambda x: (x.get("priority_rank", 999), -x.get("base_strength", 0.0)))
        
        return axioms
    
    def _build_coherence_instructions(self, axioms: List[Dict[str, Any]],
                                     feature_vector: Dict[str, Any]) -> str:
        """
        构建格局相干性指令集
        定义LLM处理"复合干涉"的准则
        
        Args:
            axioms: 格局公理列表
            feature_vector: 特征向量
            
        Returns:
            相干性指令字符串
        """
        if len(axioms) <= 1:
            return ""
        
        instructions = []
        instructions.append("【格局相干性处理准则】")
        instructions.append("当特征向量同时触发多个格局公理时，按以下优先级处理：")
        
        # 1. 应力优先原则
        stress_tensor = feature_vector.get("stress_tensor", 0.0)
        if stress_tensor > 0.6:
            instructions.append("1. **应力优先**：如果stress_tensor > 0.6，优先处理冲突格局（Conflict类型）")
            conflict_axioms = [a for a in axioms if a.get("pattern_type") == "Conflict"]
            if conflict_axioms:
                instructions.append(f"   - 当前冲突格局：{', '.join([a['pattern_name'] for a in conflict_axioms])}")
                instructions.append(f"   - 应力值：{stress_tensor:.3f}，超过阈值0.6，系统处于不稳定状态")
        
        # 2. 动量优先原则
        momentum_term = feature_vector.get("momentum_term", {})
        if momentum_term:
            shi_to_cai = momentum_term.get("shi_to_cai", 0.0)
            if shi_to_cai > 0.5:
                instructions.append("2. **动量优先**：如果动量项显示'食神→财'转化趋势 > 0.5，优先处理输出型格局")
                output_patterns = [a for a in axioms if "食神" in a.get("pattern_name", "") or "从儿" in a.get("pattern_name", "")]
                if output_patterns:
                    instructions.append(f"   - 当前输出型格局：{', '.join([a['pattern_name'] for a in output_patterns])}")
        
        # 3. 优先级排序
        instructions.append("3. **优先级排序**：按PriorityRank排序，Rank=1的格局优先处理")
        priority_1 = [a for a in axioms if a.get("priority_rank") == 1]
        if priority_1:
            instructions.append(f"   - 最高优先级格局：{', '.join([a['pattern_name'] for a in priority_1])}")
        
        # 4. 权重坍缩
        instructions.append("4. **权重坍缩**：多个格局同时激活时，使用加权平均计算综合影响")
        instructions.append("   - 权重 = base_strength × (1 - entropy_damping)")
        instructions.append("   - 最终persona应反映所有激活格局的加权综合影响")
        
        return "\n".join(instructions)
    
    def generate_inline_prompt(self,
                               active_patterns: List[Dict[str, Any]],
                               feature_vector: Dict[str, Any],
                               structured_data: Dict[str, Any]) -> str:
        """
        [主入口点]
        生成逻辑内联Prompt（Logic Inlining）
        将所有格局公理、特征向量、权重坍缩指令合并成高密度指令压缩包
        
        Args:
            active_patterns: 激活的格局列表
            feature_vector: 特征向量（来自FeatureVectorizer）
            structured_data: 结构化数据（原有格式）
            
        Returns:
            完整的逻辑内联Prompt
        """
        # 1. 提取格局公理
        axioms = self._extract_pattern_axioms(active_patterns)
        
        # 2. 构建相干性指令
        coherence_instructions = self._build_coherence_instructions(axioms, feature_vector)
        
        # 3. 构建特征向量描述
        elemental_fields = feature_vector.get("elemental_fields_dict", {})
        stress_tensor = feature_vector.get("stress_tensor", 0.0)
        phase_coherence = feature_vector.get("phase_coherence", 0.0)
        momentum_term = feature_vector.get("momentum_term", {})
        routing_hint = feature_vector.get("routing_hint")
        
        # 4. 构建逻辑内联Prompt
        prompt_parts = []
        
        prompt_parts.append("=" * 80)
        prompt_parts.append("【QGA V25.0 逻辑内联指令包 (Logic Inlining)】")
        prompt_parts.append("=" * 80)
        prompt_parts.append("")
        
        # 特征向量数据
        prompt_parts.append("【特征向量数据 (Feature Vector)】")
        prompt_parts.append(f"五行场强分布：")
        prompt_parts.append(f"  - 金 (metal): {elemental_fields.get('metal', 0.0):.4f}")
        prompt_parts.append(f"  - 木 (wood): {elemental_fields.get('wood', 0.0):.4f}")
        prompt_parts.append(f"  - 水 (water): {elemental_fields.get('water', 0.0):.4f}")
        prompt_parts.append(f"  - 火 (fire): {elemental_fields.get('fire', 0.0):.4f}")
        prompt_parts.append(f"  - 土 (earth): {elemental_fields.get('earth', 0.0):.4f}")
        prompt_parts.append(f"应力张量 (stress_tensor): {stress_tensor:.4f}")
        prompt_parts.append(f"相位一致性 (phase_coherence): {phase_coherence:.4f}")
        if routing_hint:
            prompt_parts.append(f"路由暗示 (routing_hint): {routing_hint}")
        if momentum_term:
            prompt_parts.append(f"动量项 (momentum_term): {json.dumps(momentum_term, ensure_ascii=False, indent=2)}")
        prompt_parts.append("")
        
        # 格局公理定义
        if axioms:
            prompt_parts.append("【激活格局的物理公理 (Physical Axioms)】")
            for i, axiom in enumerate(axioms, 1):
                prompt_parts.append(f"\n{i}. {axiom['pattern_name']} ({axiom['pattern_id']})")
                prompt_parts.append(f"   类型: {axiom.get('pattern_type', 'Unknown')}")
                prompt_parts.append(f"   优先级: {axiom.get('priority_rank', 999)}")
                prompt_parts.append(f"   触发条件: {axiom.get('trigger_condition', 'N/A')}")
                prompt_parts.append(f"   能量方程: {axiom.get('energy_equation', 'N/A')}")
                prompt_parts.append(f"   相位关系: {axiom.get('phase_relationship', 'N/A')}")
                prompt_parts.append(f"   修正机制: {axiom.get('correction_mechanism', 'N/A')}")
                prompt_parts.append(f"   坍缩阈值: {axiom.get('collapse_threshold', 0.0)}")
                prompt_parts.append(f"   恢复路径: {axiom.get('recovery_path', 'N/A')}")
            prompt_parts.append("")
        
        # 相干性指令
        if coherence_instructions:
            prompt_parts.append(coherence_instructions)
            prompt_parts.append("")
        
        # 原有结构化数据（保留兼容性）
        prompt_parts.append("【原始结构化数据 (Original Structured Data)】")
        prompt_parts.append(json.dumps(structured_data, ensure_ascii=False, indent=2))
        prompt_parts.append("")
        
        # 输出要求（Phase 4升级：全场能量状态审计）
        prompt_parts.append("=" * 80)
        prompt_parts.append("【输出要求 - 全场能量状态审计 (Energy State Report)】")
        prompt_parts.append("=" * 80)
        prompt_parts.append("")
        prompt_parts.append("基于上述特征向量数据和物理公理，执行以下任务：")
        prompt_parts.append("")
        prompt_parts.append("1. **公理匹配**：根据特征向量数据，判断哪些公理的触发条件被满足")
        prompt_parts.append("2. **能量计算**：使用公理中的能量方程计算每个格局的能量强度")
        prompt_parts.append("3. **相位分析**：根据相位关系描述能量流动过程")
        prompt_parts.append("4. **权重坍缩**：如果多个格局同时激活，按照相干性指令计算每个格局对最终画像的贡献百分比")
        prompt_parts.append("5. **全局状态**：输出全局能量状态报告，包括系统稳定性、能量流向、临界状态等")
        prompt_parts.append("6. **修正应用**：根据修正机制和恢复路径，生成corrected_elements")
        prompt_parts.append("")
        prompt_parts.append("输出格式（纯JSON，无markdown标记）：")
        prompt_parts.append('{')
        prompt_parts.append('  "persona": "...",  // 最终命运画像描述')
        prompt_parts.append('  "corrected_elements": {"金": XX, "木": XX, "水": XX, "火": XX, "土": XX},')
        prompt_parts.append('  "energy_state_report": {  // [Phase 4] 全场能量状态报告')
        prompt_parts.append('    "system_stability": 0.XX,  // 系统稳定性（0.0-1.0）')
        prompt_parts.append('    "energy_flow_direction": "...",  // 能量流向描述')
        prompt_parts.append('    "critical_state": "...",  // 临界状态描述（如：崩态、稳态、临界态）')
        prompt_parts.append('    "total_energy": 0.XX  // 总能量值')
        prompt_parts.append('  },')
        prompt_parts.append('  "logic_collapse": {  // [Phase 4] 逻辑权重坍缩')
        prompt_parts.append('    "PATTERN_ID_1": 0.XX,  // 格局1的贡献百分比（0.0-1.0，总和应约等于1.0）')
        prompt_parts.append('    "PATTERN_ID_2": 0.XX,  // 格局2的贡献百分比')
        prompt_parts.append('    "...": 0.XX')
        prompt_parts.append('  }')
        prompt_parts.append('}')
        prompt_parts.append("")
        prompt_parts.append("**重要**：logic_collapse中所有格局的贡献百分比之和应约等于1.0（允许0.95-1.05的误差）")
        prompt_parts.append("")
        
        full_prompt = "\n".join(prompt_parts)
        
        logger.debug(f"✅ 逻辑内联Prompt生成完成，包含{len(axioms)}个格局公理")
        
        return full_prompt

