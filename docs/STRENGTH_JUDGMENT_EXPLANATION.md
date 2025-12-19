# 旺衰判定逻辑解释

## 📊 您的数据

- **能量占比**: 3.24 (0-10范围)
- **身强概率**: 61.8% (Sigmoid计算)
- **临界点**: 2.54
- **带宽**: 14.5

## ❓ 为什么身强概率61.8%却判定为"弱"？

### 关键理解：两个不同的评分体系

1. **能量占比 (Energy Ratio)**: 0-10范围
   - 您的值：3.24
   - 这是Sigmoid函数的输入（X轴）

2. **旺衰分数 (Strength Score)**: 0-100分
   - 计算公式：`strength_score = 能量占比 × 10`
   - 您的分数：3.24 × 10 = **32.4分**

### 判定逻辑（最终裁决层）

根据 `core/engine_graph.py` 的最终裁决层逻辑：

```python
# 1. 极弱/身弱区间扩大
elif strength_score <= 40.0 or normalized_score_before_override < 0.50:
    final_label = 'Weak'

# 2. 普通强弱（Sigmoid Probability）
else:
    # 必须同时满足：probability >= 0.60 AND score > 50
    if strength_probability >= 0.60 and strength_score > 50.0:
        final_label = 'Strong'
    # 如果score <= 50.0，即使probability高也判定为Weak
    elif strength_score <= 50.0 or strength_probability <= 0.40:
        final_label = 'Weak'
```

### 您的案例判定过程

1. **SVM模型检查**（优先级最高）
   - 如果SVM置信度 > 60%，直接使用SVM结果
   - 如果SVM预测为"弱"，直接返回"弱"

2. **最终裁决层**（如果SVM不适用）
   - `strength_score = 32.4分`
   - `strength_score <= 40.0` ✅ **判定为 Weak**

### 为什么概率61.8%却判定为弱？

**原因**：最终裁决层优先考虑 `strength_score`（0-100分），而不是 `strength_probability`（0-100%）。

**判定规则**：
- 如果 `strength_score <= 40.0`，**直接判定为 Weak**（无论概率多少）
- 只有当 `strength_score > 50.0` **且** `strength_probability >= 0.60` 时，才判定为 Strong

**您的案例**：
- `strength_score = 32.4分` ≤ 40.0 ✅
- 因此判定为 **Weak**（即使概率是61.8%）

### 设计理念

这个设计是为了防止"微弱变强"的误判：
- 即使Sigmoid概率显示"身强概率高"，但如果实际能量分数太低（≤40分），仍然判定为"弱"
- 只有当能量分数足够高（>50分）**且**概率也高（≥60%）时，才判定为"强"

### 如何让判定变为"强"？

需要同时满足：
1. `strength_score > 50.0`（能量占比 > 5.0）
2. `strength_probability >= 0.60`（身强概率 ≥ 60%）

或者：
- `strength_score >= 72.0`（能量占比 ≥ 7.2），直接判定为 **Special_Strong**

