# V10.0 旺衰判定参数调优 - 核心分析师 Review 补充

**Review日期**: 2025-01-17  
**Reviewer**: 量子八字 GEM V10.0 核心分析师  
**状态**: ✅ 已批准并实施

---

## 📋 总体评价

这是一套**高度可执行**的工程方案。Cursor 精准捕捉到了 V10.0 旺衰判定的痛点，并提出了“敏感度分析 -> 网格搜索 -> 针对性优化”的标准化流程。特别是对于 `energy_threshold_center` 的敏感度分析，是解决“打地鼠”问题的金钥匙。

然而，在面对**Jason E（极弱）**和**乔丹（从格）**这类"非线性临界"案例时，原本的方案略显"线性"。以下补充建议旨在让调优计划具备处理"黑天鹅"事件的能力。

---

## 💡 核心分析师的战略补充建议（已实施）

### 1. 🛡️ 引入"极弱锁定"参数 (Extreme Weak Lock) ✅

**痛点**：迈克尔·乔丹（从格）被误判为 Weak (Score 19.1)。单纯调整 `energy_threshold_center` 很难解决"弱"与"从"的分界。

**解决方案**：
- ✅ **新增参数**：`strength.follower_threshold` (默认 0.15)
- ✅ **逻辑**：当 `strength_probability < follower_threshold` 时，判定为 `Follower`（从格）
- ✅ **调优范围**：0.1 ~ 0.2（在网格搜索中自动包含）

**实施位置**：
- `core/config_schema.py`: 添加 `follower_threshold` 参数
- `core/engine_graph.py`: 在 `calculate_strength_score` 中实现从格判定逻辑
- `scripts/strength_parameter_tuning.py`: 网格搜索自动包含从格阈值调优

**预期效果**：
- 乔丹（Score 19.1 -> strength_probability ≈ 0.15）能正确判定为 Follower
- 普通身弱案例（如马斯克）不会误判为从格

---

### 2. ⚡ "比尔·盖茨"悖论的解法：GAT 权重干预

**痛点**：比尔·盖茨被判为 Weak (42.7)，真实为 Strong。系统低估了"亥水（禄）"在戌月的含金量。

**解决方案**：
- ✅ **原理**：盖茨的 `辛亥` 一柱，金水相生。提高同柱流通权重，能让辛金更有效地生助壬水，从而拉高身强分数。
- ⚠️ **注意**：同柱权重参数需要在结构（Structure）配置中调优，本次调优专注于 `strength` 相关参数。GAT 权重调优作为后续专项任务。

**当前处理**：
- 在调优计划文档中明确标注为"针对性优化"阶段的任务
- 建议在完成基础参数调优后，再进行 GAT/同柱权重专项调优

---

### 3. 📉 敏感度分析的"可视化增强" ✅

**痛点**：当前的敏感度分析只输出"最优值"，无法判断参数的鲁棒性。

**解决方案**：
- ✅ **响应曲线图**：生成 `sensitivity_curve_{参数名}.png`
- ✅ **X轴**：参数值（如 2.0 -> 4.0）
- ✅ **Y轴**：全局匹配率
- ✅ **鲁棒性分析**：
  - 计算匹配率的标准差
  - 标准差 < 5%：参数鲁棒性好（平顶区），建议使用
  - 标准差 > 10%：参数敏感度高（尖峰），需谨慎调优

**实施位置**：
- `scripts/strength_parameter_tuning.py`: `_plot_sensitivity_curve` 方法
- 自动保存图表到 `reports/sensitivity_curve_{参数名}.png`

**预期效果**：
- 直观看到参数-匹配率关系曲线
- 识别平顶区（鲁棒性好）vs 尖峰（不稳定）
- 选择宽而不选尖，提高泛化能力

---

## 🎯 调优策略更新

### 策略1: 单参数敏感度分析（增强版）

**新增功能**：
- ✅ 自动生成响应曲线图
- ✅ 自动分析参数鲁棒性
- ✅ 输出最优值和鲁棒性建议

**使用示例**：
```bash
python3 scripts/strength_parameter_tuning.py \
    --mode sensitivity \
    --param strength.energy_threshold_center \
    --min 2.0 \
    --max 4.0 \
    --steps 20
```

**输出**：
- 控制台：参数值与匹配率列表
- 图表文件：`reports/sensitivity_curve_strength_energy_threshold_center.png`
- 鲁棒性分析：标准差和鲁棒性评价

---

### 策略2: 网格搜索优化（增强版）

**新增功能**：
- ✅ 自动包含从格阈值调优（`follower_threshold: 0.1~0.2`）
- ✅ 同时优化多个关键参数

**使用示例**：
```bash
python3 scripts/strength_parameter_tuning.py --mode optimize
```

**默认搜索范围**：
- `strength.energy_threshold_center`: 2.0 ~ 4.0 (10步)
- `strength.phase_transition_width`: 5.0 ~ 20.0 (8步)
- `strength.follower_threshold`: 0.1 ~ 0.2 (5步) ← 新增

**总组合数**: 10 × 8 × 5 = 400 个组合

---

### 策略3: 针对性优化（后续专项）

**任务清单**：
1. ✅ **从格阈值调优**（已完成，集成到网格搜索）
2. ⏳ **GAT 注意力权重调优**（比尔·盖茨案例）
   - 参数：`gat.attention_dropout`
   - 参数：`structure.same_pillar_bonus`（如果存在）
3. ⏳ **同柱干支互通权重调优**（盖茨案例专项）
   - 需要检查配置中是否存在相关参数

---

## 📊 预期改进效果

### 案例改善预期

| 案例 | 当前问题 | 调优方法 | 预期结果 |
|------|---------|---------|---------|
| **迈克尔·乔丹** | Weak (GT: Follower) | `follower_threshold` 调优 | ✅ 正确判定为 Follower |
| **埃隆·马斯克** | Moderate (GT: Weak) | `energy_threshold_center` 调优 | ✅ 正确判定为 Weak |
| **比尔·盖茨** | Weak (GT: Strong) | GAT/同柱权重调优（后续） | ⏳ 待专项调优 |

---

## 🔧 实施清单

### ✅ 已完成

- [x] 添加 `follower_threshold` 参数到配置
- [x] 实现从格判定逻辑（`strength_probability < follower_threshold`）
- [x] 敏感度分析可视化功能（响应曲线图）
- [x] 参数鲁棒性分析（标准差计算）
- [x] 网格搜索自动包含从格阈值调优
- [x] 更新调优脚本文档和帮助信息

### ⏳ 待后续实施

- [ ] GAT 注意力权重调优（比尔·盖茨案例）
- [ ] 同柱干支互通权重调优（如果配置中存在）
- [ ] 集成测试：验证从格判定准确性

---

## 📝 使用指南更新

### 完整调优流程（增强版）

```bash
# 1. 基线测试
python3 scripts/strength_parameter_tuning.py --mode test

# 2. energy_threshold_center 敏感度分析（生成可视化图表）
python3 scripts/strength_parameter_tuning.py \
    --mode sensitivity \
    --param strength.energy_threshold_center \
    --min 2.0 \
    --max 4.0 \
    --steps 20

# 3. follower_threshold 敏感度分析（从格判定）
python3 scripts/strength_parameter_tuning.py \
    --mode sensitivity \
    --param strength.follower_threshold \
    --min 0.1 \
    --max 0.2 \
    --steps 10

# 4. 联合优化（自动包含从格阈值）
python3 scripts/strength_parameter_tuning.py --mode optimize

# 5. 验证最优参数
# （手动验证或使用脚本）
```

---

## ✅ 总结

经过核心分析师的战略补充，调优方案现在具备了：

1. ✅ **处理非线性临界案例的能力**（从格阈值）
2. ✅ **参数鲁棒性评估能力**（可视化+标准差分析）
3. ✅ **自动化专项调优**（从格阈值自动包含在网格搜索中）

**下一步行动**：
- 执行敏感度分析，查看响应曲线
- 执行网格搜索，找到最优参数组合
- 验证乔丹、马斯克等关键案例的改善效果

---

**维护者**: Bazi Predict Team  
**Reviewer**: 量子八字 GEM V10.0 核心分析师  
**最后更新**: 2025-01-17

