# V40 Phase 41: Production Beta Cutover Checklist

Date: 2026-06-30

## 目标

建立上线前只读 checklist，明确：

```text
自动检查是否 ready
人工签核是否仍然必须
```

新增：

```text
build_production_cutover_checklist
GET /api/v40/project/production-cutover-checklist
```

## 自动检查

Checklist 包含：

- V30 replacement candidate ready。
- Active weight audited。
- Rollback available。
- LLM ready。
- Repository configured。

所有自动项 ready 时：

```text
automatic_status = ready
cutover_status = blocked_by_human_signoff
```

也就是说，系统可以说自动条件齐备，但不能自己切生产流量。

## 人工签核

始终需要：

- 真实命例质量判断。
- 最终产品验收。
- 线上切换窗口。

## 边界

- 只读。
- 不写 V30。
- 不写 V40 production。
- 不切换流量。
- 不激活权重。

## 完成度更新

Phase 41 后，V40 当前估算：

```text
overall: ~84%
architecture: ~95%
user beta: ~76%
training validation: ~82%
v30 replacement: ~78%
```

## 下一步

Phase 42:

```text
V40 100% release candidate audit
```
