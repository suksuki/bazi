# V10.2 自动调优架构：Agentic Bazi Tuner

**版本**: V10.2  
**架构**: Optuna (TPE + Pruning) + MCP (Model Context Protocol) + Agent Loop  
**状态**: ✅ 已完成核心实现

---

## 🏛️ 架构概览

V10.2 自动调优系统是一个**"LLM-Guided Optimization"（大模型引导优化）**架构，将传统的参数优化升级为**"Agentic Workflow（智能体工作流）"**。

### 核心组件

```
┌─────────────────┐
│  Cursor (Brain) │  ← LLM智能体，负责"思考"和"决策"
└────────┬────────┘
         │ MCP Protocol
         ↓
┌─────────────────┐
│  MCP Server     │  ← 提供工具接口（Tools）
│  (v10_2_mcp_    │     - run_physics_diagnosis()
│   server.py)    │     - configure_optimization_strategy()
└────────┬────────┘     - execute_optuna_study()
         │
         ↓
┌─────────────────┐
│  Optuna Tuner   │  ← 负责参数搜索的"微操"
│  (v10_2_optuna_ │     - TPE (Tree-structured Parzen Estimator)
│   tuner.py)     │     - Pruning (自动剪枝)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  V10 Engine     │  ← 物理引擎（实际计算）
│  (Physics)      │
└─────────────────┘
```

---

## 🛠️ 核心功能

### 1. Optuna优化内核 (`v10_2_optuna_tuner.py`)

#### StrengthOptimizationObjective

**职责**: 定义优化目标函数

**核心特性**:
- ✅ **加权损失函数**: 经典案例3倍权重
- ✅ **贝叶斯先验惩罚**: 物理常识软约束（如`hour_weight > month_weight`会被惩罚）
- ✅ **分层参数空间**: 支持Physics/Structure/Threshold分层优化
- ✅ **Pruning支持**: 自动剪枝低质量试验

**Loss Function**:
```
loss = (1 - weighted_match_rate) + bayesian_penalty
```

**贝叶斯惩罚项**:
- `hour_weight > month_weight`: 惩罚系数 100.0
- `rootingWeight > 3.0`: 惩罚系数 50.0
- `samePillarBonus > 2.5`: 惩罚系数 50.0

#### 使用示例

```python
from scripts.v10_2_optuna_tuner import run_optuna_study, OptimizationConfig

config = OptimizationConfig(
    focus_layer="threshold",  # 只优化阈值层
    constraints="soft",       # 软约束（惩罚项）
    n_trials=50
)

result = run_optuna_study(tuner, config, base_config)
print(f"最佳匹配率: {result['best_match_rate']:.1f}%")
```

---

### 2. MCP服务器 (`v10_2_mcp_server.py`)

#### MCPTuningServer

**职责**: 为LLM/Cursor提供工具接口

#### 工具函数

##### 1. `run_physics_diagnosis()`

**功能**: 运行全量回归测试，返回诊断报告

**返回**:
```python
{
    'current_match_rate': 50.0,
    'total_cases': 91,
    'matched_cases': 45,
    'main_issues': [
        {
            'pattern': 'Weak → Follower',
            'count': 4,
            'examples': [...]
        }
    ],
    'violation_summary': {
        'has_violations': False,
        'violations': []
    },
    'recommendations': [
        '从格判定问题: 建议调优follower_threshold'
    ],
    'nl_description': '自然语言描述（供LLM理解）'
}
```

##### 2. `configure_optimization_strategy()`

**功能**: 设定Optuna搜索空间

**参数**:
- `focus_layer`: "physics" | "structure" | "threshold" | "all"
- `constraints`: "strict" | "soft"
- `target_case_type`: "classic" | "modern" | "all"

##### 3. `execute_optuna_study()`

**功能**: 启动Optuna优化

**参数**:
- `n_trials`: 试验次数
- `timeout`: 超时时间（秒）

**返回**:
```python
{
    'status': 'completed',
    'best_match_rate': 52.0,
    'best_loss': 0.48,
    'best_params': {...},
    'improvement': 2.0  # 相对于基线的提升
}
```

#### 使用示例

```python
from scripts.v10_2_mcp_server import MCPTuningServer

server = MCPTuningServer()

# 1. 诊断
diagnosis = server.run_physics_diagnosis()
print(diagnosis['nl_description'])

# 2. 配置策略
server.configure_optimization_strategy(
    focus_layer="threshold",
    constraints="soft"
)

# 3. 执行优化
result = server.execute_optuna_study(n_trials=50)
print(f"最佳匹配率: {result['best_match_rate']:.1f}%")
```

---

### 3. 自动驾驶主程序 (`v10_2_auto_driver.py`)

#### AutoDriver

**职责**: 实现"观察-思考-行动"的智能调优循环

#### 分层锁定策略

**Phase 1: 物理层调优**
- 目标: 优化月令、时柱等基础权重
- 锁定条件: 匹配率 ≥ 47.0%

**Phase 2: 结构层调优**
- 目标: 优化通根、透干、同柱等结构参数
- 锁定条件: 匹配率 ≥ 49.0%
- 前提: Phase 1已锁定

**Phase 3: 阈值微调**
- 目标: 微调energy_threshold_center、follower_threshold等
- 前提: Phase 1和Phase 2已锁定

#### 使用示例

```bash
# 完整自动调优（推荐）
python3 scripts/v10_2_auto_driver.py --mode auto

# 只运行Phase 1
python3 scripts/v10_2_auto_driver.py --mode phase1 --phase1-trials 50

# 自定义试验次数
python3 scripts/v10_2_auto_driver.py --mode auto \
    --phase1-trials 100 \
    --phase2-trials 100 \
    --phase3-trials 100
```

---

## 🔄 Agent Loop (智能体循环)

### "观察-思考-行动"循环

```
1. 观察 (Context Injection)
   └─> Cursor调用 run_physics_diagnosis()
       └─> 返回: "当前准确率 50%。主要问题：乔丹（从格）判成了身弱。"

2. 思考 (LLM Reasoning)
   └─> Cursor分析: "乔丹是标准从格。现在判成身弱，说明follower_threshold太低。
                    下一步应该锁定物理层，专门调优阈值层。"

3. 行动 (Action)
   └─> Cursor调用 configure_optimization_strategy(focus_layer="threshold")
   └─> Cursor调用 execute_optuna_study(n_trials=50)

4. 反馈与迭代
   └─> Optuna返回: "找到新参数，乔丹修正成功，但马斯克错了。"
   └─> 回到步骤1，继续优化...
```

---

## 📊 优势分析

### 为什么这个方案是"降维打击"？

1. **Optuna负责"微操"**
   - 擅长在0.289和0.291之间找最优解
   - 这是人脑和LLM做不到的

2. **LLM/Cursor负责"战略"**
   - 擅长判断"现在是物理层歪了"还是"阈值没卡对"
   - 这是数学算法做不到的

3. **MCP负责"连接"**
   - 让两者实时对话
   - 实现真正的"人机协作"

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install optuna  # 如果还没有安装
```

### 2. 运行测试

在开始调优前，建议先运行测试确保系统正常：

```bash
# 运行V10.2自动调优系统测试
python3 tests/test_v10_2_auto_tuning.py

# 或使用pytest（如果已安装）
pytest tests/test_v10_2_auto_tuning.py -v
```

详细测试文档请参考：`docs/V10_2_AUTO_TUNING_TESTING.md`

### 2. 测试Optuna优化器

```bash
# 测试当前配置
python3 scripts/v10_2_optuna_tuner.py --mode test

# 优化阈值层（50次试验）
python3 scripts/v10_2_optuna_tuner.py --mode tune --layer threshold --trials 50
```

### 3. 测试MCP服务器

```bash
python3 scripts/v10_2_mcp_server.py
```

### 4. 运行自动调优

```bash
# 完整流程（推荐）
python3 scripts/v10_2_auto_driver.py --mode auto

# 只运行Phase 1（快速测试）
python3 scripts/v10_2_auto_driver.py --mode phase1 --phase1-trials 20
```

---

## 📝 使用场景

### 场景1: 快速验证新参数

```bash
# 只优化阈值层，快速验证效果
python3 scripts/v10_2_optuna_tuner.py --mode tune --layer threshold --trials 30
```

### 场景2: 完整自动调优

```bash
# 完整三层调优，自动保存配置
python3 scripts/v10_2_auto_driver.py --mode auto \
    --phase1-trials 100 \
    --phase2-trials 100 \
    --phase3-trials 100
```

### 场景3: 通过MCP与Cursor对话

```python
# 在Python脚本或交互式环境中
from scripts.v10_2_mcp_server import MCPTuningServer

server = MCPTuningServer()

# Cursor可以调用这些方法
diagnosis = server.run_physics_diagnosis()
print(diagnosis['nl_description'])

# 根据诊断结果决定下一步
if '从格' in diagnosis['nl_description']:
    server.configure_optimization_strategy(focus_layer="threshold")
    result = server.execute_optuna_study(n_trials=50)
```

---

## ⚙️ 配置说明

### OptimizationConfig

```python
@dataclass
class OptimizationConfig:
    focus_layer: str = "all"      # "physics" | "structure" | "threshold" | "all"
    constraints: str = "soft"     # "strict" | "soft"
    target_case_type: str = "all" # "classic" | "modern" | "all"
    n_trials: int = 50            # Optuna试验次数
    timeout: Optional[float] = None  # 超时时间（秒）
    pruner_enabled: bool = True   # 是否启用Pruning
    verbose: bool = True          # 是否输出详细信息
```

---

## 🔍 故障排除

### 问题1: "请安装 optuna"

**解决**:
```bash
pip install optuna
```

### 问题2: 优化结果不理想

**建议**:
1. 增加试验次数（`--trials 100`）
2. 检查数据集是否包含足够案例
3. 查看诊断报告，了解主要问题

### 问题3: 优化时间过长

**建议**:
1. 减少试验次数
2. 使用分层优化（只优化指定层）
3. 启用Pruning（默认已启用）

---

## 📚 相关文档

- **调优计划**: `docs/V10_STRENGTH_TUNING_PLAN.md`
- **调优工作流**: `docs/V10_STRENGTH_TUNING_WORKFLOW.md`
- **调优结果**: `docs/V10_STRENGTH_TUNING_RESULTS_NEW_DATASET.md`
- **核心分析师建议**: `docs/V10_STRENGTH_TUNING_ANALYST_REVIEW.md`

---

## 🎯 V10.2 核心分析师Final Review补充

### 1. 💾 参数时光机 (Parameter Time Machine)

**实现**: ✅ 已完成

- **Checkpoints机制**: 每个Phase完成后自动保存到 `config/checkpoints/v10.2_phaseX_timestamp.json`
- **Auto-Rollback**: 如果后续Phase导致性能下降超过阈值（默认2%），自动回滚到上一个Phase的Checkpoint
- **使用场景**: 防止Phase 3过度调优导致Phase 1/2的性能回退

### 2. 📊 物理一致性仪表盘 (Physics Consistency Dashboard)

**实现**: ✅ 已完成

在 `run_physics_diagnosis()` 的诊断报告中增加物理一致性指标：

- **Month Dominance Ratio**: 月令权重 / 时柱权重（应 > 1.5）
  - 如果 < 1.5，状态为 `warning`，表示违反物理直觉
  
- **Rooting Impact Factor**: 通根影响因子（应 > 2.0）
  - 估算有根案例与无根案例的得分比
  - 如果 < 2.0，状态为 `warning`

**目的**: 防止AI为了拟合数据，搞出"时柱比月令重"这种反物理的参数组合。

### 3. 🧪 压力测试模式 (Stress Test Mode)

**实现**: ✅ 已完成

在 `OptimizationConfig` 中添加交叉验证选项：

```python
config = OptimizationConfig(
    cross_validation=True,  # 启用交叉验证
    cv_train_ratio=0.7      # 70%训练集，30%验证集
)
```

**机制**:
- 将案例随机切分为训练集和验证集
- 在训练集上优化参数
- 在验证集上评估性能（防止过拟合）

---

## 🎯 未来扩展

### 1. MCP协议集成

将MCP服务器集成到实际的MCP协议中，让Cursor可以直接调用这些工具。

### 2. 多目标优化

支持同时优化"准确率"和"稳定性"（参数变动小）。

### 3. 自适应策略

根据诊断结果自动选择优化策略，无需人工配置。

---

**维护者**: Bazi Predict Team  
**最后更新**: 2025-01-XX  
**核心分析师Review**: ✅ 已批准并实施所有补充建议

