# V11.1 动态数据引擎架构文档

## 📋 概述

V11.1 动态数据引擎实现了"Sim-to-Real（仿真到现实）"数据闭环架构，包含三大核心模组：

1. **造血模组** (Synthetic Data Factory)：生成完美的理论合成数据
2. **代谢模组** (Dynamic Cleaner)：动态清洗脏数据
3. **融合模组** (Data Loader)：加权混合不同类型的数据

---

## 🏛️ 架构设计

### 核心思想

- **左腿（Real Data）**：真实的物理约束和历史验证（骨）
- **右腿（Synthetic Data）**：填补样本稀疏区的合成数据（肉）
- **淋巴系统（Cleaning）**：自动识别并代谢掉脏数据（免疫）

### 数据分层与权重

```
训练集配比 (Training Batch):
├── 核心层 (Core): 经典古籍案例，权重 3.0 —— 不可动摇的宪法
├── 骨架层 (Skeleton): 合成理论数据，权重 2.0 —— 撑起模型的骨架
└── 肌肉层 (Muscle): 清洗后的现代数据，权重 1.0 —— 增加泛化能力

验证集 (Validation Set):
└── 严禁包含合成数据，必须是 100% 真实案例（"练假打真"）
```

---

## 🔧 模块说明

### 1. SyntheticDataFactory (造血模组)

**位置**: `scripts/data_engine/synthetic_factory.py`

**功能**: 按照八字物理学，生成50个"教科书级"的标准案例

**生成规则**:

1. **极纯生成** (Special_Strong)：
   - 天干地支全一气（如四甲戌、四丙午）
   - 确保日主在月令得令
   - Label = `Special_Strong`

2. **极克生成** (Follower)：
   - 日主无根，满盘七杀（从杀格）
   - 日主无根，满盘财星（从财格）
   - Label = `Follower`

3. **极泄生成** (Follower)：
   - 日主无根，满盘食伤（从儿格）
   - Label = `Follower`

4. **中和生成** (Balanced)：
   - 日主有生有克，能量相对平衡
   - Label = `Balanced`

**示例代码**:

```python
from scripts.data_engine import SyntheticDataFactory

factory = SyntheticDataFactory()
synthetic_cases = factory.generate_perfect_cases(target_count=50)
```

---

### 2. DynamicCleaner (代谢模组)

**位置**: `scripts/data_engine/dynamic_cleaner.py`

**功能**: 使用RANSAC思想动态清洗脏数据

**工作机制**:

1. **基准模型训练**：
   - 使用Classic + Synthetic数据训练一个临时SVM模型

2. **偏差检测**：
   - 用基准模型预测所有Modern数据
   - 如果预测结果与Ground Truth偏离度 > 阈值（默认90%置信度反向预测）
   - 且该案例不是经典案例

3. **自动处置**：
   - 标记为 `Dirty`
   - 自动追加ID到 `config/ignored_cases.json`
   - 本轮训练权重降为0（或在内存中剔除）

**示例代码**:

```python
from scripts.data_engine import DynamicCleaner

cleaner = DynamicCleaner()
cleaned_cases, dirty_ids = cleaner.filter_outliers(
    classic_cases=classic_cases,
    synthetic_cases=synthetic_cases,
    modern_cases=modern_cases,
    confidence_threshold=0.90,
    use_svm=True
)
```

---

### 3. DataLoader (融合模组)

**位置**: `scripts/data_engine/data_loader.py`

**功能**: 加权混合不同类型的数据

**数据流程**:

1. **加载经典案例**（权重 3.0）
2. **生成合成数据**（权重 2.0）
3. **加载现代案例**
4. **动态清洗现代案例**（移除脏数据）
5. **合并并标记**数据来源和权重

**返回数据**:

- `cases`: 合并后的案例列表
- `sample_weights`: 样本权重数组（Classic: 3.0, Synthetic: 2.0, Modern: 1.0）
- `is_synthetic`: 是否合成的标记列表（用于验证集隔离）

**示例代码**:

```python
from scripts.data_engine import DataLoader

loader = DataLoader()
cases, sample_weights, is_synthetic = loader.load_training_cases(
    use_dynamic_cleaning=True,
    generate_synthetic=True,
    synthetic_count=50
)
```

---

## 🔄 集成到SVM训练器

**位置**: `scripts/v11_svm_trainer.py`

**修改内容**:

1. 导入新的数据引擎
2. 使用`DataLoader`加载数据（替代原有的加载逻辑）
3. 传递`sample_weights`到SVM训练函数
4. 在`train_svm()`中支持加权训练

**关键代码**:

```python
from scripts.data_engine import DataLoader

# 使用新的数据引擎
data_loader = DataLoader(config_model=trainer.config_model)
all_cases, sample_weights, is_synthetic = data_loader.load_training_cases(
    use_dynamic_cleaning=True,
    generate_synthetic=True,
    synthetic_count=50
)

# 提取特征
X, y, _ = trainer.extract_features_and_labels(all_cases, mark_synthetic=True)
sample_weights_array = np.array(sample_weights)

# 训练SVM（带权重）
trainer_result = trainer.train_svm(
    X, y, 
    is_synthetic=is_synthetic, 
    use_smote=True, 
    use_gridsearch=True,
    sample_weights=sample_weights_array
)
```

---

## 📊 数据流向

```
┌─────────────────┐
│  Classic Cases  │ ───┐
│   (权重 3.0)    │    │
└─────────────────┘    │
                       │
┌─────────────────┐    │    ┌──────────────────┐
│ Synthetic Data  │ ───┼───▶│   DataLoader     │
│   Factory       │    │    │   (融合模组)     │
│  (权重 2.0)     │    │    └──────────────────┘
└─────────────────┘    │             │
                       │             │
┌─────────────────┐    │             ▼
│  Modern Cases   │ ───┤    ┌──────────────────┐
│                 │    │    │ Dynamic Cleaner  │
└─────────────────┘    │    │   (代谢模组)     │
                       │    └──────────────────┘
                       │             │
                       └─────────────┘
                                  │
                                  ▼
                          ┌──────────────────┐
                          │   SVMTrainer     │
                          │  (加权训练)      │
                          └──────────────────┘
```

---

## ✅ 关键特性

### 1. 严格的数据隔离

- ✅ 合成数据**严禁**进入验证集/测试集
- ✅ 验证集必须是100%真实历史案例
- ✅ 遵循"练假打真"原则

### 2. 加权训练

- ✅ Classic案例权重 3.0（最高优先级）
- ✅ Synthetic案例权重 2.0（中等优先级）
- ✅ Modern案例权重 1.0（最低优先级）
- ✅ SVM训练时使用`sample_weight`参数

### 3. 动态清洗

- ✅ 自动识别脏数据
- ✅ 自动更新`ignored_cases.json`
- ✅ 每次训练前自动执行清洗

### 4. 合成数据生成

- ✅ 基于八字物理原理
- ✅ 确保日主得月令（符合专旺格特征）
- ✅ 涵盖五行（金木水火土）
- ✅ 明确标记`synthetic: true`

---

## 🚀 使用方法

### 完整训练流程

```python
# 1. 导入模块
from scripts.v11_svm_trainer import SVMTrainer
from scripts.data_engine import DataLoader

# 2. 创建训练器
trainer = SVMTrainer()

# 3. 使用数据引擎加载数据
data_loader = DataLoader(config_model=trainer.config_model)
cases, sample_weights, is_synthetic = data_loader.load_training_cases(
    use_dynamic_cleaning=True,
    generate_synthetic=True,
    synthetic_count=50
)

# 4. 提取特征
X, y, _ = trainer.extract_features_and_labels(cases, mark_synthetic=True)

# 5. 训练SVM
result = trainer.train_svm(
    X, y,
    is_synthetic=is_synthetic,
    use_smote=True,
    use_gridsearch=True,
    sample_weights=np.array(sample_weights)
)

# 6. 保存模型
trainer.save_model(result, Path("models/v11_strength_svm.pkl"))
```

### 直接运行训练脚本

```bash
cd /home/jin/bazi_predict
source venv/bin/activate
python3 scripts/v11_svm_trainer.py
```

---

## 📈 预期效果

### 性能提升

1. **类别平衡**：
   - Special_Strong从1个增加到30+个（合成数据）
   - Follower从4个增加到15+个（合成数据）

2. **数据质量**：
   - 自动剔除脏数据
   - 提高数据纯净度

3. **模型准确性**：
   - 加权训练让模型更重视经典案例
   - 合成数据填补稀疏区域
   - 预期交叉验证准确率提升至 50%+

---

## 🔍 调试与监控

### 检查数据分布

```python
from scripts.data_engine import DataLoader
from collections import Counter

loader = DataLoader()
cases, weights, is_synthetic = loader.load_training_cases()

# 统计标签分布
labels = [c.get('ground_truth', {}).get('strength', 'Unknown') for c in cases]
print("标签分布:", Counter(labels))

# 统计数据来源
sources = ['synthetic' if s else 'real' for s in is_synthetic]
print("数据来源:", Counter(sources))

# 统计权重分布
print("权重分布:", Counter([f'{w:.1f}' for w in weights]))
```

### 检查脏数据识别

```python
from scripts.data_engine import DynamicCleaner
import json

cleaner = DynamicCleaner()
ignored_ids = cleaner.load_ignored_cases()

print(f"已忽略的案例数: {len(ignored_ids)}")
print(f"忽略列表: {sorted(ignored_ids)}")
```

---

## 📝 注意事项

1. **合成数据质量**：
   - 确保生成的八字符合物理原理
   - 验证日主是否真的得月令

2. **清洗阈值**：
   - `confidence_threshold`需要根据实际情况调整
   - 过高可能误杀好数据
   - 过低可能漏掉脏数据

3. **权重平衡**：
   - Classic权重不应过高，否则Modern数据可能被忽略
   - Synthetic权重不应过低，否则无法填补稀疏区域

4. **SMOTE与权重**：
   - SMOTE生成的新样本使用较小权重（原始最小权重的50%）
   - 避免合成样本过度影响模型

---

## 🎯 未来优化方向

1. **自适应权重**：
   - 根据模型表现动态调整权重
   - 使用强化学习优化权重分配

2. **合成数据验证**：
   - 使用引擎验证合成数据的特征值
   - 确保合成数据符合预期分布

3. **清洗策略优化**：
   - 使用更复杂的偏差检测算法
   - 支持软清洗（降权而非剔除）

4. **数据增强策略**：
   - 尝试ADASYN替代SMOTE
   - 使用GAN生成更真实的合成数据

---

**文档版本**: V11.1  
**最后更新**: 2025-12-18  
**维护者**: Bazi Predict Team

