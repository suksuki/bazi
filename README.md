
# 🔮 Quantum Bazi AI (量子八字推演系统)

> **"当东方玄学遇见神经网络 与 量子物理"**
> *When Oriental Metaphysics meets Neural Networks & Quantum Physics*

## 🌟 项目愿景 (Vision)
本项目旨在构建一个**“可解释、可验证、可进化”**的现代化八字推演引擎。
不同于传统的死板算命程序，我们引入了：
1.  **量子化 (Quantization)**: 将“命运”视为概率波函数，而非宿命定论。
2.  **微观模拟 (Micro-Simulation)**: 深入到**流日 (Daily)** 级别的五行能量碰撞。
3.  **神经符号 AI (Neuro-Symbolic)**: 结合传统物理规则（符号）与深度学习（神经网络）进行参数自进化。

---

## 🚀 核心功能 (Key Features)

### 1. 🌋 命运熔炉 (Quantum Flux Engine)
*   **代码**: `core/flux.py`
*   **原理**: 将 **原局(8字) + 大运(2字) + 流年(2字)** 放入同一个熔炉。
*   **输出**: 计算五大人生类像（财、官、印、比、食）的**能量值**与**熵值 (Entropy/Chaos)**。
*   **意义**: 不仅告诉你“财运旺”，还能告诉你这笔财是“稳定工资”还是“高风险投机”。

### 2. 📈 高保真人生模拟 (High-Fidelity Simulation)
*   **代码**: `core/trajectory.py`
*   **精度**: 支持 **按年 (Yearly)**、**按月 (Monthly)** 甚至 **硬核按日 (Daily)** 模拟。
*   **算法**: 对人生 0-90 岁（约 32,850 天）进行逐日刑冲合害计算，生成人生能量 K 线图。

### 3. 🤖 AI 智能投顾 (AI Advisor)
*   **集成**: Ollama (Local LLM)
*   **功能**:
    *   **直断**: 每次排盘，AI 自动读取八字结构，给出“3点核心建议”。
    *   **学习**: 具备 `TheoryMiner`（古籍挖掘）与 `RealDataMiner`（名人案例挖掘）模块，可不断进化。

### 4. 🧬 可进化参数系统 (Evolutionary Weights)
*   **配置**: `data/model_weights.json`
*   **机制**: 所有的物理规则（如“子午冲扣多少分”）都已参数化。未来配合遗传算法，可根据历史真实数据自动微调，实现“越算越准”。

---

## 📂 项目结构 (Structure)

```text
bazi_predict/
├── main.py                 # Streamlit UI 入口
├── core/
│   ├── calculator.py       # 基础排盘 (基于 lunar_python)
│   ├── alchemy.py          # 化学反应堆 (刑冲合害基础逻辑)
│   ├── wuxing_engine.py    # 五行强弱计算
│   ├── trajectory.py       # 人生轨迹模拟 (Time-Series)
│   ├── flux.py             # 命运熔炉 (12字交互 + 熵计算)
│   ├── profile_manager.py  # 档案管理 (CRUD)
│   └── config_manager.py   # 配置持久化
├── learning/
│   ├── theory_miner.py     # 古籍学习机 (RAG)
│   └── real_data_miner.py  # 名人案例挖掘机
├── data/
│   ├── learned_rules.json  # AI 学习到的知识库
│   ├── model_weights.json  # 核心物理引擎参数 (可微调)
│   └── profiles.json       # 用户档案
├── run_bazi.sh             # 启动脚本
└── README.md               # 本文档
```

## 🛠️ 快速开始 (Usage)

1.  **启动系统**:
    ```bash
    ./run_bazi.sh
    ```
2.  **配置 AI**:
    *   在侧边栏 "LLM 设置" 中输入 Ollama 地址 (默认 `http://115.93.10.51:11434`)。
    *   点击 "测试连接" 并选择模型。
3.  **开始排盘**:
    *   在侧边栏输入出生信息，点击 "开始排盘"。

---

## 🧠 技术路线图 (Roadmap)
详情请见 `.gemini/antigravity/brain/` 下的规划文档：
*   `task.md`: 开发进度表
*   `implementation_plan.md`: 技术实现细节
*   `training_plan.md`: AI 训练与 GNN 架构展望
