# 物理核心（L1）— 全局熵与交互流水线

本文档描述 Qiazhi 0.13 实验室 **L1 原子交互流水线** 在 `physics_tensor` 上的只读产物，与 **全局熵（global_entropy）** 的定义。算法系数以 `physics_interaction_params`（及 `DEFAULT_INTERACTION_PARAMS` 种子）为唯一来源，不在业务代码中写死权重。

## 全局熵 `meta.global_entropy`

**语义**：对当前盘面的「结构不稳定性」与「内耗—钳制—冲损」张力做 **0..1** 归一化标量，供 UI 驱动流光、脉冲与故障艺术（Glitch），**不构成** L2 吉凶判词。

**合成公式**（`interaction_pipeline` 末尾 `EntropySynthesizer` 等价实现）：


\text{globalentropy} = \mathrm{clamp}\Big(\sum_i M_i \cdot w_i,\ 0,\ 1\Big)


- **M_{\text{torque}}**：扭力审计总量 `audit_log.l1_impact_torque_total` 除以参数 `ENTROPY_TORQUE_REF` 后限幅到 1。
- **M_{\text{clamp}}**：处于 **三合 AGGREGATED** 或 **墓库 LOCKED** 所触及的**柱位**占四柱（4）的比例，0..1。
- **M_{\text{clash}}**：所有 `base.clash` 步的 `abs_loss` 之和除以 `ENTROPY_CLASH_REF` 后限幅到 1。

**默认权重**（可通过 DB 覆盖）：


| 参数                   | 默认值   |
| -------------------- | ----- |
| `ENTROPY_W_TORQUE`   | 0.4   |
| `ENTROPY_W_CLAMP`    | 0.3   |
| `ENTROPY_W_CLASH`    | 0.3   |
| `ENTROPY_TORQUE_REF` | 180.0 |
| `ENTROPY_CLASH_REF`  | 160.0 |


**诊断分解**：`meta.global_entropy_metrics` 携带 M_{\text{torque}}、M_{\text{clamp}}、M_{\text{clash}} 及原始标量，便于审计与调参。

## UI 语义映射（建议）


| 区间        | 建议表现                                  |
| --------- | ------------------------------------- |
| 0.0 – 0.3 | 平稳、低动效                                |
| 0.4 – 0.7 | 张力条加速脉冲（`StrategicCoreHUD`）、轻量 Glitch |
| 0.8 – 1.0 | 强 Glitch、可选触觉反馈（`LogicGlitchOverlay`） |


前端从 `physics_tensor.meta.global_entropy` 读取；具体阈值以产品设计为准，可独立于后端权重迭代。

## 相关代码

- 流水线：`backend/app/services/helpers/interaction_pipeline.py`
- 参数默认值：`backend/app/skills/physics_rules.py` → `DEFAULT_INTERACTION_PARAMS`
- Stream Board：`frontend/src/features/stream-board/useStreamBoardController.ts` → `globalEntropy` 状态

## 与 L2 的边界

- L1 只产出 **可审计物理增量** 与 **熵标量**；**做功语义、格神与断语** 仍由 L2 插件与终判链路完成。
- `global_entropy` **不**替代 `work_eligible`、合局 `phi` 门控或墓库爆发逻辑；三者并行供不同消费方使用。