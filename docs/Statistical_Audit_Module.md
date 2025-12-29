# 统计审计工具模块文档 (Statistical Audit Module)

## 概述

统计审计工具模块 (`core.statistical_audit`) 是 QGA V25.0 格局审计系统的核心基础设施，遵循 **RSS-V1.4 规范**，提供通用的统计方法用于格局审计中的离群值检测、梯度消失判定、分布统计和奇点存在性验证。

## 模块信息

- **模块ID**: `MOD_22_STATISTICAL_AUDIT`
- **主题**: `FRAMEWORK_UTILITIES`
- **层级**: `ALGO`
- **版本**: V1.4
- **规范**: RSS-V1.4

## 核心类

### `StatisticalAuditor`

统计审计器类，提供所有统计审计功能。

#### 初始化

```python
from core.statistical_audit import StatisticalAuditor

auditor = StatisticalAuditor(
    z_score_threshold=3.0,    # Z-Score阈值（默认3.0，即3-Sigma规则）
    gradient_threshold=0.05  # 梯度消失判定阈值（默认0.05，即5%差异）
)
```

#### 主要方法

##### 1. `detect_outliers(values, method="combined")`

离群值检测（RSS-V1.4规范：动态离群值检测）

**参数**:
- `values`: `List[float]` - 数值列表（如稳定性值）
- `method`: `str` - 检测方法（"z_score", "iqr", "combined"）

**返回**:
```python
{
    "outlier_indices": List[int],      # 离群值索引列表
    "normal_indices": List[int],       # 正常值索引列表
    "statistics": {
        "mean": float,                 # 均值
        "std": float,                  # 标准差
        "median": float,                # 中位数
        "min": float,                   # 最小值
        "max": float,                   # 最大值
        "skewness": float,              # 偏度
        "q1": float,                    # 第一四分位数
        "q3": float,                    # 第三四分位数
        "iqr": float,                   # 四分位距
        "lower_bound": float,           # IQR下界
        "upper_bound": float            # IQR上界
    },
    "z_scores": List[float],            # Z-Score列表
    "detection_methods": {
        "z_score_outliers": int,        # Z-Score检测到的离群值数量
        "iqr_outliers": int,            # IQR检测到的离群值数量
        "combined_outliers": int,       # 组合方法检测到的离群值数量
        "method_used": str              # 使用的方法
    },
    "has_outliers": bool                # 是否存在离群值
}
```

**示例**:
```python
stability_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.01, 0.02]
result = auditor.detect_outliers(stability_values, method="combined")
print(f"检测到 {len(result['outlier_indices'])} 个离群值")
```

##### 2. `check_gradient_vanishing(values, outlier_indices=None)`

梯度消失判定（RSS-V1.4规范：逻辑平滑检测）

**参数**:
- `values`: `List[float]` - 数值列表
- `outlier_indices`: `Optional[List[int]]` - 离群值索引列表（如果已检测）

**返回**:
```python
{
    "has_gradient": bool,               # 是否存在显著梯度
    "gradient": float,                  # 梯度值（均值 - 最差值）
    "gradient_ratio": float,            # 相对差异百分比
    "mean": float,                      # 均值
    "worst": float,                     # 最差值
    "verdict": str                      # 判定结果（"has_gradient" 或 "gradient_vanished"）
}
```

**RSS-V1.4规范**: 如果差异小于20%，判定为"逻辑平滑"，拒绝奇点注册。

**示例**:
```python
values = [0.5, 0.51, 0.52, 0.53, 0.54, 0.05, 0.06, 0.07]
result = auditor.check_gradient_vanishing(values)
if result["has_gradient"]:
    print(f"存在显著梯度: {result['gradient']:.4f}")
else:
    print("梯度消失，判定为逻辑平滑")
```

##### 3. `calculate_distribution_stats(values)`

计算分布统计量（RSS-V1.4规范：全量分布审计）

**参数**:
- `values`: `List[float]` - 数值列表

**返回**:
```python
{
    "count": int,                       # 样本数量
    "mean": float,                      # 均值
    "std": float,                       # 标准差
    "median": float,                    # 中位数
    "min": float,                       # 最小值
    "max": float,                       # 最大值
    "q1": float,                        # 第一四分位数
    "q3": float,                        # 第三四分位数
    "iqr": float,                       # 四分位距
    "skewness": float,                  # 偏度
    "kurtosis": float,                  # 峰度
    "dynamic_singularity_threshold": float  # 动态离群红线（RSS-V1.4核心特性）
}
```

**动态离群红线公式** (RSS-V1.4规范):
$$S_{singular} = \min(0.15, \mu - 3\sigma)$$

**示例**:
```python
stats = auditor.calculate_distribution_stats(stability_values)
print(f"均值: {stats['mean']:.4f}")
print(f"标准差: {stats['std']:.4f}")
print(f"动态离群红线: {stats['dynamic_singularity_threshold']:.4f}")
```

##### 4. `verify_singularity_existence(values, outlier_indices=None)`

奇点存在性验证（RSS-V1.4规范：统计层面验证）

**参数**:
- `values`: `List[float]` - 数值列表
- `outlier_indices`: `Optional[List[int]]` - 离群值索引列表（如果已检测）

**返回**:
```python
{
    "singularity_exists": bool,         # 是否存在奇点
    "verdict": str,                     # 判定结果（"singularity_exists" 或 "no_singularity"）
    "reason": str,                       # 原因（"verified", "no_statistical_outliers", "gradient_vanished", "unknown"）
    "outlier_detection": Dict,          # 离群值检测结果
    "gradient_check": Dict,              # 梯度检查结果
    "statistics": Dict                   # 分布统计结果
}
```

**RSS-V1.4规范**: 只有同时满足"存在离群值"和"存在梯度"时，才判定为存在奇点。

**示例**:
```python
verification = auditor.verify_singularity_existence(stability_values)
if verification["singularity_exists"]:
    print("✅ 存在奇点，需要LLM会诊")
else:
    print(f"❌ 不存在奇点，原因: {verification['reason']}")
```

## 单例模式

模块提供了全局单例实例：

```python
from core.statistical_audit import get_statistical_auditor

auditor = get_statistical_auditor()  # 获取全局实例
```

## 在格局审计中的应用

### Step B: 动态因子全量仿真与统计分布

```python
# 1. 执行全量仿真，获取所有样本的稳定性
stability_values = [s['system_stability'] for s in all_samples]

# 2. 计算分布统计
stats = auditor.calculate_distribution_stats(stability_values)

# 3. 检测离群值（3-Sigma原则）
outlier_result = auditor.detect_outliers(stability_values, method="combined")

# 4. 标记潜在奇点候选
potential_singularities = [all_samples[i] for i in outlier_result["outlier_indices"]]
```

### Step C: 奇点存在性验证与语义审计

```python
# 1. 验证奇点存在性
verification = auditor.verify_singularity_existence(stability_values)

# 2. 如果存在奇点，进入LLM会诊
if verification["singularity_exists"]:
    # 获取离群样本
    outlier_samples = [all_samples[i] for i in verification["outlier_detection"]["outlier_indices"]]
    
    # 调用LLM进行语义审计
    for sample in outlier_samples:
        llm_result = llm_synthesizer.analyze_singularity(sample)
        # ... 处理LLM结果
else:
    # 仅输出常态报告
    print(f"不存在奇点，原因: {verification['reason']}")
```

## 注册的算法规则

以下算法规则已注册到 `logic_manifest.json`:

1. **ALGO_OUTLIER_DETECTION**: 离群值检测算法
2. **ALGO_GRADIENT_CHECK**: 梯度消失判定算法
3. **ALGO_DISTRIBUTION_STATS**: 分布统计算法
4. **ALGO_SINGULARITY_VERIFICATION**: 奇点存在性验证算法

## 测试

运行测试套件：

```bash
# 单元测试
python tests/test_statistical_audit.py

# 全面自动化测试
python tests/test_rss_v1_4_comprehensive.py
```

## 参考

- **规范文档**: `docs/RSS-V1.4_Specification.md`
- **模块注册**: `core/logic_manifest.json` (MOD_22_STATISTICAL_AUDIT)
- **源码**: `core/statistical_audit.py`

## 版本历史

- **V1.4** (2025-12-28): RSS-V1.4规范实现，支持动态离群值检测和奇点存在性验证

