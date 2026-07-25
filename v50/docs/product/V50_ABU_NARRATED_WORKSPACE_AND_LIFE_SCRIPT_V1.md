# V50 Abu Narrated Workspace & Life Script v1

## 0. Frozen Product Principle

> 页面先到，声音随后；结论一眼可见，阿布负责讲深。

DeepLife 的语音能力不是播客播放器，也不取代页面。它把同一份正式命理认知投影成四种同步表达：

```text
Formal Insight
├── Readable Projection   页面文字
├── Narration Projection  阿布语音
├── Visual Projection     四柱 / 路径 / 条件高亮
└── Evidence Entry        来源与专业依据
```

页面、声音和动画不得各自形成不同命理结论。用户关闭声音后，正式信息不能缺失。

## 1. Product Experience

### Scan

- 默认静音；
- 页面摘要、四柱、主路径、成立条件和不确定性立即可读；
- TTS 不参与页面首屏可用性。

### Abu Narration

- 用户主动点击 `听阿布讲`；
- 阿布按短段讲解整盘重心、主路径、关键条件和未决部分；
- 当前段落驱动页面锚点高亮；
- 用户可以暂停、继续、结束或跳到指定段落；
- 点击页面中的四柱、路径或条件，可以从对应段落开始讲。

### Long-term Modes

本合同预留精简讲解、专业讲解、剧场 / Live，但 v1 只实现 `看见命局 · standard`。未实现的模式不得提前包装为现有能力。

## 2. Authority Boundary

```text
LifeCase.baseline_insight (committed)
        ↓
NarrationManifest (deterministic projection)
        ↓
SpeechAsset (Qwen TTS expression asset)
        ↓
Page / Abu bubble / audio / visual anchors
```

Narration Compiler 可以：

- 选择正式断言；
- 加入听觉过渡语；
- 按完整句子分段；
- 绑定页面锚点；
- 绑定视觉 Cue。

Narration Compiler 不可以：

- 重新看盘；
- 调用 LLM 产生新结论；
- 改写 LifeCase；
- 删除条件或不确定性；
- 把竞争假设说成事实。

## 3. Contracts

### NarrationManifest

每个 Manifest 绑定：

```text
Case
Chart Version
LifeCase Version
Formal Insight
Narration Script Version
Language
Voice ID / Voice Version
```

硬约束：

```yaml
autoplay: false
page_available_without_audio: true
scope: participant_private
```

每个 `NarrationSegment` 必须包含：

```text
source_claim_refs
source_refs
visual_anchor_ids
visual_cues
```

### SpeechAsset

`SpeechAsset` 是版本化、不可变、案例私有的表达资产。缓存键覆盖：

```text
Case / Chart / LifeCase Version
Claim refs / Source refs / Source text hash
Script Version
Language
Voice / TTS Model Version
Pronunciation Lexicon
Speaking Style / Speed
```

相同版本重复播放不得再次调用 TTS。正式认知、脚本、声线或模型版本变化时生成新资产，旧资产不被静默覆盖。

## 4. Implemented Slice

### API

```text
GET  /api/v50/narration/cases/{case_id}/baseline
POST /api/v50/narration/cases/{case_id}/baseline/segments/{segment_id}
GET  /api/v50/narration/cases/{case_id}/audio/{speech_asset_id}
GET  /api/v50/narration/cases/{case_id}/audio/{speech_asset_id}/opus
```

`GET manifest` 不调用 TTS。只有用户主动播放缺失段落时，`POST segment` 才生成语音。

### Page Anchors

```text
baseline-summary
baseline-pillar-0..3
baseline-work-path
baseline-condition
baseline-uncertainty
```

Guest / Member 不读取完整专业 `work_path`。服务器只投影 `public_work_path` 中已经获批的路径陈述、可读转换步骤与体用说明；事实 ID、证据引用和研究字段仍留在专业模式。旧案例缺少该公开字段时，页面只允许从同一 `baseline_insight` 的推理路径兜底，不调用新推理。

### Playback

- 当前段按需生成；
- 播放开始后只预取下一段；
- 浏览器阻止播放时，音频保持 ready，等待用户再次点击；
- 切页、换案例或用户结束时停止播放并清除高亮；
- `prefers-reduced-motion` 下保留语义高亮，取消脉冲和位移动画。

## 5. TTS Capacity Evidence

2026-07-18 对 `http://127.0.0.1:17860` 的 Qwen TTS 隧道使用 4 组纯合成命理台词，分别测试并发 1 / 2 / 4，共 12 个请求：

```text
passed: 12 / 12
error: 0
```

| 并发 | RTF p50 | RTF p95 | 首包 p95 |
|---:|---:|---:|---:|
| 1 | 0.5623 | 0.5740 | 19.99s |
| 2 | 1.1509 | 1.4107 | 36.67s |
| 4 | 2.1943 | 3.0195 | 56.54s |

解释：

- 单并发稳定；
- 当前 HTTP 服务整段返回 WAV，不是真正的流式首帧；
- 并发增加时延迟近似排队增长；
- 主页面必须坚持文字先到、语音缓存和受控预取；
- 当前不适合同时为一个用户并发生成全部段落；
- WAV 约 2.8 MB / 分钟，正式规模化前应增加 Opus/AAC 播放资产。

完整数据：

- `reports/qwen-tts-capacity-v1/qwen_tts_capacity_v1.json`
- `reports/qwen-tts-capacity-v1/QWEN_TTS_CAPACITY_V1.md`

### Capacity v2 And Opus Follow-up

`Abu Voice & Comprehension Validation v1` 已补充并发 8、完整生成时间、失败率和 Opus 派生。16/16 合成请求成功，但未缓存首包 p95 为 `87.0772s`，并发 1 首包 p95 也为 `20.5231s`。因此页面提交后预生成和缓存优先仍是发布硬要求；不能把即时 TTS 放进页面首屏阻塞路径。

完整数据：

- `reports/qwen-tts-capacity-v2/qwen_tts_capacity_v2.json`
- `reports/qwen-tts-capacity-v2/QWEN_TTS_CAPACITY_V2.md`
- `docs/product/V50_ABU_VOICE_COMPREHENSION_VALIDATION_V1.md`

## 6. Life Script Direction

“人生剧本”不是新的命理大脑，而是 LifeCase 的开放叙事投影：

```text
Formal Insight
→ LifeScript Projection
→ Story Beats
→ Performance Cue
→ Abu Theater
```

剧本由以下内容组成：

```text
人物底色
核心矛盾
主运行路径
当前章节
成立条件
开放分支
用户选择
现实反馈
```

必须避免：

- 把人生写成固定结局；
- 为戏剧性制造灾难；
- 隐藏不确定性；
- 编造用户未提供的人生经历；
- 让用户选择改写命盘事实。

建议的下一条个人体验是《我的命局序章》，但它在本轮只冻结方向，尚未实现。应在同步论命的理解效果和语音容量通过人工体验验证后再制作。

## 7. Validation

自动验证覆盖：

- Manifest 只读取已提交 LifeCase；
- GET 不调用 TTS；
- SpeechAsset 缓存命中不重复生成；
- 声线版本变化产生新资产；
- 私人案例与音频拒绝未授权访问；
- 页面默认静音；
- 页面锚点与声音双向定位；
- reduced-motion；
- JavaScript / Python 静态检查；
- 产品全量回归。

2026-07-18 验收结果：

```text
targeted tests: 55 passed
full regression: 302 passed
desktop browser: passed at 1440 × 900
mobile browser: passed at 390 × 844
mobile horizontal overflow: false
live Qwen TTS: generated and played
chapter jump: passed
page anchor highlight: passed
pause / continue / stop: passed
```

真实浏览器验收同时发现并修复两项发布问题：静态资源版本号未更新导致浏览器复用旧页面；公开角色未携带安全的主路径投影，导致声音能讲、页面没有对应锚点。两项都已加入回归合同。

Internal v1 当时尚未完成用户理解度 A/B、Eric 命理术语人工听审，以及生产级 Opus/AAC 派生与音频删除策略；这些不得被写成已经通过。

后续更新：生产级私有 Opus 派生、理解度实验合同、结构化播放事件和 Eric 12 条审听语料已经实现；定向回归 `10 passed`、全量回归 `308 passed`。真人 A/B 与人工听审仍未发生。当前状态为 `machine_ready_human_pending`，不得进入《我的命局序章》Prototype。

本轮状态边界：

```yaml
training_performed: false
weights_modified: false
brain_logic_modified: false
mingli_algorithm_modified: false
life_case_modified: false
llm_used_for_narration: false
tts_used: true
autoplay_enabled: false
narrated_workspace_v1: implemented
life_script_runtime: not_implemented
```
