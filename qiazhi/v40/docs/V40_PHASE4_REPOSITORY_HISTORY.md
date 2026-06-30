# V40 Phase 4: Repository And Run History

更新时间：2026-06-30

## 目标

把 V40 从“可启动、可返回一次 shadow compare”推进到“可保存、可追踪、可回放”的运行时。

Phase 4 只做 V40 自己的仓储层：

```text
RuntimeResult -> v40_runtime_records
ShadowCompareResult -> v40_shadow_compare_runs
```

不会：

```text
写 V30 state
读取 V30 runtime
写 V40 production verdict/weight
启动训练参数更新
```

## 新增模块

```text
v40/storage/config.py
v40/storage/postgres.py
tests/test_v40_repository_phase4.py
```

## Repository 边界

`V40PostgresRepository` 只允许访问：

```text
v40_runtime_records
v40_shadow_compare_runs
```

连接配置只从：

```text
V40_DATABASE_URL
.env.v40.local
```

读取。API health 只返回是否配置，不返回 DSN 或密码。

## API 更新

```text
POST /api/v40/shadow-compare?persist=true
GET  /api/v40/shadow-compare/runs?limit=20
```

`persist=true` 的语义：

```text
保存本次 RuntimeResult 和 ShadowCompareResult 到 V40 历史表。
```

`persist=false` 的语义：

```text
只做一次内存 shadow compare，不落库。
```

## 为什么先保存 Shadow Compare

V40 alpha 阶段还没有接用户正式流量。当前最重要的是：

1. 迁移样本可回放；
2. 每次 V40 输出能和旧系统导出结果比较；
3. 后续 Admin Console 可以查看历史；
4. Release Gate 能基于历史记录做趋势判断。

## 后续接入

下一阶段已进入 Phase 5：

```text
EvaluationCaseRepository
TrainingLabelRepository
ReleaseGateRepository
```

其中训练和 release gate 必须继续遵守：

```text
训练只能产生 candidate / impact diff；
生产生效必须通过 release gate；
chart facts 永远不可训练改写。
```
