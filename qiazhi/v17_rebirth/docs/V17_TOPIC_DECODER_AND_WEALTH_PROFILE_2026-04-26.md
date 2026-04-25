# V17 主题解码器与财富画像合同

Date: 2026-04-26

## 1. 背景

宏观象不是把十神强弱直接翻译成断语。财富、事业、感情、性格等用户真正关心的主题，都需要先从 L0-L2 微观材料中解出一份结构化专题画像，再交给 LLM 做领域专属表达。

当前 `v17.macro.theme.v1` 已能给出四个主题的激活度、置信度、风险、证据和机会。下一层应是 `topic_decoder`：

```text
L0-L2 微观材料
八字、十神、强弱、流通、合冲刑害、体用、格局、盲派、象法、调候、运行关系
        ↓
主题解码器 Topic Decoder
wealth_profile / career_profile / relationship_profile / personality_profile
        ↓
领域专属 Prompt
财富 prompt / 事业 prompt / 感情 prompt / 性格 prompt
        ↓
领域专属断言
财富断言 / 事业断言 / 感情断言 / 性格断言
```

核心原则：LLM 不负责从原始八字中自由找主题，LLM 只负责把系统已经解码好的专题画像写成人能读懂的断言。

## 2. 主题解码器定位

`topic_decoder` 属于 L3 专题解码层：

- 只读 L0/L1/L2、`god_ring_authority`、`macro_theme`、盲派、象法、调候、关系动力和命理师本次覆盖前提。
- 不回写 `ten_gods_runtime`、格局候选、体用裁决、参数配置或学习发布状态。
- 输出专题画像合同，而不是最终自然语言断言。
- 每个专题画像必须保留证据、矛盾、风险、置信度和 LLM 写作边界。
- 命理师反馈和真实案例只能进入学习候选、实验队列和 benchmark，不能直接修改专题判断。

## 3. 四类专题画像

第一阶段建议拆成四个 profile：

- `wealth_profile.v1`：财富来源、变现方式、守财能力、财富风险、触发条件。
- `career_profile.v1`：职业路径、组织/平台关系、职位压力、权责边界、事业风险。
- `relationship_profile.v1`：亲密关系模式、伴侣星状态、合冲牵引、稳定度、关系风险。
- `personality_profile.v1`：性格外显、内在驱动、表达方式、边界感、防御模式。

`macro_theme` 只回答“哪个主题更值得看”。`topic_decoder` 回答“这个主题到底如何发生、从哪里来、能否承载、有什么代价、适合怎么表达”。

## 4. 财富相关微观材料

财富专题至少读取以下材料。

### 4.1 十神主材料

- 正财：稳定收入、确定资源、经营秩序、长期现金流、可被规则管理的钱。
- 偏财：机会型资源、市场、外部资金、项目收益、副业、投资与流动性。
- 食神：技能、产品、服务、长期输出、温和变现。
- 伤官：表达、销售、创意、差异化、主动破局变现，也带波动和规则摩擦。
- 比肩：同辈竞争、共同经营、自主性、分工协作，也可能分财。
- 劫财：强竞争、合伙分利、抢夺性资源、破财、杠杆冲动。
- 正官/七杀：平台、组织、职位、规则、合同、权责、风控。
- 正印/偏印：资质、知识、保护、学习、IP、专业壁垒，也可能压制食伤变现。

### 4.2 格局与插件材料

- `classical.pattern.wealth_star.v1`：正财格 / 偏财格候选。
- `classical.pattern.shishen_shengcai.v1`：食神生财。
- `classical.pattern.shangguan_shengcai.v1`：伤官生财。
- `classical.pattern.congcai.v1`：从财格。
- 财官结构：资源进入组织、职位、规则和平台。
- 财印结构：资源与资质、知识、防护之间的转换或冲突。
- 劫财夺财：竞争、合伙、分利、破财风险。
- 运行关系：合冲刑害、稳定度变化、流年/大运触发。

### 4.3 体用与专题材料

- `god_ring_authority`：财、食伤、官杀、印、比劫是否为用神、忌神或通关神。
- `blind_theme`：食伤生财、财官同流、家内家外等主线。
- `xiangfa_theme`：事件框架、外显象、可被叙事引用的场景。
- `climate_theme`：调候张力和环境条件，决定财富表达是否需要先调环境。
- `macro_theme.wealth`：财富主题总激活度和总风险。
- practitioner override：命理师本次选择的格局、用神、忌神，只影响本次断言前提。

## 5. 微观到宏观的财富映射

财富判断至少要经过以下问题，不能只看财星强弱。

### 5.1 财富是否显性

- 财星强：财富议题显性，但不代表一定能得财。
- 财星弱、食伤强：可能是“先输出后变现”，财富不在表层而在转化链路。
- 财星弱、官印强：财富可能来自组织、资质、职位或长期规则，不适合写成偏财机会。
- 财星强、比劫强：钱与竞争、合伙、分利高度绑定。

### 5.2 财富从哪里来

- 正财主稳定现金流、长期经营、确定收入。
- 偏财主项目、市场、外部机会、流动资源。
- 食神生财主产品、服务、技能、可持续输出。
- 伤官生财主表达、销售、创意、差异化、主动获客。
- 财官主平台、职位、规则、合同、组织资源。
- 财印主资质、知识、IP、专业壁垒，也要检查财是否破印。
- 从财主资源场强于自我承载，适合顺势借势，但风险在承载力和边界。

### 5.3 财富是否可用

- 财为用神：财富主题可作为主线写，但仍要写风险和条件。
- 财为忌神：财富强也可能带压力、消耗、关系牵扯或判断失衡。
- 食伤为用、财不强：财富应写成“输出变现路径”，不是现成财库。
- 官杀为通关：财富需要规则、平台、合同、风控来承接。
- 印为通关：财富需要知识、资质、方法论或长期积累来承接。

### 5.4 财富能否守住

- 比劫/劫财强：分利、竞争、合伙、朋友同辈牵引增强。
- 冲财或关系动力不稳：现金流、合作或项目节奏容易波动。
- 伤官过强且官杀受损：赚钱靠表达和破局，但规则风险高。
- 财破印：短期资源诱惑可能伤害长期资质、口碑或学习体系。
- 身弱财重或承载不足：机会多但消耗也大，不宜直接写“大财”。

## 6. `wealth_profile.v1` 合同草案

`wealth_profile.v1` 是财富专题解码器的输出，不是最终断语。

```json
{
  "contract": "v17.topic.wealth_profile.v1",
  "is_l3_topic_decoder": true,
  "topic": "wealth",
  "score": 0.0,
  "confidence": 0.0,
  "risk": 0.0,
  "stance": "active | watch | latent | volatile",
  "visibility": "explicit_wealth | hidden_wealth | indirect_wealth | weak_signal",
  "usable_state": "wealth_as_use | wealth_as_taboo | wealth_needs_bridge | unclear",
  "primary_channels": [
    {
      "id": "stable_income | opportunity_income | output_to_wealth | authority_income | knowledge_asset | resource_integration",
      "label": "稳定现金流",
      "score": 0.0,
      "evidence": []
    }
  ],
  "source_gods": {
    "wealth": ["正财", "偏财"],
    "output": ["食神", "伤官"],
    "peer": ["比肩", "劫财"],
    "authority": ["正官", "七杀"],
    "seal": ["正印", "偏印"]
  },
  "strengths": [],
  "risks": [],
  "contradictions": [],
  "bridge_requirements": [],
  "timing_hooks": [],
  "evidence": [],
  "llm_prompt_focus": [],
  "assertion_style": {
    "tone": "practical | cautious | opportunity | risk_first",
    "must_include": [],
    "must_avoid": []
  },
  "learning_hooks": [
    "topic.wealth.channel.calibration",
    "topic.wealth.usable_state.calibration",
    "topic.wealth.risk.calibration"
  ],
  "guardrails": []
}
```

## 7. 财富专属 LLM Prompt 边界

LLM 只消费 `wealth_profile.v1` 和必要的短证据，不直接自由解释原始八字。

财富断言必须包含：

- 财富总判断：主题活跃度、置信度、风险。
- 财富来源：稳定收入、项目机会、输出变现、平台收入、知识资产或资源整合。
- 财富优势：最可用的变现路径。
- 财富风险：竞争分利、冲动投资、现金流波动、规则风险、财破印、承载不足等。
- 行动建议：保守、扩张、先建规则、先打磨产品/技能、先控风险等。
- 证据引用：至少引用 `wealth_profile.evidence` 中的 2 条。

财富断言禁止：

- 直接说“必发财”“无财”“破产”等绝对结论。
- 把财星强等同于钱多。
- 把财星弱等同于不能赚钱。
- 忽略体用状态、风险和承载条件。
- 虚构系统没有给出的财富渠道、时间点或金额。

## 8. 学习与验证

财富专题学习不直接改参数，先进入候选和实验：

- 命理师反馈：财富来源判断是否正确、风险是否命中、建议是否可用。
- 真实案例：收入模式、职业行业、资产来源、合伙/投资/负债事件。
- 合成数据：构造正财强、偏财强、食伤生财、劫财夺财、财破印、从财、身弱财重等样本。
- 验证指标：渠道识别准确率、风险召回率、命理师一致性、LLM 是否遵守 profile 边界。

第一阶段不自动发布学习结果。只有通过 synthetic baseline、practitioner benchmark、shadow run 和 admin 审批后，才允许成为后续参数候选。

## 9. 分阶段实施建议

1. 文档阶段：确认 `topic_decoder` 架构和 `wealth_profile.v1` 合同。
2. 解析阶段：实现只读 `wealth_profile` resolver，不接 LLM，不改 UI。
3. 审计阶段：把 `wealth_profile` 暴露到证据链/幕后观察，先让命理师看结构是否合理。
4. Prompt 阶段：新增财富专属 prompt，让 LLM 只基于 `wealth_profile` 写财富断言。
5. UI 阶段：在运势分析中增加“财富断言”专题入口，支持证据展开。
6. 学习阶段：把命理师反馈和案例归入财富专题校准，不自动改参数。
