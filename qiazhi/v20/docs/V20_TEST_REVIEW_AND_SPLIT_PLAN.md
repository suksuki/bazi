# V20 测试用例 Review 与拆分计划

## 当前结论

V20 本地全量测试已经不是“快速循环”。最近一次全量结果是：

```text
407 passed in 466.69s
```

所以测试流程需要按真实用途拆分，不能继续让 `fast` 直接覆盖所有测试。

## 新测试分层

| 层级 | 脚本 | 目标 | 适用场景 |
| --- | --- | --- | --- |
| `smoke` | `scripts/test_smoke.sh` | 编译和最小主链冒烟 | 很小改动后的第一步 |
| `fast` | `scripts/test_fast.sh` | 主线哨兵，不等于全量 | 日常默认循环 |
| `core` | `scripts/test_core.sh` | Runtime、API、ops、存储、鉴权 | 系统底座变更 |
| `brain` | `scripts/test_brain.sh` | 中枢大脑、问题链、角色链、编排 | 智能逻辑变更 |
| `training` | `scripts/test_training.sh` | 训练、知识、规则、画像、合成数据、指针 | 自我训练和调参变更 |
| `ui` | `scripts/test_ui.sh` | Admin 和 Workbench 静态 UI 契约 | 前端页面变更 |
| `targeted` | `scripts/test_targeted.sh` | 指定表达式或路径 | 精准修 bug |
| `full` | `scripts/test_full.sh` | 全量本地 407 用例收口 | 阶段完成、提交前 |
| `services` | `scripts/test_services.sh` | Postgres、Redis、服务同步 | 显式打开服务测试 |
| `corpus` | `scripts/test_corpus.sh` | 518K 和长语料任务 | 显式打开长任务 |

## 清理标准

保留：

- 覆盖真实运行链路、训练生效链路、Admin UI 链路的用例。
- 能防止参数直接生效、runtime pointer、问题链、画像链倒退的用例。
- 能独立、可重复、无外部服务依赖运行的单元/契约用例。

改造：

- 直接拉起 ASGI `TestClient` 导致卡住的用例，改成直接调用路由 endpoint。
- 聚合过重、一次测太多的用例，拆到 `core/brain/training/ui`。
- 只验证工程术语的 UI 文案断言，改成验证用户能理解的中文叙事。

删除：

- 已移除页面、旧审核流、旧训练脚本、旧 main chain 入口的测试。
- 只验证过时实现细节、但不保护主线能力的测试。
- 把只读审计当成训练生效 gate 的测试。

## 主线要求

- `fast` 是默认开发循环，只跑主线哨兵。
- `training` 必须覆盖“训练结果直接生效”的自动调参链路。
- `brain` 必须覆盖中枢大脑对规则、画像、问题、角色上下文的调配。
- `full` 只作为阶段收口，不作为每次小改动的默认入口。
- `services/corpus` 必须显式 opt-in，避免日常测试误跑长任务或依赖服务。

## 当前状态

测试清理与重构主线已完成 100%：

- 分层完成：`fast/core/brain/training/ui/full/services/corpus` 已区分日常、主线、训练、UI、全量和 opt-in 长任务。
- 聚合用例拆分完成：UI、知识、规则 review、corpus artifact、runtime guardrails 已拆出独立主题。
- 慢点治理完成：重复 corpus precompute 已清理；runtime 仅保留不同命盘/不同问题模式的真实慢路径。
- 收口完成：最新本地全量为 `407 passed`，无 diff 空白错误。

## 后续维护

1. 新增主线能力时，先放入对应 tier，不再默认塞进 `fast`。
2. 单个测试文件超过 30 秒时，优先拆主题；只有真实完整链路才允许保留慢路径。
3. 新增训练脚本时，必须同步 `training` tier 和 Admin 训练 UI 的状态文案。
4. `services/corpus` 继续保持显式 opt-in，避免日常开发误跑外部服务或 518K 长任务。

## 2026-05-17 第二轮清理

- 新增 `tests/support_paths.py`，统一测试读取 V20 根目录、仓库根目录和前端目录的方式。
- 清理所有 `server.py` 相对路径读取，测试从仓库根目录、`v20/` 目录或 runner 子进程运行时行为一致。
- 将知识文档契约从 `test_v20_knowledge_ranking.py` 拆到 `test_v20_knowledge_docs.py`。
- `training` tier 已纳入 `test_v20_knowledge_docs.py`，避免拆分后漏跑。
- 已验证：
  - `fast`: 18 passed
  - `brain`: 94 passed
  - `training`: 186 passed
  - `ui`: 1 passed

## 2026-05-17 第三轮清理

- `test_v20_ui.py` 从 1 个巨型测试拆成 6 个主题测试：
  - 入口与路由资源
  - 档案页资源
  - 角色工作台壳层
  - 工作台脚本运行链
  - Admin 训练 UI
  - 样式、页面控制器和二进制资源
- `fast` tier 的 UI sentinel 已更新为新的入口测试名。
- 从 `test_v20_runtime.py` 拆出低风险 runtime guardrails 到 `test_v20_runtime_guardrails.py`：
  - corpus precompute 只读 dry-run
  - V20 包不导入 V19
- 已验证：
  - `test_v20_ui.py`: 6 passed
  - `test_v20_runtime.py + test_v20_runtime_guardrails.py`: 20 passed

## 2026-05-17 第四轮清理

- `test_v20_knowledge_ranking.py` 继续拆分：
  - `test_v20_knowledge_review_and_rules.py` 承载 review queue、review packet、approval preflight、review assist、rule proposal、rule extraction、rule library。
  - 原文件保留 retrieval、catalog、directory、feature graph、source/release 和 runtime endpoint 契约。
- `test_v20_learning_corpus.py` 继续拆分：
  - `test_v20_learning_corpus_artifacts.py` 承载 nightly skeleton、full corpus enumerator、precompute preview/job、artifact build、sqlite-skip artifact。
  - 原文件保留 coverage plan、synthetic/evolution、validation、run plan、endpoint wiring。
- `training` tier 已纳入新增文件，避免拆分后漏跑。
- durations 记录的当前慢点：
  - corpus artifact build and similarity: 40s
  - corpus artifact no-sqlite: 20s
  - runtime LLM fallback guard: 20s
  - dynamic decision training batch/artifact/intent: 19s 左右
- 已验证：
  - `test_v20_knowledge_ranking.py + test_v20_knowledge_review_and_rules.py`: 34 passed
  - `test_v20_learning_corpus.py + test_v20_learning_corpus_artifacts.py`: 14 passed

## 2026-05-17 第五轮清理

- `test_v20_learning_corpus_artifacts.py` 去掉 artifact build 的重复 precompute：
  - module 级 fixture 只生成一次 2 条 corpus snapshot。
  - artifact build 和 no-sqlite 两个用例复制同一份预计算结果，各自验证独立 runtime 输出。
  - 保留最小有效样本数 2，确保 coverage、cluster、similarity 分支仍然真实运行。
- corpus artifact 单文件耗时从约 90 秒下降到 34.86 秒。
- 已验证：
  - `test_v20_learning_corpus_artifacts.py`: 6 passed in 34.86s
  - `test_v20_learning_corpus.py + test_v20_learning_corpus_artifacts.py`: 14 passed in 49.36s
  - `test_v20_runtime.py`: 18 passed in 154.62s
  - `core`: 118 passed in 155.14s
  - `training`: 186 passed in 201.41s
  - `full`: 407 passed in 466.69s
  - `git diff --check`: pass

## 2026-05-17 第六轮清理

- `test_v20_runtime.py` 增加测试内 runtime result cache：
  - cache key 排除 `input_id`，避免同一命盘只因测试输入 ID 不同而重复完整构建。
  - 返回 `deepcopy`，避免测试之间共享可变结果。
  - LLM fallback 环境变量用例只让真实 rewrite/practitioner 路径走 uncached，基准测算结果复用缓存。
- 剩余 runtime 慢路径被明确保留：
  - 多语言渲染需要覆盖中英韩不同输出。
  - 组合链、强弱、用神、LLM fallback 需要各跑两条完整 runtime 分支。
  - 这些用例保护中枢大脑、八字画像、问题链和答案上下文，不再作为“待清理重复”处理。
- 已验证：
  - `test_v20_runtime.py`: 18 passed in 149.49s
  - `core`: 118 passed in 155.14s
  - `training`: 186 passed in 201.41s
  - `full`: 407 passed in 466.69s
  - `git diff --check`: pass
