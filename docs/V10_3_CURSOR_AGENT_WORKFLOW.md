# V10.3 Cursor智能体工作流完整指南

**版本**: V10.3  
**状态**: ✅ 已实现完整的"观察-思考-行动"循环

---

## 🎯 核心概念

你说得完全正确！**Cursor确实可以修改程序**，实现真正的自动化调优：

1. **自动调优脚本运行** → 生成诊断结果和代码变更建议
2. **通过MCP或终端日志** → 将上下文传递给Cursor
3. **Cursor读取上下文** → 理解问题并自动修改代码
4. **修改后继续执行** → 形成完整的自动化循环

---

## 🔄 完整工作流程

```
┌─────────────────┐
│ 运行智能体循环  │
│ (agent_loop.py) │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ [观察] 运行诊断  │
│ - 保存到        │
│   cursor_context│
│   .json         │
│ - 输出到终端    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ [思考] 分析问题  │
│ - 生成代码变更  │
│   建议          │
│ - 决定行动策略  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ [行动] 执行优化  │
│ - 参数优化:     │
│   自动执行      │
│ - 逻辑重构:     │
│   生成建议      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Cursor读取上下文│
│ - 读取终端日志  │
│ - 读取JSON文件  │
│ - 理解问题      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Cursor修改代码  │
│ - 根据建议修改  │
│ - 实施逻辑重构  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 重新运行循环     │
│ - 验证改进效果  │
│ - 继续优化      │
└─────────────────┘
```

---

## 📋 使用方式

### 方式1: 运行完整循环

```bash
python3 scripts/v10_3_cursor_agent_loop.py --mode auto
```

**输出**：
- 终端输出结构化的JSON信息（供Cursor读取）
- 保存上下文到 `config/cursor_context.json`
- 生成代码变更建议

### 方式2: 分阶段运行

```bash
# 只运行观察阶段
python3 scripts/v10_3_cursor_agent_loop.py --mode observation

# 只运行思考阶段
python3 scripts/v10_3_cursor_agent_loop.py --mode thinking

# 只运行行动阶段
python3 scripts/v10_3_cursor_agent_loop.py --mode action
```

---

## 📝 Cursor如何读取上下文

### 1. 读取终端日志

脚本会在终端输出结构化的JSON信息：

```json
================================================================================
📋 [CURSOR CONTEXT] 上下文信息（供Cursor读取）
================================================================================
{
  "timestamp": "2025-12-18T13:29:54.223297",
  "stage": "observation",
  "diagnosis": {
    "match_rate": 51.4,
    "main_issues": [...],
    "recommendations": [...]
  },
  "code_changes": [
    {
      "file": "core/engine_graph.py",
      "function": "calculate_strength_score",
      "change": "降低Special_Strong判定阈值或增强判定逻辑",
      "reason": "有9个案例被误判为Balanced"
    }
  ],
  "next_action": "modify_code"
}
================================================================================
```

**Cursor可以**：
- 读取终端输出
- 解析JSON信息
- 理解当前状态和需要的操作

### 2. 读取上下文文件

**文件位置**: `config/cursor_context.json`

**内容示例**:
```json
{
  "timestamp": "2025-12-18T13:29:54.223297",
  "stage": "result",
  "diagnosis": {
    "match_rate": 51.4,
    "total_cases": 91,
    "matched_cases": 45,
    "main_issues": [
      {
        "pattern": "Special_Strong → Balanced",
        "count": 9,
        "examples": [...]
      }
    ],
    "recommendations": [...]
  },
  "action_taken": "logic_refactoring_requested",
  "code_changes": [
    {
      "file": "core/engine_graph.py",
      "function": "calculate_strength_score",
      "change": "降低Special_Strong判定阈值或增强判定逻辑",
      "reason": "有9个案例被误判为Balanced"
    }
  ],
  "next_action": "modify_code",
  "status": "needs_attention"
}
```

**Cursor可以**：
- 读取JSON文件
- 理解诊断结果
- 根据代码变更建议修改代码

### 3. 根据上下文修改代码

当Cursor读取到上下文后，可以：

1. **理解问题**：
   - 匹配率51.4%，低于目标65%
   - 主要问题：Special_Strong → Balanced (9个案例)

2. **执行代码修改**：
   - 根据建议修改 `core/engine_graph.py`
   - 实施逻辑重构

3. **重新运行验证**：
   - 修改后，重新运行脚本
   - 验证改进效果

---

## 🚀 完整示例

### 步骤1: 运行智能体循环

```bash
python3 scripts/v10_3_cursor_agent_loop.py --mode auto
```

**输出示例**:
```
🔍 [观察] 运行物理诊断...
📊 当前匹配率: 51.4%

💭 [思考] 分析问题，制定策略...
💡 决策: logic_refactoring - 匹配率 51.4% 过低，需要逻辑重构
📝 建议的代码变更:
   - core/engine_graph.py: 降低Special_Strong判定阈值或增强判定逻辑

🚀 [行动] 执行: logic_refactoring
⚠️  需要逻辑重构，但代码修改需要Cursor执行
📝 已生成代码变更建议，请Cursor根据建议修改代码
```

### 步骤2: Cursor读取上下文

Cursor会看到：
- 终端输出的JSON信息
- `config/cursor_context.json` 文件
- 代码变更建议

### 步骤3: Cursor修改代码

Cursor根据建议修改代码，例如：
- 降低Special_Strong判定阈值
- 优化通根识别逻辑

### 步骤4: 重新运行验证

```bash
python3 scripts/v10_3_cursor_agent_loop.py --mode auto
```

验证改进效果，如果还有问题，继续循环。

---

## 💡 关键特性

### 1. 结构化输出

- ✅ JSON格式，便于Cursor解析
- ✅ 清晰的阶段标识（observation/thinking/action/result）
- ✅ 明确的下一步行动建议

### 2. 代码变更建议

- ✅ 明确指出需要修改的文件和函数
- ✅ 提供具体的修改建议
- ✅ 说明修改的原因

### 3. 状态跟踪

- ✅ 保存每次循环的状态
- ✅ 记录匹配率变化
- ✅ 跟踪代码变更历史

---

## 📊 上下文文件结构

```json
{
  "timestamp": "ISO格式时间戳",
  "stage": "observation|thinking|action|result|error",
  "diagnosis": {
    "match_rate": 51.4,
    "total_cases": 91,
    "matched_cases": 45,
    "main_issues": [
      {
        "pattern": "误判模式",
        "count": 案例数,
        "examples": [...]
      }
    ],
    "recommendations": ["优化建议1", "优化建议2"]
  },
  "action_taken": "已执行的操作",
  "code_changes": [
    {
      "file": "文件路径",
      "function": "函数名",
      "change": "修改建议",
      "reason": "修改原因"
    }
  ],
  "next_action": "下一步建议",
  "status": "ok|needs_attention|error"
}
```

---

## 🎯 最佳实践

1. **首次运行**：
   ```bash
   python3 scripts/v10_3_cursor_agent_loop.py --mode auto
   ```

2. **Cursor读取上下文**：
   - 查看终端输出
   - 读取 `config/cursor_context.json`

3. **Cursor修改代码**：
   - 根据代码变更建议修改代码
   - 实施逻辑重构

4. **重新运行验证**：
   ```bash
   python3 scripts/v10_3_cursor_agent_loop.py --mode auto
   ```

5. **持续循环**：
   - 如果匹配率仍低于目标，继续循环
   - 直到达到目标匹配率

---

## 🔗 相关文档

- `scripts/v10_3_cursor_agent_loop.py` - 智能体工作流源码
- `config/cursor_context.json` - 上下文文件（运行时生成）
- `docs/V10_2_AUTO_TUNING_ARCHITECTURE.md` - V10.2自动调优架构

