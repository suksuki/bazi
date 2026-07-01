# V40 Phase 50: User UI Visual QA

日期：2026-07-01

## 目标

Phase 50 把 V40 用户侧从“功能可跑”推进到“页面可验收”。本阶段不改变命理算法，不改 DecisionEngine，不改 LLM 权限，只验证产品壳和关键交互边界。

## 验收场景

自动视觉 QA 覆盖三种首屏：

| 场景 | 视口 | 身份 | 重点 |
| --- | --- | --- | --- |
| desktop_user | 1440x960 | user | 普通用户主流程、报告优先、无工程词 |
| desktop_practitioner | 1440x960 | practitioner | Practitioner Lens 只在命理师身份出现 |
| mobile_user | 390x844 | user | 手机端无横向溢出，核心输入可见 |

## 脚本

```text
qiazhi/v40/scripts/run_user_ui_visual_qa.py
```

运行：

```bash
PYTHONPATH=qiazhi/v40 qiazhi/.venv312/bin/python qiazhi/v40/scripts/run_user_ui_visual_qa.py
```

默认目标：

```text
http://127.0.0.1:9040/v40/ui
```

默认输出：

```text
qiazhi/v40/.runtime/visual_qa/phase50/
```

输出包括：

1. 每个场景一张 full-page PNG；
2. `visual_qa_report.json`；
3. 失败时列出具体场景和原因。

## 检查项

1. 页面必须出现品牌与输入表单；
2. 普通用户身份显示为普通用户；
3. 命理师 header 会触发命理师视角；
4. 命理师视角下 Practitioner Lens 可见；
5. 普通用户和手机端不出现 Practitioner Lens；
6. 页面可见文字不得泄漏 provider/model/prompt/acceptance/policy/debug/telemetry/admin 等工程词；
7. 页面源码不得使用 URL role hook；
8. 手机端不得出现明显横向滚动；
9. 常见按钮和输入控件不得明显文本溢出。

## 边界

Phase 50 不做：

1. 真实命例质量验收；
2. LLM 输出质量评审；
3. ConsentGrant；
4. Practitioner Review Queue；
5. 线上浏览器矩阵。

这些进入 Phase 51+。

## 完成标准

Phase 50 完成时：

1. 视觉 QA 脚本可运行；
2. 三个场景截图生成；
3. 自动 QA 报告 `passed=true`；
4. V40 全量测试通过；
5. 项目状态进入 Phase 50。
