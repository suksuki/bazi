# 📋 FDS-V1.4 规范 Review 报告

**Review日期**: 2025-12-29  
**Reviewer**: Cursor (Core Engine)  
**规范版本**: FDS-V1.4 (The Matrix & Phase Transition)

---

## 一、关键变化总结

### 1.1 三大物理公理（新增）

#### ✅ 公理1: 能量守恒与转化方向 (Conservation of Sign)
- **比劫、印枭** → E 必须为正贡献 (+)
- **财星、食伤** → M 必须为正贡献 (+)
- **冲、刑、七杀** → S 默认正贡献 (+)

**影响**: 转换矩阵的符号方向必须符合此公理。

#### ✅ 公理2: 格局特异性修正 (Pattern Override)
- **A-03修正案**：
  - 七杀 (Power)：从主要贡献 S (灾) 强制扭转为主要贡献 O (秩序/权)
  - 比劫 (Parallel)：从负贡献 M (破财) 强制修正为正贡献 E (抗压底座)

**影响**: 特定格局可以改写物理常数，这是格局特异性的核心。

#### ✅ 公理3: 正交性 (Orthogonality)
- 五维轴线在语义上互斥
- M (钱) ≠ O (权)；E (命) ≠ S (运)

**影响**: 描述必须解耦，不能混淆。

---

### 1.2 转换矩阵（transfer_matrix）- 重大升级

#### ❌ 现有实现（V1.1）
```python
# 简单的frequency_vector映射
E = 比劫 + 印枭
O = 官杀
M = 财星
S = 官杀 - 印枭
R = 食伤
```

#### ✅ V1.4要求
```json
"transfer_matrix": {
  "E_row": {
    "parallel": 1.2,    // 比劫 → E (正贡献)
    "resource": 0.8,    // 印枭 → E (正贡献)
    "wealth": -0.5,     // 财星 → E (负贡献，财坏印)
    "output": -0.2,     // 食伤 → E (负贡献)
    "power": -0.1       // 官杀 → E (负贡献)
  },
  "O_row": {
    "power": 0.9,       // 官杀 → O (主要贡献，格局特异性)
    "parallel": 0.3,    // 比劫 → O (次要贡献)
    ...
  },
  ...
}
```

**关键变化**:
1. 从**简单映射**升级为**5x5矩阵**
2. 支持**负贡献**（如财坏印为忌）
3. 值域 **[-1.0, 1.0]**，由拟合得出
4. 每个十神对每个维度都有贡献（不再是单一映射）

---

### 1.3 成格/破格条件（dynamic_states）- 新增

#### ✅ 破格条件（collapse_rules）
```json
{
  "trigger": "Day_Branch_Clash",
  "action": "Downgrade_Matrix",
  "fallback_matrix": "Standard_Weak_Killings",
  "description": "羊刃逢冲，根基动摇，七杀攻身，S轴爆炸。"
}
```

#### ✅ 成格条件（crystallization_rules）
```json
{
  "condition": "Missing_Blade_Arrives",
  "action": "Upgrade_Matrix",
  "target_matrix": "A-03",
  "validity": "Transient",
  "description": "运至成格，瞬间获得 A-03 矩阵加持。"
}
```

#### ✅ 结构完整性阈值（integrity_threshold）
- **alpha < 0.4** → 破格（降级到标准矩阵）
- **alpha >= 0.4** → 成格（使用格局专属矩阵）
- **公式**: `T_final = alpha * T_Pattern + (1-alpha) * T_Standard`

---

### 1.4 Schema V2.1 vs V2.0 对比

#### ✅ 新增字段
1. `physics_kernel.transfer_matrix` (5x5矩阵)
2. `physics_kernel.integrity_threshold` (alpha阈值)
3. `dynamic_states.collapse_rules` (破格规则)
4. `dynamic_states.crystallization_rules` (成格规则)

#### ❌ 需要迁移
1. 从 `frequency_vector` 映射迁移到 `transfer_matrix`
2. 从 `tensor_operator.weights` 迁移到 `transfer_matrix`
3. 添加 `integrity_threshold` 计算逻辑
4. 实现成格/破格检测机制

---

## 二、关键问题识别

### 2.1 transfer_matrix如何计算？

**问题**: 转换矩阵需要从Tier A样本拟合得出，但具体算法未明确。

**建议**:
1. **梯度下降法**: 调整矩阵权重，使得 `T × V_input` 的结果接近 `y_true`
2. **约束优化**: 必须满足三大公理的约束
3. **初始化**: 可以从现有的frequency_vector映射推导初始值

**示例**:
```python
# 初始化（基于现有映射）
E_row = {
    "parallel": 1.0,    # 比劫 → E
    "resource": 1.0,    # 印枭 → E
    "wealth": 0.0,      # 财星 → E (初始为0)
    "output": 0.0,      # 食伤 → E
    "power": 0.0        # 官杀 → E
}

# 拟合后（由数据驱动）
E_row = {
    "parallel": 1.2,    # 比劫 → E (增强)
    "resource": 0.8,    # 印枭 → E (略降)
    "wealth": -0.5,      # 财星 → E (负贡献，财坏印)
    ...
}
```

---

### 2.2 如何从现有frequency_vector迁移？

**问题**: 当前实现使用硬编码的映射，需要转换为矩阵形式。

**当前代码** (`scripts/fds_v11_refit_a03_v2.py`):
```python
# 基于frequency_vector计算5维投影
bi_jie = frequency_vector.get('比劫', 0.0)
yin_xiao = frequency_vector.get('印枭', 0.0)
guan_sha = frequency_vector.get('官杀', 0.0)
cai_xing = frequency_vector.get('财星', 0.0)
shi_shang = frequency_vector.get('食伤', 0.0)

# 简单映射
E = bi_jie + yin_xiao
O = guan_sha
M = cai_xing
S = guan_sha - yin_xiao
R = shi_shang
```

**V1.4要求**:
```python
# 矩阵乘法
input_vector = {
    "parallel": bi_jie,
    "resource": yin_xiao,
    "power": guan_sha,
    "wealth": cai_xing,
    "output": shi_shang
}

# 5x5矩阵乘法
E = transfer_matrix["E_row"]["parallel"] * bi_jie + \
    transfer_matrix["E_row"]["resource"] * yin_xiao + \
    transfer_matrix["E_row"]["wealth"] * cai_xing + \
    transfer_matrix["E_row"]["output"] * shi_shang + \
    transfer_matrix["E_row"]["power"] * guan_sha
```

**迁移策略**:
1. 保留现有frequency_vector计算逻辑
2. 添加transfer_matrix应用层
3. 逐步迁移，保持向后兼容

---

### 2.3 integrity_threshold如何计算？

**问题**: alpha值的物理意义和计算方法未明确。

**规范定义**:
- `alpha < 0.4` → 破格（降级到标准矩阵）
- `alpha >= 0.4` → 成格（使用格局专属矩阵）

**建议计算方式**:
```python
def calculate_integrity_alpha(chart, pattern_id):
    """
    计算结构完整性alpha值
    
    考虑因素：
    1. 格局核心要素是否完整（如A-03需要羊刃+七杀）
    2. 是否有破坏性因素（如冲、刑、合）
    3. 是否有支撑性因素（如印星通关）
    
    返回: alpha (0.0 - 1.0)
    """
    # 1. 检查格局核心要素
    core_score = check_core_elements(chart, pattern_id)
    
    # 2. 检查破坏性因素
    damage_score = check_damage_factors(chart)
    
    # 3. 检查支撑性因素
    support_score = check_support_factors(chart)
    
    # 综合计算
    alpha = core_score * (1 - damage_score) * (1 + support_score)
    return max(0.0, min(1.0, alpha))
```

---

### 2.4 成格/破格检测如何实现？

**问题**: 需要检测哪些条件，如何触发矩阵切换？

**破格检测**:
```python
def check_collapse(chart, pattern_id, registry):
    """
    检测是否破格
    
    触发条件：
    1. Day_Branch_Clash: 日支羊刃逢冲
    2. Resource_Destruction: 印星被破坏
    3. 其他collapse_rules中定义的条件
    """
    collapse_rules = registry[pattern_id]["dynamic_states"]["collapse_rules"]
    
    for rule in collapse_rules:
        if evaluate_trigger(chart, rule["trigger"]):
            return {
                "collapsed": True,
                "rule": rule,
                "action": rule["action"],
                "fallback_matrix": rule["fallback_matrix"]
            }
    
    return {"collapsed": False}
```

**成格检测**:
```python
def check_crystallization(chart, luck_pillar, year_pillar, pattern_id, registry):
    """
    检测是否成格
    
    触发条件：
    1. Missing_Blade_Arrives: 运至成格（大运/流年补齐格局缺口）
    2. 其他crystallization_rules中定义的条件
    """
    crystallization_rules = registry[pattern_id]["dynamic_states"]["crystallization_rules"]
    
    for rule in crystallization_rules:
        if evaluate_condition(chart, luck_pillar, year_pillar, rule["condition"]):
            return {
                "crystallized": True,
                "rule": rule,
                "action": rule["action"],
                "target_matrix": rule["target_matrix"],
                "validity": rule["validity"]  # Transient or Permanent
            }
    
    return {"crystallized": False}
```

---

## 三、实现建议

### 3.1 分阶段迁移策略

#### 阶段1: 保持兼容（当前）
- 保留现有frequency_vector映射
- 添加transfer_matrix字段（初始化为现有映射）
- 不改变现有计算逻辑

#### 阶段2: 逐步迁移（V1.4）
- 实现transfer_matrix计算逻辑
- 添加integrity_threshold计算
- 实现成格/破格检测

#### 阶段3: 完全迁移（V1.5）
- 移除frequency_vector映射
- 完全使用transfer_matrix
- 优化性能

---

### 3.2 需要新增的函数

#### `core/math_engine.py`
```python
def project_tensor_with_matrix(
    input_vector: Dict[str, float],
    transfer_matrix: Dict[str, Dict[str, float]]
) -> Dict[str, float]:
    """
    使用转换矩阵计算5维投影
    
    Args:
        input_vector: 十神频率向量 {"parallel": float, "resource": float, ...}
        transfer_matrix: 5x5转换矩阵
        
    Returns:
        5维投影向量 {"E": float, "O": float, "M": float, "S": float, "R": float}
    """
    pass
```

#### `core/registry_loader.py`
```python
def calculate_integrity_alpha(
    chart: List[str],
    pattern_id: str
) -> float:
    """
    计算结构完整性alpha值
    
    Returns:
        alpha (0.0 - 1.0)
    """
    pass

def check_pattern_state(
    chart: List[str],
    luck_pillar: str,
    year_pillar: str,
    pattern_id: str
) -> Dict[str, Any]:
    """
    检测成格/破格状态
    
    Returns:
        {
            "state": "CRYSTALLIZED" | "COLLAPSED" | "STABLE",
            "alpha": float,
            "matrix": "A-03" | "Standard",
            ...
        }
    """
    pass
```

---

## 四、与AI设计师需要确认的问题

### 4.1 转换矩阵拟合
- **问题**: transfer_matrix如何从Tier A样本拟合得出？
- **建议**: 使用梯度下降法，约束满足三大公理

### 4.2 结构完整性计算
- **问题**: integrity_threshold (alpha) 的具体计算公式是什么？
- **建议**: 基于格局核心要素、破坏性因素、支撑性因素综合计算

### 4.3 成格/破格触发条件
- **问题**: collapse_rules和crystallization_rules中的条件如何具体判断？
- **建议**: 需要明确每个trigger/condition的具体判断逻辑

### 4.4 向后兼容性
- **问题**: 是否需要保持与V1.1的兼容性？
- **建议**: 分阶段迁移，保持向后兼容

---

## 五、总结

### ✅ 规范优点
1. **物理公理明确**: 三大公理为转换矩阵提供了严格的约束
2. **格局特异性**: 支持格局特异性修正，符合命理实际
3. **动态演化**: 成格/破格机制使系统更加灵活

### ⚠️ 需要澄清
1. **转换矩阵拟合算法**: 需要明确具体的拟合方法
2. **结构完整性计算**: alpha值的计算公式需要明确
3. **成格/破格判断**: 触发条件的具体判断逻辑需要明确

### 🚀 下一步行动
1. 与AI设计师确认上述问题
2. 实现transfer_matrix计算逻辑
3. 实现integrity_threshold计算
4. 实现成格/破格检测机制
5. 更新registry.json到Schema V2.1

---

**Review完成日期**: 2025-12-29  
**状态**: 等待AI设计师确认

