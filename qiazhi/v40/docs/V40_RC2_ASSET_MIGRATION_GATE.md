# V40-RC2 Asset Migration Gate

Date: 2026-07-01

## 目标

所有 V30 命理资产迁入 V40 前，必须通过统一 gate。

这不是代码搬迁，而是资产萃取：

```text
V30 asset → V40 native evidence/signal/candidate/probe/training material
```

## MigratedMingliAsset Contract

```python
class MigratedMingliAsset:
    asset_id: str
    source_v30_module: str
    source_ref: str
    asset_type: Literal[
        "fact_rule",
        "feature_rule",
        "diagnosis_rule",
        "path_rule",
        "portrait_rule",
        "knowledge_card",
        "probe_template",
        "domain_adapter_seed",
    ]

    target_v40_type: Literal[
        "runtime_signal",
        "knowledge_card",
        "probe_template",
        "decision_candidate_seed",
        "advice_seed",
        "training_rule",
    ]

    topic: str
    domain: str | None
    claim_key: str | None

    evidence_policy: str
    default_confidence: float
    assertion_hint: str
    max_assertion_level: str
    forbidden_user_claims: list[str]

    allowed_roles: list[str]
    user_visible: bool

    required_tests: list[str]
    migration_status: Literal[
        "draft",
        "sidecar",
        "evaluating",
        "enabled",
        "disabled",
        "rejected",
    ]
```

## 状态流

```text
draft → sidecar → evaluating → enabled
```

含义：

- `draft`：资产已登记，但不可运行。
- `sidecar`：只观察，不影响 Verdict。
- `evaluating`：进入 Acceptance Window，不影响线上。
- `enabled`：通过验收后可影响 Decision。

## Gate Questions

每个迁移资产必须回答：

1. 它产出的是什么？
2. 对应哪个 domain？
3. 它是 fact / signal / candidate / advice / probe / training label 哪一类？
4. 有没有 evidence_ref？
5. 有没有 confidence / assertion_hint？
6. 能不能映射到 RuntimeSignal？
7. 能不能进入 DecisionCandidate？
8. 是否允许用户可见？
9. 是否可能造成过度断言？
10. 有没有 golden/synthetic regression case？

## 禁止项

- 禁止直接 import `v30.*`。
- 禁止 V30 rule 直接成为 Verdict。
- 禁止 KnowledgeCard 自己下断语。
- 禁止 PortraitSignal 直接输出强断语。
- 禁止未经过 before/after diff 的 enabled。
- 禁止迁移后 overclaim rate 上升。

## Before / After Diff

每批迁移都必须比较：

```text
V40 baseline
V40 + migrated asset
diff
```

观察：

- Verdict 有没有变好。
- Advice 有没有更具体。
- Probe 有没有更有效。
- Overclaim 有没有升高。
- 工程语言有没有泄漏。
- LLM 有没有越界。
- 用户输出是否变复杂。
