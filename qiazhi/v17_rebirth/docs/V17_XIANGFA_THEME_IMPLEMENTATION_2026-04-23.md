# V17 象法专题第一阶段实现记录

日期：2026-04-23

## 1. 目标

这一轮只做一件事：把象法收敛成一个**纯语义专题**，不让它污染底层物理或主裁决。

明确边界：

- 允许：
  - `semantic mapping`
  - `evidence`
  - `narrative hint`
  - `event framing`
- 禁止：
  - 修改五行能量
  - 修改十神结构
  - 进入 bias
  - 覆盖 authority

## 2. 已实现内容

### 2.1 主题 core

新增：

- `backend/logic/L2_structure_patterns/xiangfa_theme_core.py`

当前协议：

- `contract = v17.xiangfa.theme.v1`
- `is_optional_topic = True`
- `authority_bridge_mode = disabled`

当前输入来源：

- `god_ring_authority`
- `blind_theme`
- `climate_theme`
- `relation_formation_summary`
- `relation_dynamics_summary`

当前输出：

- `semantic_mapping`
- `evidence`
- `narrative_hint`
- `event_framing`
- `prompt_digest`
- `source_topics`

### 2.2 专题插件

新增：

- `classical.xiangfa.semantic_mapping.v1`
- `classical.xiangfa.evidence.v1`
- `classical.xiangfa.narrative_hint.v1`
- `classical.xiangfa.event_framing.v1`

它们统一读取 `xiangfa_theme_core`，只输出 `pattern_observation`，不产出 proposal，不进入 bias。

### 2.3 元数据与 Prompt

当前已接入：

- `l1_meta_hydration.py`
  - 自动汇总 `meta.xiangfa_theme`
- `physics_canonical.py`
  - 新增：
    - `象法专题合同`
    - `象法证据`
    - `象法专题摘要`

### 2.4 UI / Admin

当前已接入：

- Oracle 辅助页
- Admin Core 面板
- Admin 插件分类：`象法专题`
- Admin runtime status API：`xiangfa_theme`

说明方式：

- 明确显示 `semantic-only`
- 明确显示 `不入 bias`
- 明确显示 `不改能量`

## 3. 当前边界

### 3.1 已完成

- semantic-only contract
- meta 汇总
- Prompt 接入
- Oracle 辅助页展示
- Admin 展示
- 测试覆盖

### 3.2 暂未开放

- 不进入 `blind_bias_protocol`
- 不进入 `judgement_bias_protocol`
- 不进入 `authority_use_score / authority_taboo_score`

## 4. 验证

已覆盖：

- `test_xiangfa_theme_core.py`
- `test_physics_canonical.py`

验证目标：

- 协议边界不漂移
- semantic-only 不被后续误接到 bias 链
- Prompt 始终能看到象法摘要

## 5. 结论

象法第一阶段已经完成，但它当前仍是**解释层增强器**，不是裁决器。

后续是否进入低权重 bias，必须等待：

- Synthetic Lab
- Practitioner Benchmark

证明其稳定且不会污染主物理链之后，再另行裁决。
