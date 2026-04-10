# ETRM Protocol (V0)

## 目标

将 L1 Abs 真值与 L2 关系矩阵并网，输出可审计的做功拓扑图 `Topology_Graph`。

## 输入

- `physics_tensor.deity_energy_axes`（Abs）
- `metadata.conflict_matrix.points`（刑冲合穿等）
- `runtime_physics_config`（阻抗参数）

## 核心公式

- `Raw_Energy = mean(Abs) * relation_gain`
- `Final_Work = Raw_Energy * Resonance_Boost * Distance_Decay`
- `Distance_Decay = max(0.1, 1 - TRANSFER_DISTANCE_DECAY * distance)`

## 参数主权

- `STEM_RESONANCE_BOOST`
- `TRANSFER_DISTANCE_DECAY`
- `WORK_MIN_THRESHOLD`

所有参数必须来自运行时配置，不得在技能内硬编码业务常量。

## 审计字段

- `topology_graph_v1.nodes`
- `topology_graph_v1.edges`
- `topology_graph_v1.topology_audit[]`
  - `Raw_Energy`
  - `Resonance_Boost`
  - `Decay`
  - `Final_Work`

## 守恒要求

- `Final_Work` 仅由输入能量与阻抗变换得到，不允许凭空增益。
- UI 渲染必须尊重 `WORK_MIN_THRESHOLD`，避免噪声路径污染解释链。