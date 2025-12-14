# Antigravity 核心算法二级补充文档 (Level 2)
## 专题：墓库拓扑学与量子隧穿 (Storehouse Topology & Quantum Tunneling)
**版本：** V3.0 (Parametric Evolution)
**依赖：** `Core_Algorithm_Master_V2.5`
**生效范围：** 仅针对地支中的土元素 (辰 Chen, 戌 Xu, 丑 Chou, 未 Wei)

### 1. 物理定义 (Physics Definition)
墓库是时空曲率极大的**引力陷阱**。

* **库 (Vault):** 高能粒子的**约束态 (Bound State)**。类似于加压的储气罐，能量巨大但不可用，需外部撞击释放。
* **墓 (Tomb):** 低能粒子的**湮灭态 (Annihilation State)**。类似于废墟，结构脆弱，外部撞击将导致坍塌。

### 2. 参数化状态判定 (Parametric State Logic)
废除固定数值，采用 **Config-Driven** 判据。

#### 2.1 判定公式
令 $\mathbf{E}_{\text{Storage}}$ 为该地支所藏**库神**（如辰中之水、戌中之火）的能量值。

* $\text{State} = \begin{cases} \text{Vault (库)} & \text{if } \mathbf{E}_{\text{Storage}} \ge \text{config.vault.threshold} \\ \text{Tomb (墓)} & \text{if } \mathbf{E}_{\text{Storage}} < \text{config.vault.threshold} \end{cases}$

* **config.vault.threshold**: 墓库界限阈值（用户在 UI 可调）。

### 3. 动态交互机制 (Interaction Dynamics)

#### 3.1 闭库态 (The Sealed State)
**条件：** 无冲 (No Clash) 且 无有效刑 (No Effective Punishment)。
**物理后果：** 能量被封锁。
**算法修正：**
$$ \mathbf{E}_{\text{Effective}} = \mathbf{E}_{\text{Total}} \times \text{sealedDamping} $$

* *注：`sealedDamping` 通常设为 0.3~0.5。即如果不冲，库里 100 万只能当 30 万用。*

#### 3.2 隧穿态 (The Tunneling / Open Vault)
**条件：** 状态为 **Vault** 且 (遇冲 OR (遇刑 AND 允许刑开库))。
**物理后果：** 势垒击穿，能量释放。
**算法修正：**

1. **豁免土战：** 忽略土与土之间的基础相克/刑冲折损。
2. **能量释放：**
$$ \mathbf{E}_{\text{Effective}} = \mathbf{E}_{\text{Storage}} \times \text{openBonus} $$


* *注：`openBonus` 通常 > 1.0 (e.g., 1.5)，代表积蓄力量的爆发。*

#### 3.3 坍塌态 (The Collapse / Broken Tomb)
**条件：** 状态为 **Tomb** 且 (遇冲 OR 遇刑)。
**物理后果：** 结构瓦解，剩余能量逸散。
**算法修正：**
$$ \text{Score}_{\text{Impact}} = -10.0 \times \text{breakPenalty} $$

* *注：产生负值，代表对盘面的震荡伤害。*

---

### 4. 数据结构更新 (Schema Update)
请 Antigravity 将以下参数追加至 `FinalAlgoParams` 的 `interactions` 节点中。

```typescript
interface VaultParams {
  // 1. 界定标准
  threshold: number;      // [UI] 库与墓的分界线 (e.g., 20 分)
  
  // 2. 闭库折损 (没钥匙打不开)
  sealedDamping: number;  // [UI] 封闭状态下的能量利用率 (0.0 - 1.0, 默认 0.4)
  
  // 3. 开库爆发 (量子隧穿)
  openBonus: number;      // [UI] 冲开后的能量倍率 (1.0 - 2.0, 默认 1.5)
  punishmentOpens: boolean; // [UI开关] 是否允许"刑"开库 (默认 false)
  
  // 4. 破墓惩罚 (结构坍塌)
  breakPenalty: number;   // [UI] 冲破后的伤害系数 (0.0 - 1.0, 默认 0.5)
}
```
