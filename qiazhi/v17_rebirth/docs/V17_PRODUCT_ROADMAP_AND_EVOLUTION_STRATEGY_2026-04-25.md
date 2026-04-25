# V17 产品路线与进化策略

日期：2026-04-25  
状态：Roadmap Draft  
上位约束：[V17 产品需求宪法](V17_PRODUCT_REQUIREMENTS_CONSTITUTION.md)

## 1. 路线总判断

V17 下一阶段的核心路线不是继续堆更多命理功能，而是建立一个可信闭环：

```text
证据 Evidence
  -> 主张 Claim
  -> 断语 Verdict
  -> 命理师反馈 Practitioner Feedback
  -> 案例验证 Benchmark
  -> 参数/Prompt/规则候选 Learning Candidate
  -> 审计与回归 Governance
  -> 系统进化 Evolution
```

产品优先级应是：

> 先成为命理师可信的 AI 推理工作台，再扩展成普通用户也能顺滑使用的八字产品。

这条路线能同时服务三件事：

- 对普通用户：输出更简洁可信的断语。
- 对命理师：提供可审计、可验证、可反馈的推理工作台。
- 对系统：用高质量反馈、真实案例和合成数据持续优化参数和推理质量。

## 2. 三条主线

### 2.1 证据化主线

系统必须从“会给结论”升级为“能解释结论从哪里来”。

每个关键判断都应尽量包含：

- `evidence_id`
- `evidence_type`
- `source_plugin`
- `source_pillars`
- `source_relations`
- `strength`
- `confidence`
- `candidate_status`
- `claim_id`

典型场景：

- 格局判断：羊刃、杂气、化气、从格、专旺等必须展示证据。
- 用忌判断：必须显示用神、忌神、通关神来源。
- 风险判断：必须说明风险来自冲、刑、刃、枭、伤官见官，还是运流触发。
- LLM 断语：必须能回到 evidence 和 claim，而不是只留自然语言。

### 2.2 命理师共建主线

命理师不是普通用户的一个子集，而是 V17 的共建者和验证者。

系统应为命理师提供：

- 证据审计视图。
- 格局候选确认/否定。
- 用神和风险点修正。
- LLM 断语质量标注。
- 真实案例提交与校盘记录。
- 对系统参数候选的人工复核。

命理师反馈应优先绑定到结构化对象：

- `chart_snapshot`
- `evidence_key`
- `claim_id`
- `plugin_id`
- `verdict`
- `reason`
- `reviewer_role`
- `reviewer_reliability`

### 2.3 自动学习与自我进化主线

V17 已经具备自动学习、自我进化、参数优化、合成数据和治理框架的雏形。后续产品设计必须把它们放在主线，而不是后台实验。

学习系统的职责：

- 收集偏差。
- 映射到参数族。
- 生成 synthetic cases。
- 生成参数候选。
- 比较候选配置。
- 通过真实案例和合成案例回归。
- 交给 admin/命理师审计后再进入系统。

学习系统不应直接做：

- 自动改写核心命理定义。
- 自动覆盖命理师高可信反馈。
- 用普通用户单次反馈直接调参。
- 用 LLM 自己的解释反向证明自己的正确性。

## 3. 反馈可信度分层

不同来源的反馈价值不同，系统应显式建模。

| 来源 | 可信度定位 | 主要用途 |
|---|---|---|
| 职业命理师 | 高可信 | 案例校准、格局/用神/风险审计、参数候选复核 |
| 高质量业余命理师 | 中高可信 | 真实案例补充、推理链验证、术语和解释修正 |
| 普通用户 | 体验可信，命理定义低可信 | 断语体验、结果回访、易读性、产品流程优化 |
| 系统自动回归 | 稳定性可信 | 防退化、参数候选筛选、合成数据覆盖 |
| LLM 自评 | 辅助可信 | 找冲突、生成候选解释、不可作为最终证据 |

设计含义：

- 命理师反馈应拥有更高学习权重。
- 普通用户反馈更适合优化 UI、语言、体验和回访标签。
- 参数候选必须经过 synthetic + practitioner benchmark 双轨验证。
- LLM 可以帮助整理反馈，但不能替代命理师审计。

### 3.1 LLM 协作角色

LLM 后续按四个受治理角色进入系统，详见 [V17 LLM Collaboration Layer](V17_LLM_COLLABORATION_LAYER_2026-04-25.md)：

- `Weaver`：生成短断语。
- `Reviewer`：审阅 evidence / claim 是否足以支撑强断语。
- `Arbiter`：对 `PLAN / CONFLICT` 批次给出结构化仲裁建议。
- `Analyst`：把反馈、错判和回归结果归因为学习候选解释。

其中 `Reviewer / Arbiter / Analyst` 只能产出辅助建议，不得直接改写物理层、参数、authority 或发布状态。

## 4. 阶段路线

### P1：证据工作台

目标：让系统每个关键判断都能被点开看证据。

范围：

- 格局 evidence 展示。
- 用神/忌神 evidence 展示。
- 风险 evidence 展示。
- LLM 断语引用 evidence。
- 手机端默认收起，桌面端可展开。

验收：

- 用户看到“羊刃制杀”时，能看到羊刃在哪里、七杀在哪里、是否只是候选。
- 没有 evidence 的结论不能作为强断语展示。

当前落地：

- `v17.evidence.bundle.v1` 已作为后端快照协议接入，统一汇总 pattern / risk / work / climate / semantic 等插件证据。
- 命盘核心页已接入 `EvidencePanel`，桌面端可展开证据，手机端默认以摘要卡片展示并折叠细节。
- 快照前端读取已切换到 `payload.plugins.claims` 与 `payload.evidence_bundle`，避免 claim/evidence 因位置不一致而丢失。

### P2：命理师反馈闭环

目标：让命理师可以对 evidence 和 claim 做结构化反馈。

范围：

- 确认、否定、待观察。
- 补充理由。
- 绑定 `evidence_key / claim_id / plugin_id`。
- 反馈进入审计日志。
- 管理端可筛选命理师反馈。

验收：

- 一条格局候选可以被命理师确认或否定。
- 反馈可以回放到当时命盘和系统证据。

当前落地：

- `practitioner_feedback` 已进入运行时认证数据库，绑定 `session_id / evidence_id / claim_id / plugin_id`。
- 反馈状态支持 `confirm / reject / watch / review`，并记录理由、置信度、角色与 `reviewer_weight`。
- `/v17/auth/practitioner-feedback` 已提供提交与查询接口；`practitioner / manager / admin` 可提交专业反馈，manager/admin 可用 `scope=all` 查看全量反馈。
- 命盘核心页证据卡片已接入反馈入口；普通用户看到简明断语，`practitioner` 以上账号进入专业证据链工作台。
- 专业工作台新增“命理师账本”，可回看最近反馈、确认/否定/复核状态，以及全量或本人范围的反馈记录。

### P3：真实案例库与基准测试

目标：把命理师案例变成长期回归资产。

范围：

- 案例录入。
- 案例标签。
- 期望判断。
- 边界案例标记。
- 错判案例库。
- 与现有 Practitioner Benchmark 对齐。

重点案例类型：

- 假从。
- 羊刃误判。
- 杂气透藏不足。
- 化气条件不足。
- 调候与格局冲突。
- 运流触发和原局结构混淆。

验收：

- 每次核心插件或参数修改前后，都能看到真实案例是否退化。

当前落地：

- `practitioner_cases` 已进入运行时认证数据库，记录真实样盘、期望判断、边界标签、错判类型、来源反馈和命理师权重。
- `/v17/auth/practitioner-cases` 已提供提交与查询接口；`practitioner / manager / admin` 可提交案例，manager/admin 可用 `scope=all` 查看全量案例。
- API 响应会生成 `benchmark_seed`，把真实案例整理成接近 `PractitionerBenchmarkCase` 的结构，为后续转入长期回归集做准备。
- 命盘核心页的证据卡片已接入案例收录入口：`practitioner` 以上账号可直接沉淀为命理师基准候选，并自动绑定命盘、运流、证据、反馈和 `chart_fingerprint`。
- “命理师账本”同步展示真实案例与基准候选，作为后续参数候选、回归审计和学习治理的入口。
- manager/admin 可将案例状态推进为 `accepted / rejected`，作为转入长期 Practitioner Benchmark 前的运营标记；该动作只更新运行时案例状态，不自动改测试文件。

### P4：Synthetic Lab 与参数候选

目标：把偏差转化为可审计的参数优化候选。

范围：

- 从失败案例映射参数族。
- 自动生成 synthetic cases。
- 自动跑候选参数。
- 比较候选配置。
- 输出 `manual_review_required` 的候选计划。

验收：

- 系统能说清楚“这个失败更像是羊刃门槛问题、从格根气问题，还是 LLM 表达问题”。
- 参数候选不会自动上线，必须经过审计。

当前落地：

- `/v17/auth/practitioner-learning-candidates` 已把 `practitioner_feedback` 与 `practitioner_cases` 聚合为 `v17.practitioner.learning_candidates.v1` 报告。
- 学习候选会按参数族归因，例如 `pattern_specialization.yangren_gate`、`pattern_specialization.follow_gate`、`relation_gate.*`、`authority.leader_axis`、`narrative.prompt_contract`。
- 每个候选输出 `signal_score / priority / recommended_action / safety_gate / review_hints`，并保留来源插件、证据 ID、案例 key 和错判标签。
- 专业工作台“命理师账本”已展示学习候选摘要；候选只进入 `manual_review_required` 队列，不会自动修改运行时参数。
- 学习候选已读取 `practitioner_contribution` 作为 reputation multiplier：贡献等级会影响候选分数、优先级与人工复核排序，并在账本 UI 中展示贡献等级来源。
- `practitioner_learning_reviews` 已记录 manager/admin 对学习候选的审计意见，状态只允许 `watch / approved_for_experiment / rejected`；准入实验只代表可进入 shadow run，不会直接应用参数。

### P5：学习治理与进化发布

目标：建立系统进化的发布流程。

范围：

- 参数候选版本化。
- 回归报告。
- 命理师与管理端审计意见。
- admin 批准。
- 回滚机制。

验收：

- 每次系统进化都有来源、理由、测试、审计和回滚路径。

当前落地：

- 学习候选已有审计留痕接口 `/v17/auth/practitioner-learning-reviews`。
- `approved_for_experiment` 只准入实验队列，仍需 synthetic + practitioner benchmark 与后续发布审批。
- `/v17/auth/practitioner-learning-experiments` 会把已准入候选转换为 dry-run 实验队列，输出候选 patch 范围、必跑命令和安全门。
- `/v17/auth/practitioner-learning-scorecards` 记录 shadow run 的 synthetic / practitioner benchmark 结果、改善/退化数量和 promote/rework/reject 结论。
- `/v17/auth/practitioner-learning-releases` 记录 admin 发布审批、测试报告和回滚方案；批准发布前必须存在无退化的 `promote` scorecard，响应固定 `applied=false`，不自动写配置。
- `/v17/auth/practitioner-learning-governance-export` 可导出候选、审计、实验、scorecard 与发布记录，作为长期归档和版本对照的审计包。

### P6：产品化分层

目标：让同一套核心能力服务不同用户。

普通用户：

- 简洁输入。
- 短断语。
- 少量可展开解释。
- 手机体验优先。

命理师：

- 证据工作台。
- 推理链。
- 反馈和审计。
- 案例库。
- 身份申请通过 manager/admin 审核后才开放专业工作台和高可信反馈权重。
- 贡献画像沉淀 feedback / case / benchmark / score / tier，后续可进入可信权重与共建档案。

管理员/研究者：

- 插件治理。
- 参数候选。
- Prompt 审计。
- 学习记录和发布控制。

当前落地：

- 普通用户与命理师已通过 `user / practitioner / manager / admin` 权限分层进入不同工作台；普通用户保留简明断语，命理师进入专业证据链、反馈、案例与账本。
- 命理师身份通过 `auth_role_requests` 申请与审核，不再由注册入口直接授予。
- 管理员可在 `/v17/admin` 管理成员权限、命理师申请、插件/参数/学习任务，以及学习治理链路。
- Admin 学习治理面板已串起学习候选、审计、dry-run 实验队列、scorecard、发布审批和回滚记录。
- 关键治理动作均保留 `applied=false` 安全边界，不自动写线上配置。

## 5. 与现有系统的对齐

当前已经具备的基础：

- `classical_evidence`：古典证据公共层。
- `V17 Learning Governance Layer`：插件治理、元数据边界、Synthetic Lab 调优桥。
- `Synthetic Lab`：合成案例和参数族映射基础。
- `Practitioner Benchmark`：命理师校盘基准集基础。
- `Decision Inbox`：裁决项和反馈入口基础。
- 多语言、多终端、权限控制主链。
- `auth_role_requests`：命理师身份申请与审核链路，保证 practitioner 权限不是注册时自选标签。
- `practitioner_contribution`：从反馈、真实案例和基准候选聚合出的贡献画像，已随用户权限数据返回。

这些能力已经串成产品闭环：证据、反馈、案例、候选、审计、实验、评分、发布记录和回滚路径都能在运行时系统中留痕。

## 6. 下一步建议

当前主线已完成，后续建议转入运营化打磨：

1. 扩充真实命理师案例库，把更多 `benchmark_candidate` 转成长期 `PractitionerBenchmarkCase`。
2. 对 scorecard 接入真实 shadow run 报告导入，而不是只由管理员手工记录摘要。
3. 继续做移动端验收与普通用户表达减噪，让 P6 的消费侧体验更顺。
4. 持续把审计包与真实版本号、配置 diff 和部署记录对齐，形成长期发布档案。

## 7. 产品判断

V17 的护城河不是“能算八字”，而是：

- 能把判断拆成证据。
- 能让命理师参与验证。
- 能把验证变成可治理的学习。
- 能用 AI 把复杂推理翻译成不同用户能理解的表达。

这会让 V17 从一个测算工具，逐步成长为命理 AI 推理与研究平台。
