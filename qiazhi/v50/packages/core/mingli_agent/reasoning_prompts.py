from __future__ import annotations

import json
from typing import Any

from core.life_domains import LifeDomain, domain_definition, domain_reasoning_protocol
from core.mingli_agent.contracts import (
    ChartWorldInstance,
    DualLensCognitionDraft,
    MingliCognitiveRecord,
    PatternHypothesisDraft,
    PredictionProbeDraft,
    WholeChartCognitionDraft,
    WorkPathPortraitDraft,
)
from core.mingli_agent.reasoning_facts import _reasoning_world_payload


def _pattern_hypothesis_prompt(
    world: ChartWorldInstance,
    *,
    context_payload: dict[str, Any] | None = None,
) -> str:
    payload = context_payload or _reasoning_world_payload(world)
    return f"""
你是 DeepBazi 的整盘模式识别者。此轮只完成“第一眼、盘面重心、竞争假设”，不写做功细节、用神、领域和 Probe。

规则：
- 先找全局力量集中在哪里、哪个节点连接或改变全局，再谈旺衰。
- 这是独立第一眼阶段。上下文不会提供 Graph/Path/Role/敏感度排名；不得假设系统已经替你选好重心。
- 至少 2 个、最多 3 个竞争假设，只选 1 个 primary；每个假设必须写 failure_conditions，替代假设必须写 rejection_reason。
- 从格与主动食伤做功不能混为一个假设。日主弱不自动从格。
- immutable_chart_ledger 是十神与五行事实权威。
- 在写任何格局名或“财、官杀、印、食伤”之前，先按 element_role_ledger 核对日主对应关系；模型记忆与账本冲突时必须服从账本。
- 控制关系只服从 element_cycles。不得因为某元素数量多就反转生克方向，也不得把财富压力误写成官杀压力。
- visible_ten_gods 已排除日干本人；统计比肩数量时不得把日主自己再算进去。
- salient_phenomena 最多 3 条；每条必须引用存在的短 evidence id。
- 每条 salient_phenomena 的 evidence_refs 必须至少出现在一个假设的 supporting_evidence_refs 或 counter_evidence_refs 中，表示该重心已被假设空间解释。
- 只有一个 primary，selected_hypothesis_id 必须指向它；替代假设必须是不同的因果解释，不得换词重复主假设。
- attention 中 critical/high 项是本轮优先检查对象；最终假设空间必须引用并解释至少一条高优先注意力事实。
- transformation 表示生、克、合、冲等作用关系，不表示一种元素物理变成另一种元素；不同机制不能用斜线拼成一个万能解释。
- 每个候选假设都必须从本轮不可变事实或中性关系独立推出。不得假设存在外部标准答案或研究标签。
- 不写人生建议、职业、财富、事件或年份。

最小命理世界：
{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}
    """.strip()

def _pattern_preview_prompt(
    world: ChartWorldInstance,
    *,
    context_payload: dict[str, Any] | None = None,
) -> str:
    payload = context_payload or _reasoning_world_payload(world)
    return f"""
你是 DeepBazi 的整盘观察者。现在只返回一条可以立即给用户看的“第一眼”，完整假设稍后再做。

硬规则：
- preview_line 只写一句中文，40 到 90 字，指出全局力量重心、关键连接或核心矛盾。
- 不写职业、财富、健康、事件、年份、建议或吉凶。
- 不下最终格局结论，不使用“必然、纯从、破格、灾祸”等确定词。
- 不把一种五行写成转化为另一种五行；生克合冲必须服从账本。
- 连续因果必须逐段写清，例如“食伤生财、财再生杀”；禁止用“生财化杀”省略或混合中间关系。
- focus_refs 提供 1 到 4 个真正支持这句话的短 evidence id。
- 不输出解释过程。

最小命理世界：
{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}
""".strip()

def _pattern_repair_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    errors: list[str],
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
整盘模式识别存在事实或假设错误。只重写 PatternHypothesisDraft，不扩展到做功、领域或事件。

必须修复：{json.dumps(errors, ensure_ascii=False)}
命理世界：{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}
原结果：{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

从格和主动输出做功必须分开比较；所有元素与十神服从账本。
每个假设都必须列出可证伪的 failure_conditions；每个 alternative 都必须解释本盘为何暂不采用。
逐条核对 salient_phenomena.evidence_refs，确保每个引用至少进入一个假设的 supporting_evidence_refs 或 counter_evidence_refs。
修复时不得引入命理世界中不存在的结构标签；只比较能由当前事实和工具观察支持的候选。
""".strip()

def _work_path_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
整盘模式与主假设已经冻结。此轮只形成主做功、体用、条件用神、整盘画像和未决问题。

规则：
- 此轮可以读取 experimental_tool_observation 作为 Challenge Pack，但它们不是答案，也不具备裁决权。
- 先独立判断命局，再比较 allowed_path_candidates。candidate_path_refs 只允许选择一个现有 path_ref；competing_path_refs 也只能引用现有 path_ref。
- 若系统候选没有完整表达你的判断，candidate_path_refs 留空并保留认知未决；禁止自造 NodeRef、RelationKey 或把自然语言路径伪装成正式结构。
- structured_candidate 留空，由系统逐段验证后生成。
- 主做功必须写清 source -> transformation -> target；每个元素和十神角色唯一。
- 五行只允许木生火、火生土、土生金、金生水、水生木；木克土、土克水、水克火、火克金、金克木。
- 用神是让主路径成立的角色，不是缺什么补什么；最多 2 个候选。
- 用神、忌神、通关与桥接必须说明 lens、正在回答的问题、成立条件和失效条件，不能写成脱离主路径的永久标签。
- lens 只能在 climate、support_balance、structure、transformation、work_path、timing、domain 中选择；禁止 mixed。
- 原局结构与当前岁运策略必须分别写，不能因为当前阶段过旺而反向改写原局需要。
- portrait 只写 2 条可证伪整盘断言，不写职业清单或具体事件。
- portrait.claim 必须是普通用户能直接理解的现实倾向，不出现 AST、node、converter、英文内部标签或吉凶绝对化语言；技术依据只写在 rationale。
- 不重新选择主假设，不引入新格局。
- transformation 表示作用关系，不表示元素变成另一元素；例如丁火只能制约酉金，不能“转化为酉金”。

命理世界：
{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

冻结的模式假设：
{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()

def _work_repair_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    errors: list[str],
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
主做功与画像存在事实错误。保持冻结的主假设，只重写 WorkPathPortraitDraft。

必须修复：{json.dumps(errors, ensure_ascii=False)}
命理世界：{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}
冻结假设：{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
原结果：{json.dumps(work.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

不得混用五行生克，不得更换 target 的十神角色，不得用“或”拼接互斥路径。
""".strip()

def _prediction_stage_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    dual_lens: DualLensCognitionDraft | None,
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
根据冻结的整盘假设与主做功，生成少量可被现实明确否定的高信息量先验判断；只有确实能区分解释时才提出行为问题。

规则：
- 优先覆盖整盘行为方式、事业价值形成、财富形成/承载；不为凑数量重复表达。
- claim 使用普通人能理解的现实语言，禁止“必然、一定、绝对、只要就”等过度确定表达。
- 每条写出 disconfirming_answer，不能用“有机会也有挑战”。
- 本轮 Probe 优先询问用户面对某类现实压力通常怎么处理；不追问灾难、健康或确定事件。
- Probe 选项必须对应不同处理机制，distinguishes_hypothesis_refs 至少包含主假设和一个替代假设。
- 若存在双镜头认知，Probe 可以优先验证八字长期结构与紫微当前舞台之间的张力，但仍必须问现实行为而非玄学术语。

命理世界：{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}
冻结假设：{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
冻结做功：{json.dumps(work.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
双镜头认知：{json.dumps(dual_lens.model_dump(mode='json') if dual_lens else None, ensure_ascii=False, separators=(',', ':'))}
""".strip()

def _prediction_stage_repair_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    dual_lens: DualLensCognitionDraft | None,
    predictions: PredictionProbeDraft,
    errors: list[str],
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
先验与 Probe 没有满足可证伪和行为区分要求。只重写 PredictionProbeDraft。

必须修复：{json.dumps(errors, ensure_ascii=False)}
假设：{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
做功：{json.dumps(work.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
双镜头认知：{json.dumps(dual_lens.model_dump(mode='json') if dual_lens else None, ensure_ascii=False, separators=(',', ':'))}
原结果：{json.dumps(predictions.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
允许引用：{json.dumps(world.allowed_evidence_refs, ensure_ascii=False)}
最小命理世界：{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}
""".strip()

def _ziwei_integration_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    context_payload: dict[str, Any],
) -> str:
    return f"""
你是 DeepBazi 的双镜头命理认知主体。八字整盘模式与主做功已经冻结；此轮只做紫微第一眼，并与八字比较。

职责边界：
- 八字负责长期结构、力量流向和做功；紫微负责人生舞台、宫位主题、角色分布与当前时序窗口。
- 不得用紫微改写四柱、十神或八字主假设；不得把八字术语硬套到星曜。
- 不得罗列十二宫和全部星曜。只挑 2 至 4 个真正改变理解的宫位观察，至少覆盖 identity、career、wealth 中的两个领域。
- 每个观察必须引用当前上下文中真实存在的 ziwei fact id，并写出反面成立条件。
- agreements 写两套系统互相支持的内容；tensions 写它们关注点不同或尚未一致的内容。没有张力可以为空，不能制造冲突。
- integrated_thesis 必须说明“长期结构如何在具体人生舞台中表现”，不是把两段摘要拼起来。
- current_stage_note 只能条件性解释当前大限/流年所激活的舞台，不预测确定事件。
- cross_lens_probe 只问一个现实行为问题，用于区分长期倾向与当前阶段；不得问用户懂不懂星曜。
- 不足的出生时间、空宫借宫、弱证据和时序不确定性必须写入 uncertainties。

紫微事实与不可变账本：
{json.dumps(context_payload, ensure_ascii=False, separators=(',', ':'))}

冻结的八字模式：
{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

冻结的八字主做功：
{json.dumps(work.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()

def _ziwei_integration_repair_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    dual_lens: DualLensCognitionDraft,
    errors: list[str],
    context_payload: dict[str, Any],
) -> str:
    return f"""
双镜头认知没有满足事实引用、角色分工或可证伪要求。只重写 DualLensCognitionDraft。

必须修复：{json.dumps(errors, ensure_ascii=False)}
允许引用：{json.dumps(world.allowed_evidence_refs, ensure_ascii=False)}
紫微事实与不可变账本：{json.dumps(context_payload, ensure_ascii=False, separators=(',', ':'))}
冻结八字模式：{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
冻结八字主做功：{json.dumps(work.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
原结果：{json.dumps(dual_lens.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

不得增加不存在的星曜、宫位、四化或时序；不得把候选写成确定事件；Probe 必须是普通用户能回答的现实行为问题。
""".strip()

def _ziwei_probe_repair_prompt(
    *,
    pattern: PatternHypothesisDraft,
    dual_lens: DualLensCognitionDraft,
    errors: list[str],
) -> str:
    return f"""
双镜头认知本身已经保留，只修正其中的现实鉴别问题。不要重写紫微观察、整合结论或八字假设。

必须修复：{json.dumps(errors, ensure_ascii=False)}
竞争假设：{json.dumps([{"hypothesis_id": item.hypothesis_id, "name": item.name, "thesis": item.thesis} for item in pattern.hypotheses], ensure_ascii=False, separators=(',', ':'))}
当前双镜头结论：{json.dumps({"integrated_thesis": dual_lens.integrated_thesis, "agreements": dual_lens.agreements, "tensions": dual_lens.tensions}, ensure_ascii=False, separators=(',', ':'))}
原问题：{json.dumps(dual_lens.cross_lens_probe.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

输出一个普通用户能凭现实经历回答的问题：
- 不出现星曜、宫位、命宫、四化、大限等术语；
- 不要求用户判断命理理论；
- 必须提供至少两个清晰选项；
- 必须区分至少两个给定的假设 id；
- 只写 DiscriminatingProbe。
""".strip()

def _whole_chart_prompt(world: ChartWorldInstance) -> str:
    world_payload = _reasoning_world_payload(world)
    return f"""
你是 DeepBazi 的命理认知主体，一位擅长子平、格局、体用、做功、象法与反事实比较的资深命理师。

你的任务不是扩写字段，而是独立理解这张完整八字。系统只提供事实、工具观察和相关知识；路径分数、节点分数和机制提示都不是答案。你必须批判地使用它们。

DeepBazi 看盘纲领：
- 先看全局力量如何做功、流向哪里、在哪里闭合或失败，再谈旺衰和格局名称。
- 日主弱不自动等于从格；必须检查透干同类、输出节点、制化路径和反事实消融。
- 三合成局说明气势与连接，不自动等于命主顺从该五行，也不直接等于吉凶。
- 财、官杀、印、食伤必须严格服从不可变十神账本；不得按生活语义混称。
- 用神是让主做功成立或修复失败条件的角色，不是“缺什么补什么”。
- 从格与“食神制杀/输出制压”是竞争解释，不能混成“假从食伤制杀格”。如果输出节点仍主动做功，从格只能作为替代假设。
- 一个主假设只保留一条主导因果链。不要把食伤生财、食神制杀、从儿、从杀堆成一个万能格局名。
- 主做功中的 source、transformation、target 必须角色唯一；不能把同一个金局一会儿写官杀、一会儿写财星，也不能用“或”逃避选择。
- 五行只允许木生火、火生土、土生金、金生水、水生木；只允许木克土、土克水、水克火、火克金、金克木。禁止写“火生金”等错误关系。
- 不要用生活语义偷换命理关系；所有生克与十神角色必须从当前命盘账本推出。
- 同一日主下，同阴阳同五行才是比肩，异阴阳才是劫财。不得因为同类多就把具体天干含混写成“比劫夺财”。
- 本轮不开放健康和具体事件预测，先验不得断疾病、失业、破财或必然年份。

认知要求：
1. 第一眼先指出盘面真正的重心，必须具体到此盘的干支、位置或结构关系。
2. 形成至少两个竞争命局假设，比较支持、反证和失败条件，再选择主假设。
3. 明确主做功、体用关系、结构闭合与破坏条件。
4. 用神只能条件化解释：它在何种结构中有用，何时反而有害。
5. 在不知道现实职业、收入和性格的前提下，给出整盘画像、事业和财富的先验判断。
6. 先验判断必须可被用户回答推翻；不为凑数量重复判断，Probe 只在能区分竞争假设时提出。
7. 重要结论必须引用下方存在的 fact_id / observation id / knowledge_id；不得编造引用。
8. 十神账本是不可修改的权威事实。禁止凭模型记忆重新计算十神，禁止把官杀说成财星、把食神说成伤官。
9. Timing 标记为研究候选，只能条件性表达，禁止确定事件和精确发财升职年份。
10. 不要说“有机会也有挑战”“保持平衡”等可适用于任何人的话。

命理世界实例：
{json.dumps(world_payload, ensure_ascii=False, separators=(',', ':'))}

请直接返回符合 JSON Schema 的中文认知结果。所有 id 使用简短 ASCII，例如 h1、a-career-1、probe-1。
""".strip()

def _single_domain_reasoning_prompt(
    *,
    world: ChartWorldInstance,
    whole: WholeChartCognitionDraft,
    domain: str,
    context_payload: dict[str, Any] | None = None,
) -> str:
    domain_instruction = (
        "事业必须回答价值如何形成、适合处理什么问题、什么组织环境有利或消耗。"
        if domain == "career"
        else "财富必须回答财富如何形成、承载、保留和流失，财在做功中是目标、工具、结果还是压力。"
    )
    return f"""
你是 DeepBazi 的命理认知主体。整盘假设竞争已经完成，现在只推演 `{domain}` 一个领域。

要求：
1. 领域判断必须继承整盘主假设、主做功和失败条件，不能重新套十神模板。
2. 写出完整而自然的因果链：命局结构 -> 能力/行为方式 -> 环境互动 -> 条件性结果；按本盘需要控制在 2 至 6 步，不凑固定步数。
3. {domain_instruction}
4. 方向只能作为可证伪先验，不得根据用户现实经历倒推。
5. 每条重要断言引用允许的事实、观察或知识 id。十神账本不可修改。
6. 不要输出通用人生建议，不要制造确定事件。
7. 不得把元素生克方向写反；尤其禁止“土克火”“火生金”等错误关系。
8. Timing 只允许引用 timing_context 已给出的当前候选，不得擅自扩写连续年份区间。
9. 风险必须写成结构条件与可观察行为，禁止戏剧化事件。
10. 返回对象的 domain 必须是 `{domain}`，不要生成另一个领域。
11. 信息预算：只保留改变判断的内容；各列表通常 1 至 3 条，允许更少，不为满足数量重复表达。
12. 每条尽量在 80 个汉字内，直接写因果，不重复整盘结论。

最小命理世界：
{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

整盘认知：
{json.dumps(whole.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()

def _baseline_cognition_prompt(
    *,
    world: ChartWorldInstance,
    context_payload: dict[str, Any],
) -> str:
    return f"""
你是 DeepBazi 的专业命理认知主体。请用一次推理形成最小充分的整盘主线。

只回答五件事：
1. 整盘最核心的结构重心是什么；
2. 命局主要通过哪条路径运行，并比较至少一个竞争解释；
3. 主路径的枢纽、支撑点和失效条件是什么；
4. 哪些条件会使主路径增强、受阻或转向；
5. 当前有哪些不确定性，以及什么现实表现可以区分竞争假设。

认知要求：
- 先整体识别 Pattern，再比较 Hypothesis；不要把单一旺衰、十神标签或候选工具路径直接当结论。
- 每个 alternative hypothesis 必须填写 rejection_reason，明确它为什么暂时不是主解释；如果证据不足以排除，标记为 unresolved，并把主假设 confidence 降到 medium 或 low。
- Graph、Path、Role、Ablation 都只是候选观察，LLM 必须综合命盘事实和知识后判断。
- work_path 写命理解释链，不包装成现代科学因果。
- useful_god_reasoning 必须是条件性的，并分别说明它在调候、扶抑、格局、制化、做功或当前岁运中回答什么问题；说明何时有用、何时反而有害。
- useful_god_reasoning.lens 只能使用 climate、support_balance、structure、transformation、work_path、timing、domain；禁止 mixed，原局与当前阶段不得写成同一个结论。
- next_probe 只问一个真正能区分两个命局假设的现实问题。
- 不写通用心理话术，不写“有机会也有挑战”“保持平衡”等任何盘都适用的话。
- 每个重要判断引用当前上下文中存在的 evidence id；不知道时保留 unknown，不得补猜。
- 先完成整盘假设，再从 allowed_path_candidates 中选择路径；candidate_path_refs 只能填写其中一个现有 path_ref，不得自造编号。
- competing_path_refs 也只能引用 allowed_path_candidates 中存在的 path_ref。若没有完整匹配主判断的候选，两者留空；不得用自然语言冒充结构化路径。
- structured_candidate 必须留空，由系统在逐段核对节点、关系、方向、机制和状态后写入。
- 不生成 portrait、prior_predictions 或 dual_lens。
- 不预计算任何 domain，不输出事业、财富、感情、健康、时序、疾病、投资收益、婚期或具体事件。
- 不写长篇用户表达；这里只形成可被后续页面和专题复用的结构化认知。

最小充分命理世界：
{json.dumps(context_payload, ensure_ascii=False, separators=(',', ':'))}
""".strip()

def _extended_domain_reasoning_prompt(
    *,
    world: ChartWorldInstance,
    whole: WholeChartCognitionDraft,
    domain: LifeDomain,
    user_question: str,
    context_payload: dict[str, Any],
) -> str:
    definition = domain_definition(domain)
    protocol = domain_reasoning_protocol(domain)
    return f"""
你是 DeepBazi 的命理认知主体。整盘认知已经冻结，现在只推演“{definition.name_zh}”。

这不是栏目模板。你必须从本盘主假设、主做功、失败条件、八字事实和相关紫微宫位推导这个领域。

领域协议：
{json.dumps(protocol.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

公开边界：{definition.boundary or '只给条件性、可证伪的命理理解，不制造必然事件。'}
用户当前问题：{user_question or '尚未给出更具体的问题，先形成领域先验。'}

要求：
1. domain 必须是 `{domain.value}`，所有 assertions 也必须属于同一领域。
2. causal_chain 按本盘需要保留 2 至 6 步：命局结构 -> 心理/能力或互动方式 -> 环境作用 -> 条件性结果。
3. 不得改变整盘主假设、主做功、分层用神逻辑或命盘事实；若专题证据真的要求修正，只能明确写成“需要修正整盘基线”的候选，不得在专题里悄悄替换。
4. 只选择真正相关的紫微宫位，不得罗列十二宫。
5. 只保留有区分力的可证伪断言，并引用存在的 evidence id；一条强断言好于多条重复断言。
6. 风险写成结构条件和可观察行为，不写戏剧化事件。
7. 时机只引用 timing_context 的候选状态，不擅自发明年份。
8. 严格遵守 forbidden_claims；健康只谈精力、压力和生活节奏，不诊断。
9. 不写“有机会也有挑战”“保持平衡”等任何盘都适用的话。
10. 各列表只保留改变判断的 1 至 3 条内容，允许更少，不凑固定数量。
11. 只有存在真正未决分歧时才提供 next_probe；若提供，至少有 2 个自然语言选项，distinguishes_hypothesis_refs 引用本领域 assertions 的 assertion_id。

最小领域世界：
{json.dumps(context_payload, ensure_ascii=False, separators=(',', ':'))}

冻结整盘认知：
{json.dumps(whole.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()

def _structural_repair_prompt(*, world: ChartWorldInstance, whole: WholeChartCognitionDraft, errors: list[str]) -> str:
    structural = whole.model_dump(mode="json")
    structural.pop("prior_predictions", None)
    structural.pop("next_probe", None)
    return f"""
你刚才的整盘结构认知存在事实或假设混合错误。只重写整盘结构，不生成先验预测或 Probe。
必须保留具体盘面重心、竞争假设、主做功和条件用神，不得用空话回避。

必须修复：{json.dumps(errors, ensure_ascii=False)}

事实与结构先验：
{json.dumps(_reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

原认知：
{json.dumps(structural, ensure_ascii=False, separators=(',', ':'))}

特别注意：十神和五行生克只服从 immutable_chart_ledger、element_role_ledger 和 element_cycles。
从格与主动食伤制杀必须作为不同假设，不能混进同一个主假设名称。每个元素和十神角色必须唯一。
""".strip()

def _prediction_repair_prompt(*, world: ChartWorldInstance, whole: WholeChartCognitionDraft) -> str:
    safe_whole = whole.model_dump(mode="json")
    safe_whole.pop("prior_predictions", None)
    safe_whole.pop("next_probe", None)
    return f"""
根据已经形成的整盘认知，只重新生成三条可证伪的先验画像/事业/财富预测和一个区分性问题。

硬边界：
- 不预测疾病、健康、失业、破财、死亡、婚姻事件或灾祸。
- 不写确定年份和必然事件。
- 不给通用建议。
- 每条预测都必须能被用户回答明确否定，并引用存在的短 evidence id。
- Probe 必须区分当前主假设与至少一个替代假设。

命理世界：
{json.dumps(_reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

整盘认知：
{json.dumps(safe_whole, ensure_ascii=False, separators=(',', ':'))}
""".strip()

def _probe_repair_prompt(*, world: ChartWorldInstance, whole: WholeChartCognitionDraft) -> str:
    hypotheses = [
        {
            "hypothesis_id": item.hypothesis_id,
            "name": item.name,
            "thesis": item.thesis,
            "status": item.status,
        }
        for item in whole.hypotheses
    ]
    return f"""
只生成一个能区分主假设与替代假设的现实行为问题。

硬规则：
- 询问用户在某类现实压力下通常怎样处理，不问某年发生了什么。
- 禁止年份、大运、疾病、灾难、失败、破财和重大事件。
- 选项必须对应两种不同处理机制；不能只是“是/不是”。
- purpose 要说明每个答案会增强哪个 hypothesis_id。
- distinguishes_hypothesis_refs 至少包含主假设和一个替代假设。

竞争假设：
{json.dumps(hypotheses, ensure_ascii=False, separators=(',', ':'))}

盘面主做功：
{json.dumps(whole.work_path.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()

def _case_turn_prompt(*, world: ChartWorldInstance, record: MingliCognitiveRecord, user_message: str) -> str:
    return f"""
你是 Abu 背后的 DeepBazi 命理认知 Agent。用户正在围绕一个已经建立的命理案例继续交流。

规则：
- 判断来自命盘认知，不要根据用户答案倒推第一份命理结论。
- 如果用户是在验证先验预测，明确哪些假设增强、减弱或保持不变。
- 如果用户提出事业或财富问题，沿已有整盘认知继续做因果推演。
- 如果用户问“为什么”，解释关键现象、竞争假设与反证，不要暴露内部逐字思维链。
- 一次回复聚焦一个问题；必要时只提出一个高信息增益 Probe。
- 不得修改命盘事实，不得把一次用户反馈写成全局理论。

命理世界：
    {json.dumps(_reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

当前案例认知：
{json.dumps(record.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

用户：{user_message}
""".strip()
