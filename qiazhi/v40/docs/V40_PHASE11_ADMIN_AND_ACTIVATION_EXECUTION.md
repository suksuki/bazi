# V40 Phase 11: Admin Console And Activation Execution

更新时间：2026-06-30

## 目标

把 V40 控制面从“只记录激活审核”推进到“可以显式执行 V40 候选权重激活”，并提供独立 Admin/Lab 前端服务。

Phase 11 新增：

```text
WeightActivationExecution
POST /api/v40/weights/activate
GET  /api/v40/weights/activation-executions
v40_weight_activation_executions
v40/admin/app.py
scripts/start_v40_admin.sh
```

## 激活执行协议

激活必须同时满足：

```text
review.decision=approve
executed_by_role=admin
rollback_version_id 非空
confirm_phrase=ACTIVATE_V40_WEIGHT
```

执行后只改变 V40 控制面权重状态：

```text
目标 GlobalWeightVersion.active=true
其他 active 版本降为 false
记录 WeightActivationExecution
```

不会：

```text
写 V30 state
修改 chart facts
绕过 release readiness
绕过 activation review
```

## 独立 Admin/Lab 服务

启动：

```bash
V40_PYTHON=/path/to/python scripts/start_v40_admin.sh
```

默认地址：

```text
http://127.0.0.1:9041/admin/v40
```

默认读取：

```text
V40_API_BASE=http://127.0.0.1:9040
```

当前页面是 read-only control plane，用于查看：

```text
batch
release readiness
candidate weights
activation reviews
activation executions
```

## 下一阶段

Phase 12 已进入：

1. Synthetic case generator；
2. V40 原生命理引擎骨架；
3. V30 DTO batch export 工具进入后续阶段；
4. Admin Console 增加操作流进入后续阶段，但继续要求显式确认；
5. 多候选版本 rollback 演练进入后续阶段。
