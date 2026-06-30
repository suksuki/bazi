# V40 Phase 2: Migration Importer And Shadow Compare

更新时间：2026-06-30

## 目标

Phase 2 开始真正迁移 V30 成熟能力，但仍然只通过 plain JSON DTO 边界进入 V40。V40 不 import V30 runtime，不读 V30 数据库，不读 V30 Redis，不读 V30 runtime file。这里的 importer 是迁移工具，不是 V40 正式 runtime 主链依赖。

本阶段建立：

```text
V30ExportEnvelope
  -> V40 RuntimeSignal
  -> V40 DecisionVerdict
  -> V40 AdvicePlan
  -> V40 ProductProjectionBundle
  -> ShadowCompareResult
```

## 新增模块

```text
v40/migration/v30_importer.py
v40/evaluation/shadow_compare.py
```

## Migration Importer 边界

V30 必须先导出 plain JSON：

```text
chart_facts
feature_rows
signal_rows
verdict_rows
advice_rows
probe_rows
product_projection_rows
```

V40 只消费这些 rows，不接收：

```text
raw_runtime_path
raw_database_ref
raw_redis_key
```

`V30ExportEnvelope` 已用模型校验拒绝这些 raw 引用。

## 转换策略

| V30 DTO | V40 Contract | 规则 |
| --- | --- | --- |
| `signal_rows` | `RuntimeSignal` | 归一化 source/topic/polarity/assertion_hint/evidence。 |
| `feature_rows` | `RuntimeSignal` | 作为 feature signal 进入 SignalRegistry。 |
| `verdict_rows` | `DecisionVerdict` | 保留 topic/headline/confidence/evidence；强断语无证据时降为 `weak_candidate`。 |
| `advice_rows` | `AdvicePlan` | 必须绑定 Verdict；没有独立 advice 时从 Verdict 生成保守建议。 |
| Verdict/Advice | `ProductProjectionBundle` | 生成用户可见卡片，并做最小泄漏检查。 |

## Shadow Compare

`ShadowCompareResult` 比较：

```text
V30 signal count vs V40 signal count
V30 verdict count vs V40 verdict count
V30 advice count vs V40 advice count
import coverage
verdict topic overlap
product projection readiness
surface leakage status
```

当前推荐策略固定为 `needs_review`，因为 Phase 2 只允许 shadow compare，不允许写生产。

## 当前验收

1. Migration importer 可把 V30 fixture 转成 V40 RuntimeResult。
2. RuntimeResult 不导入 V30 runtime。
3. ShadowCompare 不写 V30，不写 V40 production。
4. ProductProjection 生成且 `leakage_scan_passed=True`。
5. 测试继续证明 V40 代码无 `from v30` / `import v30`。

## 下一步

1. 增加 V30 export script，但脚本必须在 V30 侧输出 plain JSON artifact。
2. 增加 V40 artifact importer，只读 JSON，不连 V30 runtime。
3. 增加真实 V30 smoke case 的 shadow compare fixture。
4. 增加 `/api/v40/shadow-compare` 只读接口。
