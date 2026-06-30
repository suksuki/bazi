# V40 Phase 40: V30 Replacement Readiness Closeout

Date: 2026-06-30

## 目标

让 V40 自己回答：

```text
当前是否具备替代 V30 的候选条件？
```

新增：

```text
build_v30_replacement_readiness
GET /api/v40/project/v30-replacement-readiness
```

## Readiness Gates

候选替代 V30 需要六个 gate：

- V30 shadow compare batch evidence。
- Evaluation batch + release readiness。
- Training examples + replay + replay batch。
- Candidate weight + activation review audit。
- User surface beta ready。
- V40 isolated runtime。

全部通过时：

```text
status = candidate_ready
readiness_percent = 100
```

## 人工确认仍然必须保留

即使系统 gates 全部通过，也仍需要：

- 真实命例质量判断。
- 最终产品验收。
- 线上切换窗口。

这三个不由自动脚本代替。

## 边界

- 只读。
- 不写 V30。
- 不写 V40 production。
- 不激活权重。
- 不启动训练。

## 完成度更新

Phase 40 后，V40 当前估算：

```text
overall: ~81%
architecture: ~94%
user beta: ~72%
training validation: ~80%
v30 replacement: ~70%
```

## 下一步

Phase 41:

```text
production beta cutover checklist
```
