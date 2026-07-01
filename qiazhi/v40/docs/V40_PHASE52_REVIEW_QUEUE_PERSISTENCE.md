# V40 Phase 52: Review Queue Persistence And Assignment

日期：2026-07-01

## 目标

Phase 51 已经建立：

```text
ConsentGrant
AnonymizedCaseView
PractitionerReviewRequest
PractitionerReviewQueueItem
PractitionerReviewResult
```

但它们还只是 API 返回的合同产物。Phase 52 要把它们落到 V40 独立 Postgres 仓储，让用户授权、审阅请求、队列项和命理师复核结果可以被后续 Admin、训练闭环和用户侧 consent UI 消费。

## 本阶段要完成

1. 新增 V40 Postgres 表：
   - `v40_consent_grants`
   - `v40_practitioner_review_requests`
   - `v40_practitioner_review_queue`
   - `v40_practitioner_review_results`
2. Repository 支持：
   - 保存 / 查询 consent grants；
   - 保存 / 查询 review requests；
   - 保存 / 查询 queue items；
   - 更新 queue item assignment；
   - 保存 / 查询 review results；
   - review result 内的 `TrainingLabelEvent` 同步进入训练标签表。
3. API 支持：
   - `persist=true` 时写入 V40 repository；
   - `GET /api/v40/practitioner/review-queue` 返回持久化队列；
   - review result persist 时同时保存 local training labels；
   - assignment 只改变 queue item 元数据，不改 verdict。
4. Project status 进入 Phase 52。

## 不做

Phase 52 不做：

1. 真实命理师账号匹配；
2. 排班、抢单、计费；
3. review UI；
4. raw runtime 或 chart facts 分享；
5. 全局权重写入；
6. V30 状态写入。

## 数据边界

### ConsentGrant

持久化为用户授权记录，允许后续创建审阅请求。它不能授予 admin 权限，也不能允许 raw chart share。

### Review Request

保存 `PractitionerReviewRequest`，其中包含 `AnonymizedCaseView`。这里仍不保存 raw runtime。

### Queue Item

保存可分配队列元数据：

```text
queue_item_id
review_request_id
reading_id
topic
status
assigned_to_practitioner_ref
summary
```

assignment 只影响 `status` 和 `assigned_to_practitioner_ref`。

### Review Result

保存命理师复核结果，同时将 result 内的 local training label 保存到 `v40_training_label_events`。

## API 行为

```text
POST /api/v40/consent/grants
POST /api/v40/practitioner/review-requests
GET  /api/v40/practitioner/review-queue
POST /api/v40/practitioner/review-results
```

Phase 52 增强：

- 创建 consent / review request / review result 默认仍支持 `persist=false`。
- 显式 `persist=true` 时写入 repository。
- review queue GET 优先读取 repository；未配置数据库时返回空队列和清晰状态。
- review result persist 会保存训练标签，但仍然 `writes_v40_production=false`。

## 验收

1. schema 包含四张新表和 reading/status 索引；
2. repository 包含 save/list/assign 方法；
3. API persist=false 保持轻量；
4. API persist=true 在 repository 配置时可读回；
5. review result persist 保存 local training labels；
6. lab summary 能统计 review records；
7. V40 全量测试通过。
