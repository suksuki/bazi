# V11 当前工作状态总结

## 📋 当前版本：V11.6

### 已完成的工作

#### V11.0 - RANSAC + SVM 基础架构
- ✅ RANSAC 异常值检测：识别并移除了20个离群点
- ✅ SVM 特征提取：5维特征向量
- ✅ SVM 模型训练：基础分类器

#### V11.1 - 动态数据引擎
- ✅ 合成数据工厂：生成50个完美合成案例
- ✅ 动态清洗器：自动识别脏数据
- ✅ 加权混合器：Classic(3.0) + Synthetic(2.0) + Modern(1.0)
- ✅ SMOTE数据增强：平衡类别分布
- ✅ GridSearchCV参数调优

#### V11.2 - 反过拟合优化
- ✅ 强制开启SMOTE
- ✅ 降低Classic权重：4.0 → 2.0
- ✅ GridSearch重点搜索小C值：[0.01, 0.1, 1.0]
- ✅ 更换测试集划分random_state：42 → 100

#### V11.3 - 法医式诊断
- ✅ 特征工程升级：5维 → 7维
  - 新增特征6：`day_master_polarity` (阴阳干性)
  - 新增特征7：`is_yangren` (是否坐阳刃)
- ✅ 错误验尸报告：生成详细的错误分析
- ✅ 强制使用stratify：确保测试集分布均衡

#### V11.4 - 平衡打击
- ✅ 启用类别权重平衡：`class_weight='balanced'`
- ✅ 激进的SMOTE策略：`sampling_strategy='auto'`
- ✅ 特征标准化诊断

#### V11.5 - 暴力纠偏
- ✅ 手动设置惩罚权重（废弃balanced）
  - Strong: 1.0, Balanced: 1.5, Weak: 3.0
  - Special_Strong: 5.0, Follower: 5.0, Extreme_Weak: 3.0
- ✅ 提高惩罚系数C：[10, 100, 500, 1000]
- ✅ 特征质心诊断：检查类别特征均值

#### V11.6 - 集成学习
- ✅ 数据冲突侦探：发现1886对冲突样本
- ✅ 引入随机森林：训练集准确率97.78%
- ✅ 使用Random Forest作为最终模型

---

## 📊 当前性能指标

### 模型性能
- **训练集准确率**: 97.78% (Random Forest)
- **测试集准确率**: 33.33%
- **交叉验证准确率**: 53.07% (±8.83%)

### 特征维度
- **7维特征向量**:
  1. `strength_score`: 能量绝对值 (0-100)
  2. `self_team_ratio`: 同党占比 (0.0-1.0)
  3. `is_month_command`: 得令系数 (1.0=得令, 0.5=失令)
  4. `main_root_count`: 主气根数量 (整数)
  5. `clash_count`: 冲克数量 (整数)
  6. `day_master_polarity`: 日主阴阳性 (1.0=阳干, 0.0=阴干) [V11.3]
  7. `is_yangren`: 是否坐阳刃 (1.0=是, 0.0=否) [V11.3]

---

## 🔧 当前配置

### 配置文件位置
- **Agentic配置**: `config/v11_agentic_config.json`
- **参数配置**: `config/parameters.json`
- **忽略案例**: `config/ignored_cases.json`

### 当前配置值
```json
{
  "use_smote": true,
  "smote_target_ratio": 0.2,
  "use_gridsearch": true,
  "classic_weight": 2.0,
  "synthetic_weight": 2.0,
  "modern_weight": 1.0,
  "synthetic_count": 30,
  "use_dynamic_cleaning": true,
  "confidence_threshold": 0.9,
  "test_random_state": 100,
  "gridsearch_c_range": [10, 100, 500, 1000],
  "gridsearch_gamma_range": ["scale", "auto", 0.1, 0.01]
}
```

---

## 📁 关键文件

### 核心代码
- **训练脚本**: `scripts/v11_svm_trainer.py`
- **Agentic优化器**: `scripts/v11_1_agentic_optimizer.py`
- **数据引擎**:
  - `scripts/data_engine/data_loader.py` (加权混合器)
  - `scripts/data_engine/synthetic_factory.py` (合成数据工厂)
  - `scripts/data_engine/dynamic_cleaner.py` (动态清洗器)
- **特征提取**: `core/engine_graph.py` (方法: `extract_svm_features`)

### 模型文件
- **SVM模型**: `models/v11_strength_svm.pkl`

### 文档
- **V11.0架构**: `docs/V11_0_RANSAC_SVM_ARCHITECTURE.md`
- **V11.0分析报告**: `docs/V11_0_RANSAC_ANALYSIS_REPORT.md`
- **V11.2反过拟合报告**: `docs/V11_2_ANTI_OVERFITTING_REPORT.md`
- **V11.6集成学习报告**: `docs/V11_6_ENSEMBLE_REPORT.md`

---

## 🎯 当前问题与挑战

### 1. 严重过拟合
- **训练集**: 97.78%
- **测试集**: 33.33%
- **差距**: 64.45%（严重过拟合）

### 2. 数据冲突
- **冲突样本对数**: 1886对（相似度>0.95但标签不同）
- **影响**: 导致模型学习到错误的模式

### 3. 测试集准确率未提升
- **目标**: 50%+
- **当前**: 33.33%
- **差距**: 16.67%

---

## 💡 下一步优化方向

### 1. 数据清洗
- 分析1886对冲突样本
- 识别真正的脏数据
- 更新`config/ignored_cases.json`

### 2. 模型优化
- 降低Random Forest的`max_depth`（减少过拟合）
- 尝试其他集成方法（XGBoost、LightGBM）
- 调整类别权重策略

### 3. 特征工程
- 验证阴阳干特征是否真正生效
- 考虑添加更多特征（通根深度、冲克类型等）
- 优化特征权重

### 4. 测试集策略
- 使用更大的测试集
- 尝试不同的划分策略
- 分析测试集与训练集的分布差异

---

## 🚀 快速启动命令

### 运行训练
```bash
cd /home/jin/bazi_predict
source venv/bin/activate
python3 scripts/v11_svm_trainer.py
```

### 运行Agentic优化器
```bash
python3 scripts/v11_1_agentic_optimizer.py --max_iterations 5 --target_accuracy 50
```

### 查看最新报告
```bash
cat docs/V11_6_ENSEMBLE_REPORT.md
```

---

## 📝 在新Chat中继续工作的提示

1. **读取此文档**: `docs/V11_CURRENT_STATUS.md`
2. **查看最新报告**: `docs/V11_6_ENSEMBLE_REPORT.md`
3. **检查当前配置**: `config/v11_agentic_config.json`
4. **运行训练验证**: `python3 scripts/v11_svm_trainer.py`

### 关键上下文
- 当前使用**Random Forest**作为最终模型（训练集97.78%）
- 存在**严重过拟合**问题（训练97.78% vs 测试33.33%）
- 发现**1886对数据冲突样本**需要清洗
- 特征维度：**7维**（包含阴阳干和阳刃特征）

---

**最后更新**: 2025-12-18  
**版本**: V11.6  
**状态**: 等待进一步优化

