"""
语义蒸馏器 (Semantic Distiller)
将古籍文本转化为结构化JSONLogic和物理权重

基于: FDS_KMS_SPEC_v1.0-BETA.md 第4.1节
"""

from typing import Dict, Any, Optional
import json


class SemanticDistiller:
    """
    计算语文学家 - 将古文转化为机器可执行的逻辑
    """
    
    # 十神代码标准映射表 (与FDS_ARCHITECTURE一致)
    TEN_GOD_CODES = {
        "正官": "ZG", "偏官": "PG", "七杀": "PG",
        "正印": "ZC", "偏印": "PC", "枭神": "PC",
        "食神": "ZS", "伤官": "PS",
        "正财": "ZR", "偏财": "PR",
        "比肩": "ZB", "劫财": "PB"
    }
    
    # 变量白名单
    VARIABLE_WHITELIST = [
        "ten_gods.ZG", "ten_gods.PG",
        "ten_gods.ZC", "ten_gods.PC",
        "ten_gods.ZS", "ten_gods.PS",
        "ten_gods.ZR", "ten_gods.PR",
        "ten_gods.ZB", "ten_gods.PB",
        "self_energy"
    ]
    
    @staticmethod
    def get_system_prompt(source_book: str = "子平真诠", topic: str = "食神格") -> str:
        """
        生成LLM System Prompt模板
        
        Args:
            source_book: 典籍名称
            topic: 主题/格局名称
            
        Returns:
            完整的System Prompt字符串
        """
        return f"""# Role
你是一个精通中国传统命理学与现代计算机逻辑的"计算语文学家"。
你的任务是将输入的古籍片段（Raw Text）转化为 FDS-KMS 规范定义的结构化 JSON 数据。

# Input Context
- Source Book: 《{source_book}》
- Topic: {topic}

# Output Schema
必须严格遵守以下 JSON 格式：
{{
  "original_text": "输入的原文本",
  "logic_extraction": {{
    "logic_type": "breaking_condition" | "forming_condition" | "saving_condition",
    "target_pattern": "格局名称",
    "expression_tree": {{ JSONLogic 格式的布尔表达式 }},
    "priority": 整数 (1-100)
  }},
  "physics_impact": {{
    "target_ten_god": "十神标准代码 (如 ZS, PC, ZG...)",
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

# Variable Whitelist (严格使用以下变量名)
- ten_gods.ZG (正官), ten_gods.PG (七杀)
- ten_gods.ZC (正印), ten_gods.PC (枭神)
- ten_gods.ZS (食神), ten_gods.PS (伤官)
- ten_gods.ZR (正财), ten_gods.PR (偏财)
- ten_gods.ZB (比肩), ten_gods.PB (劫财)
- self_energy (日主能量)

# Rules
1. **逻辑转化**: 
   - "忌"、"怕"、"畏" → `>` (大于) 或 `exist` 逻辑
   - "喜"、"宜" → 权重增加
   - "无"、"绝" → `== 0` 或 `!exist`
   
2. **物理映射**: 
   - "冲"、"克"、"夺" = 负面影响或增加应力(S轴)
   - "生"、"扶" = 正面影响或增加能量(E轴)
   - "财" = 影响M轴 (Material/财富)
   - "官" = 影响O轴 (Order/权力)
   
3. **Hard Tanh**: 权重必须在 [-1.0, 1.0] 之间。极度凶险/吉利的情况取绝对值 0.8-1.0。

4. **逻辑类型判断**:
   - "成格"、"宜"、"喜" → `forming_condition`
   - "破格"、"忌"、"畏" → `breaking_condition`
   - "救"、"解"、"化" → `saving_condition`

# Task
Process the following text and output ONLY valid JSON (no markdown, no explanation):"""

    @staticmethod
    def validate_output(output: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证LLM输出的JSON是否符合Schema
        
        Returns:
            (is_valid, error_message)
        """
        # 检查必需字段
        required_fields = ["original_text", "logic_extraction"]
        for field in required_fields:
            if field not in output:
                return False, f"缺少必需字段: {field}"
        
        # 检查logic_extraction
        logic = output.get("logic_extraction", {})
        if "logic_type" not in logic:
            return False, "logic_extraction缺少logic_type字段"
        
        if logic["logic_type"] not in ["forming_condition", "breaking_condition", "saving_condition"]:
            return False, f"无效的logic_type: {logic['logic_type']}"
        
        if "expression_tree" not in logic:
            return False, "logic_extraction缺少expression_tree字段"
        
        # 验证expression_tree不是字符串（必须是JSON对象）
        expression_tree = logic["expression_tree"]
        if isinstance(expression_tree, str):
            return False, f"expression_tree不能是字符串，必须是JSON对象。当前值: {expression_tree[:50]}..."
        
        if not isinstance(expression_tree, dict):
            return False, f"expression_tree必须是JSON对象（dict），当前类型: {type(expression_tree).__name__}"
        
        if "target_pattern" not in logic:
            return False, "logic_extraction缺少target_pattern字段"
        
        # 检查physics_impact (可选)
        if "physics_impact" in output:
            physics = output["physics_impact"]
            if "target_ten_god" not in physics:
                return False, "physics_impact缺少target_ten_god字段"
            
            if "impact_dimensions" not in physics:
                return False, "physics_impact缺少impact_dimensions字段"
            
            # 验证十神代码（支持"ZS"或"ten_gods.ZS"格式）
            target_god = physics["target_ten_god"]
            if "." in target_god:
                # 提取简单代码，如"ten_gods.ZS" -> "ZS"
                target_god = target_god.split(".")[-1]
            
            if target_god not in SemanticDistiller.TEN_GOD_CODES.values():
                return False, f"无效的十神代码: {physics['target_ten_god']} (提取后: {target_god})"
            
            # 标准化为简单代码格式
            physics["target_ten_god"] = target_god
            
            # 验证维度
            for dim in physics["impact_dimensions"]:
                if dim["axis"] not in ["E", "O", "M", "S", "R"]:
                    return False, f"无效的维度轴: {dim['axis']}"
                
                weight = dim.get("weight_modifier", 0)
                if not (-1.0 <= weight <= 1.0):
                    return False, f"权重超出范围 [-1.0, 1.0]: {weight}"
        
        return True, None

    @staticmethod
    def parse_llm_response(response: str) -> Dict[str, Any]:
        """
        解析LLM响应，提取JSON
        
        Args:
            response: LLM的原始响应
            
        Returns:
            解析后的JSON字典
        """
        # 尝试提取JSON（可能被markdown包裹）
        response = response.strip()
        
        # 移除可能的markdown代码块标记
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        try:
            output = json.loads(response)
            
            # 如果expression_tree是字符串，尝试转换为JSONLogic
            logic_extraction = output.get("logic_extraction", {})
            expr = logic_extraction.get("expression_tree")
            
            if isinstance(expr, str):
                try:
                    from kms.core.logic_adapter import convert_python_to_jsonlogic
                    converted_expr = convert_python_to_jsonlogic(expr)
                    if isinstance(converted_expr, dict):
                        logic_extraction["expression_tree"] = converted_expr
                        output["logic_extraction"] = logic_extraction
                except Exception:
                    # 转换失败，保留原始字符串，由验证器处理
                    pass
            
            return output
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析JSON: {e}\n响应内容: {response[:200]}")

