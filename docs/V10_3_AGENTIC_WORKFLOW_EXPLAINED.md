# V10.3 Agentic Workflow（智能体工作流）完整机制说明

**版本**: V10.3  
**状态**: ✅ 已完全实现  
**创建日期**: 2025-12-18

---

## 🎯 什么是Agentic Workflow？

**Agentic Workflow（智能体工作流）**是一种**自动化的"观察-思考-行动"循环**，让AI（Cursor）能够：

1. **观察**：自动运行诊断，发现问题
2. **思考**：分析问题，制定解决方案
3. **行动**：执行优化或生成代码修改建议
4. **反馈**：验证效果，持续迭代

**核心价值**：将手动调优过程自动化，形成闭环优化系统。

---

## 🔄 完整工作流程机制

### 流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    Agentic Workflow 循环                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐
│ 阶段1: 观察      │
│ (Observation)   │
└────────┬────────┘
         │
         ↓
    ┌─────────────────────────────┐
    │ 1. 运行物理诊断              │
    │    - MCPTuningServer        │
    │      .run_physics_diagnosis()│
    │    - 评估所有案例            │
    │    - 计算匹配率              │
    │    - 识别误判模式            │
    └────────┬────────────────────┘
             │
             ↓
    ┌─────────────────────────────┐
    │ 2. 保存上下文                │
    │    - 写入 cursor_context.json│
    │    - 输出到终端（JSON格式）  │
    │    - 包含诊断结果和状态      │
    └────────┬────────────────────┘
             │
             ↓
┌─────────────────┐
│ 阶段2: 思考      │
│ (Thinking)      │
└────────┬────────┘
         │
         ↓
    ┌─────────────────────────────┐
    │ 1. 分析诊断结果              │
    │    - 匹配率 < 55%?          │
    │      → 需要逻辑重构         │
    │    - 匹配率 55-65%?         │
    │      → 尝试参数优化         │
    │    - 匹配率 >= 65%?         │
    │      → 已达到目标           │
    └────────┬────────────────────┘
             │
             ↓
    ┌─────────────────────────────┐
    │ 2. 生成代码变更建议          │
    │    - 分析主要误判模式        │
    │    - 确定需要修改的文件      │
    │    - 提供具体修改建议        │
    └────────┬────────────────────┘
             │
             ↓
    ┌─────────────────────────────┐
    │ 3. 制定行动策略              │
    │    - logic_refactoring      │
    │    - parameter_tuning       │
    │    - done                   │
    └────────┬────────────────────┘
             │
             ↓
┌─────────────────┐
│ 阶段3: 行动      │
│ (Action)        │
└────────┬────────┘
         │
         ↓
    ┌─────────────────────────────┐
    │ 判断行动类型                  │
    └──┬──────────────────────┬───┘
       │                      │
       ↓                      ↓
┌─────────────┐      ┌─────────────┐
│ 参数优化     │      │ 逻辑重构     │
│ (可自动执行) │      │ (需要Cursor) │
└──────┬──────┘      └──────┬──────┘
       │                     │
       ↓                     ↓
┌─────────────┐      ┌─────────────┐
│ 执行Optuna   │      │ 生成代码变更 │
│ 自动调优     │      │ 建议并保存   │
│              │      │ 到上下文     │
└──────┬──────┘      └──────┬──────┘
       │                     │
       └──────────┬──────────┘
                  ↓
┌─────────────────────────────────┐
│ 阶段4: 反馈 (Feedback)          │
│                                 │
│ 1. 保存最终结果到上下文         │
│ 2. 输出到终端（JSON格式）       │
│ 3. 等待Cursor读取并响应         │
└─────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────┐
│ Cursor读取上下文                │
│                                 │
│ 1. 读取终端日志（JSON）         │
│ 2. 读取 cursor_context.json     │
│ 3. 理解问题和建议               │
└────────────────┬────────────────┘
                 │
                 ↓
┌─────────────────────────────────┐
│ Cursor修改代码                  │
│                                 │
│ 1. 根据建议修改代码             │
│ 2. 实施逻辑重构                 │
│ 3. 保存修改                     │
└────────────────┬────────────────┘
                 │
                 ↓
┌─────────────────────────────────┐
│ 重新运行循环                     │
│                                 │
│ python3 scripts/v10_3_         │
│   cursor_agent_loop.py          │
│   --mode auto                   │
└─────────────────────────────────┘
                 │
                 ↓
            (继续循环...)
```

---

## 📋 详细机制说明

### 阶段1: 观察 (Observation)

**目标**：收集当前系统状态

**执行步骤**：

1. **运行物理诊断**
   ```python
   diagnosis = server.run_physics_diagnosis()
   ```
   - 评估所有校准案例
   - 计算当前匹配率
   - 识别误判模式（如 "Special_Strong → Balanced"）
   - 生成优化建议

2. **保存上下文**
   ```python
   save_context_for_cursor(
       stage='observation',
       diagnosis=diagnosis,
       next_action='analyze_diagnosis'
   )
   ```
   - 保存到 `config/cursor_context.json`
   - 输出结构化JSON到终端
   - 供Cursor读取和分析

**输出示例**：
```json
{
  "stage": "observation",
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
    ]
  },
  "next_action": "analyze_diagnosis"
}
```

---

### 阶段2: 思考 (Thinking)

**目标**：分析问题，制定策略

**执行步骤**：

1. **分析诊断结果**
   ```python
   if match_rate < 55.0:
       # 需要逻辑重构
       decision['action_type'] = 'logic_refactoring'
   elif match_rate < 65.0:
       # 尝试参数优化
       decision['action_type'] = 'parameter_tuning'
   else:
       # 已达到目标
       decision['action_type'] = 'done'
   ```

2. **生成代码变更建议**
   ```python
   if 'Special_Strong → Balanced' in pattern:
       decision['code_changes_needed'].append({
           'file': 'core/engine_graph.py',
           'function': 'calculate_strength_score',
           'change': '降低Special_Strong判定阈值或增强判定逻辑',
           'reason': f'有{count}个案例被误判为Balanced'
       })
   ```

3. **保存决策上下文**
   - 包含决策理由
   - 包含代码变更建议
   - 明确下一步行动

**输出示例**：
```json
{
  "stage": "thinking",
  "diagnosis": {...},
  "code_changes": [
    {
      "file": "core/engine_graph.py",
      "function": "calculate_strength_score",
      "change": "降低Special_Strong判定阈值",
      "reason": "有9个案例被误判为Balanced"
    }
  ],
  "next_action": "logic_refactoring"
}
```

---

### 阶段3: 行动 (Action)

**目标**：执行优化策略

#### 场景A: 参数优化 (Parameter Tuning)

**自动执行**：
```python
if decision['action_type'] == 'parameter_tuning':
    result = driver.run_full_auto(
        phase1_trials=50,  # 物理层调优
        phase2_trials=50,  # 结构层调优
        phase3_trials=50   # 阈值微调
    )
```

**执行过程**：
1. Phase 1: 调优物理层参数（如 `energy_threshold_center`）
2. Phase 2: 调优结构层参数（如 `samePillarBonus`）
3. Phase 3: 调优阈值参数（如 `follower_threshold`）
4. 保存最优配置到 `config/parameters.json`

#### 场景B: 逻辑重构 (Logic Refactoring)

**需要Cursor参与**：
```python
if decision['action_type'] == 'logic_refactoring':
    # 生成代码变更建议
    action_result['code_changes_made'] = decision['code_changes_needed']
    # 保存上下文，等待Cursor读取
    save_context_for_cursor(
        stage='action',
        code_changes=decision['code_changes_needed'],
        next_action='modify_code'
    )
```

**Cursor的任务**：
1. 读取 `cursor_context.json`
2. 根据建议修改代码
3. 实施逻辑重构
4. 保存修改

---

### 阶段4: 反馈 (Feedback)

**目标**：验证效果，准备下一轮循环

**执行步骤**：

1. **重新诊断**
   ```python
   final_diagnosis = server.run_physics_diagnosis()
   ```

2. **保存最终结果**
   ```python
   save_context_for_cursor(
       stage='result',
       diagnosis=final_diagnosis,
       action_taken=action_result['action_type'],
       code_changes=action_result.get('code_changes_made', []),
       next_action='review_result' if needs_attention else 'done'
   )
   ```

3. **输出最终状态**
   - 匹配率变化
   - 是否需要继续优化
   - 下一步建议

---

## 🔗 Cursor如何参与循环？

### 1. Cursor读取上下文

**方式A: 读取终端日志**
```bash
python3 scripts/v10_3_cursor_agent_loop.py --mode auto
```
Cursor会看到终端输出的JSON格式上下文。

**方式B: 读取JSON文件**
```python
# Cursor可以读取
config/cursor_context.json
```

### 2. Cursor理解问题

从上下文中，Cursor可以理解：
- 当前匹配率（如 51.4%）
- 主要问题（如 "Special_Strong → Balanced" 有9个案例）
- 代码变更建议（如 "降低Special_Strong判定阈值"）

### 3. Cursor修改代码

根据建议，Cursor可以：
```python
# 例如：修改 core/engine_graph.py
# 降低Special_Strong判定阈值从0.75到0.70
if self_team_ratio > 0.70:  # 从0.75降低到0.70
    # ... Special_Strong判定逻辑
```

### 4. Cursor触发下一轮循环

修改代码后，Cursor可以：
```bash
# 重新运行循环
python3 scripts/v10_3_cursor_agent_loop.py --mode auto
```

---

## 🎯 实际运行示例

### 示例1: 完整循环（参数优化）

```bash
$ python3 scripts/v10_3_cursor_agent_loop.py --mode auto

🔍 [观察] 运行物理诊断...
📊 当前匹配率: 58.2%

💭 [思考] 分析问题，制定策略...
💡 决策: parameter_tuning - 匹配率 58.2% 接近目标，尝试参数优化

🚀 [行动] 执行: parameter_tuning
🔧 执行参数优化...
   Phase 1: 物理层调优... ✅
   Phase 2: 结构层调优... ✅
   Phase 3: 阈值微调... ✅
✅ 参数优化完成，新匹配率: 63.5%

📊 智能体工作流完成
最终匹配率: 63.5%
状态: success
```

### 示例2: 完整循环（逻辑重构）

```bash
$ python3 scripts/v10_3_cursor_agent_loop.py --mode auto

🔍 [观察] 运行物理诊断...
📊 当前匹配率: 51.4%

💭 [思考] 分析问题，制定策略...
💡 决策: logic_refactoring - 匹配率 51.4% 过低，需要逻辑重构
📝 建议的代码变更:
   - core/engine_graph.py: 降低Special_Strong判定阈值或增强判定逻辑

🚀 [行动] 执行: logic_refactoring
⚠️  需要逻辑重构，但代码修改需要Cursor执行
📝 已生成代码变更建议，请Cursor根据建议修改代码

📊 智能体工作流完成
最终匹配率: 51.4%
状态: success

⚠️  需要Cursor关注:
   - 需要修改代码进行逻辑重构
   - 请查看 config/cursor_context.json 了解详情
   - 修改代码后，重新运行此脚本
```

**然后Cursor执行**：
1. 读取 `config/cursor_context.json`
2. 根据建议修改代码
3. 重新运行脚本验证效果

---

## 💡 关键特性

### 1. 自动化程度

- ✅ **参数优化**：完全自动化（Optuna自动调优）
- ⚠️ **逻辑重构**：半自动化（生成建议，Cursor执行）

### 2. 上下文传递

- ✅ **终端输出**：结构化JSON，便于Cursor解析
- ✅ **文件保存**：`cursor_context.json`，持久化存储
- ✅ **状态跟踪**：每次循环保存状态和历史

### 3. 决策智能

- ✅ **自适应策略**：根据匹配率自动选择策略
- ✅ **问题分析**：自动识别主要误判模式
- ✅ **代码建议**：生成具体的代码修改建议

---

## 🚀 使用方式

### 方式1: 完整自动循环

```bash
python3 scripts/v10_3_cursor_agent_loop.py --mode auto
```

**适合场景**：
- 首次运行诊断
- 需要完整优化流程
- 参数优化场景

### 方式2: 分阶段运行

```bash
# 只运行观察阶段
python3 scripts/v10_3_cursor_agent_loop.py --mode observation

# 只运行思考阶段（需要先运行observation）
python3 scripts/v10_3_cursor_agent_loop.py --mode thinking

# 只运行行动阶段（需要先运行observation和thinking）
python3 scripts/v10_3_cursor_agent_loop.py --mode action
```

**适合场景**：
- 调试特定阶段
- 手动控制流程
- 理解各阶段逻辑

---

## 📊 上下文文件结构

完整上下文文件示例：

```json
{
  "timestamp": "2025-12-18T13:29:54.320181",
  "stage": "result",
  "diagnosis": {
    "match_rate": 51.4,
    "total_cases": 91,
    "matched_cases": 45,
    "main_issues": [
      {
        "pattern": "Special_Strong → Balanced",
        "count": 9,
        "examples": [
          {"name": "毛泽东", "score": 65.4},
          {"name": "张学良", "score": 70.9}
        ]
      }
    ],
    "recommendations": [
      "身强误判为弱: Special_Strong → Weak (6个案例)。建议：降低energy_threshold_center"
    ]
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

---

## ✅ 总结

**Agentic Workflow已经完全实现**，它是一个：

1. **自动化循环**：观察 → 思考 → 行动 → 反馈
2. **智能决策**：根据匹配率自动选择策略
3. **上下文传递**：通过JSON文件和终端日志传递信息
4. **Cursor集成**：Cursor可以读取上下文并修改代码
5. **持续优化**：形成闭环，持续提升匹配率

**核心价值**：将手动调优过程自动化，让AI和人类协作，实现持续优化。

