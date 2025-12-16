# V29.0 Task 74: 对齐状态报告

## 📊 当前对齐状态

### ✅ V29.0 参数对齐

| 参数 | 当前值 | 预期值 | 对齐状态 |
|------|--------|--------|----------|
| **ctl_imp** | 1.25 | 1.25 | ✅ 已对齐 |
| **k_capture** | 0.25 | 0.25 | ✅ 已对齐 |

**配置文件位置：**
- `ctl_imp`: `config/parameters.json` → `flow.controlImpact = 1.25`
- `k_capture`: `config/parameters.json` → `ObservationBiasFactor.k_capture = 0.25`

---

### ✅ 第二层参数冻结状态

**SpacetimeCorrector 配置：**
- ✅ ExclusionList: ["C01", "C02", "C07"]
- ✅ CaseSpecificCorrectorFactor: {"C03": 1.464, "C04": 3.099, "C06": 0.786, "C08": 0.9}
- ✅ C07 不在 CaseSpecificCorrectorFactor 中（已回滚）

**所有第二层参数保持 V18.0 冻结值。**

---

## 📊 C07 事业相计算结果

### 当前计算结果

**C07 八字：** 辛丑、乙未、庚午、甲申  
**日主：** 庚金  
**模型得分（原始）：** 67.43  
**GT (Ground Truth)：** 80.0  
**MAE：** 12.57

### ⚠️ 关键发现

**ctl_imp 参数已更新为 1.25，但计算结果未变化。**

**可能原因：**
1. `ctl_imp` 参数在代码中未正确应用到 Officer 能量计算
2. `ctl_imp` 的应用位置可能不在 `_calculate_ten_gods` 方法中

**代码检查：**
- `core/processors/domains.py` → `_calculate_ten_gods` 方法：
  - 返回：`'officer': officer_energy * officer_weight`
  - **未发现 ctl_imp 的应用**

**预期应用位置：**
根据 V29.0 要求，ctl_imp 应该应用到 Officer 能量上：
```python
# 预期公式
E_Officer = E_Officer,Final × (1 + ctl_imp)
E_Officer = 25.60 × (1 + 1.25) = 57.60
```

**当前代码状态：**
```python
# 实际代码（_calculate_ten_gods方法）
'officer': officer_energy * officer_weight
# 没有应用 ctl_imp
```

---

## 📊 C04 财富相验证状态

**状态：** ⚠️ calibration_cases.json 未找到，无法验证

**预期：** k_capture = 0.25 应应用于身旺案例的财富计算

**代码检查：**
- `core/processors/domains.py` → `_calc_wealth` 方法：
  - ✅ 已添加 k_capture 应用逻辑
  - ✅ 应用条件：verdict == 'Strong'
  - ✅ 计算公式：`capture_bonus = gods['wealth'] * k_capture`

---

## 🔍 详细分析

### ctl_imp 应用位置分析

**当前代码流程：**
1. `_calculate_ten_gods` 方法计算十神能量
2. 返回 `'officer': officer_energy * officer_weight`
3. `_calc_career` 方法使用 `gods['officer']` 计算事业得分

**ctl_imp 应该在哪里应用？**

**选项 1：在 `_calculate_ten_gods` 方法中应用**
```python
# 在返回之前应用 ctl_imp
if hasattr(self, '_context') and self._context:
    flow_config = self._context.get('flow_config', {})
    ctl_imp = flow_config.get('controlImpact', 0.7)
    officer_energy_boosted = officer_energy * (1 + ctl_imp)
else:
    officer_energy_boosted = officer_energy

return {
    ...
    'officer': officer_energy_boosted * officer_weight,
    ...
}
```

**选项 2：在 `_calc_career` 方法中应用**
```python
# 在计算事业得分时应用 ctl_imp
officer = gods['officer']
if hasattr(self, '_context') and self._context:
    flow_config = self._context.get('flow_config', {})
    ctl_imp = flow_config.get('controlImpact', 0.7)
    officer = officer * (1 + ctl_imp)
```

**当前状态：** 两个位置都未应用 ctl_imp

---

## 📋 对齐总结

### ✅ 已完成的对齐

1. ✅ V29.0 参数：ctl_imp = 1.25, k_capture = 0.25
2. ✅ 第二层参数：保持 V18.0 冻结值
3. ✅ k_capture 代码应用：已在 `_calc_wealth` 方法中正确应用

### ⚠️ 待确认的对齐

1. ⚠️ **ctl_imp 代码应用：** 参数已更新，但代码中未发现应用位置
2. ⚠️ **C07 MAE：** 仍为 12.57，未达到预期 < 5.0

### 📊 预期 vs 实际

**预期（V29.0）：**
- Step C: E_Officer = 25.60 × (1 + 1.25) = 57.60
- Step D: S_Base ≈ 46.50
- Step E: S_Final ≈ 79.7
- MAE: < 5.0

**实际：**
- 模型得分：67.43
- MAE: 12.57

**差异分析：**
- 如果 ctl_imp 正确应用，Officer 能量应从 48.64 提升到 57.60
- 预期提升约 9.0，但实际得分未变化
- **说明：ctl_imp 可能未在代码中应用**

---

## 💡 建议

### 1. 确认 ctl_imp 应用位置

需要确认：
- ctl_imp 是否应该在 `_calculate_ten_gods` 方法中应用？
- 还是应该在 `_calc_career` 方法中应用？
- 或者在其他位置应用？

### 2. 代码对齐

如果确认应用位置，需要：
- 在相应位置添加 ctl_imp 应用逻辑
- 确保从 flow_config 中正确读取 controlImpact 参数

### 3. 验证

应用 ctl_imp 后，重新运行验证：
- 检查 C07 事业相得分是否提升
- 验证 MAE 是否收敛至 < 5.0

---

**报告生成时间：** V29.0 Task 74  
**对齐状态：** ✅ 参数已对齐，⚠️ ctl_imp 代码应用待确认  
**下一步：** 等待确认 ctl_imp 应用位置，不进行代码修改

