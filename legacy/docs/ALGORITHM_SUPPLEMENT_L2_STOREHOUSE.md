# Antigravity L2 补充文档：墓库拓扑学 (Storehouse Topology)
**主题**: 墓库状态定义的纯逻辑描述
**版本**: V3.0 (Parametric Topology)
**依赖**: `ALGORITHM_CONSTITUTION_v3.0.md`
**状态**: ACTIVE (Logic Standard)

---

## 1. 物理定义
地支中的土元素 (辰/戌/丑/未) 具有 **波粒二象性**，可坍缩为两种基本状态：
1.  **库 (Vault)**: 高能约束态。能量巨大但不可用。
2.  **墓 (Tomb)**: 低能湮灭态。结构脆弱。

---

## 2. 状态转化逻辑 (State Transition)
* **判定阈值**: $\mathbf{E}_{Storage}$ 与 `@config.vault.threshold` 的比较决定初始状态。

### 2.1 闭库态 (Sealed State)
* **条件**: 无冲且无有效刑。
* **逻辑**: 能量被封锁，应用 **闭库折损系数** (`@config.vault.sealed_damping`)。

### 2.2 隧穿态 (The Tunneling / Open Vault)
* **条件**: 状态为 Vault 且 (遇冲 OR 有效刑)。
* **逻辑**: 
    1. 势垒击穿，忽略土元素的本气克制。
    2. 释放积蓄能量，应用 **开库爆发系数** (`@config.vault.open_bonus`)。

### 2.3 坍塌态 (Collapse)
* **条件**: 状态为 Tomb 且遭遇对撞。
* **逻辑**: 容器破碎，不产生能量释放，反而产生 **结构震荡惩罚** (`@config.vault.collapse_penalty`)。
