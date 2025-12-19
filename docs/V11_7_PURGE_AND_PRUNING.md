# V11.7 肃反运动：大清洗与剪枝 (The Great Purge & Pruning)

**执行时间**: 2025-01-XX  
**版本**: V11.7.0  
**状态**: ✅ 完成

---

## 📋 核心目标

解决 V11.6 发现的 **1886 对冲突样本** 和 **33% 的测试准确率** 问题。

**核心洞察**: 97.78% 的训练准确率说明模型在"死记硬背"矛盾数据，导致过拟合。我们需要：
1. **消灭矛盾**：通过"血统论"清洗策略统一思想
2. **强力镇静**：通过剪枝防止过拟合

---

## 🩸 实施内容

### 1. 血统论清洗策略 (Lineage-Based Purge)

**文件**: `scripts/data_engine/conflict_resolver.py`

**清洗逻辑**：

1. **宪法优先** (Classic > Modern)
   - 如果 A 是 `Classic` (古籍)，B 是 `Modern` (现代)
   - **保留 A，删除 B**
   - 古籍永远是对的

2. **理论优先** (Synthetic > Modern)
   - 如果 A 是 `Synthetic` (理论合成)，B 是 `Modern`
   - **保留 A，删除 B**
   - 教科书比模糊的历史名人更可信

3. **内战同归于尽** (Modern vs Modern)
   - 如果 A 和 B 都是 `Modern` 且标签矛盾
   - **两个都删除**
   - 我们承担不起脏数据的风险

4. **自身矛盾** (Self-Contradiction)
   - 如果 A 和 B 是同一个 ID（数据重复）但标签不同
   - **删除该 ID**

**实现细节**：
- 使用余弦相似度检测冲突样本对（相似度 > 0.95，但标签不同）
- 自动将被删除的案例ID追加到 `config/ignored_cases.json`
- 提供详细的清洗统计和删除原因说明

### 2. 随机森林剪枝 (Tree Pruning)

**文件**: `scripts/v11_svm_trainer.py`

**剪枝参数**：

| 参数 | 原值 (V11.6) | 新值 (V11.7) | 说明 |
|:---|:---|:---|:---|
| `n_estimators` | 200 | **300** | 提升树数量，通过投票平滑噪声 |
| `max_depth` | 10 | **6** | 限制深度，防止过拟合（八字的逻辑层级通常不需要超过6层） |
| `min_samples_leaf` | 默认 (1) | **3** | 禁止为1-2个样本单独建立规则 |
| `max_features` | 默认 ('sqrt') | **'sqrt'** | 强制每棵树只看一部分特征，防止某个强特征（如 Score）统治所有树 |

**预期效果**：
- 训练集准确率从 97% **降至 80% 左右**（不再死记硬背）
- 测试集准确率从 33% **提升至 50% 以上**（泛化能力提升）

---

## 🔧 使用方法

### 自动执行（推荐）

在训练脚本中，冲突解决器会自动执行（如果启用）：

```python
# 在 v11_agentic_config.json 中配置
{
  "use_conflict_resolution": true,  # 启用冲突解决
  "conflict_similarity_threshold": 0.95  # 相似度阈值
}
```

### 手动执行

```python
from scripts.data_engine.conflict_resolver import ConflictResolver
from core.models.config_model import ConfigModel

# 创建冲突解决器
resolver = ConflictResolver(config_model=ConfigModel())

# 加载案例
cases = [...]  # 你的案例列表

# 执行冲突解决
cleaned_cases, removed_ids, removal_notes = resolver.resolve_all_conflicts(
    cases,
    similarity_threshold=0.95
)
```

---

## 📊 预期结果

### 数据清洗效果

- **原始案例数**: N 个
- **冲突对数**: 1886 对（预期）
- **删除案例数**: 预计减少 10-30%（取决于冲突分布）
- **清洗后案例数**: 预计减少到 70-90% 的原始数量

### 模型性能提升

- **训练集准确率**: 从 97.78% → **80% 左右**（不再过拟合）
- **测试集准确率**: 从 33% → **50% 以上**（泛化能力提升）
- **信噪比**: **爆炸式提升**（数据质量显著改善）

---

## 🎯 核心原则

### 1. 数据质量 > 数据数量

> "我们要的是一支精锐的特种部队，而不是一群乌合之众。"

虽然样本量会减少，但 **信噪比 (Signal-to-Noise Ratio)** 会爆炸式提升。

### 2. 逻辑自洽 > 死记硬背

当那 1886 对矛盾消失后，剩下的数据将形成一个 **"逻辑自洽"** 的真理闭环。

### 3. 泛化能力 > 训练精度

97.78% 的训练精度是"精神分裂"的表现。我们需要的是能够从容画出强弱边界的模型。

---

## 📝 技术细节

### 冲突检测算法

```python
# 使用余弦相似度检测冲突
similarity = cosine_similarity(feature_vector_a, feature_vector_b)

# 如果相似度 > 0.95 且标签不同，则认为是冲突
if similarity > 0.95 and label_a != label_b:
    # 标记为冲突对
    conflicts.append((case_a, case_b))
```

### 血统优先级

```
Classic (古籍) > Synthetic (理论合成) > Modern (现代数据)
```

### 剪枝策略

- **max_depth=6**: 八字的逻辑层级通常不需要超过6层
- **min_samples_leaf=3**: 禁止为1-2个样本单独建立规则
- **max_features='sqrt'**: 防止某个强特征统治所有树
- **n_estimators=300**: 让更多的树通过投票来平滑噪声

---

## 🔍 验证方法

### 1. 检查清洗效果

```bash
# 查看 ignored_cases.json
cat config/ignored_cases.json

# 检查删除的案例数量
python scripts/data_engine/conflict_resolver.py
```

### 2. 重新训练模型

```bash
# 运行训练脚本
python scripts/v11_svm_trainer.py

# 观察训练和测试准确率
# 预期：训练准确率 ~80%，测试准确率 > 50%
```

### 3. 对比性能

- **训练前**: 训练 97.78%，测试 33%
- **训练后**: 训练 ~80%，测试 > 50%

---

## 📚 相关文档

- **V11.6 报告**: `docs/V11_6_ENSEMBLE_REPORT.md` - 发现冲突样本
- **数据引擎**: `docs/V11_1_DYNAMIC_DATA_ENGINE.md` - 数据加载和清洗机制
- **训练脚本**: `scripts/v11_svm_trainer.py` - SVM/RF 训练主脚本

---

## ✅ 检查清单

- [x] 创建 `conflict_resolver.py` 实施血统论清洗策略
- [x] 修改 `v11_svm_trainer.py` 中的 RandomForestClassifier 参数（剪枝）
- [x] 集成冲突解决器到训练流程
- [x] 更新 `data_engine/__init__.py` 导出 ConflictResolver
- [ ] 测试清洗和剪枝后的模型性能
- [ ] 验证训练集准确率降至 ~80%
- [ ] 验证测试集准确率提升至 > 50%

---

**最后更新**: 2025-01-XX  
**版本**: V11.7.0  
**维护者**: 量子八字 GEM V10.0 核心分析师

