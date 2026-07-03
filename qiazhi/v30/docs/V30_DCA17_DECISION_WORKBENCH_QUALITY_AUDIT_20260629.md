# V30 DCA-17 Decision Workbench Quality Audit

更新时间：2026-06-29

## 目标

DCA-17 解决一个主线问题：已有模块、Signal Registry、Decision Engine、ConflictResolver、命理师交互和 7 阶段 UI 是否真的变成了用户侧产出。

本阶段不是新增命理规则，也不是让 LLM 或训练系统做最终决策，而是新增一层只读质量审计：

```text
runtime facts
-> thinking projection
-> decision_workbench surface
-> practitioner option sets
-> customer projection contract
-> quality audit
```

## 角色边界

- `Decision Engine`：唯一可产生 `Verdict` 的裁决层。
- `ConflictResolver`：识别分支、反证、置信差和待校准问题，不直接改分数。
- `Central Brain`：组织证据、反馈、权重、对话和质量门禁，不直接替代 Verdict。
- `LLM`：负责最终表达、对话语言、必要解释和边界复核，不生成命盘事实，不做最终命理裁决。
- `Quality Audit`：只读观察层，检查产出是否进入产品，不写 runtime、不晋级策略、不修改命盘事实。

## 检查内容

DCA-17 审计 `v30.decision_workbench_quality_audit.v1` 覆盖：

- 7 阶段流程是否启用，避免回退旧 `11/13` 步 LLM 解释流。
- Journey 页面是否默认 `llm_enhancement=not_required`，防止每页 LLM 长文污染素材。
- `decision_workbench` 是否 ready，且绑定 Verdict。
- 有分支冲突时是否形成命理师校准入口。
- 普通用户是否隐藏训练信号，命理师/Admin 是否可见训练投影。
- 智能对话是否通过 `reading_surface.current_dialogue_turn` 独立挂载，而不是混入步骤导航。
- 质量审计是否保持 `chart_fact_mutation_allowed=false`、`policy_pointer_write_allowed=false`。

## API

```text
GET /api/v30/admin/readings/{reading_id}/decision-workbench-quality
```

返回：

- `summary`：阶段数、Verdict 数、冲突数、分支选项数、角色隔离、对话入口。
- `quality_scores`：总分、产出绑定、校准、角色边界、流程和检查分。
- `checks`：结构化质量检查。
- `admin_diff_rows`：面向 admin 的基线 diff。
- `decision`：是否 ready、失败检查、下一阶段建议。

## Admin UI

Admin `测算记录` 页面读取同一 reading 后展示：

- 质量分。
- 7 阶段 / Verdict / 冲突 / 分支选项 / 命理师选项摘要。
- 关键 diff。
- 失败检查优先显示；全部通过时显示前 6 个通过检查。

## 任务状态

- [x] 新增 `v30.validation.decision_workbench_quality`。
- [x] 新增 Admin API。
- [x] Admin readings 页面接入质量审计。
- [x] 保持审计只读，不写策略指针，不修改 chart facts。
- [x] 增加专项单元测试。

## 下一阶段

DCA-18 进入真实案例回放和训练门禁：

- 用真实/合成案例批量跑 `decision_workbench_quality_audit`。
- 统计哪些模块只是 candidate/debug/test-only，没有进入 Verdict / Advice / UI。
- 把质量结果反哺训练策略候选，但仍不得修改命盘事实。
