"""
LLM语义蒸馏示例脚本 - Ollama本地版

使用本地运行的 qwen2.5:3b 进行语义蒸馏
"""

import json
import sys
import os
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kms.core.semantic_distiller import SemanticDistiller

# 配置
MODEL_NAME = "qwen2.5:3b"

# System Prompt (注入计算语文学家的人格)
SYSTEM_PROMPT_TEMPLATE = """# Role
你是一个精通中国传统命理学与现代计算机逻辑的"计算语文学家"。
你的任务是将输入的古籍片段（Raw Text）转化为 FDS-KMS 规范定义的结构化 JSON 数据。

# Output Schema
必须严格遵守以下 JSON 格式（只输出JSON，不要其他文字）：
{
  "original_text": "输入的原文本",
  "logic_extraction": {
    "logic_type": "forming_condition" | "breaking_condition" | "saving_condition",
    "target_pattern": "格局名称",
    "expression_tree": { JSONLogic 格式的布尔表达式 },
    "priority": 整数 (1-100)
  },
  "physics_impact": {
    "target_ten_god": "十神标准代码 (如 ZS, PC, ZG...)",
    "impact_dimensions": [
      {
        "axis": "E" | "O" | "M" | "S" | "R",
        "weight_modifier": 浮点数 (-1.0 到 1.0),
        "lock_request": true/false,
        "reason": "物理学解释"
      }
    ]
  }
}

# Variable Whitelist (严格使用以下变量名)
- ten_gods.ZG (正官), ten_gods.PG (七杀)
- ten_gods.ZC (正印), ten_gods.PC (枭神)
- ten_gods.ZS (食神), ten_gods.PS (伤官)
- ten_gods.ZR (正财), ten_gods.PR (偏财)
- ten_gods.ZB (比肩), ten_gods.PB (劫财)
- self_energy (日主能量)

# Rules
1. **逻辑转化**: 
   - "忌"、"怕"、"畏" → `>` (大于) 或逻辑排除
   - "喜"、"宜" → 权重增加
   - "无"、"绝" → `== 0`
   
2. **物理映射**: 
   - "冲"、"克"、"夺" = 负面影响或增加应力(S轴)
   - "生"、"扶" = 正面影响或增加能量(E轴)
   - "财" = 影响M轴 (Material/财富)
   - "官" = 影响O轴 (Order/权力)
   
3. **权重范围**: 必须在 [-1.0, 1.0] 之间。极度凶险/吉利的情况取绝对值 0.8-1.0。

4. **逻辑类型判断**:
   - "成格"、"宜"、"喜" → `forming_condition`
   - "破格"、"忌"、"畏" → `breaking_condition`
   - "救"、"解"、"化" → `saving_condition`
"""


def call_ollama_api(prompt: str, system_prompt: str) -> Optional[str]:
    """
    调用Ollama本地API
    
    Args:
        prompt: 用户提示（古文文本）
        system_prompt: 系统提示
        
    Returns:
        LLM的响应文本，如果失败返回None
    """
    try:
        import ollama
    except ImportError:
        print("❌ 错误: 需要安装ollama库")
        print("   安装命令: pip install ollama")
        return None
    
    try:
        print(f"   🤖 调用模型: {MODEL_NAME}...")
        
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"分析以下文本并输出JSON:\n\n{prompt}"}
            ],
            format='json',  # Qwen2.5 支持 JSON 模式
            options={
                'temperature': 0.1,      # 保持低创造性，保证逻辑稳定
                'num_predict': 1024,      # 增加输出上限至1024 tokens，避免JSON截断
                'num_ctx': 2048           # 确保上下文窗口足够大
            }
        )
        
        return response['message']['content']
        
    except Exception as e:
        print(f"   ❌ Ollama调用失败: {e}")
        print(f"   提示: 请确保Ollama服务正在运行 (ollama serve)")
        return None


def distill_text(text: str, 
                 source_book: str = "测试文本",
                 topic: str = "食神格") -> Optional[Dict[str, Any]]:
    """
    对古文文本进行语义蒸馏
    
    Args:
        text: 古文文本
        source_book: 典籍名称
        topic: 主题/格局名称
        
    Returns:
        结构化的codex条目，如果失败返回None
    """
    print("=" * 60)
    print("FDS-KMS 语义蒸馏 (Ollama本地版)")
    print("=" * 60)
    print()
    print(f"📝 输入文本: {text}")
    print()
    
    # 使用SemanticDistiller生成System Prompt
    distiller = SemanticDistiller()
    system_prompt = distiller.get_system_prompt(source_book, topic)
    
    # 调用LLM
    print("🤖 调用LLM进行语义蒸馏...")
    llm_response = call_ollama_api(text, system_prompt)
    
    if not llm_response:
        return None
    
    print("   ✅ LLM响应已接收")
    print()
    
    # 解析响应
    print("🔍 解析LLM响应...")
    try:
        output = distiller.parse_llm_response(llm_response)
        print("   ✅ JSON解析成功")
        print()
    except Exception as e:
        print(f"   ❌ JSON解析失败: {e}")
        print(f"   响应内容: {llm_response[:200]}...")
        return None
    
    # 验证输出
    print("✅ 验证输出格式...")
    is_valid, error = distiller.validate_output(output)
    
    if not is_valid:
        print(f"   ❌ 验证失败: {error}")
        return None
    
    print("   ✅ 格式验证通过")
    print()
    
    # 自动补全Codex必要字段
    codex_entry = {
        "canon_id": f"AUTO-{abs(hash(text)) % 10000:04d}",
        "source_book": source_book,
        "chapter": topic,
        "tags": ["LLM生成", "自动蒸馏", topic],
        "relevance_score": 0.9,
        **output  # 合并LLM生成的logic和physics
    }
    
    # 显示结果
    print("=" * 60)
    print("蒸馏结果:")
    print("=" * 60)
    print(json.dumps(codex_entry, indent=2, ensure_ascii=False))
    print()
    
    return codex_entry


def main():
    """主函数：测试用例"""
    
    print("🧪 开始测试LLM语义蒸馏...")
    print()
    
    # 测试用例1：食神生财（成格）
    print("【测试1】食神生财（成格条件）")
    print("-" * 60)
    text1 = "食神生旺，且见财星引通食神之气，此为上格。"
    entry1 = distill_text(text1, source_book="测试典籍", topic="食神格")
    
    if entry1:
        logic_type = entry1.get("logic_extraction", {}).get("logic_type", "unknown")
        print(f"✅ 蒸馏成功 (Logic Type: {logic_type})")
        print()
    else:
        print("❌ 蒸馏失败")
        print()
    
    # 测试用例2：枭神夺食（破格）
    print("【测试2】枭神夺食（破格条件）")
    print("-" * 60)
    text2 = "食神格，最忌枭印夺食，若无财星解救，则贫贱之命。"
    entry2 = distill_text(text2, source_book="测试典籍", topic="食神格")
    
    if entry2:
        physics = entry2.get("physics_impact", {})
        target_god = physics.get("target_ten_god", "unknown")
        print(f"✅ 蒸馏成功 (Target Ten God: {target_god})")
        print()
    else:
        print("❌ 蒸馏失败")
        print()
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
