# QGA V24.7 下一步工作计划

## 立即需要处理的问题

### 1. 格局引擎匹配问题（高优先级）🔴

**问题描述**: 
- BaseVectorBias未计算，警告显示"engines=0, weighted_patterns=8/9"
- 说明格局引擎匹配失败，导致`pattern_engines_dict`为空

**需要检查**:
1. PFA引擎实际检测到的格局名称格式
   - 添加日志输出PFA检测到的所有格局名称
   - 检查格局名称是否包含emoji或特殊字符
   
2. PatternEngineRegistry中的注册名称
   - 检查`PatternEngine.pattern_name`属性
   - 确认注册的格局名称格式
   
3. 匹配逻辑
   - 检查`controllers/profile_audit_controller.py`中的匹配逻辑
   - 验证关键词匹配是否正确工作

**调试步骤**:
```python
# 在profile_audit_controller.py中添加调试日志
for pattern in patterns:
    pattern_name = pattern.get('name', '')
    logger.info(f"🔍 检测到格局: {pattern_name}")
    # ... 匹配逻辑 ...
    if engine:
        logger.info(f"✅ 匹配成功: {pattern_name} -> {engine.pattern_id}")
    else:
        logger.info(f"❌ 匹配失败: {pattern_name}")
```

### 2. LLM设置更新检查（高优先级）🔴

**用户说明**: 已修改LLM设置

**需要检查**:
1. LLM配置文件
   - 检查`utils/configuration_manager.py`或相关配置文件
   - 确认LLM模型名称和API URL是否正确读取
   
2. LLM客户端初始化
   - 检查`core/models/llm_semantic_synthesizer.py`中的客户端初始化
   - 确认新的配置是否正确应用

**验证步骤**:
```python
# 检查LLM配置加载
from utils.configuration_manager import get_config_manager
config = get_config_manager()
llm_model = config.get('llm_model_name', 'qwen2.5:2.5b')
llm_host = config.get('llm_host', 'http://localhost:11434')
print(f"LLM配置: model={llm_model}, host={llm_host}")
```

### 3. LLM语义合成优化（中优先级）🟡

**问题描述**:
- LLM生成的persona未包含预期的关键语义
- 实验A未包含"崩塌语义"，实验B未包含"转化语义"

**需要优化**:
1. Prompt因果映射规则
   - 添加"伤官见官"的特殊因果映射规则
   - 强化Few-shot示例
   
2. BaseVectorBias信息传递
   - 确保BaseVectorBias正确传递给LLM
   - 在Prompt中明确说明BaseVectorBias的物理含义

**修改位置**:
- `core/models/llm_semantic_synthesizer.py`
- `_construct_structured_prompt`方法

### 4. 测试脚本优化（中优先级）🟡

**问题描述**:
- 测试执行缓慢
- `test_shangguan_jianguan_path_split.py`已删除

**需要创建**:
1. 简化版本的测试脚本
   - 先验证BaseVectorBias计算（不使用LLM）
   - 再单独测试LLM语义合成
   
2. 添加调试信息
   - 输出格局名称、匹配结果、BaseVectorBias等关键信息
   - 方便快速定位问题

## 后续工作计划

### 阶段1：修复核心问题（预计1-2小时）

1. ✅ 修复格局引擎匹配问题
2. ✅ 验证LLM设置更新
3. ✅ 优化LLM语义合成

### 阶段2：完成逻辑路径分叉测试（预计1小时）

1. ✅ 重新创建测试脚本
2. ✅ 验证BaseVectorBias计算
3. ✅ 对比实验A和实验B的差异

### 阶段3：优化和文档（预计30分钟）

1. ✅ 优化测试性能
2. ✅ 更新文档
3. ✅ 代码审查和清理

## 关键代码位置参考

### 格局名称匹配
- `controllers/profile_audit_controller.py` (约213-229行)

### 格局引擎定义
- `core/models/pattern_engine_implementations.py` (约15-124行)

### LLM语义合成
- `core/models/llm_semantic_synthesizer.py` (约353-477行)

### Pattern Lab
- `tests/pattern_lab.py` (约17-32行，SHANG_GUAN_JIAN_GUAN模板)

## 测试命令

### 快速验证格局匹配
```bash
cd /home/jin/bazi_predict
python3 tests/test_shangguan_jianguan_lab.py
```

### 验证LLM配置
```bash
cd /home/jin/bazi_predict
python3 -c "
from utils.configuration_manager import get_config_manager
config = get_config_manager()
print('LLM Model:', config.get('llm_model_name', 'N/A'))
print('LLM Host:', config.get('llm_host', 'N/A'))
"
```

### 运行完整审计测试
```bash
cd /home/jin/bazi_predict
timeout 300 python3 tests/test_shangguan_jianguan_path_split.py
```

