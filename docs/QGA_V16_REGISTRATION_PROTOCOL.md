# 📜 QGA V16.2 [QUANTUM_REGISTRY] 量子分层与级联注册协议

## 1. 概述 (Overview)
为了支撑 Antigravity 系统向高维物理仿真的演进，本项目从 V16.0 起正式废弃扁平化逻辑注册，全面推行**“分层级联注册协议”**。该协议解决了算法、模型、专题之间命名混乱、依赖不透明、回溯困难的问题。

## 2. 核心架构：四维层级 (Four-Layer Hierarchy)

系统中的每一个注册项（Item）必须归属于以下四个能级之一：

| 层级 (Layer) | 名称 (Type) | 描述 (Description) | ID 范式 | UI 呈现 |
| :--- | :--- | :--- | :--- | :--- |
| **L0: INFRA** | 基础设施 | 系统级辅助工具、数据管理器、翻译表。 | `UTIL_XXX` | 隐藏 |
| **L1: ALGO** | 核心算子 | 纯数学/物理算法公式（如：磁饱和曲线、流体力学系数）。 | `ALGO_XXX` | 隐藏 |
| **L2: MODEL** | 物理模型 | 具体物理场景的边界定义（如：CIWS 对撞模型、整流桥模型）。 | `MODEL_XXX` | 调试可见 |
| **L3: TOPIC** | 业务专题 | 命理格局、人生专题、风险探测。 | `MOD_XXX` | **主选单展示** |
| **L4: SUB_TOPIC** | 嵌套子专题 | 专题内部的细分能核或物理算子。 | `MOD_XXX` | 级联/穿透展示 |

## 3. 注册规范 (Registration Standards)

### 3.1 强制属性 (Required Attributes)
所有的 L3 专题注册项必须包含以下属性：
*   **`reg_id`**: 全局唯一逻辑 ID。
*   **`name_cn`**: 中文名称（UI 第一公民）。
*   **`icon`**: 展示图标。
*   **`layer`**: 归属层级 (INFRA/ALGO/MODEL/TOPIC)。
*   **`dependencies`**: 依赖链（引用 L1/L2 的 ID 列表）。
*   **`sub_modules`**: [可选] 该专题下挂载的子专题 (L4) 清单。
*   **`parent_topic`**: [L4 强制] 指向其主专题 (L3) 的回溯 ID。

### 3.2 扩展性支持 (Extensibility)
系统支持自定义项注册。未来可新增 `EVENT`（突发事件）、`INTERVENTION`（干预措施）等层级，只需在 `layers` 枚举中添加即可。

## 4. 级联依赖与回溯映射 (Traceability)

每个专题通过 `dependencies` 指向其背后的物理驱动。
*   **回溯逻辑**：当一个 Audit 报告生成时，系统会扫描专题的依赖链，自动聚合底层 ALGO 和 MODEL 的元数据，确保结论有物理依据。

## 5. 命名规范 (Naming Conventions)
*   **中文名称**：必须使用专业物理命理词汇，并在末尾统一佩戴 **✨**（代表 V16.0 兼容）。
*   **ID 映射**：不再允许在代码中直接写路径，必须通过 `LogicRegistry.resolve()` 进行装配。

## 6. 专题嵌套与级联审计 (Topic Nesting)

从 V16.2 起，系统正式支持 **Topic -> Sub-Topic** 的树状拓扑：
*   **L3: TOPIC** (如 MOD_129 MBGS) 作为容器，挂载 **L4: SUB_TOPIC** (如 MOD_131 JSG) 为内部能核。
*   **审计引擎** 会自动识别 `parent_topic`。当审计主专题时，系统会自动激活其关联的子专题联动，实现复合场关联矩阵分拣。
*   **UI 协议**：子专题默认为级联展开或穿透式展示，不占用主选单空间，确保高维复杂性的有序呈现。

---

**Protocol Authenticated by Antigravity Core V16.2**
