# V30 Dialogue Chain Architecture

更新时间：2026-06-29

## 背景判断

当前 7 阶段测算页已经走对了：它负责把排盘、结构、用神候选、规则、画像、特征、路径、时运、领域和 Verdict 收束成可读产出。

但八字智能对话不应该被 7 个测算页面“消耗完”。对话是用户和系统沟通的核心，应该是一个可无限延展的会话链：

```text
用户问题 / 系统种子问题
-> 中枢理解意图
-> 绑定命盘与 Verdict
-> 先回答当前问题
-> 生成下一轮高价值追问
-> 用户点击 / 选择 / 输入
-> 更新会话记忆和中枢权重
-> 继续回答与追问
```

因此本阶段新增一条主线：

```text
Dialogue-Centered Layer over Decision-Centered Architecture
```

## 关键原则

### 1. 测算页和对话会话分离

7 阶段页面：

- 负责测算产出、素材展示、Verdict、建议、命理师校准。
- 可以挂载一个当前追问入口。
- 不拥有完整对话生命周期。

智能对话：

- 是独立 `DialogueSession`。
- 可以从任意页面启动。
- 可以由系统种子问题启动，也可以由用户自由提问启动。
- 回答完成后必须生成下一轮候选追问，直到用户停止。

### 2. 先回答，再追问

用户问“我今年财运如何？”时，系统不能只反问。

正确流程：

```text
识别用户问题
-> 给出当前可判断的结论和建议
-> 标出证据边界与待确认点
-> 给出 1 个最值得继续确认的问题
```

### 3. LLM 是表达与理解助手，不是命理裁决者

LLM 可以：

- 解析用户自然语言问题。
- 把结构化 Verdict/Advice 表达成人话。
- 生成自然的追问措辞。
- 做 answer rewrite 和 clarification。

LLM 不可以：

- 修改四柱、大运、流年、用神候选等事实。
- 绕过 Decision Engine 生成最终命理裁决。
- 把未确认隐藏属性说成事实。

### 4. 种子问题是可训练入口

种子问题来源：

- 系统推荐：来自 Verdict gap、ConflictResolver、hidden factor、useful-god uncertainty、domain cards、timing gaps。
- 用户发起：如“我今年财运如何？”、“适合创业吗？”、“感情什么时候稳定？”。
- 命理师发起：从分支选项、校准点、Verdict 卡或边栏素材发起。
- 运营/训练发起：合成案例、真实案例 replay、失败簇。

## 核心数据模型

### BaziDialogueSeed

```ts
type BaziDialogueSeed = {
  seed_id: string;
  reading_id: string;
  source: "system" | "user" | "practitioner" | "training";
  raw_text: string;
  normalized_question: string;

  macro_domain:
    | "wealth"
    | "career"
    | "relationship"
    | "health"
    | "family"
    | "timing"
    | "decision"
    | "overview";

  bazi_topics: Array<
    | "ten_god"
    | "useful_god"
    | "structure"
    | "path"
    | "luck_cycle"
    | "flow_year"
    | "hidden_factor"
    | "verdict"
  >;

  time_scope: "natal" | "current_year" | "current_luck" | "month" | "custom";
  user_intent: "ask_conclusion" | "ask_advice" | "compare_options" | "verify_event" | "open_chat";
  answer_priority: "answer_first" | "clarify_first" | "calibrate_first";
  confidence: number;
  evidence_binding: string[];
  boundary: "dialogue_seed_is_intent_not_chart_fact";
};
```

### BaziDialogueSession

```ts
type BaziDialogueSession = {
  dialogue_id: string;
  reading_id: string;
  seed: BaziDialogueSeed;
  status: "active" | "paused" | "completed";
  turn_count: number;
  active_domain: string;
  active_question_id: string;
  unresolved_slots: string[];
  memory_summary: DialogueMemory;
  policy_state: DialoguePolicyState;
  created_at: string;
  updated_at: string;
  boundary: "dialogue_session_updates_memory_not_chart_facts";
};
```

### BaziDialogueTurn

```ts
type BaziDialogueTurn = {
  turn_id: string;
  dialogue_id: string;
  reading_id: string;
  turn_index: number;

  user_input: {
    text: string;
    selected_option: string;
    structured_payload: Record<string, unknown>;
  };

  interpreted_seed: BaziDialogueSeed;
  answer_contract: {
    must_answer_user_seed: boolean;
    uses_decision_verdicts: boolean;
    uses_dialogue_memory: boolean;
    llm_expression_only: boolean;
  };

  answer: {
    verdict_refs: string[];
    conclusion_items: string[];
    advice_items: string[];
    uncertainty_items: string[];
    display_text: string;
    llm_metadata: Record<string, unknown>;
  };

  next_question_candidates: DialogueQuestionCandidate[];
  selected_next_question: DialogueQuestionCandidate | null;
  training_signal: Record<string, unknown>;
  boundary: "dialogue_turn_is_feedback_and_expression_not_chart_fact";
};
```

## 中枢调度层

新增 `DialogueOrchestrator`，职责是把“用户想问什么”和“命盘现在最值得问什么”合在一起。

```text
DialogueSeedRouter
-> DialogueContextBuilder
-> DialogueAnswerPlanner
-> DialogueQuestionExpander
-> DialoguePolicyScorer
-> DialogueMemoryUpdater
```

### DialogueSeedRouter

输入：

- 用户自然语言。
- 当前页面 stage。
- 当前 reading 的 Decision Workbench。
- 7 阶段素材。
- 历史 dialogue memory。

输出：

- `BaziDialogueSeed`。

策略：

- 先用规则/词典识别宏观领域：财运、事业、关系、健康、亲情、时运、决策。
- 再用 LLM 做轻量语义归一，但只产出 intent，不产出命理事实。
- 典型用户问法要被稳定识别：
  - “我今年财运如何？” -> `wealth + current_year + ask_conclusion`
  - “适合创业吗？” -> `career/wealth + compare_options`
  - “感情什么时候稳定？” -> `relationship + timing`
  - “身体要注意什么？” -> `health + ask_advice`

### DialogueAnswerPlanner

决定本轮是：

- 直接回答。
- 先澄清一个必要信息。
- 回答后追问。
- 建议进入命理师校准。

原则：

- 用户明确问结论时，默认 `answer_first`。
- 只有缺少关键出生资料、时柱边界、或问题无法绑定命盘时，才 `clarify_first`。
- 隐藏属性不直接下断语，只能通过问题逐步校准。

### DialogueQuestionExpander

根据当前答案生成下一轮候选问题。

候选来源：

- Decision Verdict 的 `next_question_slots`。
- ConflictResolver 的 branch gaps。
- Hidden factor 的 event-year / repeated-state slots。
- Domain cards 的行动建议缺口。
- 用户 seed 的后续语义方向。
- 历史 turn 的 unanswered slot。

候选不是死模板。系统先生成结构化候选，再由 LLM 做自然表达。

### DialoguePolicyScorer

核心公式：

```text
score =
  user_intent_alignment
+ evidence_gain
+ verdict_gap_gain
+ hidden_factor_gain
+ timing_relevance
+ novelty
- repetition_penalty
- user_cost
- overask_penalty
```

输出：

- 最多 1 个主问题。
- 2-3 个可点击快捷方向。
- 一个“自由输入继续问”的入口。

## UI 设计

### 页面内追问

7 阶段页可以显示一个轻量入口：

```text
围绕本页继续问
```

点击后进入同一个 `DialogueSession`，回答显示在对话面板，而不是污染阶段页。

### 独立八字对话面板

新增一个可持续的对话 surface：

- 桌面端：右侧对话抽屉或底部对话栏。
- 手机端：独立聊天页。
- 入口文案：`问八字`。
- 页面阶段只是上下文，不是对话边界。

对话显示：

- 用户问题。
- 系统结论列表。
- 建议列表。
- 证据标签。
- 下一轮主问题。
- 快捷选项。
- 自由输入框。

### 种子问题入口

用户可直接输入：

```text
我今年财运如何？
最近适合换工作吗？
感情什么时候稳定？
这个八字适合创业吗？
```

系统先回答，再继续问。

## API 设计

新增 API，旧 `/questions/{question_id}/answer` 保留为阶段内兼容入口。

```text
POST /api/v30/readings/{reading_id}/dialogues
GET  /api/v30/readings/{reading_id}/dialogues/{dialogue_id}
POST /api/v30/readings/{reading_id}/dialogues/{dialogue_id}/turns
POST /api/v30/readings/{reading_id}/dialogues/{dialogue_id}/next
GET  /api/v30/readings/{reading_id}/dialogue-seeds
```

### Create Dialogue

输入：

```json
{
  "seed_text": "我今年财运如何？",
  "source": "user",
  "stage_id": "journey_path_timing_domain"
}
```

输出：

```json
{
  "dialogue_id": "...",
  "seed": "...",
  "first_turn": "...",
  "next_question": "..."
}
```

## 训练与验证

### 训练目标

训练只影响：

- seed intent routing。
- question expansion。
- next-question policy。
- answer expression quality。
- role-specific dialogue UX。

训练不得影响：

- 四柱事实。
- 大运流年计算。
- Deterministic Bazi facts。
- 未确认隐藏属性事实化。

### 合成验证

新增 `dialogue_chain` synthetic tier：

- 用户问“今年财运如何”，必须先回答财运，再追问收入/风险/合作。
- 用户问“适合创业吗”，必须比较稳定/突破/风险，而不是只问背景。
- 用户连续追问 5 轮，不能重复同一个问题。
- 回答必须绑定 Verdict、domain cards、timing context。
- 智能对话不能作为第 8 步进入 7 阶段导航。
- 普通用户不能看到 internal_next_question_id、raw_score、training_signal。

### Admin 观察

Admin 增加：

- Dialogue Session replay。
- Seed routing audit。
- Turn quality audit。
- next-question policy diff。
- failed dialogue cluster。

## 分阶段任务

### DLG-1 Dialogue Schema And Store

- 新增 `BaziDialogueSeed / BaziDialogueSession / BaziDialogueTurn`。
- Postgres 持久化 dialogue sessions 和 turns。
- 保留 chart facts 不变。

### DLG-2 Seed Router

- 支持系统种子与用户自然语言种子。
- 首批覆盖财富、事业、关系、健康、亲情、时运、决策。
- “我今年财运如何？”作为必须通过案例。

### DLG-3 Dialogue Orchestrator

- 接入 Decision Workbench、Verdict、ConflictResolver、HiddenFactor、question outcomes。
- 实现 answer-first / clarify-first / calibrate-first 策略。

### DLG-4 Infinite Chain Policy

- 每轮回答后生成下一轮主问题和快捷选项。
- 防重复、防过问、防幽灵问题。
- 支持用户自由输入继续改变方向。

### DLG-5 UI Surface

- 新增独立 `问八字` 对话面板。
- 阶段页追问只作为入口，回答进入对话 surface。
- 手机端独立聊天页。

### DLG-6 Training And Validation

- 新增 `dialogue_chain` synthetic tier。
- Admin 增加 replay、quality audit 和 policy diff。
- 训练信号进入 question/dialogue policy，不改 chart facts。

## 当前结论

V30 现在不缺问题推荐能力，缺的是把它从“阶段页附属功能”升级为“独立、持久、可无限延展、可训练、可验证的八字对话链”。

下一步应先做 DLG-1 到 DLG-3：建模型、建种子路由、建中枢编排；UI 可以随后接入，不要再把对话塞进 7 阶段页面里。
