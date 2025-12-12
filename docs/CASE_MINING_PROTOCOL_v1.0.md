# 八字案例挖掘协议 (Bazi Case Mining Protocol)

**版本**: V1.0  
**代号**: Crimson Vein (深红矿脉)  
**目标**: 构建高质量、可验证的八字案例库，用于物理内核参数回归。

---

## 1. 数据质量分级 (Data Quality Tiers)

我们只收录 **Tier A** 和 **Tier B** 的数据。

### 🥇 Tier A: 黄金级 (Gold Standard)
- **出生信息**: 必须包含 年、月、日、**时** (精确到时辰)。
- **性别**: 明确。
- **反馈验证**: 必须包含至少 **3个** 已验证的人生关键节点 (如：2015结婚、2018生子、2020升职)。
- **来源**: 论坛反馈贴、擂台贴、经过考证的名人传记。

### 🥈 Tier B: 白银级 (Silver Standard)
- **出生信息**: 包含 年、月、日。时辰可推测或不确定。
- **性别**: 明确。
- **反馈验证**: 必须包含至少 **5个** 公开的人生大事件 (用于反推时柱或校正六字)。
- **来源**: 名人百科、公开履历。

### 🚫 Tier C: 废矿 (Discard)
- **出生信息**: 只有年月日。
- **事件**: 模糊不清 (“前几年运气不好”)，无具体年份。
- **来源**: 合成数据、AI生成内容、无反馈的求测贴。

---

## 2. 标准数据结构 (Standard JSON Schema)

所有挖掘出的案例必须清洗为以下 JSON 格式：

```json
{
  "id": "CASE_HASH_ID",
  "source_url": "https://...",
  "quality_tier": "A",
  "profile": {
    "name": "匿名/姓名",
    "gender": "M/F",
    "birth_year": 1990,
    "birth_month": 5,
    "birth_day": 20,
    "birth_hour": 14,
    "birth_city": "Shanghai"   // 可选，用于真太阳时校正
  },
  "chart": {
    "year_pillar": "庚午",
    "month_pillar": "辛巳",
    "day_pillar": "丙xh",
    "hour_pillar": "乙未"
  },
  "life_events": [
    {
      "year": 2015,
      "age": 25,
      "event_type": "Marriage",  // 结婚, 生子, 升职, 破财, 意外, etc.
      "description": "领证结婚",
      "verified": true
    },
    {
      "year": 2018,
      "event_type": "CareerPromotion",
      "description": "提拔为部门经理"
    }
  ],
  "tags": ["身旺", "伤官驾杀", "离婚案例"]
}
```

---

## 3. 挖掘策略 (Mining Strategy)

1.  **聚焦文本 (Text-First)**: 优先抓取长文本分析贴，利用 LLM (Gemini) 提取其中的结构化信息。
2.  **交叉验证 (Cross-Validation)**: 对于 Tier B 名人数据，需爬取多个源进行出生时间比对。
3.  **隐私脱敏 (Privacy)**: 对于论坛普通人案例，必须去除用户名、头像等隐私信息，只保留八字和事件。

---

**生效日期**: 2025-12-12
