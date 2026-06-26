# V20 智能中枢主线完成度对齐

更新时间：2026-05-19

## 对齐目标

早期主线文档把 V20 定义为一条可审查、可训练、可交互的八字测算链：

```text
八字排盘
-> 当前盘结构事实
-> 知识库命理单元
-> 候选规则定义
-> 当前盘规则命中
-> 裁决与命理师校准
-> 动态命理画像
-> 推荐问题
-> LLM 命理师式对话
-> 反馈与训练脚本
-> 晋升后的规则/参数
```

当前中枢主线在这条链中新增了确定性编排层：

```text
ChartFacts
-> CoreInference
-> FeatureLayer
-> RuleDecision / PortraitProjection
-> StructureDynamics
-> OrchestratorEvidence
-> MainlineArbitration
-> QuestionMainlineFocus
-> BrainState
-> BrainMemorySignal
-> AnswerPlan / AnswerText / LLM Context
```

该层不替代规则、知识库、画像或 LLM，而是把它们组织成同一条当前回答主线。

## 当前完成度

| 模块 | 状态 | 完成度 | 说明 |
| --- | --- | ---: | --- |
| 统一证据编译 `orchestrator_evidence` | 已落地并接入当前主线 | 100% | 已把规则、画像、结构动态、问题意图和知识桥证据编译成中枢候选证据；结构动态证据读取 `primary_dynamic_chain`。 |
| 主线仲裁 `mainline_arbitration` | 已落地并接入策略权重 | 100% | 已按证据权重、问题领域、时间层、命理师校准选择第一主线；已能消费 runtime pointer 中的主线权重策略，只重排候选，不改命盘事实。 |
| 问题贴合主线 `question_mainline_focus` | 已落地并接入策略权重 | 100% | 推荐问题围绕第一主线、当前八字上下文和角色视图重排，并保留用户显式问题。 |
| 中枢公开状态 `brain_state.public_summary` | 已落地 | 100% | 已提供主线、选择理由、统筹状态、动态链、证据摘要和下一步提示；已接入 UI、确定性回答和 LLM context。 |
| 结构动态 `structure_dynamics` | 主线完成 | 100% | SDE v2 Weighted Dynamic Graph 已接入 runtime、中枢证据、公开 brain state、UI、合成验证、`structure_dynamics_runtime_policy_pointer`、runtime path scorer 消费、`knowledge.structure_mechanisms` 命名桥接层、完整 KnowledgeUnit 晋升、22 个合成样本、反例候选、岁运阻断、Admin 覆盖展示、结构知识覆盖审计、518K 分片语料回放任务和主链切换报告；`primary_dynamic_chain` 已切到 `dominant_chain_v2` 主读，旧 `dominant_chain` 已从 raw runtime 和角色投影移除，仅保留内部 `legacy_dynamic_chain` 排查字段。 |
| 中枢统筹自检 | 已落地 | 100% | 已判断主线、问题、动态结构、时间层和八字上下文是否对齐；训练结果提供 context quality signal。 |
| 中枢记忆信号 `brain_memory_signal` | 已落地第一版 | 100% | 已编译中枢状态、命理师选择和命主事件校准为训练信号，并进入离线聚合、候选策略和 Admin 可观测链路。 |
| 角色投影 | 已落地 | 100% | 用户只看公开中枢状态；命理师、lab、admin 看校准和观测信息；Admin 独立训练页展示 runtime pointer 和训练直生效状态。 |
| LLM 中枢上下文 | 已落地 | 100% | LLM rewrite 和 practitioner answer 消费 compact brain state、role context、bazi context profile、answer contract 和 context budget。 |
| UI 中枢卡片 | 已落地 | 100% | 用户页显示中枢主线、统筹状态、选择理由和依据；Admin 页面已改为最新主线框架，不再展示旧审核模块。 |
| 中枢训练闭环 | 已完成主链闭环第一版 | 100% | 已有信号入口、显式 ledger、离线聚合、自动策略候选、候选版本包、候选质量排序、版本化质量评分策略、静态回放比较、runtime 策略版本指针、在线观测摘要、策略观测 ledger、策略效果聚合报告、admin 观测面板、lab/observe 只读观测、回滚指针入口、恢复 latest candidate 入口、策略趋势摘要、自动策略建议摘要、版本切换时间线、训练总报告策略学习摘要、策略观测建议回灌候选生成、observe 只读趋势入口和 release smoke；runtime 已能自动读取 active pointer，并让主线仲裁与问题聚焦消费候选权重。 |

### 本轮主线更新（2026-05-12）

- ✅ 结构动态主线重新对焦：确认旧 SDE 偏离 Weighted Dynamic Graph 设计，新增 `docs/V20_STRUCTURE_DYNAMICS_V2_REDESIGN.md`，P4 升级为“结构动态 v2 重构与训练专题”。
- ✅ SDE v2 runtime 主读已落地：`dominant_chain_v2` 从动态图路径生成，`primary_dynamic_chain` 已读取 v2，示例可从 `丁食神 -> 辛七杀 -> 癸偏印 -> 乙日主` 定性为“食神制杀”，不再依赖固定套路。
- ✅ SDE v2 已进入中枢和 UI 主读消费：`orchestrator_evidence`、`mainline_arbitration`、`brain_state.public_summary` 和测算页结构动态面板都优先读取 `primary_dynamic_chain`，旧 `dominant_chain` 已移除，内部 `legacy_dynamic_chain` 只做排查。
- ✅ SDE v2 合成验证第一版已落地：`validation.structure_dynamics_synthetic` 覆盖相邻机制，当前 `dynamic_path_consistency` 和 `semantic_candidate_precision` 均为 1.0。
- ✅ Admin 训练计划已纳入 `structure_dynamics_synthetic`：结构动态专题现在显式训练 `dynamic_path_weight` 和 `semantic_match_weight`，训练任务归入 `synthetic_validation` 中枢节点。
- ✅ 结构动态 runtime pointer 写入器已落地：`build_structure_dynamics_runtime_pointer` 可从合成回放生成候选参数，`write_structure_dynamics_runtime_pointer_activate_candidate` 可在机器通过后直接写 active pointer，不走人工审核。
- ✅ 结构动态 runtime scorer 已消费 active pointer：`dynamics.graph_engine` 读取 `structure_dynamics_policy_versions/active_pointer.json`，把动态路径权重和语义阈值用于 path score / semantic candidate，并在 `sde_v2.runtime_policy` 输出消费状态。
- ✅ 结构动态语义命名桥接知识库：新增 `knowledge.structure_mechanisms`，SDE v2 不再在图算法里硬编码结构命名，改由知识机制单元匹配路径。
- ✅ 结构动态合成样本扩容：`validation.structure_dynamics_synthetic` 从 3 个样本扩到 22 个，覆盖食神制杀、伤官制杀、财生官/财滋杀、食伤生财、泛化输出制官杀、不同日主同构稳定性和岁运冲合阻断。
- ✅ 结构动态反例机制进入 synthetic gate：`财破印`、`比劫夺财`、`印制食伤` 已作为食伤生财样本的语义候选边界被验证。
- ✅ 结构动态分布报告与 Admin 展示已落地：`validation.structure_dynamics_path_distribution` 聚合标签分布、反例覆盖和岁运阻断覆盖，Admin 训练计划显示“结构动态覆盖”卡。
- ✅ 结构动态知识覆盖审计已并入主线：`validation.structure_dynamics_knowledge_coverage` 要求观察到的结构标签回到 `knowledge.structure_mechanisms`、八字知识目录和规则目录，Admin 训练计划显示“结构知识覆盖”卡。
- ✅ 结构动态 518K 分片回放已并入主线：新增 `validation.structure_dynamics_corpus_distribution` 和 `scripts/run_structure_dynamics_corpus_distribution.py`，Admin 训练计划显示“结构语料回放”卡；结构动态 runtime pointer 会消费最新语料分布，发现 unsupported label 时阻断候选策略。
- ✅ 结构动态兼容主链切换报告已完成主读切换：`validation.structure_dynamics_legacy_v2_switch` 对比旧 `dominant_chain` 与新 `dominant_chain_v2`，当前 synthetic gate 无不可解释冲突，状态为 `switch_ready_primary`，runtime 主读为 `primary_dynamic_chain`。
- ✅ 结构动态 1024 分片扩容已完成：`codex_structure_dynamics_1024` 回放 1024 盘，failure 0、unsupported label 0，观察到输出制官杀、食神制杀、伤官制杀、财生官/财滋杀、食伤生财、印星承身、官印/杀印相生等主结构分布；结构动态 pointer 已直接推进到 `candidate_active`，active version 为 `v20.structure_dynamics_policy.candidate.ae30e2a428eb`。
- ✅ 结构动态计划分片任务已进入 Admin：新增 `structure_dynamics_scheduled_shard`，默认从 `start=1024` 跑下一段 `limit=1024`，归属 `corpus_replay_518k`，风险标记为 high，只适合低峰期继续扩容。
- ✅ 结构动态第二个 1024 分片已跑通：`codex_structure_dynamics_2048_window` 从 `start=1024` 回放到 2048 样本，failure 0、unsupported label 0；补入 `比劫承身` 机制覆盖 `self -> day_master` 同气承接路径，避免退回泛化“核心做功链”；结构动态 active pointer 已直接推进到 `v20.structure_dynamics_policy.candidate.7a59d11d275d`，payload 记录分片 `run_id/start/target_count` 方便 Admin/UI 追踪。
- ✅ 结构动态第三个 1024 分片已跑通：`codex_structure_dynamics_3072_window` 从 `start=2048` 回放到 3072 样本，failure 0、unsupported label 0；知识覆盖覆盖输出制官杀、食神制杀、伤官制杀、食伤生财、财生官/财滋杀、财破印等观察标签；结构动态 active pointer 已直接推进到 `v20.structure_dynamics_policy.candidate.4c3aea1d148d`。
- ✅ 结构动态机制已晋升完整知识库单元：`default_knowledge_units()` 现在为每个 `knowledge.structure_mechanisms` 结构机制生成 reviewed KnowledgeUnit，覆盖 evidence_template、boundary、feature_hooks、question_hooks、portrait mapping、answer guidance 和 counterexamples；Admin 结构知识覆盖已显示完整知识单元覆盖。
- ✅ 结构动态第四个 1024 分片已跑通：`codex_structure_dynamics_4096_window` 从 `start=3072` 回放到 4096 样本，failure 0、unsupported label 0，`full_knowledge_unit_supported=true` 覆盖当前观察标签；结构动态 active pointer 已直接推进到 `v20.structure_dynamics_policy.candidate.c5acf8e15805`。
- ✅ 结构动态 synthetic gate 扩到 24 例：新增 `authority_resource_self.jia_day` 和 `authority_resource_self.gui_day`，把“官印/杀印相生”主链和“印星承身”语义候选固化到合成回归。
- ✅ 结构动态第五个 1024 分片已跑通：`codex_structure_dynamics_5120_window` 从 `start=4096` 回放到 5120 样本，failure 0、unsupported label 0；本段观察到“官印/杀印相生”主标签 18 次，完整知识单元覆盖为 true；结构动态 active pointer 已直接推进到 `v20.structure_dynamics_policy.candidate.8091b46fe584`。
- ✅ 结构动态 synthetic gate 扩到 25 例：新增 `output_controls_authority.zhengguan_jia_day`，把“食神见正官”的泛化输出制官杀路径固化，防止误升为食神制杀或食伤生财。
- ✅ 结构动态第六个 1024 分片已跑通：`codex_structure_dynamics_6144_window` 从 `start=5120` 回放到 6144 样本，failure 0、unsupported label 0；本段观察到“印星承身”和“比劫承身”主标签，观察标签扩大到 11 个且完整知识单元覆盖为 true；结构动态 active pointer 已直接推进到 `v20.structure_dynamics_policy.candidate.7c0151f8b726`。
- ✅ 结构动态 synthetic gate 扩到 27 例：新增“印星承身”和“比劫承身”主链样本；图引擎现在会把最终选中的闭合主链同步进入 `semantic_candidates`，避免 UI/知识层看不到中枢已采用的主链。
- ✅ 结构动态第七个 1024 分片已跑通：`codex_structure_dynamics_7168_window` 从 `start=6144` 回放到 7168 样本，failure 0、unsupported label 0；空主链兜底状态已从知识覆盖标签中剥离为 no-path 诊断；结构动态 active pointer 已推进到 `v20.structure_dynamics_policy.candidate.90dddd0fbe77`。
- ✅ 第二阶段质量扩容已启动：新增 `docs/V20_QUALITY_EXPANSION_EXECUTION_PLAN.md`，将知识库覆盖、synthetic 扩容、518K 分片、真实反馈和角色叙事质量收束为阶段二执行计划。
- ✅ 结构动态第八个 1024 分片已跑通：`codex_structure_dynamics_8192_window` 从 `start=7168` 回放到 8192 样本，failure 0、unsupported label 0；观察到输出制官杀、食神制杀、伤官制杀、财生官/财滋杀、食伤生财、比劫承身、印星承身、官印/杀印相生等主标签，知识覆盖仍为 `covered_current_scope`；结构动态 active pointer 已直接推进到 `v20.structure_dynamics_policy.candidate.5f6beabbf3b2`。
- ✅ 结构动态第九个 1024 分片已跑通：`codex_structure_dynamics_9216_window` 从 `start=8192` 回放到 9216 样本，failure 0、unsupported label 0；主标签集中在输出制官杀、食神制杀、伤官制杀、财生官/财滋杀和食伤生财，语义候选覆盖 10 类，知识覆盖仍为 `covered_current_scope`；结构动态 active pointer 已直接推进到 `v20.structure_dynamics_policy.candidate.189b9461a5e6`。
- ✅ 中枢主线合并已对齐结构动态：当闭合结构动态主链与规则候选节点一致时，中枢使用结构动态主链命名，RuleSpec/画像只补证据和分数；`丁巳 乙巳 乙丑 乙酉 / 庚子 / 丙午` 线上复测已显示中枢主线和结构主链均为“食神制杀”。
- ✅ 智能问题新主线已立项：`docs/V20_SMART_QUESTION_RECOMMENDER_PLAN.md` 定义对话式问题推荐系统，把问题库、角色化表达、问题 DAG、下一问策略、已问 suppression、点击训练和 UI 展示统一到中枢大脑框架。
- ✅ 智能问题下一问计划已接入 runtime：新增 `QuestionAtom` 和 `NextQuestionPlan`，运行时输出 `next_question_plan`，UI 智能问题区显示下一问摘要；Admin/命理师可见推荐原因和已隐藏数量。
- ✅ 智能问题下一问计划已参与实际排序：`next_question_plan` 只重排已有 `QuestionCandidate`，命中的问题带上 atom/topic/stage/reasons；Admin/命理师问题卡可看到下一问阶段、专题和推荐理由。
- ✅ 智能问题页面投影已验证：宿主服务重启后，角色视图接口能返回 `next_question_plan` 和每个问题的 atom/stage/topic/reasons，UI 不再只停留在摘要层。
- ✅ 智能问题训练直生效已落地第一版：新增下一问合成验证、训练迭代阶段、question runtime pointer 消费和 active pointer 版本化缓存 key；linux_0_13 已激活 `next_question_plan_policy`。
- ✅ Admin 训练 UI 已对齐：新增“下一问合成验证”后台脚本任务，纳入智能问答训练专题和中枢问题策略图。
- ✅ 智能问题原子库已扩容：补齐健康、关系时机、用神、强弱、地支互动、十神显隐和藏干复核专题；合成验证扩展到 7 个用例，并修正同 question key 多原子合流优先级。
- ✅ 智能问题 DAG 约束已接入：`followup_targets` 会做原子存在性验证，运行时输出 `active_followup_targets` / `followup_edges`，UI 显示“当前问题 -> 下一问”的链路摘要。
- ✅ 智能问题点击反馈已进入训练闭环：UI 点击上报携带 `next_question_atom_id/topic/stage`，`role_question_click_training` 聚合原子奖励，`question_runtime_pointer` 可把 `next_question_feedback_policy` 合入 active `next_question_plan_policy` 并直接生效；样本不足时只保持观测，不改变策略。
- ✅ 智能问题会话记忆已细化：`next_question_plan` 输出 `session_memory` 与 `role_journey`，排序消费 topic depth、上一问阶段和角色 stage order，并把 `domain_reading/time_context/arbitration` 等业务阶段归一到原子问题阶段；前端点击后同时记录 `question_id`/`question_key`，减少同盘重复追问。
- ✅ 智能问题显式反馈已直连 runtime：用户/游客回答反馈写入 `role_question_click_ledger` 的 `answer_helpful/followup/skip` 奖励，Admin/命理师结构化评价写入 `question_review_training`，`question_runtime_pointer` 会把两类反馈都合入 `next_question_plan_policy` 的 atom boost/penalty；linux_0_13 已激活 `v20.question_policy.candidate.f28823dd745f`。
- ✅ 智能问题 UI 已按角色分层：用户/游客只看自然语言下一步建议；Admin/命理师可见 atom、followup edges、session memory、role journey、policy trace 和 active pointer 版本，方便确认训练结果是否在线生效。
- ✅ 智能问题主线已完成 100% 验收：覆盖问题原子、合成验证、runtime pointer、显式反馈、问题评价训练、DAG 回放、ranking、Redis 缓存版本、角色访问权限、UI 接线和 linux_0_13 运行态抽样；后续进入样本和质量扩容阶段。
- ✅ 已把问题来源训练（question source training）接入到 `orchestrator_policy_candidates`，支持 `question_source_graph_quality_policy` 候选；
- ✅ `run_training_iteration` 已修正执行顺序，保证 `orchestrator_policy_candidates` 使用已计算的 `question_source_training`；
- ✅ `orchestrator_policy_replay` 已补齐 `question_source_graph_quality_policy` 的回放比较路径；
- ✅ `orchestrator_policy_versioning` 已保留问题来源候选的 `source_key`、`sample_count`、`average_graph_score`、`average_question_score`；
- ✅ 已补充回归测试覆盖（来源候选是否可进入候选报告）。
- ✅ 角色页导航与角色工作流保持一致，访客页面“nav_profiles”已固定为“入口”跳转；
- ✅ 动态结构显示组件（`dynamic-chain-line` / `dynamic-interpretation` / `dynamic-structure-list`）已补齐自适应换行样式，移动端不再撑开卡片宽度，卡片标题与解释文案支持收敛换行。
- ✅ 工作台全局容器增加统一居中约束（`app-shell`/主台布局宽度封顶），减少不同终端下“动态结构”与面板边界漂移问题。
- ✅ 移动端角色页 UI 继续对齐：工作台模式条支持稳定横向滚动，问题卡片/反馈按钮/问题组标题增加窄屏收敛规则，游客入口表单在手机端切为单列。
- ✅ 角色工作台页默认角色键对齐：`workbench-practitioner.html`、`workbench-observe.html`、`workbench-guest.html` 的 `role_key` 默认值已与页面角色一致，减少匿名态下角色推断抖动。
- ✅ 训练总入口已拆成默认快速链路和显式重型链路：`knowledge_rule_review_overlay`、`rule_subcondition_split`、`decision_registry_iteration` 默认只输出 skipped 状态，需 `--include-knowledge-overlay` / `--include-rule-iteration` 才执行；`rule_synthetic_training` 默认限量，需 `--rule-synthetic-limit 0` 才全量。
- ✅ 晋升门 blocked 不再算总训练失败；它会进入 quality findings，表示样本/回放不足而非脚本错误。
- ✅ Learning Orchestrator V1 计划层已落地：`fast/nightly/weekly/full` 四类学习任务、518K 夜间确定性 replay 计划、分片/checkpoint/resume 策略、bounded LLM sample eval 边界和统一 `/api/v20/learning/orchestrator/run-plan` 入口。

本轮评估完成度：**100% 主链闭环**。后续工作不再算第一阶段缺口，而是第二阶段质量扩容：更大的 518K shard、更多 synthetic topic cases、真实角色/问题反馈样本和更细的上下文偏离诊断。

## 已完成验收点

- `brain_state` 只总结已有 runtime 输出，不创建命盘事实。
- 公开状态不暴露 `source_key`、`evidence_id`、`evidence.*` 等内部标记。
- 第一主线、推荐问题、确定性回答、LLM context 已使用同一份中枢主线。
- 主线选择理由已经用户可读，不再显示内部规则工程语言。
- 中枢自检能输出 `coordination_status` 和 `coordination_note`。
- 命理师结构化选择和命主事件校准已经能进入 `brain_memory_signal`。
- `learning/orchestrator_memory_training.py` 已能聚合中枢记忆信号。
- `interaction/orchestrator_memory_record.py` 已能显式记录中枢记忆信号到 append-only ledger。
- `learning/orchestrator_policy_candidates.py` 已能从训练汇总生成 auto fast-track 策略候选。
- `learning/orchestrator_policy_versioning.py` 已能把策略候选打包为锁定候选版本。
- `learning/orchestrator_policy_replay.py` 已能比较 baseline 与候选版本的只读差异。
- `orchestrator/runtime_policy.py` 已能给每次测算输出中枢策略版本指针，并自动激活 runtime 目录下 latest fast-track 候选版本。
- `orchestrator/mainline.py` 已能消费 `mainline_arbitration_weight_policy`，用 fast-track 候选策略重排主线候选。
- `orchestrator/question_focus.py` 已能消费 `question_focus_policy`，用 fast-track 候选策略调整问题聚焦权重。
- `orchestrator/policy_observability.py` 已能汇总 active policy、consumer 状态、fallback 状态和 rollback 指针。
- `interaction/orchestrator_policy_observability_record.py` 已能显式记录策略观测摘要到 append-only ledger。
- `learning/orchestrator_policy_observability_training.py` 已能聚合策略消费率、fallback 率和模块消费效果。
- `/api/v20/admin/policy-observability` 已能给 admin 页面提供当前策略指针和策略效果聚合报告。
- `frontend/admin.html` / `frontend/admin.js` 已加入只读策略观测面板。
- `/api/v20/admin/policy-observability/rollback` 已能把 active pointer 回滚到 baseline，并写入 append-only audit ledger。
- `orchestrator/runtime_policy.py` 已能优先读取 `active_pointer.json`，回滚后不再自动消费 latest candidate。
- `/api/v20/admin/policy-observability/activate-latest` 已能把 active pointer 恢复到 latest candidate。
- `learning/orchestrator_policy_observability_training.py` 已能按 active policy version 输出 consumed/fallback 分组效果、趋势摘要和自动策略建议。
- `learning/orchestrator_policy_observability_training.py` 已能读取 rollback/activate audit ledger 与 active pointer，生成只读版本切换时间线。
- `learning/training_iteration.py` 已能把策略趋势、建议和版本切换事件汇入总训练迭代报告。
- `learning/orchestrator_policy_candidates.py` 已能把策略观测建议作为下一轮候选生成的输入摘要。
- `/api/v20/policy-observability` 已提供 admin/命理师可读的只读趋势入口，不暴露 rollback/activate 写操作。
- `frontend/admin.html` / `frontend/admin.js` 已能展示策略趋势摘要、只读自动策略建议和版本切换时间线。
- `frontend/workbench-observe.html` / `frontend/app.js` 已能在 observe/lab 页面只读展示策略趋势和版本切换时间线。
- `scripts/release_smoke.py` 已能一键检查 health、admin/observe 静态页、active pointer、policy observability、training iteration summary 和候选来源追溯。
- `learning/orchestrator_policy_candidates.py` 已能输出候选质量评分、质量分层和候选质量摘要。
- `learning/orchestrator_policy_candidates.py` 已能输出版本化 `quality_scoring_policy`，质量评分只用于候选排序。
- `learning/orchestrator_policy_versioning.py` 已能在候选版本包保留策略观测建议来源摘要、候选质量摘要和质量评分策略来源。
- `frontend/workbench-observe.html` 与 `frontend/app.js` 已能在 observe/lab 视图只读展示单次策略观测摘要。
- `frontend/workbench_routes.js` 已把 lab 路由到 observe 页面，并限制为 reading/observe 模式。
- 普通用户不暴露 `brain_memory_signal`。
- 普通用户不暴露 `orchestrator_policy_observability`，命理师、lab、admin 可见策略观测摘要。
- 当前相关回归测试覆盖：
  - `tests/test_v20_orchestrator.py`
  - `tests/test_v20_orchestrator_evidence.py`
  - `tests/test_v20_question_mainline_focus.py`
  - `tests/test_v20_orchestrator_brain_state.py`
  - `tests/test_v20_orchestrator_memory.py`
  - `tests/test_v20_orchestrator_memory_record.py`
  - `tests/test_v20_orchestrator_memory_training.py`
  - `tests/test_v20_orchestrator_policy_candidates.py`
  - `tests/test_v20_orchestrator_policy_versioning.py`
  - `tests/test_v20_orchestrator_policy_observability.py`
  - `tests/test_v20_orchestrator_policy_observability_record.py`

## 原计划差距对齐

2026-05-18 口径：原先列出的知识、规则、画像/问题、裁决、LLM 和反馈训练差距已经进入同一条 runtime pointer 闭环。它们不再作为第一阶段 blocker，而是第二阶段质量扩容对象。

| 领域 | 当前状态 | 下一阶段质量目标 |
|---|---|---|
| 知识库系统 | 知识桥、知识映射 pointer 和知识覆盖审计已接入中枢 | 把 `knowledge.structure_mechanisms` 从桥接层扩成完整机制知识单元 |
| 规则系统 | 规则 runtime pointer 已被 `rules.engine` 消费，反例作为继续训练信号 | 扩大 rule replay 和反例分布 |
| 动态画像和推荐问题 | 画像、问题意图、角色问题和 DAG 已对齐当前八字上下文 | 增加真实交互 reward，稳定 role/question candidate |
| 裁决系统 | 主线仲裁、反证模型、结构动态和时间层已统一进入 brain state | 扩大用神、岁运、关系、健康边界 synthetic cases |
| LLM 命理师回答 | LLM 消费 compact brain state、角色上下文和八字上下文包 | 用 answer safety / stream quality 扩容训练 |
| 反馈与训练 | 反馈进入训练脚本，并通过机器 gate 和 runtime pointer 直接生效 | 增加样本量和回放规模，不恢复人工审核 |

### 反馈与训练

当前已有 practitioner calibration、latent event calibration、brain memory signal、orchestrator memory ledger、orchestrator memory training report、orchestrator policy candidate report、candidate policy quality ranking、candidate policy version、static replay report、runtime policy pointer、在线观测摘要、策略观测 ledger、策略效果聚合报告、admin 观测面板、lab/observe 只读观测、回滚操作入口、恢复 latest candidate 入口、策略趋势摘要、自动策略建议摘要、版本切换时间线、训练总报告策略学习摘要、策略观测建议回灌候选生成、observe 只读趋势入口和 release smoke。主线策略已从人工审核门改为自动快速迭代链；runtime 指针已能自动激活 latest 候选版本、回滚 baseline、再恢复候选版本，候选权重已开始接入主线仲裁和问题聚焦。后续主要是更多真实样本、阈值校准和候选质量评估细化。

完成度：主链第一版 100%。

## 总体判断

当前智能中枢主线已经完成第一阶段闭环：

```text
证据编译
-> 主线仲裁
-> 问题聚焦
-> 公开状态
-> 统筹自检
-> 回答/LLM 共用
-> 记忆信号
```

这说明“中枢大脑”已经不是概念，已经进入 runtime 并可被 UI、回答和 LLM 消费。

中枢第一阶段已经完成策略闭环。下一阶段主线不再继续扩 UI 分支，而是进入“合成训练 + 问题链 DAG + 角色互动学习”阶段：

```text
SyntheticBaziCase DSL
-> Runtime Replay
-> Evaluator Suite
-> Question DAG
-> Role Interaction Training
-> Candidate Policy
-> Synthetic Validation / Historical Replay
-> Runtime Pointer
```

新阶段的核心目标是：让规则、画像、问题、问题链和角色互动都能被合成数据和回放验证；用户交互只进入经验层和候选策略，不直接修改核心模型。

## 新主线完成度

| 模块 | 状态 | 完成度 | 下一步 |
| --- | --- | ---: | --- |
| 角色视图与角色问题 | 已落地第一版 | 100% | 进入 DAG 化和训练化，不再扩散 UI 分支。 |
| 角色点击学习 | 已落地结构化 reward 汇总 | 100% | 已支持 select/followup/skip/helpful/unhelpful/downrank，只生成候选建议。 |
| 问题链 DAG | 已接入 replay 和 promotion gate | 100% | 已验证合法转移、角色路径边界、训练候选、离线 replay 和上线 gate；后续若上线需显式 pointer。 |
| 问题反馈互动 | 已接入 DAG 候选策略、admin 观测和前台快捷反馈 | 100% | 已完成结构化审核 ledger、训练聚合、候选建议、DAG policy 接入、admin 可见性和命理师/admin 快捷反馈按钮。 |
| 合成训练 DSL | 已扩充到 14 个最小 case | 100% | 已覆盖极端同气、全冲边界、多时间层、角色泄露。 |
| Runtime Replay Harness | 已落地第一版 | 100% | 14 个 synthetic case 已能全量回放通过。 |
| Evaluator Suite | 已落地第一版 | 100% | 已完成 expected/actual、coverage gate、DAG coherence gate、answer safety gate。 |
| 角色互动训练 | 已落地候选策略和脚本第一版 | 100% | 后续接真实用户 interaction reward。 |
| Contextual Bandit 问题策略 | 第一版闭环完成 | 100% | 已完成点击 reward、候选策略、A/B replay、阈值校准、promotion gate、显式 pointer、admin 面板；后续属于真实样本积累和阈值持续调参。 |
| 训练总入口 | 已接入 synthetic/DAG/role/coverage 四类报告 | 100% | 14 case synthetic suite 已 pass，后续接入更多反例簇。 |

## 新主线任务计划

### N1：合成训练 Schema

目标：建立 `SyntheticBaziCase` 作为规则、画像、问题、DAG、角色视图的统一训练样本。

交付：

- `case_id`
- `case_type`
- `chart_constraints`
- `chart_input`
- `expected_features`
- `expected_rules`
- `expected_portraits`
- `expected_questions`
- `expected_dag_path`
- `expected_role_views`
- `negative_expectations`

验收：

- 已完成：10 个最小案例可被 loader 读取。
- 已完成：支持 dry-run manifest。
- 已完成：不包含用户隐私和自由文本训练字段。

### N2：Runtime Replay Harness

目标：把合成案例跑过现有 runtime，得到可评估的 actual result。

交付：

- synthetic case loader。
- runtime replay runner。
- actual output normalizer。
- replay artifact。

验收：

- 已完成：不写 runtime pointer。
- 已完成：不改规则。
- 已完成：输出 normalized actual，可被 evaluator 消费。

### N3：Evaluator Suite 第一版

目标：把“画像准不准、问题聚不聚焦、角色有没有泄露”变成机器可测。

交付：

- `RuleEvaluator`
- `PortraitEvaluator`
- `QuestionEvaluator`
- `RoleViewEvaluator`

验收：

- 已完成：每个 evaluator 输出 pass/fail。
- 已完成：每个失败有 case id、expected/actual、failure reason。
- 已完成第一版：rule、portrait、question、role view evaluator 已可汇总 failure report。

### N4：Question DAG Model

目标：把推荐问题从列表升级为问题节点图。

交付：

- `QuestionNode`
- `ChoiceOption`
- `NextQuestionRule`
- stage：entry/focus/structure/timing/review/observe/advice/closure

验收：

- 已完成：guest/user 默认走短链。
- 已完成：analyst 能走复核链。
- 已完成：admin/lab 能走观测链。
- 已完成模型层：普通用户路径不包含 observe，guest 路径不包含 review。

### N4.5：Question Feedback Interaction

目标：把命理师/admin 对推荐问题质量的审核变成结构化互动信号。

交付：

- `QuestionReviewAction`
- `QuestionReviewReason`
- `QuestionReviewSignal`
- `question_review_ledger`
- 问题反馈训练报告

反馈动作：

```text
[通过]
[改写]
[降权]
[合并]
[删除]
[角色不匹配]
[主线不匹配]
[术语过重]
[重复]
[发散]
```

验收：

- 已完成模型层：反馈只影响问题排序、问题模板、DAG 路径和角色展示。
- 已完成：反馈不改命盘事实、规则真值、用神判断。
- 已完成 ledger 第一版：反馈信号进入 append-only ledger，后续由 training 转 candidate policy。
- 已完成训练报告：`question_review_training` 聚合 action/reason/question/role-stage，并输出 approve/rewrite/suppress 类候选建议。
- 已完成训练总入口接入：`run_training_iteration.py` 已包含 `question_review_training`。
- 已完成 DAG 接入：`question_dag_training` 已消费 `question_review_training`，在 `question_review_policy.training_recommendations` 中输出反馈候选建议。
- 已完成只读 API：`/api/v20/learning/question-dag` 输出包含反馈建议的 next-question candidate policy。
- 已完成 admin 观测：admin 页面展示 review count、actions、reasons、recommendations、DAG policy 接入状态和 replay blocking gate。
- 已完成前台快捷反馈：analyst/admin/lab/practitioner 角色在回答区显示通过、降权、改写、删除按钮；反馈绑定“已生成回答的当前问题”，避免用户未读答案就反馈，并写入 `/api/v20/question-review/record`。
- 当前边界：问题反馈建议已进入 DAG replay，但仍不写 runtime pointer；后续必须进入显式 promotion/pointer 链路后才能影响线上排序。

### N5：Question DAG Training

目标：用合成 interaction case 和用户结构化选择训练下一步问题策略。

交付：

- `next_question_policy` candidate。
- baseline/candidate DAG replay。
- 发散、重复、跨角色泄露检测。

验收：

- 已完成第一版：从 SyntheticBaziCase expected DAG path 生成 `next_question_policy` candidate。
- 已完成第一版：候选包含 role default path、stage transition policy、question review policy。
- 已完成 `question_dag_coherence_report`：验证 synthetic path 合法转移、角色默认路径和禁止串线边界。
- 已完成 `question_dag_policy_replay`：比较 baseline/candidate，输出 coherence gate、stage coverage、transition support、review recommendation 接入影响。
- 已完成只读 API：`/api/v20/learning/question-dag-replay` 输出 DAG policy replay。
- 已完成 `question_dag_policy_promotion_gate`：检查 replay ready、comparison count、score average、risk、candidate win 和显式 rollout switch。
- 已完成只读 API：`/api/v20/learning/question-dag-promotion` 输出 DAG promotion gate。
- 已保持边界：候选、replay 和 gate 不写 runtime pointer，后续必须接显式 pointer 后才能影响线上问题链。

### N6：Role Interaction Training

目标：把 guest/user/analyst/admin 的互动差异训练成可回放策略。

交付：

- guest entry policy。
- user guided policy。
- analyst review policy。
- admin observe policy。

验收：

- guest 问题更少更入口化。
- user 问题更像咨询。
- analyst 校准项结构化。
- admin 观测项可追溯来源。

进度：

- 已落地 `learning/role_interaction_training.py`。
- 已落地 `scripts/run_role_interaction_training.py`。
- 已覆盖 `tests/test_v20_role_interaction_training.py`。

### N7：Training Iteration Integration

目标：把合成训练、DAG 训练、角色互动训练接入现有训练总入口。

交付：

- `run_synthetic_case_suite.py --summary`
- `run_question_dag_training.py --write --progress`
- `run_role_interaction_training.py --write --progress`
- `run_training_iteration.py` 汇总新报告。

验收：

- release smoke 可检查训练报告。
- runtime pointer 不直接消费原始训练数据。
- 候选来源和验证结果可追溯。

进度：

- 已接入 `learning/training_iteration.py`。
- 已新增 `--synthetic-replay-limit`，默认轻量 replay，避免日常迭代拖慢。
- 已落地 `scripts/run_synthetic_case_suite.py`、`scripts/run_question_dag_training.py`、`scripts/run_role_interaction_training.py`。
- 当前 synthetic suite 默认 smoke 和 14 个最小 case 全量均可 `pass`；不会直接修改 runtime pointer。
- 已新增极端同气、全冲边界、多时间层、角色泄露防护 case。
- 已新增 `synthetic_bazi_coverage_report()`，并接入 synthetic suite 与 `run_training_iteration.py`，机器可读地输出 domain/stage/role/capability 覆盖状态。
- 已新增 `answer_safety_evaluator`，校验回答边界、禁断言、内部标记泄露；全量 14 case 通过。

### N8：Role Interaction Reward Training

目标：把真实交互中的选择、跳过、追问、答案有用/无用、降权信号转成候选策略经验。

交付：

- `role_question_click` ledger 支持 `action_type` 和 `reward_value`。
- `role_question_click_training` 输出 action/reward summaries。
- reward 只生成 boost/suppress/keep_collecting candidate recommendation。
- `run_training_iteration.py` 汇总 role question click training。
- `role_view_policy_candidates` 消费 reward recommendation，生成 reward candidate policy。
- `role_view_policy_replay` 输出 offline score、positive/negative count 和候选版本比较。
- `role_view_policy_replay` 已输出 A/B offline summary，包括 candidate win、net lift、average lift、risk count、by-role 和 by-policy-key 分布。
- `role_view_policy_calibration` 已输出 reward/A-B 观察和建议阈值，包括 min comparisons、min score average、min A/B lift、max risk。
- `role_view_policy_promotion_gate` 输出候选是否满足 replay、样本数、reward margin、score average 和 rollout switch。
- `role_view_policy_promotion_gate` 已纳入 A/B gate：候选必须有正向净提升且无负向风险。
- `role_view_policy_promotion_gate` 已消费 calibration suggested thresholds，不再只依赖固定常量。
- `role_view_runtime_pointer` 支持显式 active pointer，只有 promotion gate 通过且 active pointer 指向候选版本时才应用候选策略。
- admin API 支持 `/api/v20/admin/role-view/runtime-pointer/activate-candidate` 和 `/api/v20/admin/role-view/runtime-pointer/rollback`。
- admin 页面已显示 role-view policy pointer、promotion gate、A/B replay、calibration、payload counts、guardrails，并提供激活候选/回滚按钮。

验收：

- 原始用户文本、问题标题和隐私字段不进入 ledger。
- reward 不直接改 runtime pointer、规则真值或画像结论。
- 正负反馈只进入候选策略和后续 replay。
- runtime pointer 已改为必须通过 promotion gate 才能应用候选；默认 baseline 生效，不自动写入候选。
- 已完成：显式激活会写入 role-view active pointer 和 append-only audit；回滚会恢复 baseline，runtime 下次读取立即生效。
- 已完成：admin 面板可以观测和操作 role-view pointer，测试覆盖静态 UI 契约、A/B replay、calibration 字段和 API 路径。
- 当前实现闭环：用户结构化互动 -> click/reward ledger -> training report -> candidate policy -> A/B replay -> calibration -> promotion gate -> explicit pointer -> role-view runtime ordering。

## 下一阶段建议

### P1：中枢记忆训练汇总

状态：已落地自动快速迭代第一版。

已建立 `learning/orchestrator_memory_training.py`：

- 读取 runtime 产生的 `brain_memory_signal` 或本地 ledger。
- 按 `primary_mainline_key`、问题领域、校准方向聚合。
- 输出主线接受率、切换率、证据不足率、问题重排倾向。
- 只生成报告，不改 runtime。

验收标准：

- 已有测试覆盖聚合结果。
- 已有 dry-run 报告。
- 报告包含 guardrails：不自动改规则、不自动改主线。
- 已接入 `run_training_iteration(...)`。

### P2：中枢记忆 ledger

状态：已落地第一版。

已把 `brain_memory_signal` 作为 append-only 训练材料写入本地 ledger，并加入 Postgres import dry-run 白名单。

验收标准：

- 普通测算不默认写入，必须由 admin/训练脚本或显式 record 入口触发。
- 已可 dry-run 导入 Postgres。
- 已拒绝 `user_text`、`feedback_text`、`raw_feedback` 等自由文本标记。

### P3：中枢权重候选

状态：已落地第一版。

已基于训练汇总生成候选权重建议：

- 哪类问题更容易提升某条主线。
- 哪类命理师选择会切换主线。
- 哪类时间层缺失应保留复核而不是强行结论。

验收标准：

- 候选已进入自动记录 artifact。
- 候选默认进入 fast-track 策略版本链。
- 已接入 `run_training_iteration(...)`。
- 后续不再卡人工审核，改为回放观测与可回滚版本指针。

### P4：版本锁定、回放与 runtime 指针

状态：已落地自动候选版本、静态回放与 runtime fast-track 指针第一版。

已建立中枢策略候选版本：

- `mainline_arbitration_weight_policy`
- `question_focus_policy`
- `brain_memory_policy`

验收标准：

- 已能把策略候选自动打包为 `candidate_policy_version`。
- 已能输出 baseline 与候选版本的静态 replay diff。
- 已接入 `run_training_iteration(...)`。
- runtime 已输出策略版本指针和 fast-track 状态。
- runtime 已能自动读取 `training/orchestrator_policy_versions/latest.json` 并把允许运行的候选版本设为 `active_policy_version`。
- runtime 指针保留 `rollback_policy_version=v20.orchestrator_policy.baseline.v1`。
- 每次回答已可追踪当前策略版本。
- 候选权重已开始影响 `mainline_arbitration` 和 `question_mainline_focus`，且只做排序/权重调整，不改核心命盘事实。

### P5：在线观测与权重消费

状态：已落地第一版。

目标：

- 已增加中枢策略在线观测摘要：当前 active 版本、consumer 状态、fallback 状态、回滚目标。
- 已把候选版本中的 `mainline_arbitration_weight_policy` 接入主线仲裁权重。
- 已把候选版本中的 `question_focus_policy` 接入推荐问题重排。
- 保持核心命盘事实确定性不变，只允许中枢排序、权重和推荐策略快速迭代。

验收标准：

- 策略权重接入后，runtime 输出 active policy version 和实际消费模块。当前 `mainline_arbitration.runtime_policy_effect` 与 `question_mainline_focus.runtime_policy_effect` 已输出消费状态。
- `orchestrator_policy_observability` 已输出 active policy、consumer 状态、fallback 状态和 rollback policy。
- 候选版本异常时自动回到 baseline pointer。
- 测试覆盖 baseline、candidate active、candidate ignored/fallback 三种路径。

### P6：策略效果统计与回滚面板

状态：已落地后台统计第一版。

目标：

- 已能把 `orchestrator_policy_observability` 写入 append-only 策略观测 ledger。
- 已能聚合测算里的 candidate consumed、no consumer match、baseline fallback 比例。
- 在 admin/lab 页面展示 active version、rollback target、模块消费状态和最近策略效果。
- 保持自动快速迭代：不增加人工审核门，只保留可回滚、可观测、可追踪。

验收标准：

- 已有只读聚合报告，不泄露用户自由文本。
- 策略观测 ledger 已加入 Postgres import dry-run 白名单。
- admin/lab 能看到策略版本与消费效果。
- 出现异常候选版本时能明确显示 fallback 到 baseline。

### P7：admin/lab 策略观测面板

状态：admin 页面第一版已落地。

目标：

- 已在 admin 页面展示当前策略指针和策略效果聚合结果。
- 已展示 active version、candidate version、rollback target、consumer status、fallback ratio、candidate consumed ratio。
- lab 专用视图待补。
- 保持自动快速迭代，不增加人工审核门。

验收标准：

- 页面只展示观测和回滚目标，不允许页面直接写策略。
- 普通用户页面不出现策略观测面板。
- 后台聚合为空时显示 baseline/fallback 空状态。

### P8：跨版本效果对比与回滚入口

状态：admin 回滚入口第一版已落地。

目标：

- 已对比 baseline、candidate 和最近 active version 的观察次数。
- 已增加只写版本指针的回滚入口，回滚到 `rollback_policy_version`。
- 已把回滚写入单独 audit ledger。
- 回滚仍只切换策略版本指针，不改命盘事实、不改用户历史数据。

验收标准：

- admin 能看见当前版本与回滚目标的差异。
- 回滚操作写入单独 audit ledger。
- runtime 下次测算读取回滚后的 active pointer。

### P9：候选恢复与跨版本效果细化

状态：已落地第一版。

目标：

- 已增加从 baseline rollback 恢复到 latest candidate 的版本指针入口。
- 已按 active policy version 分组展示 consumed ratio 和 fallback ratio。
- lab 视图复用同一套观测数据。

验收标准：

- admin 可在 rollback 和 latest candidate 之间切换 active pointer。
- 所有切换都写 audit ledger。
- runtime 不改核心命盘事实，只读取 active pointer 影响中枢排序策略。

### P10：lab 视图与趋势面板

状态：lab/observe 只读视图已落地。

目标：

- 已给 lab/observe 页面复用策略观测摘要。
- 增加最近版本切换时间线和策略效果趋势。
- 已把 rollback/activate 操作入口限定在 admin，lab/observe 只读。

验收标准：

- lab/observe 可见单次 active version、rollback target、consumer status。
- admin 仍可切换 active pointer。
- 普通用户不可见策略观测。

### P11：趋势摘要与自动策略建议

状态：已落地第一版。

目标：

- 已把 version_summaries 聚合为策略趋势摘要。
- 已根据 fallback/consumed 比例和 consumer 应用率生成自动策略建议摘要。
- 已在 admin 页面展示趋势和建议。
- 最近版本切换时间线留到下一步细化。

验收标准：

- admin 可见趋势摘要和建议摘要；lab/observe 已能看单次策略观测，跨版本趋势待补只读入口。
- 建议摘要只读，不阻塞 fast-track。
- runtime 仍只读取 active pointer，不改核心命盘事实。

### P12：跨版本时间线与训练总报告融合

状态：已落地第一版。

目标：

- 已增加最近版本切换时间线，把 rollback、activate latest candidate 和 runtime active pointer 串成可读历史。
- 已把策略趋势摘要和自动建议接入 `run_training_iteration(...)` 总报告。
- 已在 admin 策略观测面板展示版本切换时间线。
- lab/observe 目前仍展示单次策略观测，跨版本趋势入口留作 release hardening 的只读增强。

验收标准：

- admin 可见版本切换时间线，lab/observe 保持单次只读策略观测。
- 训练总报告包含趋势摘要、建议摘要和版本切换事件摘要。
- 自动建议继续走 fast-track，可观测、可回滚，不增加人工审核门。

### P13：Release hardening 与样本质量提升

状态：已落地第一版。

目标：

- 已给 lab/observe 增加只读跨版本趋势入口，不提供 rollback/activate 写操作。
- 已把策略建议进一步映射到下一轮 candidate 生成的输入摘要，形成更强自学习闭环。
- 增加 release smoke 对策略观测、训练总报告和 admin 面板的联测。
- 累积更多真实测算样本，提升趋势判断稳定性。

验收标准：

- 普通用户仍不可见策略观测。
- admin 可写 rollback/activate，lab/observe 只读。
- 策略观测建议可进入下一轮候选生成，但仍通过版本包、回放和 active pointer 生效。
- release smoke 覆盖 active pointer、policy observability、training iteration summary。

### P14：Release smoke 与候选质量评估

状态：已落地第一版。

目标：

- 已增加 release smoke 对 active pointer、policy observability、training iteration summary、admin/observe 静态页的联测。
- 已在候选版本包里补充策略观测建议来源摘要，便于对比候选质量。
- 累积更多真实测算样本，校准 fallback/consumed 阈值。

验收标准：

- 一条命令可验证中枢策略闭环的关键端点和页面。
- 候选版本包能追溯来自记忆信号还是策略观测建议。
- 不新增人工审核门，继续 fast-track + rollback。

### P15：样本规模与阈值校准

状态：已落地候选质量排序第一版。

目标：

- 累积真实测算样本和命理师校准样本。
- 已增加 fallback/consumed、样本量、support ratio、策略观测建议类型参与的候选质量评分。
- 已把候选质量评估从“可追溯”推进到“可排序”。
- 后续继续用真实样本校准 fallback/consumed 阈值、模块覆盖率阈值和质量评分权重。

验收标准：

- 训练报告能输出候选质量排序。
- 策略观测建议能按质量分进入下一轮候选。
- 主链仍保持 fast-track、可观测、可回滚。

### P16：真实样本阈值校准

状态：已落地版本化质量评分策略第一版。

目标：

- 累积真实测算样本和命理师校准样本。
- 对 fallback/consumed、模块覆盖率、候选质量分段进行离线校准。
- 已把固定阈值推进为可版本化的质量评分策略。
- 后续用真实样本继续校准质量评分策略权重。

验收标准：

- 质量评分策略可版本化、可回放、可回滚。
- 候选质量排序能解释主要得分来源。
- runtime 仍只读取 active pointer，不直接读取训练报告。

### P17：质量评分策略校准报告

状态：下一步。

目标：

- 从真实测算、命理师校准和策略观测样本中统计质量评分策略的命中效果。
- 输出下一版 `quality_scoring_policy` 候选权重。
- 比较当前策略和候选策略的候选排序差异。

验收标准：

- 策略校准报告只读，不直接改 runtime。
- 候选策略可进入版本包、回放和 active pointer 链路。
- 保持 fast-track、自学习、自纠错和可回滚。

### P18：问题生成模块边界清理

状态：已完成；候选来源拆分与 manifest 边界已落地。

目标：

- 对齐当前“角色画像 + 推荐问题 + 问题链 DAG + 中枢策略”的主线，把 `decision/questions.py` 从巨型混合文件逐步拆成配置、标题表达、生成策略、链路仲裁几个边界。
- 已新增 `decision/question_config.py`，承接问题域映射、策略 key、规则前缀、技术词过滤、命理师控制域和潜在事件域。
- 已新增 `decision/question_titles.py`，承接 runtime fusion 标题、画像轴标题和运行时文案清洗。
- 已新增 `decision/question_builders.py`，承接 runtime fusion question builder 和 portrait tag question builder。
- 已新增 `decision/question_feature_hooks.py`，承接 feature hook question builder 和特征语义材料映射。
- 已新增 `decision/question_decision_hits.py`，承接 decision hit question builder 和规则命中问题标题。
- 已新增 `decision/question_mainline_time.py`，承接 mainline question builder 和 time context question builder。
- 已新增 `decision/question_interaction_refresh.py`，承接命理师结构化选择刷新问题和命主潜在事件刷新问题。
- 已新增 `decision/question_sources.py`，显式登记 runtime、主线、画像、规则命中、feature hook、seed、交互刷新和 fallback 的候选来源顺序。
- 已删除重复 `_question_signature` 和未使用 fusion title 映射；当前不改变推荐算法，只做行为保持式拆分。

验收标准：

- 游客、普通用户、命理师、admin 的问题推荐行为不退化。
- 组合链主问题、命理师刷新问题、潜在事件刷新问题继续通过测试。
- 已整理统一候选来源 manifest，为 graph 仲裁升级做准备。

完成度：100%。下一步主线进入 `Graph 仲裁升级`，把当前显式候选来源接入路径权重、冲突检测和可学习排序。

### P19：Graph 仲裁升级

状态：已完成；问题候选来源图、路径级评分、候选质量信号、只读观测和 release smoke 已落地。

目标：

- 对齐当前“中枢大脑智能化 + 高迭代 + 自我学习”的主线，把 graph 从简单列表排序升级为可解释、可学习、可检测冲突的路径仲裁层。
- 已新增 `graph/question_source_graph.py`，消费 `decision/question_sources.py` 的候选来源 manifest，生成 `QuestionSourcePath`。
- 已在 `graph/schema.py` 新增 `QuestionSourcePath`，为问题来源提供 `phase`、`order`、`base_weight`、`score`、`conflict_tags` 和 `learning_tags`。
- 已把 `runtime_fusion`、`mainline`、`portrait_axis`、`decision_hit`、`feature_hook`、`seed_registry`、`practitioner_refresh`、`latent_event`、`fallback` 纳入来源图。
- 已加入路径级评分：`propagated_weight` 表示相邻阶段传播，`conflict_penalty` 表示来源冲突惩罚，`learning_boost` 表示交互经验和策略信号加成。
- 已接入候选质量信号：`quality_boost` 可消费 `source_quality_scores` 或策略候选报告里的 `quality_score`，只做来源重排，不生成新问题。
- 已输出 `conflict_summary` 和 `learning_summary`，让后续训练和 admin 观测能看到来源为什么被压低或抬高。
- 已输出 `quality_summary`，让候选质量如何影响来源路径变成可观测字段。
- 已接入 `/api/v20/admin/policy-observability` 和 `/api/v20/policy-observability` 的 `question_source_graph` 字段，admin 与命理师观测入口可只读查看来源路径。
- 已接入 admin 与 observe/lab 前端，只读展示来源图状态、路径数量、质量 artifact 状态和高分来源路径。
- 已把来源图检查纳入 `scripts/release_smoke.py`，确认来源路径、质量重排 guardrail 和静态页面标记都存在。
- 已明确 guardrails：来源图只重排和解释候选来源，不生成新问题，不修改命盘事实；fallback 不允许覆盖证据候选；学习标签只进入策略输入。

验收标准：

- `question_source_graph` 能消费 manifest，不新增问题 key。
- `seed_registry` 带冲突标签，避免种子问题压过当前盘特异候选。
- `practitioner_refresh` 和 `latent_event` 带学习标签，只进入经验层和候选策略。
- 来源路径已经能应用传播权重、冲突惩罚和学习加成。
- 来源路径已经能消费候选质量信号，且 guardrail 明确为 `QUALITY_SIGNALS_RERANK_ONLY`。
- 来源图报告已经进入 admin/observe policy observability，且 guardrail 明确为 `QUESTION_SOURCE_GRAPH_OBSERVABILITY_READ_ONLY`。
- admin/lab 前端已展示来源图，release smoke 已覆盖 `question_source_graph_observability`。
- 保持现有问题推荐、runtime、结构动态行为不退化。

完成度：100%。下一步主线转入 `P20：Graph 与 Runtime 推荐链闭环`，把来源图评分用于真实推荐候选的可解释排序报告，并继续保持只重排、不生成事实。

### P20：Graph 与 Runtime 推荐链闭环

状态：已完成；来源图评分已经进入真实 runtime 推荐链的只读解释报告。

目标：

- 对齐“中枢大脑智能化 + 高迭代 + 自我学习”的主线，把 P19 的来源图评分用于解释真实推荐问题，但不直接生成问题、不修改命盘事实、不改变推荐顺序。
- 已新增 `decision/question_source_runtime.py`，把最终推荐问题映射到 `QuestionSourceGraph` 路径，输出 `question_source_ranking_report`。
- 已在 runtime 结果中新增 `question_source_ranking_report`，逐条记录推荐问题的 `source_key`、来源图分数、问题原始分数和仲裁说明。
- 已把该报告开放给 analyst/lab/admin 观测角色，普通用户和游客不暴露内部来源图报告。
- 已在 observe/lab 页面展示 runtime 问题来源报告，admin/lab 可看到当前问题列表对应的来源路径和图分数。
- 已把 `runtime_question_source_ranking_report` 纳入 `scripts/release_smoke.py`，确保 release smoke 覆盖 runtime 真实推荐链。

验收标准：

- `question_source_ranking_report` 只解释已有问题，不新增问题 key。
- 报告行顺序与最终 `questions` 顺序一致，guardrail 明确为 `NO_QUESTION_ORDER_MUTATION`。
- 来源图评分只作为解释和训练信号，不改变本轮问题排序。
- admin/lab 前端可只读查看 runtime 问题来源路径。
- release smoke 本地检查覆盖 `runtime_question_source_ranking_report`。

完成度：100%。下一步主线转入 `P21：Learning Orchestrator V1`，把零散训练脚本收拢为可调度、可分片、可夜间全量回放的学习中枢。

### P21：Learning Orchestrator V1

状态：已完成 V1 计划层；夜间 518K 全量学习任务已可建模、可读取、可分片、可纳入主学习计划。

目标：

- 对齐“高迭代、自我学习、中枢大脑智能化”的主线，把 fast、nightly、weekly、full 训练模式统一成一个学习任务模型。
- 支持晚上低流量窗口跑 518,400 全量确定性 replay，用于规则、特征、画像、问题和角色视图的分布评估。
- 明确 LLM 只做抽样 eval，不参与 518K 全量调用，不训练 LLM 本体。
- 输出候选策略目标：规则权重、特征阈值、画像轴权重、问题排序、问题 DAG、角色视图策略。
- 保持 runtime 指针边界：run plan 不写 pointer，只产出 replay/promotion 前置计划。

已落地：

- 新增 `learning_orchestrator/job_schema.py`：定义 `fast`、`nightly`、`weekly`、`full` 四类任务。
- 新增 `learning_orchestrator/dataset_plan.py`：统一 synthetic、interaction ledger、full corpus 和 LLM sample 边界。
- 新增 `learning_orchestrator/sharding.py`：统一分片、batch、parallelism、checkpoint 和 resume 策略。
- 新增 `learning_orchestrator/run_plan.py`：输出 dataset -> shard replay -> evaluator suite -> candidate policy search -> replay compare -> promotion preflight。
- `/api/v20/learning/orchestrator/run-plan?job=nightly` 已可读取夜间全量学习计划。
- `/api/v20/learning/run-plan` 已嵌入默认 nightly orchestrator 摘要。

验收标准：

- `nightly` 目标盘数为 518,400，默认 128 shard、512 batch。
- `nightly` 的 `llm_eval_sample_limit=0`，避免全量 LLM 成本。
- `weekly/full` 仅允许 bounded LLM sample eval。
- 所有 stage `runtime_mutation=False`，并声明 pointer 只能由 replay/promotion 后显式激活。
- 计划中明确候选策略只优化规则权重、阈值、画像轴、问题排序、DAG 和角色视图，不生成命盘事实。

完成度：Learning Orchestrator V1 计划层 100%。下一步先进入 `P22：Admin Training Task Console V1`，把学习任务变成 admin 可见的后台任务；之后再进入 shard executor，不在 executor 完成前启动真实 518K 重跑。

### P22：Admin Training Task Console V1

状态：已完成 MVP；admin 页面已新增自我训练任务控制台，训练脚本可作为后台任务独立运行并落盘显示进度。

目标：

- 把自我学习和合成数据训练从“开发者命令行脚本”升级为 admin 可见、可启动、可恢复观察的后台能力。
- 所有训练任务独立于 runtime 测算请求运行，不阻塞用户测算页面。
- 刷新 admin 页面后仍能读取任务状态、进度、当前阶段、日志尾部和历史任务。
- 训练任务只生成 artifact/candidate/report，不默认写 runtime pointer。

已落地：

- 新增 `ops/training_tasks.py`：训练任务 registry、状态落盘、后台 worker 启动、任务列表和状态读取。
- 新增 `scripts/run_admin_training_task.py`：独立 worker 进程，负责执行脚本并持续更新 `runtime/training/tasks/*.json`。
- 新增 `scripts/run_learning_orchestrator_plan.py`：把 Learning Orchestrator run plan 做成可注册任务。
- 新增 admin API：`/api/v20/admin/training/tasks/registry`、`/api/v20/admin/training/tasks`、`/api/v20/admin/training/tasks/{task_id}`、`/api/v20/admin/training/tasks/start`。
- `frontend/admin.html` 新增 `Training Tasks / 自我训练` 控制台。
- `frontend/admin.js` 支持启动任务、轮询进度、展示日志尾部、刷新后恢复 latest task。
- Admin 页面已拆成两个顶层 Tab：`系统配置` 承载 DB/LLM/Redis，`训练任务` 承载策略观测、问题训练和自我训练脚本。
- 训练任务 registry 已扩展到主要训练/学习脚本：training iteration、synthetic suite、rule synthetic、dynamic decision、practitioner calibration、question DAG/ranking/source、role interaction、arbitration、self evolution、knowledge rule review、rule replay、rule subcondition、decision registry、rule portrait batch、full precompute preview、nightly executor skeleton、release smoke 等。

验收标准：

- 后台任务状态持久化到 runtime 目录，刷新页面不丢。
- UI 显示任务 registry、当前任务进度条、阶段、pid、更新时间、日志尾部和历史。
- 启动按钮来自 registry 动态渲染，不硬编码单个脚本。
- 任务启动 API 只允许 admin 调用。
- worker 通过子进程执行脚本，不在 HTTP 请求线程里同步跑训练。
- 默认任务不直接写 runtime pointer；`training_iteration_fast` 只写训练 artifact。

完成度：Admin Training Task Console V1 100%。下一步进入 `P23：Nightly Executor Skeleton`，把 518K 计划层变成可分片 checkpoint executor，并接入同一个 admin task console。

### P23：Nightly Executor Skeleton

状态：已完成 skeleton；夜间学习计划已经具备有限 shard 执行、checkpoint、resume 状态和 admin task 接入。

目标：

- 把 `Learning Orchestrator V1` 的 518K 夜间计划从“只读计划”推进为“可执行的小规模 shard executor”。
- 默认只跑极小 case limit，不启动真实 518K 全量。
- 复用 full corpus deterministic precompute 能力，写本地 checkpoint/status。
- 训练状态继续通过 admin Training Task Console 展示。
- 不调用 LLM，不写 runtime pointer，不修改规则真值。

已落地：

- 新增 `learning_orchestrator/nightly_executor.py`：封装 nightly executor skeleton，默认有限 shard replay，并写 `runtime/training/nightly_executor/*/status.json`。
- 新增 `scripts/run_nightly_learning_executor.py`：可由命令行或 admin task worker 启动。
- `ops/training_tasks.py` 新增 `nightly_executor_skeleton` 任务，默认 `--limit 8 --status-every 2 --progress`。
- 新增 `/api/v20/learning/orchestrator/nightly-executor/status` 只读状态入口。
- 测试覆盖有限 shard 执行、状态读取、guardrails 和 admin registry。

验收标准：

- skeleton 只跑有限 `limit`，不会误触发 518K 全量。
- executor status 明确 `executor_mode=skeleton_limited_shard`。
- 状态包含 executed/completed/progress/precompute_status。
- guardrails 包含 `NO_LLM_CALL`、`NO_RUNTIME_POINTER_MUTATION`、`LIMITED_SHARD_RUN_NOT_FULL_518K`。
- admin Training Console 能启动 `nightly_executor_skeleton` 并看到进度。

完成度：Nightly Executor Skeleton 100%。下一步进入 `P24：Evaluator Merge Skeleton`，把 shard 产物汇总为规则/画像/问题/角色视图 evaluator summary，但仍不做大规模参数优化。
