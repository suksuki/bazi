# Antigravity 核心算法二级补充文档 (Level 2)

## 专题：墓库理论与量子隧穿机制 (Storehouse & Quantum Tunneling)

**版本：** Draft v1.0 for Engine V3.0
**依赖：** 需基于 `Core_Algorithm_Master_V2.9.md` 计算出的基础势能 ($\mathbf{E}_{\text{Potential}}$)。

### 1. 物理定义 (Physics Definition)

在 Antigravity 物理引擎中，**辰 (Dragon)、戌 (Dog)、丑 (Ox)、未 (Goat)** 四个地支不仅仅是“土 (Earth)”元素，它们被定义为 **“量子容器” (Quantum Containers)**。

容器内的粒子处于 **“叠加态” (Superposition State)**。在未受到外部干扰（刑冲破害）之前，其能量被锁定，无法直接作用于宏观相 ($\mathbf{V}_{\text{real}}$)。

#### 1.1 容器分类

*   **辰 (Water Vault):** 水的容器。
*   **戌 (Fire Vault):** 火的容器。
*   **丑 (Metal Vault):** 金的容器。
*   **未 (Wood Vault):** 木的容器。

---

### 2. 状态判定逻辑 (State Determination Logic)

这是本理论的核心。容器的状态决定了“冲 (Clash)”是吉是凶。

#### 2.1 两个核心状态

根据容器内**藏干粒子 (Hidden Stem Particle)** 的基础势能 ($\mathbf{E}_{\text{Inside}}$)，容器分为两种状态：

| 状态名称 | 物理类比 | 能量阈值条件 | 物理特性 |
| :--- | :--- | :--- | :--- |
| **库 (Vault)** | **银行金库** | $\mathbf{E}_{\text{Inside}} \ge 2.0$ (旺相有气) | 能量活跃但被锁住。内部压力大，渴望释放。 |
| **墓 (Tomb)** | **ICU / 坟墓** | $\mathbf{E}_{\text{Inside}} < 2.0$ (休囚无气) | 能量濒死。依赖容器壁的保护维持存在。 |

#### 2.2 状态计算公式

---

### 3. 动态触发机制：冲与隧穿 (Trigger: Clash & Tunneling)

当容器遇到 **“冲” (Clash)**（如辰戌冲、丑未冲）时，会触发**“开闭逻辑”**。

#### 3.1 场景 A：冲开库 (Opening the Vault)

*   **条件：** 状态判定为 **“库 (Vault)”** + 发生 **“冲 (Clash)”**。
*   **物理事件：** **量子隧穿 (Quantum Tunneling)**。外部冲击力打破了势垒，内部高压能量瞬间释放。
*   **算法修正：**
    1.  **取消惩罚：** 豁免原本的土冲土结构性惩罚 (参考 V2.9 Earth Amnesty)。
    2.  **能量暴击：** 释放出的能量 = $\mathbf{E}_{\text{Inside}} \times \mathbf{K}_{\text{Vault\_Open}}$。
    3.  **参数建议：** $\mathbf{K}_{\text{Vault\_Open}} = 2.0 \sim 3.0$ (暴击系数)。
*   **宏观表现：** 暴富、升迁、突发性成功。

#### 3.2 场景 B：冲破墓 (Destroying the Tomb)

*   **条件：** 状态判定为 **“墓 (Tomb)”** + 发生 **“冲 (Clash)”**。
*   **物理事件：** **结构坍塌 (Structural Collapse)**。外部冲击力摧毁了脆弱的保护壁，内部微弱的粒子消散。
*   **算法修正：**
    1.  **执行惩罚：** 应用结构性破坏惩罚 (参考 V2.8 Structural Damage)。
    2.  **能量湮灭：** 该粒子的剩余势能归零，并产生负面冲击波。
    3.  **公式：** $\mathbf{E}_{\text{Impact}} = -(\mathbf{E}_{\text{Inside}} \times \mathbf{K}_{\text{Collapse}})$。
*   **宏观表现：** 六亲刑伤、健康恶化、破财。

---

### 4. 算法实现伪代码 (Implementation Blueprint)

```python
def process_storehouse_logic(day_branch, other_branch, E_Hidden):
    """
    V3.0 核心逻辑：处理墓库的冲开与冲破
    """
    # 1. 检测是否为同气相冲 (如辰戌冲)
    if not is_earth_clash(day_branch, other_branch):
        return 0.0

    # 2. 状态判定 (The State Check)
    # 阈值 Threshold 需通过贝叶斯校准设定，暂定 2.0
    if E_Hidden > 2.0:
        # 状态：库 (Vault) -> 喜冲
        # 触发 "开库" 特效
        bonus = E_Hidden * K_VAULT_OPEN (2.5)
        trigger_narrative("🚪【金库洞开】积蓄已久的势能被冲开，能量喷涌而出！")
        return bonus
    else:
        # 状态：墓 (Tomb) -> 忌冲
        # 触发 "破墓" 警告
        penalty = E_Hidden * K_COLLAPSE (1.5) * -1
        trigger_narrative("⚰️【根基崩塌】微弱的生机失去保护，结构瓦解。")
        return penalty
```

---

### 5. 与 V2.9 逻辑的兼容性说明

*   **V2.9 (现状):** 采用了 **“土之豁免 (Earth Amnesty)”**。即遇到土冲土，简单粗暴地认为“无罪”。这是一种**防御性策略**，防止了误判“库”为灾难。
*   **V3.0 (目标):** 将从“无罪”进化为“有功”或“有过”。V3.0 将取代 V2.9 的豁免逻辑，提供更精准的**双向判定**。
