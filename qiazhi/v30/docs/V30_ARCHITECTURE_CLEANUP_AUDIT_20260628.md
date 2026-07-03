# V30 架构级清理审计

更新时间：2026-06-28

## 本轮目标

近期 V30 主线改动集中在中枢智能大脑、LLM thinking、小结生成、智能对话、训练校准与验证链路。代码和文档都出现了阶段性沉积。本轮清理先处理低风险、确定废弃、确定重复的部分，并给后续清理划出边界。

## 已完成清理

### 运行缓存

已删除 Python 运行缓存：

- `v30/**/__pycache__/`
- `tests/**/__pycache__/`
- `v30/**/*.pyc`
- `tests/**/*.pyc`

清理前发现 31 个 `__pycache__` 目录、626 个 `.pyc` 文件；清理后均为 0。

这些文件不是源码，不应进入架构判断，也不应参与后续同步或提交。

### DTC 文档合并

已将 DTC-1 到 DTC-8 的 8 份阶段文档合并为一份主线文档：

- `docs/V30_DIALOGUE_TRAINING_PIPELINE_20260628.md`

已删除的碎片文档：

- `docs/V30_DIALOGUE_TRAINING_CALIBRATION_LOOP_20260627.md`
- `docs/V30_DIALOGUE_POLICY_CANDIDATE_REVIEW_20260627.md`
- `docs/V30_DIALOGUE_STRATEGY_VALIDATION_GATE_20260627.md`
- `docs/V30_DIALOGUE_SYNTHETIC_REPLAY_QUEUE_20260627.md`
- `docs/V30_DIALOGUE_OPERATOR_REVIEW_PACK_20260627.md`
- `docs/V30_DIALOGUE_HEAVY_VALIDATION_DECISION_20260628.md`
- `docs/V30_DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_20260628.md`
- `docs/V30_DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_20260628.md`

合并后的边界更清晰：

- DTC-1 到 DTC-8 是同一条训练验证管线，不再分散维护。
- 当前阶段仍然只读，不发布策略、不写 production pointer、不修改八字事实层。
- 下一步主线是 DTC-9：显式执行 runner。

### 第二批历史阶段文档归档

已将已完成阶段计划从 `docs/` 根目录移入 `docs/archive/`：

- `V30_BRAIN_TRAINING_SYNTHETIC_COMPLETION_MAINLINE.md`
- `V30_MULTI_USER_TERMINAL_LOCALE_PRODUCTIZATION_MAINLINE.md`
- `V30_CONTROLLED_RELEASE_READINESS_PLAN.md`
- `V30_POST_SEAL_RELEASE_HARDENING_PLAN.md`
- `V30_M1_M2_BAZI_CALCULATION_FACT_LAYER_COMPLETION_PLAN.md`
- `V30_M3_CORE_KNOWLEDGE_STRUCTURE_COMPLETION_PLAN.md`
- `V30_M4_TEN_GOD_ENERGY_MODEL_COMPLETION_PLAN.md`
- `V30_M5_RANKED_DECISION_COMPLETION_PLAN.md`
- `V30_M6_PRACTICAL_READING_OUTPUT_COMPLETION_PLAN.md`
- `V30_M7_REAL_CASE_CALIBRATION_COMPLETION_PLAN.md`
- `V30_M8_USER_PRESENTATION_API_PROJECTION_COMPLETION_PLAN.md`

这些文档不是废弃内容，而是已完成阶段的历史证据。当前开发入口改由 `V30_MAINLINE_STATUS_20260628.md` 和 `V30_DOCUMENTATION_INDEX_20260628.md` 控制。

### 前端旧交互上下文清理

已确认前端不再渲染批量推荐问题列表。当前用户页只通过 `reading_surface.current_dialogue_turn` 渲染一个聚焦问题。

同时移除了 `renderReading()` 中已经不再使用的旧上下文字段，包括 `questions`、`options`、`domainCards`、`basicAssertions`、`baziFeatures`、`baziPortraits`、`baziPaths` 等，避免后续误把旧大页面结构重新接回用户界面。

### 旧 release / core-monitoring 过程链路代码删除

已删除一批不再属于当前主线的历史过程型代码。它们原来用于记录外部发布暂停、full pytest defer、release pause 后的 core monitoring P0-S0 过程状态；现在这些信息已经进入 archive 文档，不再作为运行时代码和管理端 API 维护。

删除范围：

- 11 个 `v30/validation/*` 历史过程模块
- 11 个 `scripts/run_*.py` 历史执行脚本
- 11 个 `tests/unit/test_*.py` 历史模块测试
- 16 个管理端旧路由断言和对应 endpoint 测试

已移除的管理端 API：

- `/api/v30/admin/release/external-dry-run`
- `/api/v30/admin/release/full-pytest-decision`
- `/api/v30/admin/release/blocked-status`
- `/api/v30/admin/release/post-boundary-authorization`
- `/api/v30/admin/mainline/selection-after-release-pause`
- `/api/v30/admin/core/monitoring-loop`
- `/api/v30/admin/core/lightweight-monitoring-checks`
- `/api/v30/admin/core/calibration-observation-summary`
- `/api/v30/admin/core/calibration-drift-watch`
- `/api/v30/admin/core/focused-calibration-evidence-queue`
- `/api/v30/admin/core/calibration-queue-review`
- `/api/v30/admin/core/calibration-watch-closeout`
- `/api/v30/admin/core/monitoring-cadence-baseline`
- `/api/v30/admin/core/monitoring-cadence-documentation-sync`
- `/api/v30/admin/core/monitoring-steady-state`
- `/api/v30/admin/core/monitoring-s0-status`

保留边界：

- `core_calibration_observation_summary` 仍保留，因为当前 evidence-driven calibration queue 仍然需要轻量观测输入。
- 该模块已从旧 `lightweight_core_monitoring_checks -> core_monitoring_loop -> release pause` 依赖链中解耦，改为自包含的 `v30.core_observation_baseline.v1`。
- DTC 智能对话训练验证链路未删除，因为它是当前主线。

## 深度 review 结论

### 不能删除的主线模块

以下模块虽然很多是最近新增，但已经属于当前主线，不能按“未跟踪文件”或“新文件”直接清掉：

- `v30/brain/dialogue_planner.py`
- `v30/brain/dialogue_training.py`
- `v30/brain/final_synthesis.py`
- `v30/brain/reading_engine.py`
- `v30/llm/thinking_context.py`
- `v30/presentation/thinking.py`
- `v30/reasoning/`
- `v30/semantics/`
- `v30/training/`
- `v30/validation/dialogue_*.py`

原因：

- 它们承载智能对话、训练校准、候选策略、验证闸门、重型验证执行计划等主线功能。
- 相关 API 路由和单元测试已经绑定这些模块。
- 如果现在删除，会回到旧的模板式问答和无训练闭环状态。

### 当前文档状态

文档仍然偏多，但不应一次性粗暴删除。当前建议分三类维护：

第一类：主线架构文档，保留并继续更新。

- `V30_TRAINING_ARCHITECTURE.md`
- `V30_UNIFIED_INTERACTION_BRAIN_PLAN.md`
- `V30_BAZI_LLM_CONTEXT_AND_PROMPT_MAINLINE.md`
- `V30_DIALOGUE_TRAINING_PIPELINE_20260628.md`
- `V30_CENTRAL_BRAIN_READING_ENGINE_FRAMEWORK_20260627.md`

第二类：专项设计文档，暂时保留，后续按主题合并。

- UI 产品化
- 隐藏属性
- 八字核心模型
- 规则、画像、路径、特征
- 518k 验证
- 合成验证

第三类：阶段性任务文档，需要下一轮继续压缩。

- 带日期的任务清单
- 早期 review 改进列表
- 临时实现任务拆解

## 当前风险

- 文档数量仍然偏多，需要第二轮按“主线架构、产品体验、训练验证、部署运维”四类重排。
- 训练验证链路已有 DTC-1 到 DTC-8，但 DTC-9 runner 尚未落地，重型验证仍停留在计划层。
- 智能对话模块已经从旧系统剥离，但仍需要继续检查前端是否残留旧交互入口。
- 完整测试套件可能仍存在非本轮引入的历史阻断项，需要单独处理。

## 下一轮建议

1. 做文档目录重排：
   - `architecture`
   - `product`
   - `training`
   - `deployment`
   - `archive`

2. 清理前端旧对话入口：
   - 只保留“当前页面必要问题、点击即问、回答后生成下一组问题”的交互。
   - 删除幽灵式问题区域和旧状态文案。

3. 落地 DTC-9：
   - 执行 DTC-8 的验证命令。
   - 保存 artifacts。
   - 输出三态结果：通过、失败、阻断。
   - 不自动发布。

4. 建立文档索引：
   - 每个主线模块只保留一份 canonical doc。
   - 阶段性文档归档，不再作为实时设计依据。
