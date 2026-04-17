# Bazi OS 三方交互与插件-终判链路说明

本文面向代码评审与分析师复核，说明当前 `qiazhi_bazi` 的端到端机制，覆盖：

1. 三方交互（用户 / 系统 / LLM）
2. 插件如何启用与执行
3. 八字断言如何生成
4. LLM 提示词如何构建与注入

---

## 1) 三方交互机制

### 1.1 角色定义

- 用户（Arbiter）：提交生辰、勾选决策项、触发重算/终判
- 系统（Core）：排盘、L1 物理计算、插件调度、版本化状态管理
- LLM（Auditor）：生成结构化审计与终判文本（受上下文清洗与证据约束）

### 1.2 主流程（Seed -> Analysis -> Verdict）

1. 前端 `onSeedSubmit` 提交 `/api/v1/analyze-seed`
2. 后端 `analyze_seed_flow` 调用排盘引擎 + `analyze_clash_flow`
3. `analyze_clash_flow` 完成：
   - `PhysicsInferenceSkill` 生成 `physics_tensor`
   - `evaluate_interactions` 执行 L1 原子交互池
   - `PluginRegistry.run_hook(on_physics_complete)` 执行 L2/L3 插件
4. 前端接收并更新：
   - `metadata`, `physics_tensor`, `llm_prompt`, `audit_summary`
   - 写入 `sessionStorage[qiazhi_lab_snapshot]`
5. 用户勾选 Decision 后触发 `/api/v1/final-verdict`
6. 后端 `generate_final_verdict` 生成结构终判 + 证据 + 版本号，返回前端展示

### 1.3 审计与可观测性

- 前端 `auditItems` 记录角色动作（Arbiter/Core/Auditor）
- Debug 页展示：
  - 三方交互摘要（health/audit/pending/result_logs）
  - Plugin Trace（enabled plugins、latency、ok、evidence）
- 终判失败/回退会在 `result_logs` 写入 `⚠️` 行

---

## 2) 插件应用机制

### 2.1 插件开关与权重来源（前端）

- 状态来源：`LabConfigContext`
  - `pluginSwitches`: `blindSchool`, `wangshuai`, `wealthRisk`
  - `pluginWeights`: 例如 `classical.blind_school.v1` / `classical.wangshuai.v1` 权重
- 请求透传：
  - `analyze-seed` 传 `enabled_plugins`
  - `final-verdict` 传 `enabled_plugins` 与 `plugin_weights`

### 2.2 后端注册中心（PluginRegistry）

- 注册默认插件（示例）：
  - `classical.blind_school.v1`（hook: `on_physics_complete`）
  - `classical.wangshuai.v1`（hook: `on_physics_complete`）
  - `modern.wealth_risk.v1`（hook: `on_verdict_ready`）
- 统一执行入口：`run_hook(hook, enabled_plugins, context)`
  - 支持异常隔离（单插件失败不打断总流程）
  - 记录 `latency_ms`, `ok`, `error_rate` 等统计

### 2.3 L1 基础插件链（已去硬编码）

- `interaction_pipeline.evaluate_interactions` 仅调用 `run_l1_atomic_plugin_pool`
- clash/combine/punish/grave/sanhe 等由 L1 原子插件池汇总执行
- 满足“交互逻辑插件化、无老式硬编码分支”的目标

---

## 3) 八字断言生成机制

### 3.1 终判输入契约

`/api/v1/final-verdict` 关键输入：

- `metadata`
- `physics_tensor`（必须具备 `meta`，并包含 `abs_nodes` 或可镜像来源）
- `selected_cards`
- `consensus_history`
- `enabled_plugins`
- `plugin_weights`

前端已补齐：

- `physics_tensor.abs_nodes`：优先从 `composite_field_impact` 提取受 L1 交互（聚合/锁定）修正后的有效场强；若不存在修正值，则回退至 `deity_energy_axes.absolute_energy`。

### 3.2 断言生成步骤（后端）

1. `FinalVerdictSkill.generate(...)`
2. 执行盲派工作向量：`run_blind_school_plugin(...)`
3. 结构候选：`resolve_structure_candidates_v0(...)`
4. 结构终审：`build_structure_final_decision_v0(...)`
   - 产出 `utility_god`, `obstacle_god`, `climate_adjustment`
   - 同时产出 `strategic_advice.core_useful_gods/core_obstacle_gods`
5. 插件冲突评估：`evaluate_plugin_conflict(...)`
6. 组织 `logical_evidence`、`audit_log`、`version_id`、`verdict_body`

### 3.3 前端展示映射

- `Result Summary` 读取：
  - 优先 `utility_god` / `obstacle_god`
  - 兜底 `strategic_advice.core_useful_gods` / `core_obstacle_gods`
- 若终判失败，前端会退回 `buildFallbackVerdict(...)`
  - 该路径不会给出有效“用神/忌神”

---

## 4) LLM 提示词构建机制

### 4.1 首轮提示词（Analyze 阶段）

- 由 `analyze_clash_flow` 生成 `llm_prompt`
- 若 LLM 失败，回退 `fallback_clash_prompt(...)`
- 用于用户首轮观察与引导，不等同最终断言

### 4.2 终判提示词（FinalVerdict 阶段）

- `FinalVerdictSkill` 组装上下文：
  - 物理证据（deity/abs/topology/结构终审）
  - 历史共识（含 confirmed decisions）
  - previous verdict/evidence（可清空）
- `ContextCleaner` 对上下文裁剪，保留关键意志与高优先证据
- 通过统一 LLM 客户端发起请求，返回终判文本与证据差分

### 4.3 提示词边界约束

- 终判以物理证据 + 已确认共识为主，不允许脱离物理链路“自由发挥”
- 插件冲突通过 `plugin_conflict_report` 注入证据链
- 失败时显式写入前端日志，避免“静默降级”

---

## 附：本轮已落实的稳定性修复

1. 返回主页面的状态恢复策略：
   - 刷新（reload）默认不恢复
   - 非 reload 导航自动恢复快照（满足从 debug/admin 返回保留现场）
2. 终判请求补齐 `abs_nodes`，降低 422/回退概率
3. 终判超时窗口上调至 45s，减少误超时 fallback
4. Decision Summary “用神/忌神”支持多字段形态兜底读取

---

## 已知问题与待分析项（需分析师复核）

### A. 场景冲突：刷新与返回恢复仍有误判

用户期望：

- 刷新页面：清空，不自动恢复
- 从 debug/admin 返回主页面：保留现场，自动恢复

当前现象（用户复测）：

- 从 debug 返回主页面仍可能清空
- 刷新时仍可能出现旧八字信息

说明当前“恢复判定条件”仍存在误触发/漏触发，需要进一步精确化。

### B. 建议分析路径

1. 明确导航来源判定顺序（优先级）：
   - 显式 query（`resume=1`）
   - `pageshow` 事件 + `persisted`
   - `performance.navigation` 类型
   - `document.referrer`
   - 自定义 session marker
2. 在主页面挂载时记录一份诊断对象（仅 debug）：
   - `navType`
   - `document.referrer`
   - `window.location.search`
   - `hasSnapshot`
   - `return_restore_once`
3. 明确“首次进入首页（新会话）”与“跨页返回首页”的区分键，避免把普通刷新误判为返回场景。

### C. 复现用例（建议逐条录屏）

1. Case-1 刷新清空校验
   - 主页算出结果 -> F5
   - 期望：不恢复
2. Case-2 Debug 返回恢复校验（底部导航）
   - 主页算出结果 -> 点 debug -> 点 lab
   - 期望：恢复
3. Case-3 浏览器后退路径
   - 主页算出结果 -> 地址栏进 debug -> 浏览器后退
   - 期望：恢复
4. Case-4 手输地址路径
   - 主页算出结果 -> 手输 /debug -> 手输 /
   - 期望：恢复

### D. 临时规避建议（在根因修复前）

- 运营/演示场景统一使用“返回实验室”按钮（可强制附带恢复参数）。
- 刷新后若需恢复，使用“恢复上次会话”按钮，不依赖自动判定。

