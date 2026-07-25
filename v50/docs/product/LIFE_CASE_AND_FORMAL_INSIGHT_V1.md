# Life Case and Formal Insight v1

## Life Case

Life Case 是长期案例的唯一认知容器，保存命盘版本、整盘基线、阶段先验、按需领域洞察、现实证据和修订历史。它不等于聊天记录，也不等于一份报告。

```text
LifeCase
├── ChartVersion
├── BaselineInsight
├── TemporalPriors
├── DomainInsights
├── RealityEvidence
└── RevisionLedger
```

修改出生资料必须创建新的 ChartVersion；旧洞察不能静默继承到新命盘版本。

## Formal Insight

每条正式洞察必须保存：

```text
Claim
Basis
Reasoning Path
Conditions
Expected Manifestations
Counter Signals
Uncertainty
Provenance
Status
```

状态流转固定为：

```text
draft → validated → committed
                  ↘ rejected
committed → superseded
```

Draft 可以用于等待过程中的预览，但不能进入 Life Case。只有通过 `validate_formal_insight` 的对象才能提交。

## 认知产物分域

```text
Baseline Cognition：不含事后现实结果的整盘基线
Temporal Prior：阶段开始前形成的时间先验
Domain Analysis：用户主动选择领域后形成
Decision Support：结合当下目标与已知现实条件
Case Revision：现实证据出现后的案例修正
```

先验与事后修正不能互相覆盖。
