# V11.0/V11.1 当前状态快照

**记录时间**: 2025-12-18  
**当前版本**: V11.1（合成数据增强版）  
**状态**: ✅ 已完成基础功能，性能需要优化

---

## 📋 已完成的工作

### V11.0 基础架构（已完成）

1. ✅ **RANSAC数据清洗**
   - 识别出20个离群点
   - 创建了`config/ignored_cases.json`
   - 清洗后数据集：81个真实案例

2. ✅ **特征工程**
   - 实现了`extract_svm_features()`方法
   - 5维特征向量：[strength_score, self_team_ratio, is_month_command, main_root_count, clash_count]
   - 文件：`core/engine_graph.py`

3. ✅ **SVM模型训练**
   - 训练脚本：`scripts/v11_svm_trainer.py`
   - 模型保存：`models/v11_strength_svm.pkl`
   - 集成到推理：`core/engine_graph.py`中的`calculate_strength_score`

### V11.1 增强功能（已完成）

1. ✅ **SMOTE数据增强**
   - 引入了`imbalanced-learn`库
   - 实现了SMOTE和RandomOverSampler

2. ✅ **GridSearchCV参数调优**
   - 搜索空间：C, gamma, kernel（75个组合）
   - 最佳参数：`{'C': 100, 'gamma': 0.1, 'kernel': 'rbf'}`

3. ✅ **特征加权优化**
   - `is_month_command`放大2.0倍
   - `strength_score`进行MinMax标准化

4. ✅ **合成数据生成**
   - 生成了8个理论合成样本
   - 所有合成数据明确标注`synthetic: true`
   - 实现了严格的数据隔离（合成数据不进入测试集）

---

## 📊 当前性能指标

### 最新训练结果（V11.1 with Synthetic Data）

| 指标 | 数值 | 备注 |
|------|------|------|
| 训练集准确率 | 54.76% | 较V11.1(前)下降16.67% |
| 测试集准确率 | 29.41% | 较V11.1(前)下降29.41% ⚠️ |
| 交叉验证准确率 | 42.81% | 较V11.1(前)提升2.07% ✅ |
| 最佳CV分数 | 55.95% | GridSearchCV找到的最佳参数组合 |

### 数据集状态

- **真实数据**：81个案例（已排除20个离群点）
- **合成数据**：8个案例（5个Special_Strong, 2个Follower, 1个Balanced）
- **标签分布**：
  - Strong: 34
  - Special_Strong: 6 (1真实 + 5合成)
  - Follower: 6 (4真实 + 2合成)
  - Weak: 22
  - Balanced: 16 (15真实 + 1合成)
  - Extreme_Weak: 5

---

## ⚠️ 当前问题

### 1. 测试集准确率大幅下降

**现象**：测试集准确率从58.82%下降到29.41%

**可能原因**：
1. SMOTE过度增强（各类别平衡到28个样本）
2. 合成数据与真实数据分布差异
3. 测试集样本量太小（仅17个），统计不稳定
4. 过拟合：模型在"完美"合成数据上过度学习

### 2. Special_Strong类别仍然不足

虽然增加了5个合成样本，但在测试集中仍然没有Special_Strong样本，无法评估识别率。

---

## 📁 关键文件状态

### 已修改的文件

1. **`core/engine_graph.py`**
   - ✅ 新增`extract_svm_features()`方法
   - ✅ `calculate_strength_score()`中集成了SVM预测逻辑
   - ✅ 特征提取：5维特征向量

2. **`scripts/v11_svm_trainer.py`**
   - ✅ 实现了SMOTE数据增强
   - ✅ 实现了GridSearchCV参数调优
   - ✅ 实现了合成数据生成（`generate_theoretical_samples()`）
   - ✅ 实现了严格的数据隔离（合成数据不进入测试集）
   - ✅ 特征加权优化

3. **`config/ignored_cases.json`**
   - ✅ 包含20个离群点ID

4. **`models/v11_strength_svm.pkl`**
   - ✅ 保存了最新的SVM模型

### 文档文件

1. **`docs/V11_0_RANSAC_SVM_ARCHITECTURE.md`** - 架构设计文档
2. **`docs/V11_0_RANSAC_ANALYSIS_REPORT.md`** - RANSAC分析报告
3. **`docs/V11_1_RESCUE_REPORT.md`** - V11.1救援报告
4. **`docs/V11_1_SYNTHETIC_DATA_REPORT.md`** - 合成数据报告

---

## 🔄 下一步优化计划

### 优先级1：优化SMOTE强度

**问题**：SMOTE将各类别平衡到28个，可能过度增强

**计划**：
- [ ] 降低SMOTE目标比例（从40%降到20-30%）
- [ ] 或仅在极少数类别（Special_Strong, Follower）上使用SMOTE
- [ ] 或完全禁用SMOTE，仅使用理论合成样本

### 优先级2：验证合成数据质量

**问题**：合成数据是否真正符合专旺格特征？

**计划**：
- [ ] 用引擎计算合成数据的实际特征值
- [ ] 对比合成数据与实际Special_Strong样本的特征分布
- [ ] 调整合成数据的八字，使其特征更接近真实样本

### 优先级3：增加测试集样本量

**问题**：测试集仅17个样本，统计不稳定

**计划**：
- [ ] 减小`test_size`到0.15（保留更多真实数据用于测试）
- [ ] 或增加更多真实历史案例

### 优先级4：尝试不同的数据增强策略

**计划**：
- [ ] 尝试ADASYN替代SMOTE
- [ ] 尝试类别权重（class_weight='balanced'）而非过采样
- [ ] 尝试只使用理论合成样本，不使用SMOTE

---

## 🎯 核心目标

**最终目标**：突破65%匹配率

**当前状态**：
- 交叉验证准确率：42.81%
- 测试集准确率：29.41%
- **需要提升约22-35%**

---

## 💡 关键洞察

1. ✅ **合成数据策略是正确的**：Special_Strong从1个增加到6个，交叉验证准确率提升
2. ⚠️ **SMOTE可能过度增强**：导致过拟合，测试集准确率下降
3. ✅ **数据隔离成功**：合成数据不进入测试集，符合"训练用合成，测试用真实"的原则
4. ✅ **GridSearchCV找到了更好的参数**：最佳CV分数55.95%

---

## 📝 重启后继续工作的命令

```bash
# 1. 激活虚拟环境
cd /home/jin/bazi_predict
source venv/bin/activate

# 2. 运行当前版本的SVM训练
python3 scripts/v11_svm_trainer.py

# 3. 查看最新的训练结果
# 查看日志或报告文件

# 4. 下一步优化（根据优先级1）
# 修改 scripts/v11_svm_trainer.py 中的SMOTE目标比例
```

---

## 🔍 调试建议

如果性能仍然不佳，可以：

1. **检查合成数据特征**：
```python
from scripts.v11_svm_trainer import SVMTrainer
trainer = SVMTrainer()
synthetic = trainer.generate_theoretical_samples()
# 计算这些样本的实际特征值，验证是否符合预期
```

2. **对比合成数据与真实数据**：
```python
# 提取真实Special_Strong样本的特征
# 对比合成样本的特征分布
```

3. **尝试不使用SMOTE**：
```python
# 在 train_svm() 中设置 use_smote=False
trainer_result = trainer.train_svm(X, y, is_synthetic=is_synthetic, use_smote=False, use_gridsearch=True)
```

---

**最后更新**: 2025-12-18  
**状态**: 等待重启后继续优化

