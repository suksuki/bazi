# 📄 项目交接文档：量子八字 (Quantum Bazi) V2.4 

**日期：** 2025-12-12  
**状态：** Production Ready  
**版本：** V2.4 (Narrative & Logic Optimized)  

---

## 1. 项目概述

**Quantum Bazi** 是一个基于“多体物理相互作用”原理构建的 AI 命理预测引擎。V2.4 版本标志着从“纯计算模型”向“解释性专家系统”的重大跨越。

**核心哲学：**
*   **势能 (Energy/E)：** 量化五行粒子的强度（基于月令、通根）。
*   **权重 (Weight/W)：** 定义如果不发生冲突，各粒子对人生维度的贡献率。
*   **耦合 (Coupling/K)：** 量化粒子间的非线性相互作用（转化、克制、夺取）。

---

## 2. 核心交付物 (Deliverables)

### A. 物理引擎配置 (`data/golden_parameters.json`)
包含固化的黄金参数，通过了 20 个极端案例的验证。
*   **关键参数：**
    *   `K_Control_Conversion = 0.55`: 食神制杀的转化效率。
    *   `K_Mutiny_Betrayal = 1.8`: 伤官见官（身弱）的惩罚系数（**High Priority**）。
    *   `K_Clash_Robbery = 1.2`: 比劫夺财/克妻的惩罚系数。

### B. 叙事配置库 (`data/narrative_config.json`)
实现了“数理-命理”分离架构。
*   包含 13 种常见流年物理事件的标准断语（如“枭印夺食”、“制杀成格”）。
*   支持运营团队通过修改 JSON 直接更新前端文案，无需代码介入。

### C. 向量化运算内核 (`core/quantum_engine.py`)
*   已实现**逻辑优先级 (Priority Logic)**：
    *   **从格开关：** 当 $E_{\text{Self}} < -6.0$ 时，物理法则反转。
    *   **叛变优先：** 当触发 $K_{\text{Mutiny}}$ 时，强制屏蔽 $K_{\text{Control}}$ 收益。
    *   **参数复用：** $K_{\text{Clash}}$ 同时作用于 Wealth 和 Relationship 维度。

---

## 3. 黄金参数清单 (V2.4 Baseline)

| 符号 | 参数名称 | 最终值 | 物理含义 | 适用维度 |
| :--- | :--- | :--- | :--- | :--- |
| $\mathbf{K}_{\text{Control}}$ | 制杀/转化系数 | **0.55** | 将压力(杀)转化为成就 | 事业 |
| $\mathbf{K}_{\text{Mutiny}}$ | 伤官见官 | **1.8** | 身弱无制，以下犯上 | 事业 (负面) |
| $\mathbf{K}_{\text{Clash}}$ | 比劫夺财 | **1.2** | 竞争者对资源的直接掠夺 | 财富/感情 |
| $\mathbf{K}_{\text{Capture}}$ | 担财系数 | **0.4** | 即身旺能任财 | 财富 |
| $\mathbf{K}_{\text{Buffer}}$ | 印星防御 | **0.3** | 化解外部压力为资源 | 事业 |
| $\mathbf{K}_{\text{Leak}}$ | 泄身系数 | **0.87** | 才华过度挥发导致的虚耗 | 财富 |
| $\mathbf{K}_{\text{Pressure}}$ | 官杀攻身 | **1.0** | 外部压力超过身心承受极限 | 感情/事业 |

---

## 4. 维护与运营指南

### 4.1 如何调整预测文案？
修改 `data/narrative_config.json` 中的 `desc` (描述) 和 `verdict` (断语) 字段。修改后重启服务即可生效。

### 4.2 如何微调模型精度？
推荐在 `ui/pages/quantum_lab.py` (量子实验室) 中加载特定案例，调节滑块观察变化。
确认新参数后，请同步更新 `data/golden_parameters.json` 以保持生产环境一致。

### 4.3 已知局限性 (Known Limitations)
*   目前引擎主要处理“正五行”生克。对于极其特殊的“化气格”或“纳音”暂未包含。
*   $K_{\text{Clash}}$ 对所有比劫一视同仁，未来 V3.0 可能需要区分“比肩 (Friend)”和“劫财 (Robber)”的细微差别。

---

**Antigravity Team**
*Project Lead: Jin*
*AI Co-Pilot: Antigravity*
