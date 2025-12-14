# Antigravity 核心算法二级补充文档 (Level 2)
## 专题：量子纠缠 (Combinations) 与 粒子对撞 (Clashes)
**版本：** V3.0 (Parametric Evolution)
**依赖：** `Core_Algorithm_Master_V2.5`
**状态：** 🚀 Ready for Coding

### 1. 冲 (Clashes): 粒子对撞机模型

#### 1.1 物理定义
**冲 (Clash)** 是两个反向矢量在同一时空点的对撞。
* **湮灭 (Annihilation):** 双方能量因抵消而减少。
* **激荡 (Excitation):** 碰撞产生的冲击波导致系统熵增（不稳定性增加）。

#### 1.2 参数化算法逻辑
废除简单的加减分，采用 **Config-Driven** 的损伤/收益计算。

$$ \mathbf{E}_{\text{final}} = \mathbf{E}_{\text{base}} \times (1.0 - \text{clashDamping}) $$

* **动态喜忌判定:**
    * **喜神被冲:** 悲剧。额外扣减系数 `config.clash.favorableDamage`。
    * **忌神被冲:** 喜剧。获得能量释放或压力减轻 `config.clash.unfavorableRelief` (通常表现为负的分数带来的"加分"效果，例如减少了负分)。

---

### 2. 合 (Combinations): 量子纠缠模型

#### 2.1 天干五合 (Stem Fusion)
* **合化 (Transmutation):** 需满足 `config.stemFiveCombine.transformThreshold` (e.g., 0.8)。成功则能量 **x2.0** (`bonus`)。
* **合绊 (Binding):** 若不化，则双方能量 **x0.6** (即损失 40%, `penalty: 0.4`)。
* **[NEW] 争合 (Jealousy):**
    * **定义:** 多对一的纠缠态（如两乙合一庚）。
    * **算法:** 引入 `config.stemFiveCombine.jealousyDamping` (默认 0.3)。
    * **公式:** 庚金能量 = (原能量 / N) * (1 - jealousyDamping)。

#### 2.2 地支三合/三会 (Triangular & Directional Field)
这是能量场最强的形态。

**数据结构追加 (Config Schema Update):**

```typescript
interface ComboPhysics {
  // 三合局 (申子辰)
  trineBonus: number;        // [UI] 完整三合倍率 (e.g., 2.5)
  
  // 半三合 (申子 / 子辰)
  halfBonus: number;         // [UI] 半合(含中神)倍率 (e.g., 1.5)
  archBonus: number;         // [UI] 拱合(不含中神)倍率 (e.g., 1.1)
  
  // 三会局 (亥子丑)
  directionalBonus: number;  // [UI] 三会方局倍率 (e.g., 3.0)
  
  // 解冲消耗
  resolutionCost: number;    // [UI] 贪合忘冲的代价 (e.g., 0.1)
}
```

#### 2.3 贪合忘冲 (Resolution Logic)
**最高优先级法则 (Prime Directive):** 纠缠态 (Entanglement) 的稳定性 > 对撞态 (Collision) 的破坏性。

**算法流程:**
1. **扫描:** 识别所有 六合/三合/三会。
2. **锁定:** 参与合局的粒子标记为 `LOCKED`。
3. **豁免:** 只有非 `LOCKED` 粒子才计算冲。
4. **消耗:** 被锁定的粒子虽然免于冲，但需支付 `resolutionCost` 的能量税。

---

### 3. 数据结构更新
Antigravity 需在 `interactions` 节点下注入上述参数。

### 4. 架构执行指令
1. **Update Schema**: Inject `ComboPhysics`.
2. **Update Engines**: Refactor `HarmonyEngine`.
3. **UI**: Add "Alchemy" panel.
