# 📜 QGA 格局全息注册表 (QGA-HR V1.0)
—— 格局数字化身份证与资产管理协议 ——

## 一、注册表定位

本注册表用于锁定每一个格局专题的物理属性、数学权重及演化算法，确保所有分析均基于统一的"算法骨架"，支持实时调优与全量回溯。

## 二、层级命名规范

### L1 (Category)：大类
- 示例：`[A]` 杀刃类、`[B]` 食财类

### L2 (Subject ID)：专题唯一编号
- 示例：`[A-03]` 羊刃架杀

### L3 (Variants)：子结构变体
- 示例：`[A-03-V1]` 刃重杀轻

## 三、核心注册模块 (Standard Metadata)

### 模块 I：语义意象层 (Semantic Seed)

**内容**：由 AI 分析师执行的格局物理意象解构。

**定义**：将古典判词转化为物理态描述（如：能量流向、约束场强度、振幅频率）。

### 模块 II：张量投影算子 (Tensor Operator)

**核心参数**：定义 SAI (总能级) 向五维轴分配的初始权重系数 $\mathbf{W}$。

- **$w_E$ (能级轴)**：生命总量与抗压底气
- **$w_O$ (秩序轴)**：权力、名誉、社会地位
- **$w_M$ (物质轴)**：财富、资产、执行转化
- **$w_S$ (应力轴)**：健康损耗、结构扭曲、意外
- **$w_R$ (关联轴)**：六亲交互、情感、人际网络

**激活函数**：注册非线性转换算法（如 Sigmoid），定义能量爆发或坍缩的阈值。

### 模块 III：动力学演化注册 (Kinetic Evolution)

- **触发算子 (Trigger)**：定义引起张量突变的因子（如：冲、穿、刑的相位变化）
- **增益算子 (Gain)**：定义引起能级跃迁的因子（如：格局清纯度的提升点）
- **地理阻尼 ($\delta$)**：注册环境对张量传导的修正系数

### 模块 IV：审计对撞历史 (Audit Trail)

- **统计底色**：51.84 万全量样本中的覆盖率
- **命中指标**：记录历史回测（Ground Truth）的命中率
- **参数记录**：保留每一次调优的版本历史（Version Control）

## 四、实时调优与回溯机制 (Evolutionary Logic)

### 在线校准
根据个案反馈，实时微调模块 II 中的投影系数 $\mathbf{W}$。

### 离线对撞
参数变更后，自动触发 51.84 万样本的全量回溯，验证一致性。

### 版本回滚
支持一键恢复至之前的稳定注册版本。

## 五、使用说明

### 调用指令
执行任何分析前，必须声明"基于 QGA-HR [ID] 的注册参数"。

### 注册前提
必须先经过 FDS-V1.1 的正向拟合流程，方可正式注册封卷。

---

## 模块 V：算法复原内核 (Algorithm Implementation Kernel)

**—— 基于 Core Engine (v1.0) 的实机调用协议 ——**

本注册表中的所有物理参数，必须通过 QGA 系统底层的 Python 引擎进行实例化。以下是标准调用映射：

### 5.1 引擎路径映射 (Engine Path Mapping)

所有计算请求必须路由至以下核心模块：

```json
"algorithm_implementation": {
  "energy_calculation": "core.physics_engine.compute_energy_flux",
      // 功能：读取任意十神的物理场强（支持月令加权）
  "activation_function": "core.math_engine.sigmoid_variant",
      // 功能：执行非线性投影（支持 k斜率 和 x0阈值）
  "core_equation": "core.math_engine.calculate_s_balance",
      // 功能：计算主轴的平衡度或对抗度
  "flow_factor": "core.math_engine.calculate_flow_factor",
      // 功能：计算通关组件（印星）的安全系数
  "interaction_damping": "core.physics_engine.calculate_interaction_damping",
      // 功能：计算刑冲合害的拓扑结构与阻尼系数 lambda
  "phase_change": "core.math_engine.phase_change_determination",
      // 功能：判定是否触发奇点（Tunneling/Collapse）
  "registry_loader": "core.registry_loader.RegistryLoader"
      // 功能：读取本 JSON 配置并驱动上述引擎
}
```

### 5.2 核心算法逻辑 (Core Logic Description)

#### 1. 静态拟合流 (Static Fitting Flow)
- `Loader` 读取 `[A-03]` 配置
- 调用 `energy_calculation` 获取原始能量
- 传入 `activation_function` (参数由 JSON 指定)
- 输出 5 维张量

#### 2. 动态仿真流 (Dynamic Simulation Flow)
- 输入流年地支
- 调用 `interaction_damping` 判定结构阻尼 (λ)
- 计算冲击能量
- 调用 `phase_change` 判定是否崩塌

#### 3. 归一化约束 (Normalization Constraint)
- 所有输出向量必须经过 `core.math_engine.tensor_normalize` 处理，确保 ∑|w_i| = 1 (SAI)

---

**版本**：V1.0  
**创建日期**：2025-12-29  
**更新日期**：2025-12-29  
**状态**：规范文档（已实现）

