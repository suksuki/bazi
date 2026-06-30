# V40 Phase 3: API And Schema

更新时间：2026-06-30

## 目标

建立 V40 独立服务骨架，让 V40 能作为新 runtime 单独启动和检查，但仍不接业务页面、不接 V30 runtime、不写生产权重。

## 新增模块

```text
v40/api/app.py
v40/contracts/manifest.py
scripts/start_v40.sh
deploy/postgres_v40_schema.sql
tests/test_v40_api_phase3.py
```

## API

```text
GET  /api/v40/health
GET  /api/v40/contracts
POST /api/v40/shadow-compare
```

### `/api/v40/health`

返回 V40 独立边界：

```text
package=v40
api_prefix=/api/v40
database_boundary=qiazhi_v40
postgres_table_prefix=v40_
redis_prefix=v40
v30_runtime_import_allowed=false
```

### `/api/v40/contracts`

返回 V40 contract manifest 和边界矩阵。

### `/api/v40/shadow-compare`

只接收 `V30ExportEnvelope` plain JSON，返回：

```text
RuntimeResult
ShadowCompareResult
```

不会：

```text
写 V30 state
写 V40 production
读取 V30 database
读取 V30 Redis
读取 V30 runtime file
```

## Schema

当前 schema 只建 V40 表：

```text
v40_runtime_records
v40_evaluation_cases
v40_training_label_events
v40_shadow_compare_runs
v40_release_gates
```

所有表必须使用 `v40_` 前缀。

## 下一步

1. 把 schema apply 到本地 `qiazhi_v40`。已完成。
2. 增加 V40 local repository，只读写 `v40_*` 表。进入 Phase 4。
3. 增加 shadow compare run history 存储。进入 Phase 4。
4. 增加 V30 export artifact script，但脚本运行在 V30 侧，只输出 JSON artifact。
