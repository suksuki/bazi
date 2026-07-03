# V40 Phase 44: Final Operating Guide

Date: 2026-06-30

## 当前服务

```text
Runtime: http://127.0.0.1:9040
Admin:   http://127.0.0.1:9041/admin/v40
User UI: http://127.0.0.1:9040/v40/ui
```

## Python 版本红线

V40 只用 Python 3.12 运行。默认入口是：

```text
qiazhi/v40/scripts/start_v40.sh
qiazhi/v40/scripts/start_v40_admin.sh
```

这两个脚本会优先使用：

```text
qiazhi/.venv312/bin/python
```

不要裸用系统 `python3` 跑 V40 命令；macOS 自带 `python3` 可能是 3.9，会导致 V40 的类型合约和 Pydantic 模型加载失败。

## 实时完成度

```text
GET /api/v40/project/status
GET /admin/v40/api/project-status
```

Admin 顶部 `V40 Completion` 每 15 秒刷新。

## 自动验收接口

```text
GET /api/v40/surface/beta-readiness
GET /api/v40/project/v30-replacement-readiness
GET /api/v40/project/production-cutover-checklist
GET /api/v40/project/release-candidate-audit
GET /api/v40/project/production-smoke
```

当前自动状态：

```text
surface beta: ready
v30 replacement: candidate_ready
cutover automatic checks: ready
release candidate audit: automatic_audit_passed_human_signoff_required
production smoke: passed_handoff_ready
```

## 关键边界

V40 自动流程不做：

- 不写 V30。
- 不切生产流量。
- 不静默 fallback。
- 不让 LLM 做 verdict。
- 不让 LLM 不可用时生成替代报告。
- 训练验证通过后直接生效，但必须保留回滚和补救路径。

## 人工验收项

这些不能由 Codex 或系统自动完成：

- 真实命例质量判断。
- 最终产品验收。
- 线上切换窗口。
- 外部账号、域名、生产凭证确认。

## 回滚

上线前必须确认：

- active weight 存在。
- `rollback_version_id` 非空。
- Admin `Candidate Risk` 不存在 blocked 项。
- Production cutover checklist 自动项 ready。

## 建议验收顺序

1. 打开 User UI，跑 3 到 5 个真实命例。
2. 普通用户模式验证报告优先和继续追问。
3. 命理师模式验证校准动作是否能记录。
4. Admin 查看 V40 Completion、Candidate Risk、Training Feedback。
5. 确认 production smoke 为 `passed_handoff_ready`。
6. 决定是否进入线上切换窗口。

## 完成度更新

Phase 44 后，V40 自动交付完成度：

```text
overall: ~98%
```

剩余 2% 是人工验收和切换窗口，不应该自动完成。
