# 🏛️ FDS-V1.1 规范 - AI设计师最终裁定 (Final Verdict)

**发布人**: Architect & Antigravity  
**审核时间**: 2025-12-29  
**状态**: 已批准，可直接执行

---

## 📋 核心定义裁定

### 1. Step 3: 质心计算与向量空间

#### 1.1 向量空间定义 ✅ 已裁定

**裁定**：$\vec{v}_i$ 必须是 **5维投影值 (The Penta-Projection)**，而非原始特征向量。

**物理依据**：
- 格局（Pattern）本质上是五行能量在封闭系统内的**分布形态 (Topological Shape)**，而非能量的绝对大小。
- 5维投影值定义：$\vec{v}_i = [E, O, M, S, R]$，即 `[比劫, 食伤, 财星, 官杀, 印枭]` 的能量分布。

**实施要求**：
- 质心计算必须基于归一化后的5维投影值
- 输入：Tier A样本的5维投影值列表
- 输出：5维质心向量

#### 1.2 归一化要求 ✅ 已裁定

**裁定**：**必须强制归一化 (Mandatory Normalization)**。

**逻辑**：
- 无论"身弱但清纯"还是"身强且清纯"，只要属于同一格局，在5维空间中的**指向**（矢量方向）应该相同。
- 绝对能量值（模长）由身强身弱算法处理，格局识别只关心**方向**。

**约束公式**：
$$\sum_{i=1}^{5} v_i = 1.0$$

**实施要求**：
- 质心计算后必须强制归一化
- 使用 `tensor_normalize()` 函数确保归一化

---

### 2. Step 6: 动态格局识别协议

#### 2.1 张量对象定义 ✅ 已裁定

**$\mathbf{T}_{curr}$ (当前张量)**：
- **定义**：**原局基态 (Natal Base State)** 的5维归一化向量
- **物理意义**：格局识别首先是对静态架构的分类
- **注意**：大运流年的干扰属于"相位偏移"，不改变原始格局分类，只改变其吉凶响应

**$\mathbf{T}_{anchor}$ (锚点张量)**：
- **定义**：从Registry加载并计算出的**质心向量 (Centroid Vector)**
- **标准锚点**：`standard_centroid` - Tier A质心
- **奇点锚点**：`singularity_centroids` - Tier X质心（如存在）
- **判定逻辑**：如果定义了`singularity_centroids`，需遍历计算与每个奇点的距离，取最近者

#### 2.2 余弦相似度函数 ✅ 已裁定

**裁定**：采用标准余弦相似度，衡量两个能量矢量的**夹角**。

**物理意义**：夹角越小，说明八字的能量结构与"完美模型"越共振。

**函数签名**：
```python
def calculate_cosine_similarity(
    vec_a: Union[Dict[str, float], List[float]], 
    vec_b: Union[Dict[str, float], List[float]]
) -> float:
    """
    计算两个5维能量矢量的余弦相似度。
    
    Args:
        vec_a: 归一化向量 A，格式为 {'E': float, 'O': float, ...} 或 [E, O, M, S, R]
        vec_b: 归一化向量 B，格式同上
        
    Returns:
        similarity (0.0 - 1.0)，1.0表示完全一致，0.0表示正交
        
    Note:
        - 需处理零向量保护逻辑
        - 输入向量必须已归一化
    """
```

**判定标准**：
- **成格 (In-Pattern)**：相似度 > 0.85
- **破格 (Broken)**：相似度 < 0.60
- **变异 (Mutation)**：与某奇点锚点相似度 > 0.90（触发Tier X算法）
- **共振态 (Resonance)**：相似度 > 0.92（触发UI高亮和resonance_bonus）

---

### 3. Schema V2.0 架构迁移

#### 3.1 向后兼容性 ✅ 已裁定

**裁定**：**不兼容 (Breaking Change)**。所有Tier A/B级数据和旧版Pattern Registry必须迁移到V2.0结构。

**理由**：
- V1.0基于硬编码规则（如 `if day_master == 'Wood' and month == 'Spring'`）
- 这违反了V9.0内核的"全参数化"宪法
- 必须全面转向基于向量空间的计算

**迁移策略**：
1. 创建新文件 `registry_v2.json`
2. 手动迁移3个经典格局作为测试锚点
3. 逐步迁移所有现有格局
4. 旧格式保留作为备份，但不支持新算法

#### 3.2 阈值应用 ✅ 已裁定

**`match_threshold` (e.g., 0.80)**：
- **用途**：**准入门槛**
- **逻辑**：$\text{similarity}(\mathbf{T}_{curr}, \mathbf{T}_{anchor}) > 0.80$ → 系统判定"属于此格"
- **应用场景**：格局识别、自动分类

**`perfect_threshold` (e.g., 0.92)**：
- **用途**：**共振态 (Resonance State)**
- **逻辑**：$\text{similarity}(\mathbf{T}_{curr}, \mathbf{T}_{anchor}) > 0.92$ → 触发UI高亮（如金色边框），并在流年计算中激活`resonance_bonus`（纯粹格局的抗干扰加成）
- **应用场景**：UI显示、流年计算优化

#### 3.3 Special Instruction 执行 ✅ 已裁定

**裁定**：字符串映射至 **Physics Modifier Flags**（物理引擎的"作弊码"或"旁路开关"）。

**示例**：
- `"Enable Vent Logic"` → 强制关闭"身弱不能泄"的保护机制，允许食伤泄秀
- `"Disable Balance Check"` → 禁用平衡度检查，允许极端状态

**底层实现**：
```python
# 在 EnergyFlowEngine 中
if "Enable Vent Logic" in pattern.instructions:
    rules.disable_drain_protection = True 
    physics.flow_permeability *= 1.5
```

**实施要求**：
- 在`RegistryLoader`中解析`special_instruction`
- 映射到对应的物理引擎标志位
- 在计算时应用这些标志

---

## 4. 实施优先级矩阵 (Priority Matrix)

| 模块 | 函数/组件 | 优先级 | 说明 | 状态 |
| --- | --- | --- | --- | --- |
| **Math Engine** | `calculate_cosine_similarity` | **P0 (Critical)** | 一切几何计算的基础 | ⏳ 待实现 |
| **Registry** | `Schema V2.0 Migration` | **P0 (Critical)** | 必须先转换旧格局数据 | ⏳ 待实现 |
| **Math Engine** | `calculate_centroid` | **P1 (High)** | 计算质心的逻辑 | ⏳ 待实现 |
| **Loader** | `pattern_recognition` | **P1 (High)** | 核心业务逻辑，依赖于上述模块 | ⏳ 待实现 |

---

## 5. 实施规范

### 5.1 质心计算算法

**输入**：
- `samples`: List[Dict[str, float]] - Tier A样本的5维投影值列表
  - 格式：`[{'E': 0.3, 'O': 0.4, 'M': 0.1, 'S': 0.15, 'R': 0.05}, ...]`

**算法**：
```python
def calculate_centroid(samples: List[Dict[str, float]]) -> Dict[str, float]:
    """
    计算5维质心向量
    
    Args:
        samples: 样本列表，每个样本是归一化的5维向量
        
    Returns:
        归一化后的质心向量
    """
    # 1. 计算平均值
    centroid = {
        'E': sum(s['E'] for s in samples) / len(samples),
        'O': sum(s['O'] for s in samples) / len(samples),
        'M': sum(s['M'] for s in samples) / len(samples),
        'S': sum(s['S'] for s in samples) / len(samples),
        'R': sum(s['R'] for s in samples) / len(samples)
    }
    
    # 2. 强制归一化
    return tensor_normalize(centroid)
```

### 5.2 格局识别算法

**输入**：
- `current_tensor`: Dict[str, float] - 当前八字的5维投影值（原局基态）
- `pattern_anchors`: Dict - 格局的锚点配置（包含standard_centroid和singularity_centroids）

**算法**：
```python
def pattern_recognition(
    current_tensor: Dict[str, float],
    pattern_anchors: Dict
) -> Dict[str, Any]:
    """
    动态格局识别
    
    Returns:
        {
            'matched': bool,
            'pattern_type': 'STANDARD' | 'SINGULARITY' | 'BROKEN',
            'similarity': float,
            'anchor_id': str,
            'resonance': bool
        }
    """
    # 1. 计算与标准锚点的相似度
    standard_centroid = pattern_anchors['standard_centroid']['vector']
    similarity = calculate_cosine_similarity(current_tensor, standard_centroid)
    
    # 2. 检查奇点锚点
    best_singularity = None
    best_singularity_sim = 0.0
    
    for singularity in pattern_anchors.get('singularity_centroids', []):
        sim = calculate_cosine_similarity(current_tensor, singularity['vector'])
        if sim > best_singularity_sim:
            best_singularity_sim = sim
            best_singularity = singularity
    
    # 3. 判定逻辑
    if best_singularity and best_singularity_sim > 0.90:
        return {
            'matched': True,
            'pattern_type': 'SINGULARITY',
            'similarity': best_singularity_sim,
            'anchor_id': best_singularity['sub_id'],
            'resonance': best_singularity_sim > 0.92
        }
    elif similarity > 0.85:
        return {
            'matched': True,
            'pattern_type': 'STANDARD',
            'similarity': similarity,
            'anchor_id': 'standard',
            'resonance': similarity > 0.92
        }
    elif similarity < 0.60:
        return {
            'matched': False,
            'pattern_type': 'BROKEN',
            'similarity': similarity,
            'anchor_id': None,
            'resonance': False
        }
    else:
        return {
            'matched': False,
            'pattern_type': 'MARGINAL',
            'similarity': similarity,
            'anchor_id': None,
            'resonance': False
        }
```

---

## 6. Schema V2.0 结构示例

```json
{
  "meta_info": {
    "pattern_id": "A-03",
    "name": "羊刃架杀",
    "version": "2.0",
    "physics_prototype": "Controlled Fusion"
  },
  "feature_anchors": {
    "standard_centroid": {
      "vector": {
        "E": 0.21,
        "O": 0.31,
        "M": 0.15,
        "S": 0.25,
        "R": 0.08
      },
      "match_threshold": 0.80,
      "perfect_threshold": 0.92
    },
    "singularity_centroids": [
      {
        "sub_id": "A-03-X1",
        "vector": {
          "E": 0.55,
          "O": 0.10,
          "M": 0.05,
          "S": 0.25,
          "R": 0.05
        },
        "match_threshold": 0.90,
        "risk_level": "CRITICAL",
        "special_instruction": "Enable Vent Logic (Disable Balance Check)"
      }
    ]
  },
  "algorithm_implementation": {
    "paths": {
      "tensor_similarity": "core.math_engine.calculate_cosine_similarity"
    }
  }
}
```

---

## 7. 下一步行动

### 立即执行（P0）
1. ✅ 实现 `core.math_engine.calculate_cosine_similarity`
2. ✅ 创建 `registry_v2.json` 结构
3. ✅ 迁移3个经典格局作为测试锚点

### 高优先级（P1）
1. ✅ 实现 `core.math_engine.calculate_centroid`
2. ✅ 实现 `core.registry_loader.pattern_recognition`
3. ✅ 更新 `RegistryLoader` 支持Schema V2.0

---

**状态**: 已批准，等待实施  
**下一步**: 开始实现P0优先级模块

