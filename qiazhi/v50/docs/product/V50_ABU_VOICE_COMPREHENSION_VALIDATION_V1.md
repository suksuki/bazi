# V50 Abu Voice & Comprehension Validation v1

## 0. Status

```yaml
machine_validation_infrastructure: ready
real_user_comprehension_validation: pending
abu_voice_profile: candidate_pending_human_review
production_uncached_tts: not_release_ready
life_script_prototype: not_authorized
```

> 页面先到，语音后开；文字与语音同源；语音分段、可中断、可定位。

本阶段不增加 Reasoner、命理结论或页面模块。它只验证阿布同步论命是否真的提高理解、是否值得长期收听，以及语音服务能否以合理等待和成本运行。

## 1. Authority And Privacy

```text
Committed LifeCase / Formal Insight
        ↓
NarrationManifest
        ↓
NarrationSegment
        ↓
WAV source + private Opus playback asset
        ↓
Page anchor / subtitle / Abu voice
```

硬边界：

- 页面与语音读取同一份已提交认知；
- TTS 只生成声音，不生成命理判断；
- 语音不得删除条件、不确定性或替换页面结论；
- 实验事件只记录操作类型、段落、等待时间与播放位置；
- 理解度实验不保存出生资料或原始对话；
- 私人音频继续通过账户与案例权限读取，不进入公共静态目录。

## 2. Human Comprehension Study

### Sample

第一轮使用 `12–20` 名内部或小范围真实用户，每组至少 `6` 份完成人工评分的有效记录：

```text
Arm A: text_only
Arm B: text_and_abu_voice
```

分组由系统稳定分配。管理员仅能在内部研究 URL 中强制分组用于 QA；普通用户不能选择分组。

内部入口：

```text
/?voice_study=1
/?voice_study=1&voice_arm=text_only
/?voice_study=1&voice_arm=text_and_abu_voice
```

该入口不会出现在正式页面导航中。

### Participant Tasks

用户完成同一份正式 `看见命局` 后，用自己的话回答：

1. 整盘重心是什么；
2. 主路径从哪里开始、如何作用、走向哪里；
3. 这条判断成立的关键条件；
4. 系统仍未确定的部分；
5. 一个自然追问；
6. 疲劳度、专业信任变化和长期收听意愿。

### Analyst Scoring

分析师依据原始 Formal Insight 对前四项分别按 `0–2` 评分，并单独记录页面锚点任务是否完成。机器不根据关键词自动宣布用户“听懂”。

建议的进入下一阶段门槛：

```text
有效人工评分记录 >= 12
每组有效记录 >= 6
语音组四项理解总分中位数 > 文字组
语音组“成立条件 + 不确定性”不低于文字组
语音组疲劳度中位数 <= 3 / 5
语音组长期收听意愿中位数 >= 3 / 5
页面与语音新增命理结论 = 0
```

小样本只用于产品裁决，不包装成统计学或临床结论。

## 3. Structured Interaction Evidence

实验记录以下结构化事件：

```text
workspace_viewed
narration_requested
audio_ready
playback_started
playback_paused
playback_resumed
playback_stopped
chapter_jump
chapter_replayed
narration_completed
comprehension_opened
comprehension_submitted
```

每条事件可包含：

```text
segment_id
elapsed_since_session_ms
playback_position_ms
request_wait_ms
cache_hit
```

不记录：

```text
出生日期 / 时间 / 地点
姓名
原始聊天内容
命盘全文
自由输入原文之外的隐式画像
```

理解度回答属于私人研究资料，与匿名操作事件分开保存；提交后锁定，分析师评分也单独锁定。

## 4. Abu Voice Corpus v1

当前声线：

```yaml
voice: Eric
profile: abu-eric-candidate.v1
status: candidate_pending_human_review
```

语料覆盖：

- 亲切开场；
- 专业判断；
- 保留不确定性；
- 干支、十神、调候、扶抑、做功、大运、流年、流月等术语；
- 长期陪伴；
- 数字与日期。

已生成 `12` 条人工审听音频，但没有任何一条被机器标记为“发音通过”。人工必须逐条评估发音、重音、停顿、确定性等级、播音腔风险、儿童腔风险和两分钟连续收听适配度。

审听包：

- `reports/abu-voice-review-v1/ABU_VOICE_REVIEW_PACKET_V1.md`
- `reports/abu-voice-review-v1/abu_voice_review_packet_v1.json`

完成审听前，不冻结 Abu Voice ID、Voice Prompt、Lexicon 或 Voice Version。

## 5. SpeechAsset And Opus

正式播放资产采用：

```text
Qwen TTS WAV / PCM source
        ↓
ffmpeg libopus
        ↓
Ogg Opus, 48 kbps VBR, voip profile
```

`SpeechAsset` 同时保存 WAV source 和可选的 Opus playback variant。Opus 转码失败时可以继续播放受保护的 WAV，但不得把失败伪装成 Opus 成功。

缓存键新增 `playback_codec_profile`。以下任一内容变化都产生新资产：

```text
LifeCase / claim source
Narration script
Voice profile / TTS model
Pronunciation lexicon
Speaking style / speed
Playback codec profile
```

私有 Opus 端点：

```text
GET /api/v50/narration/cases/{case_id}/audio/{speech_asset_id}/opus
```

## 6. Capacity Evidence v2

2026-07-18 使用合成命理文本对 Qwen TTS 进行并发 `1 / 2 / 4 / 8` 测试：

```text
requests: 16
passed: 16
errors: 0
```

| 并发 | RTF p50 | 首包 p95 | 完成 p95 |
|---:|---:|---:|---:|
| 1 | 0.5633 | 20.5231s | 20.7031s |
| 2 | 1.2965 | 46.5077s | 46.6798s |
| 4 | 2.2446 | 59.1377s | 59.3017s |
| 8 | 3.9118 | 98.0706s | 98.2479s |

Opus 中位大小约 `336,978.5 bytes / audio minute`；本轮审听包的 Opus 总量约为 WAV 的 `11.69%`。

结论：

- 当前服务生成可靠，但冷启动首句不适合成为页面阻塞路径；
- LifeCase 提交后后台预生成、短段缓存和已有资产优先播放是发布硬要求；
- 用户点击缓存语音时才应接近即时播放；
- 当前服务整段返回 WAV，报告中的 first packet 不是真正流式语音首帧；
- 服务端 generation header 可能包含排队时间，因此 queue estimate 只作为观察值。

容量报告：

- `reports/qwen-tts-capacity-v2/QWEN_TTS_CAPACITY_V2.md`
- `reports/qwen-tts-capacity-v2/qwen_tts_capacity_v2.json`

## 7. Implemented API

```text
POST /api/v50/narration/validation/sessions
POST /api/v50/narration/validation/sessions/{session_id}/events
POST /api/v50/narration/validation/sessions/{session_id}/comprehension
GET  /api/v50/narration/validation/sessions/{session_id}
POST /api/v50/narration/validation/sessions/{session_id}/analyst-review
GET  /api/v50/narration/validation/summary
GET  /api/v50/narration/validation/review-packet
```

分析师审阅包隐藏实验分组、行为事件和出生资料，只提供 Case ID、正式讲解段落与参与者复述，避免被机器状态锚定。

## 8. Machine Validation Result

浏览器在登录态下验证：

```text
desktop: 1280 × 720, no horizontal overflow
mobile: 390 × 844, no horizontal overflow
assigned arm: text_and_abu_voice
narration: four segments completed
structured events: persisted
first live segment request wait: 14.771s
subsequent prepared segments: near-immediate
private Opus variants: generated
```

本轮一度出现静态前端已更新、Python 后端仍是旧进程的 `404`。重启服务后验证路由、实验会话和播放链全部恢复；这属于部署原子性问题，不是理解度实验或数据库合同失败。

## 9. Product Decision Boundary

当前允许：

- 内部运行文字 / 语音理解度对照；
- 人工审听 Eric；
- 预生成和缓存私人语音；
- 收集最小结构化播放事件。

当前不允许宣称：

- 语音已经提高理解；
- Eric 已是正式品牌声线；
- 冷启动 TTS 已达到生产首句体验；
- 《我的命局序章》已经获准实施。

只有真人理解度、人工声线审听和缓存首句体验均通过后，才进入《我的命局序章》Prototype。

