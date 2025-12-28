# QGA V24.7 代码变更清单

## 已修改的文件

### 1. controllers/profile_audit_controller.py
**修改内容**:
- [QGA V24.7] 添加虚拟档案支持（硬编码模式）
  - 在`perform_deep_audit`中检查`_use_hardcoded`字段，使用`VirtualBaziProfile`
- [QGA V24.7] 优化格局名称匹配逻辑
  - 扩展关键词匹配字典，支持"枭神"和"夺食"作为独立关键词
  - 支持部分匹配和关键词匹配

### 2. core/models/profile_audit_model.py
**修改内容**:
- [QGA V24.7] 添加虚拟档案加载逻辑
  - 在`load_profile_by_id`中检查虚拟档案名称，从Pattern Lab重新生成以获取硬编码字段
  - 如果ProfileManager中找不到，尝试从Pattern Lab加载

### 3. core/models/pattern_engine_implementations.py
**修改内容**:
- [QGA V24.7 修复] `XiaoShenDuoShiEngine.vector_bias`
  - 在北方/近水环境下，水元素强制设定为+10.0（不再抵消）
  - 代码位置: 约374-382行
- [QGA V24.7] `ShangGuanJianGuanEngine.matching_logic`
  - 扩展匹配逻辑，支持"食神见官"组合（广义的伤官见官）
  - 代码位置: 约52-63行

### 4. core/models/llm_semantic_synthesizer.py
**修改内容**:
- [QGA V24.7] `_build_structured_data`
  - 优化格局引擎匹配逻辑（多层匹配：精确匹配 -> 部分匹配 -> 关键词匹配）
  - 代码位置: 约609-626行
- [QGA V24.7] `_construct_structured_prompt`
  - 添加"枭神夺食 + 北方/近水环境"的特殊因果映射规则
  - 代码位置: 约422-476行（prompt_suffix部分）

### 5. tests/pattern_lab.py
**修改内容**:
- [QGA V24.7] 添加`SHANG_GUAN_JIAN_GUAN`模板
  - 硬编码干支：庚申/丁亥/乙巳/庚辰
  - 日主：乙木
  - 代码位置: 约17-32行

## 新增的测试文件

### 1. tests/test_xiaoshen_duoshi_audit.py
- 枭神夺食专项审计测试

### 2. tests/test_xiaoshen_duoshi_fixed.py
- 枭神夺食修复验证测试

### 3. tests/test_shangguan_jianguan_lab.py
- 伤官见官虚拟靶机完整测试

### 4. tests/test_shangguan_jianguan_path_split.py
- 伤官见官逻辑路径自动分叉测试（已删除，需要重新创建）

## 新增的文档文件

### 1. docs/QGA_V24.7_XiaoShenDuoShi_Audit_Report.md
- 枭神夺食专项审计报告

### 2. docs/QGA_V24.7_XiaoShenDuoShi_Fix_Summary.md
- 枭神夺食三项修复总结

### 3. docs/QGA_V24.7_ShangGuanJianGuan_Lab_Summary.md
- 伤官见官虚拟靶机建模总结

### 4. docs/QGA_V24.7_Session_Summary.md
- 当前会话总结（本文档）

### 5. docs/QGA_V24.7_Code_Changes_Checklist.md
- 代码变更清单（本文件）

## 关键代码片段位置

### 格局名称匹配优化
**文件**: `controllers/profile_audit_controller.py`
**位置**: 约213-229行
```python
key_patterns = {
    '从儿格': '从儿格',
    '枭神夺食': '枭神夺食',
    '枭神': '枭神夺食',  # 支持"枭神"作为关键词
    '夺食': '枭神夺食',  # 支持"夺食"作为关键词
    # ...
}
```

### 水元素增强逻辑修复
**文件**: `core/models/pattern_engine_implementations.py`
**位置**: 约374-382行
```python
if geo_context in ["北方/北京", "近水环境"]:
    bias.water = max(0, bias.water) + 10.0  # 确保水元素正向膨胀
    bias.fire -= 5.0
```

### Prompt因果链强化
**文件**: `core/models/llm_semantic_synthesizer.py`
**位置**: 约422-476行（prompt_suffix部分）
```python
elif "枭神夺食" in active_patterns_str or "XIAO_SHEN_DUO_SHI" in str(structured_data):
    if "近水" in geo_context or "北方" in geo_context or "北京" in geo_context:
        prompt_suffix = f"""
【特别因果映射规则 - 枭神夺食 + 近水/北方环境】
- 物理逻辑：水势作为燃料供给拦截器（木/枭），使得拦截力持续增强...
```

## 待解决问题

1. **格局引擎匹配问题**: BaseVectorBias未计算（engines=0）
2. **LLM语义合成问题**: Persona未包含预期的关键语义
3. **测试性能问题**: 测试执行缓慢

## 注意事项

- LLM设置已更新，需要确认配置正确加载
- 测试脚本`test_shangguan_jianguan_path_split.py`已删除，需要重新创建
- 所有代码变更都标记了`[QGA V24.7]`注释

