# Antigravity L3 补充文档：格局拓扑协议 (Pattern Topology)
**主题**: 格局结构的通用物理接口
**版本**: V3.0 (The Pattern Standard)
**依赖**: `ALGORITHM_CONSTITUTION_v3.0.md`, `QGA_HR_REGISTRY_SPEC_v3.0.md`
**状态**: ACTIVE (Interface Standard)

---

## 1. 物理识别接口 (Physics Recognition Interface)

### 1.1 协方差矩阵计算接口

**接口定义**: `calculate_covariance_matrix(samples: List[np.ndarray]) -> np.ndarray`

**功能描述**: 计算样本群的5D特征协方差矩阵。

**输入参数**:
- `samples`: 样本列表，每个样本为5D张量向量（形状为 `(5,)` 的numpy数组）

**返回值**:
- `covariance_matrix`: 5x5协方差矩阵（形状为 `(5, 5)` 的numpy数组）

**实现要求**:
- 使用numpy的 `np.cov()` 函数，参数 `rowvar=False`（表示每列是一个变量）
- 确保矩阵正定或使用伪逆处理奇异情况
- 矩阵条件数应在合理范围内（建议 < 1e10）

**示例代码**:
```python
import numpy as np
from typing import List

def calculate_covariance_matrix(samples: List[np.ndarray]) -> np.ndarray:
    """
    计算样本群的5D特征协方差矩阵
    
    Args:
        samples: 样本列表，每个样本为5D张量向量
    
    Returns:
        5x5协方差矩阵
    """
    # 转换为numpy数组 (N, 5)
    tensor_array = np.array(samples)
    
    # 计算协方差矩阵（rowvar=False表示每列是一个变量）
    covariance_matrix = np.cov(tensor_array, rowvar=False)
    
    return covariance_matrix
```

### 1.2 识别得分计算接口

**接口定义**: `get_recognition_score(tensor: np.ndarray, mean: np.ndarray, cov_matrix: np.ndarray, threshold: float) -> Tuple[float, bool]`

**功能描述**: 返回基于马氏距离的成格概率分值，并判定是否入格。

**输入参数**:
- `tensor`: 样本的5D张量向量（形状为 `(5,)` 的numpy数组）
- `mean`: 格局的均值向量（形状为 `(5,)` 的numpy数组）
- `cov_matrix`: 格局的协方差矩阵（形状为 `(5, 5)` 的numpy数组）
- `threshold`: 马氏距离阈值（从配置读取，标准值3.0）

**返回值**:
- `mahalanobis_distance`: 马氏距离值
- `is_recognized`: 布尔值，表示是否入格（True表示入格）

**计算公式**:
$$
D_M = \sqrt{(T_{fate} - \mu)^T \Sigma^{-1} (T_{fate} - \mu)}
$$

**实现要求**:
- 使用 `numpy.linalg.pinv()` 计算协方差矩阵的伪逆（处理奇异情况）
- 如果协方差矩阵不可逆，降级为加权欧氏距离
- 判定准则: `is_recognized = (mahalanobis_distance < threshold)`

**示例代码**:
```python
import numpy as np
from typing import Tuple

def get_recognition_score(
    tensor: np.ndarray,
    mean: np.ndarray,
    cov_matrix: np.ndarray,
    threshold: float
) -> Tuple[float, bool]:
    """
    返回基于马氏距离的成格概率分值，并判定是否入格
    
    Args:
        tensor: 样本的5D张量向量
        mean: 格局的均值向量
        cov_matrix: 格局的协方差矩阵
        threshold: 马氏距离阈值
    
    Returns:
        (mahalanobis_distance, is_recognized)
    """
    diff = tensor - mean
    
    try:
        # 计算马氏距离: sqrt((x - μ)^T Σ^(-1) (x - μ))
        inv_cov = np.linalg.pinv(cov_matrix)  # 使用伪逆以防奇异
        mahal_dist = np.sqrt(np.dot(np.dot(diff, inv_cov), diff))
    except np.linalg.LinAlgError:
        # 如果矩阵奇异，降级为加权欧氏距离
        mahal_dist = np.sqrt(np.dot(diff, diff))
    
    is_recognized = mahal_dist < threshold
    
    return mahal_dist, is_recognized
```

---

## 2. 核心定义 (Core Definition)
格局是特定能量流动的 **拓扑结构 (Topological Structure)**。
所有格局模块必须实现 `IPatternPhysics` 接口，包含三个强制组件。

---

## 3. 能量门控协议 (Energy Gating Protocol)
* **物理原理**: 只有达到 **临界质量 (Critical Mass)** 的命局才能支撑高阶结构。
* **实现要求**: 
    * 严禁在代码中写死阈值。
    * 必须调用 `@config.gating.min_self_energy` 进行判定。
    * 未通过门控者，必须标记为 `COLLAPSED` (破格)。

---

## 4. 拓扑分型标准 (Topology Standard)
* **同分异构体**: 一个格局 ID 下必须包含多个子流形 (Sub-Patterns)，分别对应不同的能量路径（如"正官佩印" vs "财官双美"）。
* **数据映射**: L3 拓扑直接映射到 Registry JSON 中的 `sub_patterns_registry` 数组。

---

## 5. 安全阀机制 (Safety Valve Mechanism)
* **物理原理**: 防止系统过载的负反馈机制。
* **类型**:
    * **阻尼 (Damping)**: 印星吸收压力。
    * **疏导 (Conductance)**: 财星导出能量。
    * **对抗 (Counter-Acting)**: 食伤制衡七杀。
* **输出**: 必须在结果元数据中包含安全阀的状态报告。
