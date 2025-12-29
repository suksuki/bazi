# 🏛️ QGA 建模规范执行细则 (Technical Spec)
## FDS-V1.1 执行细则补遗 (Addendum)

**作者**：QGA 首席 AI 设计师  
**日期**：2025-12-29  
**版本**：V1.1 Addendum

---

## 1. AI 分析师的输出协议 (Output Protocol)

### 格式要求
AI 必须采用 **JSON + 物理意象文本** 的混合结构。

### 归一化约束
所有权重系数必须遵循 **Unit Vector Constraint**，即 $\sum_{i=1}^{5} w_i = 1$。

### SAI 基准定标
采用 $\text{SAI}_{calibration} = \{M: \text{敏感度}, O: \text{偏移量}\}$。

### 标准输出模板示例

```json
{
  "SAI_Calibration": { 
    "M": 8.5, 
    "O": 4.2 
  }, 
  "Vector_W": [0.1, 0.4, 0.3, 0.1, 0.1], 
  "Physical_Image": "高密质量场(Wu)受焦耳热辐射(Bing)激发..."
}
```

---

## 2. "科研纯净集"的定标 (Dataset Standards)

### 筛选标准 (Tier A)
必须包含精确到**时辰**的四柱，且具备至少 3 个**确定性人生节点**（如：2015结婚、2020晋升）。

### 标签来源
采用 **"双向拟合"标注法**，即：
- 人工名家批注（专家先验）
- 历史大事件回测（物理事实）

### 初始规模
V1.1 阶段锁定 **500 例** 黄金级 (Gold Standard) 案例。

---

## 3. 非线性激活与相变 (Activation & Phase Change)

### 激活函数
主要应用于 $\mathbf{E}$ (寿夭) 与 $\mathbf{M}$ (财富) 轴，采用 **Modified Sigmoid**。

$$\sigma(x) = \frac{1}{1 + e^{-k(x - x_0)}}$$

其中：
- $x_0$ 为临界值（崩塌点）
- $k$ 为应力斜率

### 相变定义
当库神能级 $E_{vault} > 0.8$ 且遇冲时，触发**量子隧穿 (Tunneling)**，能量倍率 $\beta$ 跃迁至 1.5x 以上。

---

## 4. 动力学耦合算法 (Coupling Dynamics)

### 数学形式
大运与流年采用 **张量积 ($\otimes$)** 产生交互效应，而非简单的线性叠加。

$$\mathcal{T}_{final} = \mathcal{T}_{base} \otimes \omega_{luck} \oplus \Delta \mathcal{T}_{year}$$

### 地理因子 ($\delta$)
作为**全局增益系数**作用于五行矢量场。例如：南方 $\delta_{fire} = 1.15$。

---

## 🔧 针对 QGA-HR V1.0 的修正动作

为了响应 Cursor 的反馈，建议立即在注册表架构中追加以下**稳定性约束 (Stability Guards)**：

| 修正项 | 实施路径 | 目的 |
| --- | --- | --- |
| **权重归一化器** | 注入 `structure.normalizeWeights` 函数 | 防止权重发散导致计算结果超过 100 分。 |
| **残差阈值报警** | 设置 `error_threshold = 0.2` | 当模拟结果与真实事件偏差 >20% 时，强制触发"参数审计"。 |
| **刑冲保护锁** | 引入 `resolutionCost` | 模拟"贪合忘冲"的物理损耗，防止交互逻辑陷入死循环。 |

---

## 🚀 下一步执行指令

Cursor 的反馈实际上是要求我们将 **"玄学意象"** 彻底转化为 **"工程语言"**。

---

**状态**：已确认，待实施

