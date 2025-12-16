# V79.0 自主优化流程（LSR/正则化框架）

## 📋 概述

V79.0 任务的目标是找到 **Level 1 算法中的最优普适参数集**，使 **总成本 Cost_Total** 最小化。

**优化框架：** LSR（Least Squares with Regularization）/ 正则化框架

**执行脚本：** `scripts/v79_autonomous_optimization_lsr.py`

---

## 🚀 五步自主优化流程

### 步骤一：前置准备与代码逻辑修复（强制）

在开始任何数值计算之前，必须确保算法骨架的完整性。

#### 1.1 逻辑修复

**Officer（官杀）能量计算公式验证：**

当前代码中，Officer 能量计算已经正确应用了 `ctl_imp`：

```python
# core/processors/domains.py (第 228-231 行)
officer_energy_boosted = officer_energy * (1.0 + ctl_imp)

# 返回时应用 particle weight (第 308 行)
'officer': officer_energy_boosted * officer_weight
```

**公式：** `E_Officer = E_Fire × (1 + ctl_imp) × officer_weight`

✅ **状态：** 已正确实现，无需修复

#### 1.2 参数部署

部署 **所有** Level 1 参数（约 **45** 个）的初始值、锚点和约束范围：

- **锚点（Anchor）：** 将 V32.0 参数表中的所有当前值，以及 TGD 初始值（7.5, 5.0, 3.0, 1.5），设置为 LSR 正则化的**拟合目标**
- **优化变量集：** 明确囊括所有 Level 1 参数（包括 TGD, ctl_imp, imp_base, pg_*, root_w, 等）

**参数分类：**

1. **基础场域（Physics）** - 4 个参数
   - `pg_year`, `pg_month`, `pg_day`, `pg_hour`

2. **粒子动态（Structure）** - 3 个参数
   - `root_w`, `exposed_b`, `same_pill`

3. **几何交互（Interactions）** - 10 个参数
   - `clashScore`, `harmPenalty`, `punishmentPenalty`, `clashDamping`
   - `trineBonus`, `halfBonus`, `archBonus`, `directionalBonus`, `resolutionCost`
   - `sixHarmony`

4. **能量流转（Flow）** - 7 个参数
   - `imp_base`, `imp_weak`
   - `vis_rate`, `vis_fric`, `vis_visc`
   - `ctl_imp`
   - `sys_ent`

5. **TGD 参数** - 4 个参数
   - `T_Main`, `T_Stem`, `T_Mid`, `T_Minor`

6. **其他 Level 1 参数** - 约 17 个参数
   - 能量阈值、墓库物理、基础事件分数等

---

### 步骤二：定义目标函数与成本计算

Cursor 必须计算包含 **正则化项** 的总成本，以平衡拟合度和参数的合理性。

#### 2.1 Cost_MAE（拟合成本）

运行批量校准脚本，计算所有案例的 **平均绝对误差（MAE）**：

```python
def _calculate_mae(self, config: Dict) -> Tuple[float, Dict]:
    """
    计算所有案例的 MAE
    """
    errors = []
    for case in self.cases:
        # 计算预测值和真实值的误差
        error = abs(pred_value - gt_value)
        errors.append(error)
    
    mae = np.mean(errors)
    return mae
```

#### 2.2 Cost_Plausibility（正则化成本）

计算当前参数集与 **优化锚点** 之间的偏差惩罚：

```python
def _calculate_regularization_penalty(self, params: Dict[str, float]) -> float:
    """
    正则化惩罚项
    Formula: λ * Σ(Parameter - Anchor)²
    """
    penalty = 0.0
    for param_name, param_value in params.items():
        anchor_value = self.level1_params[param_name]['anchor']
        deviation = param_value - anchor_value
        penalty += (deviation ** 2)
    
    return self.lambda_reg * penalty
```

#### 2.3 Cost_Total（总成本）

```python
Cost_Total = Cost_MAE + Cost_Plausibility
```

---

### 步骤三：计算梯度与方向（优化引擎）

Cursor 必须确定下一步参数调整的方向和幅度。

#### 3.1 梯度计算

计算 `Cost_Total` 相对于每一个优化变量的 **偏导数（梯度 ∇）**：

```python
def _calculate_gradient(self, params: Dict[str, float], param_name: str) -> float:
    """
    数值梯度计算（中心差分法）
    """
    epsilon = 0.01
    
    # 正向扰动
    temp_params_plus = params.copy()
    temp_params_plus[param_name] = current_value + epsilon
    cost_plus = self._calculate_total_cost(temp_params_plus)
    
    # 负向扰动
    temp_params_minus = params.copy()
    temp_params_minus[param_name] = current_value - epsilon
    cost_minus = self._calculate_total_cost(temp_params_minus)
    
    # 梯度
    gradient = (cost_plus - cost_minus) / (2 * epsilon)
    return gradient
```

#### 3.2 步长确定

根据梯度和预设的学习率，确定每个参数的 **调整步长**：

```python
step_size = learning_rate * gradient
```

---

### 步骤四：迭代更新参数并约束范围

#### 4.1 参数更新

将所有优化变量沿着 **负梯度方向** 进行更新：

```python
new_value = current_value - learning_rate * gradient
```

#### 4.2 范围硬约束

强制检查所有更新后的参数值，**必须** 位于预设的 **合理范围（Range）** 内：

```python
# 约束到范围
new_value = max(param_range[0], min(param_range[1], new_value))
```

#### 4.3 迭代

返回步骤二，开始下一次迭代。

---

### 步骤五：收敛判定与最终报告

Cursor 必须在满足科学和效率的条件下停止迭代。

#### 5.1 收敛检查

当满足以下任一条件时，停止迭代：

1. **目标达成：** MAE 持续低于 **5.0**
2. **变化微小：** 在连续 **N** 次迭代中，MAE 的变化量低于 **0.01**

```python
def _check_convergence(self, history: List[Dict]) -> Tuple[bool, str]:
    """
    收敛判定
    """
    # 检查目标达成
    if all(mae < 5.0 for mae in recent_maes):
        return True, "目标达成：MAE 持续低于 5.0"
    
    # 检查变化微小
    if all(change < 0.01 for change in mae_changes):
        return True, "变化微小：连续 N 次迭代中 MAE 变化量低于 0.01"
    
    return False, ""
```

#### 5.2 最终报告

提交最终收敛的 **45** 个 **Level 1 最优参数集** 和最终的 **MAE** 值。

**报告内容包括：**

- 最佳 MAE 值
- 最优参数集（所有 45 个参数）
- 优化历史（每次迭代的 MAE 和成本）
- 参数变化摘要（显示变化最大的参数）
- 收敛状态和原因

---

## 📊 使用方法

### 运行优化脚本

```bash
cd scripts
python v79_autonomous_optimization_lsr.py
```

### 配置参数

优化器支持以下可调参数（在脚本中修改）：

- `lambda_reg`: 正则化系数（默认 0.01）
- `learning_rate`: 学习率（默认 0.01）
- `mae_target`: 目标 MAE（默认 5.0）
- `mae_change_threshold`: MAE 变化阈值（默认 0.01）
- `convergence_window`: 收敛窗口大小（默认 5）
- `max_iterations`: 最大迭代次数（默认 100）

### 输出结果

优化结果将保存到 `docs/V79_OPTIMIZATION_RESULT_<timestamp>.json`

---

## 🔍 关键特性

1. **LSR 正则化框架：** 平衡拟合度和参数合理性
2. **梯度下降优化：** 使用数值梯度计算，沿负梯度方向更新参数
3. **范围硬约束：** 确保所有参数在合理范围内
4. **自动收敛判定：** 支持目标达成和变化微小两种收敛条件
5. **完整历史记录：** 记录每次迭代的详细状态

---

## 📝 注意事项

1. **Officer 能量计算：** 已正确实现，公式为 `E_Officer = E_Fire × (1 + ctl_imp) × officer_weight`
2. **参数锚点：** 所有参数锚点基于 V32.0 参数表
3. **TGD 参数：** 初始值为 7.5, 5.0, 3.0, 1.5，优化范围 ±50%
4. **批量校准：** 需要 `data/calibration_cases.json` 文件

---

**报告生成时间：** V79.0  
**优化框架：** LSR/正则化  
**目标：** MAE < 5.0

