# V17 财富密码知识库化与合成验证

日期：2026-04-26

## 背景

本轮审计认为旧版 `wealth_code` 仍偏向手工线性打分：

- 财富路径依赖固定模板、固定权重、固定阈值。
- `食伤制杀 + 食伤生财` 的组合路径以个案补丁形式写在代码里。
- L0 干支象义、十神象义、库象等知识直接写在 Python 代码中，不利于版本管理、派别扩展和后续学习闭环。

本次改动不改变参数、不改变体用、不改变既有十神计算，只把“可解释知识”从执行代码中迁出，并新增典型财富合成命例验证。

## 已完成

### 1. 财富路径知识外置

新增知识库：

`v17_rebirth/backend/logic/knowledge/wealth_code_knowledge.v1.json`

包含：

- 财富路径关键词：财星直取、食伤生财、食伤制杀、财官、财印、资源整合、财库、漏财。
- 路径模板：经典标签、用户可读名称、白话摘要、主驱动、承接类型、风险提示。
- 评分公式：从 Python 逻辑迁移为可版本化配置。
- 组合路径：`output_work_to_money` 由 `output_controls_pressure` 与 `output_to_wealth` 组合触发。
- 财富来源改写、承接条件、承接类型、变现驱动。

代码现在负责：

- 读取知识库。
- 归一化输入事实。
- 计算特征值。
- 按知识库公式生成路径候选。
- 按知识库组合规则合并主路径。

代码不再把 `食伤制杀 + 食伤生财` 当成函数里的特例补丁。

### 2. L0 干支象义知识外置

新增知识库：

`v17_rebirth/backend/logic/knowledge/bazi_symbolic_primitives.v1.json`

包含：

- 十干象义与财富/事业/关系/性格/风险投射。
- 十二支象义与季节场景。
- 辰戌丑未库象。
- 十神家族到象义事实的映射。
- 合冲刑害等关系标签。
- 宫位上下文。

`bazi_image_core.py` 现在只负责解析、读取知识、生成象义事实，不再内置这批知识表。

### 3. 财富合成命例实验室

新增：

`v17_rebirth/testing/synthetic_wealth_lab.py`

当前样本：

- `wealth.synthetic.output_work_to_money.yi`
  - 丁巳、乙巳、乙丑、乙酉，庚子运，丙午年。
  - 期望主路径：`output_work_to_money`。
  - 验证食伤制杀与食伤生财必须合并成“做功变现”路径。

- `wealth.synthetic.direct_wealth.client_resource`
  - 财星直取样本。
  - 期望主路径：`direct_wealth`。
  - 验证明确客户、合同、现金流不被宏观摘要抢主路径。

- `wealth.synthetic.peer_leakage.split`
  - 财旺见比劫样本。
  - 期望漏财点：`peer_split`。
  - 验证合作分账、现金流泄漏和财库观察进入结构。

- `wealth.synthetic.knowledge_asset.caiyin`
  - 财印路径样本。
  - 期望主路径：`wealth_seal_asset`。
  - 验证资质、方法论、信用资产能成为财富承接。

### 4. 接入学习框架

财富合成样本已进入 `synthetic_tuning_bridge` 的 synthetic catalog。

合成财富报告会输出：

- `parameter_family_counts`
- `learning_loop_state`
- `parameter_candidate_plan`

失败时不会自动改参数，只会把问题归入：

- `topic.wealth_code.path.calibration`
- `topic.wealth_code.source_language.calibration`
- `topic.wealth_code.vault.calibration`
- `topic.wealth_code.leakage.calibration`
- `topic.wealth_code.learning_hooks`

这保持了“先审计、再候选、后人工确认”的学习闭环。

## 验证

定向测试：

```bash
python3 -m pytest -q \
  v17_rebirth/tests/test_wealth_code_core.py \
  v17_rebirth/tests/test_wealth_code_preview.py \
  v17_rebirth/tests/test_wealth_assertion_prompt.py \
  v17_rebirth/tests/test_bazi_image_core.py \
  v17_rebirth/tests/test_synthetic_wealth_lab.py
```

结果：

```text
29 passed, 2 warnings
```

## 仍需继续

本次解决的是“知识硬编码”和“典型样本验证”。

后续真正要升级模型，需要继续做：

- 结构化 claim graph：替代 facts 文本 substring 命中。
- 路径图推理：把食伤、生财、制杀、财库、财印、比劫等做成可组合图，而不是单层加权排序。
- 岁运触发图：把大运/流年作为路径节点激活器，而不是只做摘要加分。
- 知识库来源管理：给知识条目增加派别、来源、权重、适用条件和冲突策略。
- 人机反馈闭环：用用户访谈反推隐藏属性、幸运值、放大系数，再回填到审计层而非直接改命盘底层参数。
