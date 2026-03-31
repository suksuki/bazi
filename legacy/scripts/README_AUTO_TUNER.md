# 自动调优脚本使用说明

## 概述

`auto_tuner.py` 是基于爬山算法（Hill Climbing）的自动参数优化脚本，用于优化 Antigravity 系统中的算法参数。

## 功能特点

- ✅ 支持 Layer 1（微观物理层）和 Layer 2（宏观投影层）参数调优
- ✅ 使用爬山算法自动寻找最优参数组合
- ✅ 自动保存优化后的参数配置
- ✅ 生成详细的优化报告

## 使用方法

### 1. 准备测试数据

脚本需要测试案例数据文件。支持以下两种方式：

#### 方式一：使用 `data/golden_cases.json`（推荐）

创建 `data/golden_cases.json` 文件，格式如下：

```json
[
  {
    "id": "MA_YUN",
    "desc": "马云 - 极弱食伤制杀格，大富",
    "bazi": ["甲辰", "甲戌", "丁酉", "辛丑"],
    "day_master": "丁",
    "gender": "男",
    "labels": {
      "strength": "Weak",
      "wealth_score": 95.0,
      "career_score": 90.0,
      "relationship_score": 40.0
    }
  },
  {
    "id": "NORMAL_PERSON",
    "desc": "普通人 - 身弱财旺，积蓄少",
    "bazi": ["甲子", "丙子", "戊寅", "壬戌"],
    "day_master": "戊",
    "gender": "男",
    "labels": {
      "strength": "Weak",
      "wealth_score": 30.0,
      "career_score": 20.0,
      "relationship_score": 50.0
    }
  }
]
```

**字段说明**：
- `id`: 案例唯一标识
- `bazi`: 八字列表 [年柱, 月柱, 日柱, 时柱]
- `day_master`: 日主天干
- `gender`: 性别（"男" 或 "女"）
- `labels`: 真实标签（Ground Truth）
  - `strength`: 身强身弱（"Strong" 或 "Weak"）
  - `wealth_score`: 财富得分（0-100）
  - `career_score`: 事业得分（0-100）
  - `relationship_score`: 感情得分（0-100）

#### 方式二：使用现有的 `calibration_cases.json`

如果 `data/golden_cases.json` 不存在，脚本会自动尝试使用项目根目录下的 `calibration_cases.json`。

### 2. 运行脚本

```bash
cd scripts
python auto_tuner.py
```

### 3. 查看结果

优化完成后，脚本会：

1. **保存优化后的参数**到 `config/optimized_parameters.json`
2. **打印优化报告**，包括：
   - 初始损失 vs 最优损失
   - 损失下降百分比
   - 关键参数的变化

## 参数调优范围

脚本会自动调整以下关键参数：

### Layer 1（微观物理层）

- **基础场域**：`pillarWeights` (年/月/日/时权重)
- **粒子动态**：`rootingWeight`, `exposedBoost`, `samePillarBonus`, `voidPenalty`
- **几何交互**：合化阈值、三合/三会倍率、墓库物理参数
- **能量流转**：阻抗、粘滞、熵增、能量阈值

### Layer 2（宏观投影层）

- **时空修正**：`luckPillarWeight`（大运权重）

所有参数都有预设的范围和步长，确保调优过程稳定可控。

## 优化策略

脚本使用**爬山算法**（Hill Climbing）：

1. 从默认参数开始
2. 随机选择一个参数进行微调（±step）
3. 评估新参数的性能（计算损失）
4. 如果损失降低，保留新参数；否则回滚
5. 重复 N 次迭代

## 损失函数

总损失 = w1 × (预测身强 - 真实身强)² + w2 × (预测财富 - 真实财富)² + w3 × (预测事业 - 真实事业)² + w4 × (预测感情 - 真实感情)²

默认权重：
- 身强：1.0（最重要）
- 财富：0.5
- 事业：0.5
- 感情：0.3

## 注意事项

1. **测试数据质量**：确保测试案例的 Ground Truth 准确，否则优化会朝着错误方向进行
2. **迭代次数**：默认 100 次迭代，可以根据需要调整 `max_iterations` 参数
3. **计算时间**：每次迭代需要运行所有测试案例，如果案例很多可能需要较长时间
4. **参数备份**：优化前建议备份 `config/parameters.json`

## 高级用法

### 自定义损失权重

在脚本中修改 `loss_weights`：

```python
optimizer = HillClimbingOptimizer(
    param_manager, 
    engine_wrapper, 
    test_cases,
    loss_weights={
        'strength': 2.0,      # 更重视身强身弱
        'wealth': 1.0,
        'career': 0.8,
        'relationship': 0.2,
    }
)
```

### 调整迭代次数

```python
best_params, best_loss, history = optimizer.optimize(
    max_iterations=200,  # 增加迭代次数以获得更好的结果
    verbose=True
)
```

### 只调优特定参数

修改 `ParameterManager.tunable_params`，只保留需要调优的参数。

## 故障排除

**问题：找不到测试数据文件**
- 确保 `data/golden_cases.json` 或 `calibration_cases.json` 存在
- 检查文件路径和格式是否正确

**问题：优化没有改进**
- 检查测试数据是否准确
- 尝试增加迭代次数
- 检查参数范围是否合理

**问题：计算时间过长**
- 减少测试案例数量
- 减少迭代次数
- 只调优最关键的参数

## 参考资料

- 《Antigravity 核心调优总纲 V1.0》
- `QUANTUM_LAB_SIDEBAR_PARAMETERS_CONFIG.md` - 参数配置文档

