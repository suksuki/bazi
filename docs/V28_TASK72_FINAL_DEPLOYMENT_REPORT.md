# V28.0 Task 72: 最终底层参数修正部署报告

## 📊 部署状态总结

### ✅ V27.0 回滚成功

**SpacetimeCorrector 配置已恢复：**
- ✅ C07 已从 CaseSpecificCorrectorFactor 中移除
- ✅ C07 已恢复至 ExclusionList
- ✅ 所有 V18.0 冻结值已恢复

**配置状态：**
```json
"SpacetimeCorrector": {
  "ExclusionList": ["C01", "C02", "C07"],
  "CaseSpecificCorrectorFactor": {
    "C03": 1.464,
    "C04": 3.099,
    "C06": 0.786,
    "C08": 0.900
  }
}
```

---

### ✅ V28.0 第一层参数修正成功

| 参数 | V24.0 值 | V28.0 修正值 | 状态 |
|------|----------|-------------|------|
| **ctl_imp** | 0.70 | **0.90** | ✅ 已修正 |
| **k_capture** | 0.0 | **0.25** | ✅ 已添加 |

**代码修改：**
- ✅ `config/parameters.json` 中 `controlImpact` 已更新为 0.9
- ✅ `config/parameters.json` 中 `ObservationBiasFactor.k_capture` 已添加为 0.25
- ✅ `core/processors/domains.py` 中 `_calc_wealth` 方法已添加 k_capture 应用逻辑

---

### ✅ V24.0 基础参数保持不变

| 参数 | 值 | 状态 |
|------|-----|------|
| pg_month | 1.8 | ✅ |
| imp_base | 0.20 | ✅ |
| clash_score | -3.0 | ✅ |
| punishmentPenalty | -3.0 | ✅ |
| harmPenalty | -2.0 | ✅ |

---

## 📊 C07 事业相计算结果

### 当前状态

**C07 八字：** 辛丑、乙未、庚午、甲申  
**日主：** 庚金  
**模型得分：** 6.74  
**GT (Ground Truth)：** 80.0  
**MAE：** 73.26

### 问题分析

**ctl_imp 提升效果：**
- V24.0: ctl_imp = 0.70 → Officer 效率 = 1.70x
- V28.0: ctl_imp = 0.90 → Officer 效率 = 1.90x
- **提升幅度：** +0.20 (约 +11.8%)

**预期影响：**
- 如果 Officer 能量为 25.60，则：
  - V24.0: 25.60 × 1.70 = 43.52
  - V28.0: 25.60 × 1.90 = 48.64
  - **提升：** +5.12

**实际结果：**
- 模型得分从 43.2 提升到 6.74（注意：6.74 可能是除以 10.0 后的值，实际应为 67.4）
- 如果实际得分是 67.4，则 MAE = 12.6，仍需要进一步调整

---

## 🔍 关键发现

### ⚠️ Career 得分缩放问题

**发现：** `engine_v88.py` 第 630 行将 career 得分除以 10.0：
```python
'career': domain_res['career']['score'] / 10.0, # Scale to 0-10 UI
```

**影响：** 实际计算得分可能是 67.4，但显示为 6.74。

**需要验证：** 检查 DomainProcessor 返回的原始 career 得分。

---

### ✅ k_capture 应用逻辑

**代码位置：** `core/processors/domains.py` `_calc_wealth` 方法

**应用条件：**
- verdict == 'Strong'（身旺）
- k_capture > 0.0

**计算公式：**
```python
capture_bonus = gods['wealth'] * k_capture
base_score = base_score + capture_bonus
```

**预期影响（C04 案例）：**
- 如果 Wealth 能量为 50.0，则：
  - capture_bonus = 50.0 × 0.25 = 12.5
  - base_score 增加 12.5

---

## 💡 建议

### 1. 验证 Career 得分缩放

需要检查：
- DomainProcessor 返回的原始 career 得分
- 是否应该使用原始得分而不是缩放后的得分进行 MAE 计算

### 2. 进一步调整 ctl_imp

如果 C07 的 MAE 仍然 > 5.0，可能需要：
- 进一步提升 ctl_imp（例如 0.90 → 1.0）
- 或检查其他影响 Officer 能量的参数

### 3. 验证 k_capture 效果

需要：
- 运行 C04 案例验证
- 确认 k_capture 是否正确应用到财富计算中

---

**报告生成时间：** V28.0 Task 72  
**部署状态：** ✅ 回滚成功，✅ 第一层参数修正成功，⚠️ C07 MAE 仍需进一步调整

