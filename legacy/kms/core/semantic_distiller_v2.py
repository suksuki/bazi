"""
语义蒸馏器 V2 (Semantic Distiller V2)
优化版：包含Few-Shot示例，强制JSONLogic格式，针对Qwen 2.5:3b优化

基于: FDS_KMS_SPEC_v1.0-BETA.md
"""

from typing import Dict, Any, Optional
import json
from .semantic_distiller import SemanticDistiller


class SemanticDistillerV2(SemanticDistiller):
    """
    增强版语义蒸馏器
    添加Few-Shot示例，强制JSONLogic格式，提高LLM输出质量
    """
    
    @staticmethod
    def get_system_prompt(source_book: str = "子平真诠", topic: str = "食神格") -> str:
        """
        生成优化版System Prompt（针对Qwen 2.5:3b严格优化）
        """
        return f"""你是一个计算语文学家。任务是将古籍转化为 FDS-KMS 规范的 JSON。

### 🚨 核心指令 (CRITICAL INSTRUCTION)
你必须输出符合 **JSONLogic** 标准的 `expression_tree`。
**严禁**输出字符串或扁平结构，必须使用逻辑算子包裹。

❌ 错误示范 (字符串格式，禁止！):
"expression_tree": "(self_energy['ZS'] > 0) & (ten_gods.ZC['ZR'] == 1)"

❌ 错误示范 (缺少根节点，禁止！):
"expression_tree": {{ ">": [{{"var": "ten_gods.ZS"}}, 0] }}

✅ 正确示范 (必须有 'and'/'or' 根节点):
"expression_tree": {{
  "and": [
    {{ ">": [{{"var": "ten_gods.ZS"}}, 0] }},
    {{ ">": [{{"var": "ten_gods.ZR"}}, 0] }}
  ]
}}

### 输出格式
必须输出完整的JSON，包含以下字段：
{{
  "original_text": "输入的原文本",
  "logic_extraction": {{
    "logic_type": "forming_condition" | "breaking_condition" | "saving_condition",
    "target_pattern": "格局名称",
    "expression_tree": {{ 必须是JSON对象，不能是字符串 }},
    "priority": 整数 (1-100)
  }},
  "physics_impact": {{
    "target_ten_god": "十神标准代码 (ZS, PC, ZG等)",
    "impact_dimensions": [
      {{
        "axis": "E" | "O" | "M" | "S" | "R",
        "weight_modifier": 浮点数 (-1.0 到 1.0),
        "lock_request": true/false,
        "reason": "物理学解释"
      }}
    ]
  }}
}}

### 变量映射表
- ZS: 食神, PC: 枭神/偏印
- ZG: 正官, PG: 七杀
- ZR: 正财, PR: 偏财
- ZC: 正印, PS: 伤官
- ZB: 比肩, PB: 劫财

### Few-Shot 示例 (必须严格模仿)

**示例1**: 输入: "食神格，若见七杀透干，最喜食神制杀。"
输出:
{{
  "original_text": "食神格，若见七杀透干，最喜食神制杀。",
  "logic_extraction": {{
    "logic_type": "forming_condition",
    "target_pattern": "食神格",
    "expression_tree": {{
      "and": [
        {{ ">": [{{"var": "ten_gods.ZS"}}, 0] }},
        {{ ">": [{{"var": "ten_gods.PG"}}, 0] }},
        {{ ">": [{{"var": "ten_gods.ZS"}}, {{"var": "ten_gods.PG"}}] }}
      ]
    }},
    "priority": 90
  }},
  "physics_impact": {{
    "target_ten_god": "ZS",
    "impact_dimensions": [
      {{
        "axis": "O",
        "weight_modifier": 0.9,
        "lock_request": true,
        "reason": "食神制杀，格局之魂"
      }}
    ]
  }}
}}

**示例2**: 输入: "食神格，最忌枭印夺食，若无财星解救，则破格。"
输出:
{{
  "original_text": "食神格，最忌枭印夺食，若无财星解救，则破格。",
  "logic_extraction": {{
    "logic_type": "breaking_condition",
    "target_pattern": "食神格",
    "expression_tree": {{
      "and": [
        {{ ">": [{{"var": "ten_gods.PC"}}, {{"var": "ten_gods.ZS"}}] }},
        {{ "==": [{{"var": "ten_gods.ZR"}}, 0] }},
        {{ "==": [{{"var": "ten_gods.PR"}}, 0] }}
      ]
    }},
    "priority": 100
  }},
  "physics_impact": {{
    "target_ten_god": "PC",
    "impact_dimensions": [
      {{
        "axis": "S",
        "weight_modifier": 0.8,
        "lock_request": true,
        "reason": "枭神夺食导致结构断裂"
      }}
    ]
  }}
}}

### 重要规则
1. expression_tree必须是JSON对象，绝对不能是字符串
2. 必须有"and"或"or"作为根节点
3. 所有条件放在数组中
4. 只输出JSON，不要Markdown代码块标记

请处理用户输入的文本，只输出JSON。"""
