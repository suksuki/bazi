# 层级化配置系统升级文档 (V3.2)

## 概述

本次升级实现了**层级化配置系统 (Cascading Configuration)**，解决了"按下葫芦浮起瓢"的参数管理问题。

**核心问题**：
- A-03 (七杀格) 需要"宽容度高"的参数（动态平衡特性）
- A-01 (正官格) 需要"精准度高"的参数（纯粹性要求）
- 如果共用一套参数，调好了七杀，正官就崩了

**解决方案**：
- **L1 (Global Physics)**: 宇宙基准物理参数，适用于90%情况的默认值
- **L2 (Category Defaults)**: 族群特征参数（如财富组、官杀组等）
- **L3 (Pattern Specifics)**: 格局特异性参数，可以重写L1和L2

---

## 配置层级结构

### L1: Global Physics (宇宙基准物理)

```python
config.physics.precision_gaussian_sigma = 2.5      # 默认值
config.physics.precision_energy_gate_k = 0.4       # 默认值
config.physics.precision_weights = {0.5, 0.5}      # 默认平衡
```

### L3: Pattern Specifics (格局特异性参数)

| 格局 | Sigma | Energy K | Weights | 说明 |
|------|-------|----------|---------|------|
| **A-03** (七杀) | **2.2** | **0.35** | 0.5/0.5 | 高宽容度，动态平衡 |
| **A-01** (正官) | **1.8** | **0.45** | **0.8/0.2** | 高纯度，形状优先 |
| **D-02** (偏财) | **3.0** | **0.3** | **0.7/0.3** | 允许波动，形状优先 |

> 注意：**加粗**的参数是L3特异性值，重写了L1默认值

---

## API 使用指南

### 基础使用

```python
from core.config import get_pattern_param, get_pattern_weights

# 获取格局特异性参数（自动继承）
sigma = get_pattern_param('A-03', 'precision_gaussian_sigma')  
# 返回: 2.2 (L3特异性值，重写了L1的2.5)

weights = get_pattern_weights('A-03')
# 返回: {'similarity': 0.5, 'distance': 0.5}

# 未知格局自动回退到L1默认值
sigma_unknown = get_pattern_param('X-99', 'precision_gaussian_sigma')
# 返回: 2.5 (L1全局默认值)
```

### 在拟合脚本中使用

```python
from core.config import get_pattern_param

def fit_pattern(pattern_id: str, ...):
    # 获取格局特异性saturation_k
    saturation_k = get_pattern_param(
        pattern_id, 
        'k_factor', 
        default_value=config.physics.k_factor
    )
    
    fitter = HolographicMatrixFitter(
        saturation_k=saturation_k  # 使用层级化配置
    )
```

### 在样本过滤中使用

```python
def filter_samples_for_pattern(pattern_id: str, ...):
    # 使用格局特异性阈值
    min_e = get_pattern_param(
        pattern_id, 
        'standard_e_min', 
        default_value=config.gating.min_self_energy
    )
    
    if tensor[0] < min_e:  # E能量不足
        keep = False
```

---

## 更新的文件

### 1. `core/config.py` ✅

- ✅ 实现了层级化配置类结构
- ✅ 添加了 `get_pattern_param()` 函数（支持继承）
- ✅ 添加了 `get_pattern_weights()` 函数
- ✅ 定义了所有格局的L3特异性参数

### 2. `scripts/run_fds_v3_grand_slam.py` ✅

- ✅ 集成 `get_pattern_param()` 到拟合流程
- ✅ 样本过滤函数使用配置参数（替代硬编码）
- ✅ `saturation_k` 参数从配置读取
- ✅ 协议注入中添加Precision Score参数引用

### 3. `core/config_usage_example.py` ✅

- ✅ 创建了完整的使用示例文档

---

## 参数继承优先级

```
优先级: L3 (Pattern Specific) > L1 (Global Physics)
```

**示例**：
- `get_pattern_param('A-03', 'precision_gaussian_sigma')`
  1. 首先查找 `config.patterns.a03.precision_gaussian_sigma` → 找到 `2.2` ✅
  2. 返回 L3 值 `2.2`

- `get_pattern_param('UNKNOWN', 'precision_gaussian_sigma')`
  1. 查找 `config.patterns.unknown` → 不存在 ❌
  2. 回退到 `config.physics.precision_gaussian_sigma` → 找到 `2.5` ✅
  3. 返回 L1 值 `2.5`

---

## 配置值对比表

### Precision Gaussian Sigma (高斯衰减参数)

| 格局 | L3值 | L1默认值 | 说明 |
|------|------|----------|------|
| A-03 | 2.2 | 2.5 | 更严，防止泛化 |
| A-01 | 1.8 | 2.5 | 最严，要求纯粹 |
| D-02 | 3.0 | 2.5 | 更松，允许波动 |
| 其他 | - | 2.5 | 使用默认值 |

### Precision Energy Gate K (能量门控阈值)

| 格局 | L3值 | L1默认值 | 说明 |
|------|------|----------|------|
| A-03 | 0.35 | 0.4 | 放宽，允许动态平衡 |
| A-01 | 0.45 | 0.4 | 收紧，身弱不能任官 |
| D-02 | 0.3 | 0.4 | 最宽，允许身稍弱 |
| B-02 | 0.5 | 0.4 | 最严，身弱伤旺必泄 |
| 其他 | - | 0.4 | 使用默认值 |

### Precision Weights (相似度/距离权重)

| 格局 | L3值 | L1默认值 | 说明 |
|------|------|----------|------|
| A-03 | 0.5/0.5 | 0.5/0.5 | 保持平衡 |
| A-01 | **0.8/0.2** | 0.5/0.5 | **形状优先** |
| D-02 | **0.7/0.3** | 0.5/0.5 | **形状优先** |
| 其他 | - | 0.5/0.5 | 使用默认值 |

---

## 向后兼容性

- ✅ 保持了所有原有配置的访问方式
- ✅ `config.patterns.a03` 仍然可以通过字典方式访问（向后兼容）
- ✅ 所有 `@config.xxx` 引用路径保持不变
- ✅ 现有代码无需修改即可运行

---

## 下一步建议

1. ✅ **已完成**: 层级化配置系统实现
2. ✅ **已完成**: 拟合脚本集成
3. ⏳ **待完成**: 更新所有计算模块使用新的配置API
4. ⏳ **待完成**: 添加更多格局的L3特异性参数

---

## 参考文件

- `core/config.py`: 配置定义
- `core/config_usage_example.py`: 使用示例
- `scripts/run_fds_v3_grand_slam.py`: 拟合脚本集成示例

---

**版本**: V3.2  
**日期**: 2026-01-01  
**状态**: ✅ 已完成并测试通过

