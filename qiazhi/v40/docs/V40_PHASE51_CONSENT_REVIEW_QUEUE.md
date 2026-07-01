# V40 Phase 51: ConsentGrant And Practitioner Review Queue

日期：2026-07-01

## 目标

Phase 51 建立用户授权与命理师审阅的最小合同层。它解决的问题是：

```text
用户什么时候允许命理师看案例？
命理师看到的是什么材料？
命理师反馈如何进入训练闭环？
```

本阶段只做合同和最小运行时骨架，不做完整派单系统。

## 新合同

```text
ConsentGrant
AnonymizedCaseView
PractitionerReviewRequest
PractitionerReviewQueueItem
PractitionerReviewResult
```

### ConsentGrant

用户侧授权，不授予 admin 能力，不允许改命盘事实。

核心边界：

1. 只能来自 guest/user/practitioner；
2. 支持 practitioner_review、training_feedback、anonymized_case_share；
3. Phase 51 只允许脱敏案例；
4. 不允许 raw chart share；
5. 不允许 admin control。

### AnonymizedCaseView

命理师只看到可审阅摘要：

1. verdict summaries；
2. advice summaries；
3. probe questions；
4. evidence refs；
5. source signal ids。

它不包含：

1. raw runtime；
2. chart facts；
3. birth datetime；
4. account/contact/name。

### PractitionerReviewResult

命理师复核结果只生成 local training material：

```text
PractitionerReviewResult
  -> TrainingLabelEvent(local_only=true)
```

它不能直接改：

1. DecisionVerdict；
2. ChartFacts；
3. GlobalWeightVersion；
4. V30 状态。

## 新 API

```text
POST /api/v40/consent/grants
POST /api/v40/practitioner/review-requests
GET  /api/v40/practitioner/review-queue
POST /api/v40/practitioner/review-results
```

当前阶段：

1. API 返回合同产物；
2. 不持久化；
3. 不分配真实命理师；
4. 不返回 raw runtime/chart facts；
5. review result 返回 local training label。

## 运行时流程

```text
RuntimeResult
  + ConsentGrant
  -> AnonymizedCaseView
  -> PractitionerReviewRequest
  -> PractitionerReviewQueueItem
  -> PractitionerReviewResult
  -> TrainingLabelEvent
```

## 验收

1. 没有 consent 不能创建 review request；
2. consent revoked 不能创建 review request；
3. review request 返回脱敏 case view；
4. case view 不包含 chart facts/raw runtime；
5. review result 生成 local training label；
6. 所有接口不写 V30、不写生产权重；
7. V40 全量测试通过。

## 后续

Phase 52+ 再做：

1. review queue persistence；
2. practitioner assignment；
3. practitioner reliability score；
4. user-side consent UI；
5. Admin review audit。
