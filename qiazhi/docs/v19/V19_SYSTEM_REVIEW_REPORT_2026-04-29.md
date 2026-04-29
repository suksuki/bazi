# V19 System Review Report

Date: 2026-04-29
Audience: Bazi domain analysts, product reviewers, engineering reviewers
System: V19 Standalone Bazi Agent
Status: local agent-loop prototype with backend, admin, DB/LLM configuration, knowledge retrieval, and first bounded wealth-domain signal

---

## 1. Executive Summary

V19 has moved from a UI prototype into a standalone local Agent system.

Current system shape:

```text
Birth Input
-> Chart Structure
-> Luck Cycle / Flow Year Time Structure
-> Knowledge Retrieval
-> Bounded Inference Context
-> Optional LLM Agent Response
-> Session Storage
-> UI / Admin Review
```

The system is no longer only a static page. It now has:

- A standalone FastAPI backend.
- A real frontend Agent workbench.
- A real Admin page for DB, LLM, and Knowledge settings.
- Optional PostgreSQL session / knowledge persistence.
- Optional OpenAI-compatible / Ollama LLM integration.
- A V19 knowledge store with reviewed evidence-template units.
- A first bounded wealth-domain structure signal: `income_stability`.

Important boundary:

```text
V19 currently produces structure signals and evidence explanations.
It does not yet produce full fortune prediction, traditional narrative prediction, or analyst-grade final reading.
```

---

## 2. Current Capability Snapshot

### 2.1 User-Facing Agent Workbench

Entry:

```text
http://127.0.0.1:9019
```

Current capabilities:

- Input solar birth year / month / day / hour.
- Select gender.
- Select flow year.
- Generate four pillars.
- Generate approximate luck cycles.
- Generate selected flow year pillar.
- Display natal / luck / flow relations.
- Run a conversational Agent turn.
- Preserve `session_id` for follow-up questions.
- Display runtime LLM status.
- Display storage status.
- Display Knowledge Context.
- Display Income Stability structure signal.
- Display raw structured trace JSON for debugging.

### 2.2 Admin Workbench

Entry:

```text
http://127.0.0.1:9019/admin
```

Current capabilities:

- Configure DB bridge.
- Create local PostgreSQL database for V19.
- Test DB connection.
- Configure LLM provider / host / port / model / base URL.
- Load available models.
- Select model.
- Test LLM chat.
- Initialize / inspect / search V19 knowledge base.

### 2.3 Backend API

Main APIs:

```text
GET  /health
GET  /
GET  /admin
POST /api/agent/turn
GET  /api/agent/sessions
GET  /api/agent/sessions/{session_id}
GET  /api/admin/settings
POST /api/admin/settings
POST /api/admin/db/test
POST /api/admin/db/ensure-database
POST /api/admin/llm/test
POST /api/admin/llm/models
POST /api/admin/llm/chat-test
GET  /api/admin/knowledge/status
GET  /api/admin/knowledge/units
POST /api/admin/knowledge/seed
POST /api/admin/knowledge/search
```

---

## 3. High-Level Architecture

```text
v19/
├── server.py                 # FastAPI application and route orchestration
├── runtime.py                # Settings, DB connection, session storage
├── llm.py                    # OpenAI-compatible / Ollama LLM client
├── knowledge_store.py        # Knowledge persistence, seeding, retrieval
├── agent/
│   ├── structure.py          # Chart, luck cycle, flow year structure engine
│   └── income_stability.py   # Bounded income_stability signal adapter
├── knowledge/
│   ├── schema.py             # Knowledge unit schema
│   ├── kernel.py             # Knowledge kernel lifecycle
│   └── seeds.py              # A-only reviewed seed units
├── frontend/
│   ├── index.html            # Agent workbench
│   ├── admin.html            # Admin workbench
│   └── assets/
│       ├── app.js            # Agent frontend logic
│       ├── admin.js          # Admin frontend logic
│       └── styles.css        # Shared dark UI styling
└── scripts/
    ├── start_macos.sh
    └── start_linux.sh
```

---

## 4. Runtime Data Flow

### 4.1 Agent Turn Flow

```text
User input
-> POST /api/agent/turn
-> build_agent_turn(payload)
-> build_chart(birth_input)
-> build_luck_cycles(chart, birth_input)
-> build_flow_year(chart, selected_year)
-> derive_income_stability(chart)
-> retrieve_knowledge(data, user_message)
-> optional LLM response
-> create_or_append_session(...)
-> UI render
```

### 4.2 Important Current Ordering

Current inference ordering:

```text
Chart structure first
Time structure second
Income stability adapter third
Knowledge retrieval fourth
LLM explanation last
```

This ordering matters because V19 tries to keep the model clean:

```text
LLM does not calculate chart structure.
LLM does not decide income_stability.
LLM only explains supplied structure and evidence.
```

---

## 5. Core Modules

### 5.1 Chart / Time Structure Engine

File:

```text
v19/agent/structure.py
```

Responsibilities:

- Parse birth input.
- Reject unsupported lunar input.
- Generate four pillars.
- Generate approximate luck cycle sequence.
- Generate selected flow year pillar.
- Detect natal branch relations.
- Detect flow year relation with natal chart.
- Return structure-first Agent reply fallback.

Current boundary:

```text
Time structure is context, not conclusion.
Luck cycle / flow year do not directly change ResultCard or income_stability yet.
```

Current limitations:

- Solar term boundaries are approximate.
- Luck cycle start age is approximate.
- Lunar conversion unsupported.
- Timezone / birthplace not yet modeled.
- Day pillar algorithm needs domain verification before production use.

### 5.2 Income Stability Adapter

File:

```text
v19/agent/income_stability.py
```

Responsibilities:

- Produce bounded `income_stability` structure signal.
- Keep signal separate from fortune prediction.
- Use chart structure only at current phase.
- Return `is_prediction: false`.
- Return signal sources and metrics.

Current output example:

```text
self_capacity: high
wealth_presence: medium
wealth_accessibility: clear
volatility: low
structure_binding: none
income_stability: stable
```

Current meaning:

```text
This is a wealth-domain structure signal.
It is not a statement that wealth will be good.
It is not a yearly prediction.
It is not a traditional fortune judgement.
```

Current rule basis:

```text
income_stability = f(
  self_capacity,
  wealth_presence,
  wealth_accessibility,
  volatility,
  structure_binding
)
```

Current limitation:

```text
P4 time context does not modify income_stability yet.
Time-aware inference belongs to a later phase.
```

---

## 6. Knowledge System

### 6.1 Knowledge Kernel

Files:

```text
v19/knowledge/schema.py
v19/knowledge/kernel.py
```

Responsibilities:

- Define knowledge unit shape.
- Enforce lifecycle.
- Compile reviewed knowledge into evidence templates.
- Prevent reviewed knowledge mutation.
- Prevent deprecated knowledge compilation.

Lifecycle currently supported:

```text
draft
-> reviewed
-> deprecated
```

Evidence template guardrails:

```text
NO_DIRECT_PREDICTION
NO_ACTIVE_RULE
EVIDENCE_ONLY
REQUIRES_CONTRACT_VERIFIER_FOR_OUTPUT
```

### 6.2 Knowledge Store

File:

```text
v19/knowledge_store.py
```

Responsibilities:

- Seed default A-only knowledge units.
- Save/load knowledge from file or PostgreSQL.
- Retrieve relevant knowledge for each Agent turn.
- Provide Admin inspection APIs.

Storage fallback:

```text
PostgreSQL if enabled and available
otherwise v19/.runtime/knowledge_units.json
```

### 6.3 Current Seed Knowledge

File:

```text
v19/knowledge/seeds.py
```

Current seed count:

```text
13 reviewed units
```

Representative units:

```text
core.heavenly_stems
core.earthly_branches
core.five_elements
core.stem_element_yinyang
core.ten_god_mapping_boundary
core.pillar_structure
core.six_clash
core.six_combination
core.three_harmony
core.time_structure_context
core.inference_input_boundary
core.day_master_strength_boundary
wealth.income_stability_rule_basis
```

### 6.4 Current Knowledge Boundary

Knowledge currently does:

```text
Provide reviewed evidence context.
Provide rule basis language.
Provide sourceable structural statements.
```

Knowledge does not:

```text
Directly predict fortune.
Directly score a user.
Directly generate traditional judgement.
Override backend inference.
Modify chart structure.
```

---

## 7. LLM Integration

File:

```text
v19/llm.py
```

Supported modes:

```text
OpenAI-compatible /v1/chat/completions
Ollama native /api/chat fallback
Ollama /api/tags model loading
OpenAI-compatible /models model loading
```

Current LLM principle:

```text
LLM explains supplied structure and evidence.
LLM should not calculate pillars, invent rules, or replace backend inference.
```

Current prompt context includes:

```text
chart
time_context
inference_context
knowledge_context
guardrails
```

Important improvement already made:

```text
For income_stability, prompt explicitly says:
Use only inference_context.income_stability signals and evidence_summary.
Do not replace it with generic ten-god explanation.
```

Current measured behavior:

```text
LLM chat-test: ~0.5s on configured remote node
Full Agent turn with LLM + knowledge + structure: ~15-21s depending on response length
```

---

## 8. DB / Storage

Files:

```text
v19/runtime.py
v19/knowledge_store.py
```

Current storage targets:

```text
v19_agent_sessions
v19_knowledge_units
```

Runtime files:

```text
v19/.runtime/settings.json
v19/.runtime/sessions.json
v19/.runtime/knowledge_units.json
```

Current DB features:

- DB bridge configurable from Admin.
- Local DB creation supported for localhost only.
- Session storage mirrors to file fallback.
- Knowledge storage mirrors to file fallback.
- Password/API key masking supported in Admin.

---

## 9. Frontend Design

Files:

```text
v19/frontend/index.html
v19/frontend/admin.html
v19/frontend/assets/app.js
v19/frontend/assets/admin.js
v19/frontend/assets/styles.css
```

Current UI mode:

```text
Dark mode
Standalone V19 visual identity
No V17 frontend dependency
```

Agent page sections:

```text
Birth Input
Runtime Status
Chart Structure
Luck Cycle
Flow Year
Income Stability
Knowledge Context
Agent Conversation
Trace JSON
```

Admin page sections:

```text
DB Bridge
LLM Node
Knowledge Base
```

---

## 10. Current Boundaries and Guardrails

### 10.1 Hard Boundaries

```text
No lunar input support yet.
No production-grade solar-term engine yet.
No final fortune prediction yet.
No traditional prediction text as system output.
No score output for income_stability.
No time-aware income_stability yet.
No direct V17 frontend dependency.
No unrestricted V17 plugin reuse.
```

### 10.2 P4 Time Boundary

Current P4 rule:

```text
Time structure is context only.
Flow year and luck cycle do not directly alter income_stability yet.
```

Correct future phase:

```text
P5: time-aware inference.
```

### 10.3 Wealth Boundary

Current wealth capability:

```text
income_stability structure signal only.
```

Not yet supported:

```text
wealth prediction
wealth timing
wealth amount
career-specific monetization path
traditional 财运 statement
```

---

## 11. Analyst Review Checklist

### 11.1 Chart Structure Review

Please review:

```text
Are four-pillar algorithms acceptable for prototype use?
Which parts are approximate and must be replaced before serious use?
What solar-term boundary rules are required?
What timezone / birthplace assumptions must be added?
How should lunar input be converted and validated?
```

### 11.2 Luck Cycle Review

Please review:

```text
Current luck cycle start age is approximate.
Direction uses year stem yin/yang + gender.
Start age calculation needs domain-grade 起运 algorithm.
Current active luck cycle is selected by selected_year - birth_year.
```

Questions:

```text
What exact 起运 calculation should V19 use?
Should start age be day-count-to-solar-term / 3?
How should gender and year polarity be handled across schools?
What metadata must be exposed to avoid false certainty?
```

### 11.3 Flow Year Review

Please review:

```text
Flow year pillar calculation.
Flow year relation detection with natal.
Whether three-harmony / six-combination / six-clash tables are sufficient for first pass.
Whether relation output should include pillar positions.
```

### 11.4 Income Stability Review

Current rule contract:

```text
income_stability = f(
  self_capacity,
  wealth_presence,
  wealth_accessibility,
  volatility,
  structure_binding
)
```

Please review:

```text
Are these five signals sufficient as first structure layer?
Should wealth_presence use visible stems only, hidden stems, or both?
Should branch main element be enough for prototype?
Should wealth accessibility count only relations touching wealth pillars?
Should volatility be all clashes, or only wealth-touching clashes?
Should structure_binding treat three-harmony as mixed, stable, or bound?
Should self_capacity be based on simple element balance or a fuller strength model?
```

Current rule mapping:

```text
wealth_presence none -> income_stability unstable
self_capacity low -> income_stability unstable
volatility high -> income_stability unstable
wealth_accessibility disrupted -> income_stability unstable
wealth_accessibility conflicted -> income_stability mixed
self_capacity high + volatility low -> income_stability stable
structure_binding present -> income_stability mixed
otherwise -> mixed
```

Analyst should approve, reject, or revise this mapping.

### 11.5 Knowledge Base Review

Please review:

```text
Are the 13 seed units safe as A-only foundational knowledge?
Should any be downgraded to draft?
Should source_refs be made more precise?
Should wealth.income_stability_rule_basis remain reviewed or require analyst review first?
Are any statements too broad or too modernized?
```

### 11.6 LLM Behavior Review

Please review:

```text
Does LLM output stay within evidence explanation?
Does it avoid fortune prediction when asked income_stability?
Does it clearly say income_stability is not wealth prediction?
Does it over-explain or introduce unsupported concepts?
Should final user-facing output be template-based instead of LLM-generated?
```

---

## 12. Known Risks

### 12.1 LLM Drift

Risk:

```text
LLM may turn evidence into narrative or prediction.
```

Mitigation already present:

```text
Prompt guardrails.
Structured inference_context.
Knowledge evidence guardrails.
Frontend trace visibility.
```

Recommended next mitigation:

```text
Use deterministic renderer for income_stability answer.
Let LLM only answer follow-up questions.
```

### 12.2 False Precision

Risk:

```text
Current four pillars, luck cycle start age, and strength model are prototype-grade.
```

Recommended mitigation:

```text
Expose algorithm status in UI.
Add analyst-approved calendar engine.
Add provenance per calculation.
```

### 12.3 Knowledge Pollution

Risk:

```text
Old V17/V18 plugins include many narrative and judgement rules.
Direct import could pollute V19 boundaries.
```

Current mitigation:

```text
Only A-only seed units are active.
V17/V18 assets are reference only.
```

Recommended mitigation:

```text
Create an analyst review queue before any new knowledge unit becomes reviewed.
```

---

## 13. Recommended Next Engineering Steps

### Step 1: Deterministic Income Stability Renderer

Add a backend renderer:

```text
income_stability explanation = deterministic template
LLM optional follow-up only
```

Reason:

```text
This prevents LLM from over-generalizing the rule basis.
```

### Step 2: Analyst Review Status for Knowledge Units

Add statuses:

```text
draft
analyst_review
reviewed
active_evidence
rejected
deprecated
```

### Step 3: Calendar / Solar Term Engine

Replace approximate chart timing with domain-grade calendar logic.

### Step 4: Time-Aware Inference P5

Only after P4 is stable:

```text
TimeContext -> Time-aware income_stability
```

Do not let flow year directly become fortune prediction.

### Step 5: Knowledge Admin Editing

Admin should eventually support:

```text
create unit
review unit
deprecate unit
show diff
show source refs
analyst comments
```

---

## 14. Current Review Verdict

Engineering status:

```text
Functional local Agent loop exists.
DB / LLM / Knowledge / Session plumbing exists.
Knowledge now enters Agent prompt.
First bounded income_stability adapter exists.
Frontend exposes structure, knowledge, inference, and trace.
```

Domain readiness:

```text
Not production-ready.
Ready for analyst review.
Ready for rule-basis correction.
Ready for knowledge governance review.
Not ready for public fortune prediction.
```

Most important analyst decision:

```text
Approve or revise income_stability signal design before expanding to more wealth rules.
```

Recommended review priority:

```text
1. Calendar / chart correctness
2. Luck cycle correctness
3. income_stability rule mapping
4. Knowledge seed wording
5. LLM answer boundaries
```
