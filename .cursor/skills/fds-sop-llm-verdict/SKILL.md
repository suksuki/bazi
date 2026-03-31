---
name: fds-sop-llm-verdict
description: Captures the FDS SOPs for holographic LLM verdicts, Ollama/Qwen integration, streaming, and Chinese-only narrative. Use when editing core/fds_verdict_narrator.py, ui/pages/holographic_pattern.py LLM section, or system_config LLM settings.
---

# FDS LLM Verdict & Ollama Skill

## Scope

Use this skill when:

- Modifying `core/fds_verdict_narrator.py` (判词 prompt、流式输出、Qwen/Ollama 集成)。
- 修改 `ui/pages/holographic_pattern.py` 中的 LLM 判词展示区。
- 修改 `ui/pages/system_config.py` 中 LLM/Ollama 配置与测试逻辑。

目标：确保全息页 LLM 判词**稳定、中文、与物理证据/SOP 对齐**，并兼容 Qwen 3.5 + Ollama 的实际行为。

## Integration Rules (Ollama + Qwen 3.5)

1. **统一使用 chat 接口**
   - 判词与设置页测试都应使用：
     - `client.chat(model=..., messages=[...], ...)`
   - 不再使用 `generate()` 作为主路径。

2. **禁用思考流（thinking）输出**
   - 调用 chat 时优先传 `think=False`，关闭 thinking 流，让模型只把最终回答写入 `message.content`。
   - 代码中应使用类似模式：
     - 构造通用 kwargs，然后：
       - `client.chat(..., think=False)`，若抛 `TypeError`（老版本 ollama-python 不支持）再退化为不带 `think`。

3. **流式状态机**
   - 流式判词逻辑：
     - **只**从 `message.content` / `response` / `text` 读取正文。
     - **不**把 `thinking` / `reasoning_content` 当作判词展示。
     - 若 chunk 仅含 thinking 且 content 为空，只记调试日志，继续等待后续 content。
   - 只有当拿到非空 content 时才逐字输出到 UI。

4. **非流式兜底**
   - 若整轮流式没有任何 content（`emitted=False`）：
     - 再发一次 **非流式** chat 请求（同样优先带 `think=False`）。
     - 尝试从完整响应中提取正文（content/text/body）。
     - 仍然为空时，允许用 thinking 兜底展示，但要加清晰中文说明前缀，提示这只是思考过程。

5. **错误信息与调试**
   - 当模型未返回可见文本时：
     - UI 应显示友好中文提示，并附带**首个 chunk 的关键信息**（类型、d_keys、message_keys 等），便于后续调整解析逻辑。
   - 不向终端用户暴露复杂的 Python 异常堆栈；只显示高层原因与简单引导（检查 Ollama、模型是否就绪等）。

## Prompt & Narrative SOP

1. **语言锁定（中文优先权）**
   - System/Prompt 顶部必须明确：
     - 第一反应、逻辑演进、最终批导**全部**使用简体中文。
     - 严禁在判词正文中使用英文句子；必要的英文术语可嵌在中文语境中，但不鼓励。
   - 同时要求：若模型内部存在“思考过程 + 正文”的双路输出，两者也都应使用简体中文。

2. **三层 Prompt 结构**
   - 物理证据层（Evidence Layer）
     - 主权格局、状态（PURE/VERIFIED/DRIFTING/BROKEN → 中文化）、D_M、匹配度、5D 坐标、岁运/地域。
   - 古典原典与判例（RAG Layer）
     - RAG 返回的原文/判例如有，要求 LLM 至少引用或转译 1 条，与当前物理状态呼应。
   - 叙事生成指令（Narrative Layer）
     - 结构：原局格局 → 当前时空状态 → 风险与张力 → 走向与建议。
     - 风格：冷静、可带诗意，不煽情。
     - 限制：不得给出绝对化吉凶预言。

3. **输出格式范式**
   - 判词正文统一使用三个小节：
     - `【格局定性】`：以“君之命局法理以……为主权”等句式开门见山。
     - `【气象分析】`：描述当前大运/流年/地域下的张力与风险。
     - `【岁运建议】`：以一两句总结性的建议收束。

4. **与 SOP V7.7 的对齐**
   - 叙事中需体现：
     - 逻辑定性（格局是否成立）与能量成色（high/mid/low）的区分。
     - 当成色偏低时，用“格局虽成，然根基尚浅，需步步为营”等弹性语句。
     - 对 `structural_rescue`（成败救应）的加分叙事，如“杀印相生”、“财官双美”等。

## System Config Page Expectations

1. **LLM 配置区（天机设置页）**
   - 清楚说明：
     - 当前选择的对话模型将用于「全息格局」页的 LLM 判词。
     - 系统会要求模型以简体中文输出。
     - 若选用 Qwen 3.5 等思考模型，系统会用 `think=False` 调用，直接输出正文。

2. **验证模型响应（测试）按钮**
   - 测试逻辑应模拟真实判词调用：
     - 使用 `chat` 接口，发送简短中文提示。
     - 优先传 `think=False`，兼容不支持该参数的旧版本。
     - 从 `message.content` 或 `response` 中抽取文本，显示简洁的中文响应预览。

## Quick Checklist

在修改 LLM 判词/配置相关代码时，请确认：

- [ ] 使用 `client.chat` 而非 `generate` 作为主路径。
- [ ] 判词调用与配置页测试统一为“简体中文 + think=False（若支持）”。
- [ ] 流式解析只展示 content，不展示 thinking；必要时用非流式兜底。
- [ ] 错误提示为清晰简体中文，并包含最小必要的调试信息。
- [ ] Prompt 中包含三层结构与【格局定性/气象分析/岁运建议】输出范式。

