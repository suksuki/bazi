# V30 Admin Console / Control Plane 主线设计

更新时间：2026-06-30

## 核心结论

Admin Console 不是用户测算 UI 的隐藏页面，而是 V30 的后台控制面：

```text
User App = 用户测算产品面
Admin Console = 管理、训练、验证、配置、审计、发布控制面
Runtime API = 用户测算 runtime
Admin API = 后台控制面 API
Worker = 训练、验证、回放、批处理任务
```

第一阶段不做物理微服务化，先做逻辑隔离：

```text
同 repo
同后端服务
独立 /api/admin/v30/*
独立 Admin contracts
独立 RBAC
独立 Job / Artifact / Audit 边界
保留旧 /api/v30/admin/* 兼容入口
```

2026-06-30 追加执行：Admin 前台已经先行物理拆出到独立服务和端口。

```text
Runtime API / User UI: http://127.0.0.1:9030
Admin Frontend:       http://127.0.0.1:9031/admin
Admin Frontend App:   v30.api.admin_frontend_app
Static Entry:         admin_frontend/index.html
```

Admin 前台服务只做：

- 服务 Admin Console 页面。
- 代理 `/api/v30/*` 与 `/api/admin/v30/*` 到 Runtime API。
- 不直接执行训练、验证、回放或策略发布。
- 不改命盘事实。

2026-06-30 追加收口：主系统已经完成去 Admin 化。

```text
Main Product UI: guest / user / practitioner
Admin Console UI: independent control plane on 9031
```

边界：

- 主系统不再包含 Admin Shell、训练、验证、DB、Redis、LLM 配置、后台读取和审计 UI。
- 主系统前端文件 `frontend/app.js`、`frontend/index.html`、`frontend/styles.css` 不再承载 admin 模块、入口或样式。
- `admin_frontend/app.js` 与 `admin_frontend/styles.css` 独立保留后台工作台能力。
- admin 账号如果进入主测算系统，只按命理师能力使用；管理能力只在独立 Admin Console 中出现。
- `/api/v30/ui/capabilities` 只宣告 `guest / user / practitioner`，不再暴露管理台入口。

## 设计边界

用户侧只关心：

- Verdict
- Advice
- Explanation
- Probe
- 用户反馈

Admin 侧负责：

- Runtime Trace
- Signal Registry
- Module Audit
- Decision trace
- LLM acceptance
- Golden Cases
- Evaluation Runs
- Training Runs
- Training Impact
- Synthetic / 518K Validation
- Config Versioning
- Release / Rollback

硬边界：

- 用户 UI 不展示训练、验证、debug artifact。
- Admin 不直接改命盘事实。
- Admin 配置默认走 `draft -> validate -> review -> publish -> runtime`。
- 重任务必须走 Job Runner，页面请求只提交任务和轮询状态。
- 旧 `/api/v30/admin/*` 暂作为兼容层，新入口从 `/api/admin/v30/*` 开始。

## 六个工作台

### 1. Runtime Trace

查看单次测算：

- 输入
- ChartContext
- Engine outputs
- DecisionCandidate
- DecisionVerdict
- Advice
- LLM acceptance
- reading_surface

### 2. Module Audit

查看模块产出责任：

- Signal Registry
- Module Audit
- source -> consumer -> user output
- runtime_used / test_only / train_only / debug_only / orphan / output_bound

### 3. Evaluation

管理：

- Golden Cases
- Synthetic Cases
- Regression Cases
- EvaluationCaseSpec
- ExpectedVerdict
- ForbiddenAssertions
- Advice Evaluation
- Probe Evaluation

### 4. Training

管理：

- Training runs
- Policy optimizer
- Weight candidates
- Training impact diff
- Before/after verdict diff
- Rollback

### 5. Validation / Gate

管理：

- synthetic validation
- 518K validation
- readiness tests
- LLM boundary tests
- Ziwei golden cases
- release gate

### 6. Config / Release

管理版本化配置：

- ruleset version
- weight version
- prompt version
- ziwei standard version
- probe template version
- advice template version
- activation / rollback

## RBAC

第一阶段定义角色：

- `viewer`：只读概览、trace、module audit
- `analyst`：看评测、validation、signal registry
- `practitioner`：标注 case、反馈分支、备注
- `trainer`：运行训练、查看 Training Impact
- `validator`：运行验证、518K、gate
- `publisher`：发布配置、回滚版本
- `owner`：全权限

危险操作必须审计：

- 发布权重
- 激活规则版本
- 修改紫微标准
- 修改 Probe 模板
- 回滚版本
- 删除/归档 case
- 运行大规模训练
- 运行 518K validation

审计字段：

- who
- when
- what
- before
- after
- reason
- validation_run_id

## 版本化配置

所有配置统一抽象为 Versioned Config：

```text
version_id
status: draft / validating / approved / active / archived / rolled_back
created_by
approved_by
created_at
activated_at
validation_run_ids
change_summary
rollback_target
```

第一阶段定义的配置类型：

- bazi_ruleset
- portrait_ruleset
- path_ruleset
- ziwei_standard
- ziwei_ruleset
- reality_probe_template
- hidden_attribute_schema
- advice_plan_template
- llm_prompt_profile
- llm_acceptance_rule
- policy_weight
- assertion_threshold

## 第一阶段落地

本轮完成：

- `ACP-1`：新增本 canonical 文档。
- `ACP-2`：新增 `v30.admin.contracts`，定义 Admin Manifest、Workbench、RouteAlias、VersionedConfig、AuditEvent。
- `ACP-3`：新增 `v30.admin.permissions`，定义 RBAC 权限矩阵。
- `ACP-4`：新增 `v30.admin.dashboard`，生成 Admin Control Plane Manifest。
- `ACP-5`：新增 `/api/admin/v30/control-plane/manifest`。
- `ACP-6`：新增 `/api/admin/v30/*` 第一批兼容入口：
  - `/readings/{reading_id}/trace`
  - `/readings/{reading_id}/production-audit`
  - `/readings/{reading_id}/decision-workbench-quality`
  - `/evaluation/training-spine`
  - `/training/orchestrator/plans`
  - `/training/orchestrator/run`
  - `/training/orchestrator/status`
  - `/training/orchestrator/history`
  - `/training/orchestrator/diff`
  - `/validation/artifacts`
  - `/validation/518k/artifacts`
- `ACP-7`：补充单元测试和 V30 scaffold 路由检查。
- `ACP-8`：新增独立 Admin 前台服务 `v30.api.admin_frontend_app`。
- `ACP-9`：新增 `admin_frontend/index.html`，独立进入 Admin Control Plane，不再依赖 `/v30/ui/?surface=admin`。
- `ACP-10`：新增 `scripts/run_admin_console.py`，默认 9031 端口启动 Admin 前台。
- `ACP-11`：Admin 前台代理 `/api/v30/*` 和 `/api/admin/v30/*` 到 `V30_RUNTIME_API_BASE_URL`，默认 `http://127.0.0.1:9030`。
- `ACP-12`：Admin 前台 JS/CSS 从主系统拆出为 `admin_frontend/app.js` 与 `admin_frontend/styles.css`；主系统前端移除 Admin Shell、管理入口、后台工作台逻辑和 admin 样式残留。

## 下一阶段

- `ACP-13`：新增 Admin Audit Log 存储和查询接口。
- `ACP-14`：新增 Versioned Config registry 最小实现。
- `ACP-15`：把更多旧 `/api/v30/admin/*` 逐步迁移为 `/api/admin/v30/*`。
- `ACP-16`：把 518K、LLM acceptance batch、before/after verdict diff 全部纳入统一 Job Registry。
- `ACP-17`：Admin UI 改为 6 个工作台的信息架构，不再按历史模块堆按钮。

## 验收标准

- 用户 UI 不出现训练/验证 artifact。
- Admin manifest 能列出工作台、权限、版本化配置和重任务边界。
- Admin 能通过新 namespace 运行 Evaluation Spine 和 Training Orchestrator。
- Admin 能查看 Trace / Production Audit / Decision Workbench Quality。
- Admin 发布和回滚必须可审计。
- 所有发布操作必须绑定 validation_run_id。

当前状态：

```text
Phase 1 logical isolation: usable
Phase 2 admin frontend service split: frontend service and JS/CSS split complete on 9031
Admin API service split: not started
```
