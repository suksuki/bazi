# V17 古典证据层协议

日期：2026-04-25

## 产品定位

V17 的主线定位已经从“八字测算工具”升级为：

1. 可自我学习和进化的八字测算系统。
2. 深度结合 AI 技术的八字推理系统。
3. 面向职业和业余命理师的可审计推理平台，支持他们查看证据、参与反馈、验证和修正规则。

因此，系统输出不能只有“断语”，还必须能回答：

- 这个判断用了哪些命理证据？
- 这是已确认、候选，还是待核验？
- 命理师可以在哪个证据点上给出反馈？
- AI 断言是否把候选误写成定论？

## 核心原则

古典插件必须遵守三层结构：

1. `classical_evidence`：收集结构证据，只做可复用事实。
2. `classical.pattern.*`：基于证据生成候选，不直接改写物理底数。
3. `resolver / LLM / UI`：只把充分证据写成强断语，候选必须保留“待核验”语义。

## 已落地的公共证据函数

文件：

`qiazhi/v17_rebirth/backend/logic/L2_structure_patterns/classical_evidence.py`

当前提供：

- `yangren_blade_context`：按日干映射真实羊刃位，并区分原局与运流命中。
- `zaqi_evidence`：检查辰戌丑未杂气月中目标十神是否既藏于月支又有透干。
- `dominant_element_from_ten_gods`：按日主动态把十神还原为五行，避免非木日主错判专旺。
- `element_structure_evidence`：检查专旺格所需的月令、天干、地支同气证据。
- `is_followable_weak_body`：检查从格候选是否存在日主根气和印比回身。
- `is_self_party_strong`：检查从旺、从强类候选是否具备自党强根。
- `branch_main_god`：按地支主气折算目标十神，用于羊刃逢冲等风险证据。

## 当前语义约束

所有 `classical.pattern.*` 输出默认带：

- `observe_only = true`
- `candidate_status = "needs_classical_evidence"`
- `claim_type = "pattern_candidate"`

这意味着它们是给命理师、AI 和 UI 使用的候选证据，不是最终物理修改项。

## 反馈闭环建议

命理师反馈不应只记录“对/错”，还应记录到证据点：

- `pattern_candidate`：反馈针对哪个格局候选。
- `evidence_key`：反馈针对羊刃、杂气、从格根气、化气、专旺结构等哪个证据。
- `verdict`：确认、否定、待观察。
- `reason`：命理师的文字解释。
- `chart_snapshot`：当时六柱、十神能量、证据 meta 的冻结快照。

后续学习系统应优先学习“证据门槛”和“候选升降级”，而不是直接学习最终断语。

## 回归测试

新增：

`qiazhi/v17_rebirth/tests/test_classical_evidence.py`

覆盖：

- 无真实羊刃支不输出羊刃证据。
- 十神到五行必须按日主动态映射。
- 杂气格必须具备藏干与透干证据。
- 专旺格必须具备月令与地支同气证据。
- 有根有印比时不得轻判从格。
