# V17 盲派专题重构设计

日期：2026-04-23

## 1. 目标

盲派不再只是若干“做功/应期/触发象”的描述插件，而是升级为一个可选、独立、可并行存在的专题求解器。

约束如下：

- 盲派是可选专题，不覆盖子平、格局、风险等其他专题。
- 盲派不直接改写 L0 / L1 物理结算。
- 盲派可以输出 bias / evidence / narrative hint，但是否进入最终体用裁决，需要经过 authority 层吸收。
- 盲派与子平允许并行存在、并行显示、并行进入提示词，不允许互相覆盖。

## 2. 设计原则

### 2.1 盲派先看结构主通路，不先看单一十神分数

盲派中的“体”不是最大十神，也不是单个五行，而是当前最能主导命局流通的主结构。

示例：

- 食伤制杀
- 食伤生财
- 杀印相生
- 财官同流
- 双体竞争
- 体被扰动但未换体

### 2.2 “用”不是平衡工具，而是对体有正功能的耦合项

盲派中的“用”应从边际贡献来定义：

- 若某元素进入后提高体的稳定性、流通效率或输出落地性，则趋向为用。
- 若某元素进入后打断主结构、制造内耗或引发过载，则趋向为忌。

### 2.3 家里 / 家外不是静态十神标签，而是运行角色

家里 / 家外按运行角色判定：

- `inside`：承接端、回收端、控制端、落地端
- `outside`：输出端、交换端、应事端、外放端
- `bridge`：承担通关、转译、润滑、缓冲的角色

同一十神在不同结构、不同运流下可以换角色。

## 3. 盲派专题与其他专题的关系

### 3.1 与子平关系

- 子平：更偏“月令/强弱/体用裁决”的解释体系。
- 盲派：更偏“主结构/做功链/断事入口/家里家外”的解释体系。

两者不是互斥关系，而是并行专题。

系统要求：

- 子平负责 `god_ring_authority` 的当前主裁决。
- 盲派先输出 `blind_theme` 与 `blind_bias/evidence`。
- authority 后续可以吸收 blind bias，但 blind 本身不覆盖 `god_ring_authority`。

### 3.2 与格局、风险插件关系

- 格局插件给出“结构候选/格局拟合”。
- 风险插件给出“偏置/冲突/逆转风险”。
- 盲派插件给出“当前主结构如何做功、谁在家里、谁在家外、运来是否换挡”。

## 4. 元数据分层

盲派专题的元数据必须拆成两层。

### 4.1 临时求解元数据（temporary / transient）

这些用于 solver 内部迭代，不应直接作为全局主元数据对外暴露：

- `blind_route_scores_raw`
- `blind_graph_edges`
- `blind_candidate_traces`
- `blind_runtime_probes`
- `blind_debug_flags`
- `blind_temporary_house_roles`
- `blind_solver_notes`

### 4.2 最终专题元数据（final / canonical blind topic）

这些可以进入 `meta`，并允许被 UI、Admin、Prompt 消费：

- `blind_theme.contract`
- `blind_theme.is_optional_topic`
- `blind_theme.primary_route`
- `blind_theme.body_mode`
- `blind_theme.body_candidates`
- `blind_theme.use_candidates`
- `blind_theme.taboo_candidates`
- `blind_theme.house_roles`
- `blind_theme.runtime_switches`
- `blind_theme.narrative_focus`
- `blind_theme.prompt_digest`
- `blind_theme.authority_bridge_mode`

## 5. 最终输出

盲派专题最终应输出四类结果。

### 5.1 结构输出

- 主体主线：`primary_route`
- 体态：`single_body / dual_body / disturbed_body / shifted_body`
- 候选结构及置信度：`body_candidates`

### 5.2 体用输出

- `use_candidates`
- `taboo_candidates`

### 5.3 家里家外输出

- `house_roles`
- 谁是 `inside`
- 谁是 `outside`
- 谁是 `bridge`

### 5.4 运流换挡输出

- `runtime_switches`
- 当前是“扰体未换体”还是“主线抢权”
- 哪个运流变量引发换挡

## 6. Prompt 接口

PhysicsCanonical 需要为盲派专题提供单独 prompt 合同。

建议新增两行：

1. `盲派专题合同`
2. `盲派专题摘要`

内容原则：

- 明确盲派是可选并行专题，不覆盖子平。
- 明确当前主线、体态、家里/家外、运流换挡摘要。
- 明确 blind 只输出专题视角，不直接改写物理层。

## 7. 数学/算法建议

盲派建议使用“结构评分”而不是“最大分数”。

定义：

`J = α*BodyStability + β*FlowEfficiency + γ*OutputEffectiveness - δ*InternalConflict - ε*OverloadRisk`

解释：

- 体：`J` 最大的主结构
- 用：`ΔJ > 0`
- 忌：`ΔJ < 0`

家里/家外作为运行角色，由结构位置和通路位置决定，不由十神静态硬编码。

## 8. 实施顺序

1. 新增 `blind_school_core.py`
2. 现有 5 个盲派插件全部改为读取 core 结果
3. 新增 `blind_bias / blind_evidence` 协议
4. 接入 Synthetic Lab 与 practitioner benchmark
5. 最后再增加更细的 house roles / runtime switch 子插件

## 9. 当前阶段结论

本轮先完成三件事：

- 立法：盲派专题作为独立可选主题
- 分层：区分临时求解元数据与最终专题元数据
- 接口：为 LLM prompt 预留稳定出口

## 10. 第二阶段已完成内容

当前已完成：

- `blind_school_core.py` 已具备共享求解能力：
  - `route candidates`
  - `body_mode`
  - `house_roles`
  - `runtime_switches`
- 原有 5 个盲派插件已改为统一读取 `blind_theme`
- `l1_meta_hydration.py` 已将 `blind_theme` 提升进全局 `meta`
- `PhysicsCanonical` 已能把 `blind_theme` 写入 LLM prompt

这意味着盲派专题已经从“多插件各算各的标签器”升级成“一个共享主题 core + 多个展示插件”。

## 11. 第三阶段已完成内容

当前继续完成：

- `blind_bias_protocol` 已建立：
  - 合同：`v17.blind.bias.v1`
  - 模式：`bias_only`
  - 内容：`use_bias / taboo_bias / inside_roles / outside_roles / bridge_roles / runtime_switches / summary`
- `ZiPingGodRingResolverPlugin` 已并行吸收 `blind_theme`：
  - 盲派只做 soft bias，不覆盖 `god_ring_authority`
  - authority 现在会显式输出：
    - `blind_theme`
    - `blind_bias`
    - `blind_bias_protocol`
- `PhysicsCanonical` 已补 `盲派桥接合同 / 盲派桥接摘要`
- Synthetic Lab 已新增盲派并行 authority 样盘：
  - `l2.authority.blind_theme_parallel`
- UI 已同步：
  - 主页面 `God Ring Explain` 可直接查看盲派主线、家里家外、换挡、推用/推忌
  - Admin Core 面板也可查看同口径 blind bridge

## 12. 当前专题完成度

盲派专题当前已完成：

- 独立专题求解器
- 5 个视图插件统一消费 shared core
- 全局 `meta.blind_theme` 提升
- LLM blind topic prompt
- blind soft bias -> authority 并行桥接
- synthetic / protocol / UI 对齐

当前未做的是更细的盲派 house-role 子专题和 practitioner benchmark 批量扩盘；但作为“盲派专题重构主线”，已经达到可用完成态。
