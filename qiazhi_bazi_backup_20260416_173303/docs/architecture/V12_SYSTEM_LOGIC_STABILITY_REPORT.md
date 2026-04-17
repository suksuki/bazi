# V12 系统逻辑稳定性报表

- 生成时间: `2026-04-14T08:03:04.418808+00:00`
- 样本数: `10`
- REJECT 总次数: `6`

## 逐案明细

| Case | 标签 | AuditState | ReasonCode | REJECT | AssertionNodes |
|---|---|---|---|---:|---:|
| C01 | 从强倾向（金水寒凝） | REJECT | LIG_RETRY_EXHAUSTED | 1 | 7 |
| C02 | 从弱倾向（木火重压） | PASS | PASS | 0 | 4 |
| C03 | 五行中和（平衡盘） | REJECT | LIG_RETRY_EXHAUSTED | 1 | 5 |
| C04 | 官杀混杂（高冲突） | REJECT | LIG_RETRY_EXHAUSTED | 1 | 5 |
| C05 | 财多身弱（负载测试） | REJECT | LIG_RETRY_EXHAUSTED | 1 | 6 |
| C06 | 印旺比劫（守成偏好） | FLAG | LIG_AMBIGUOUS_NARRATIVE | 0 | 7 |
| C07 | 子午冲显性（情感宫波动） | FLAG | LIG_AMBIGUOUS_NARRATIVE | 0 | 7 |
| C08 | 辰戌冲（土库冲开） | REJECT | LIG_RETRY_EXHAUSTED | 1 | 5 |
| C09 | 三合趋向（木局候选） | FLAG | LIG_AMBIGUOUS_NARRATIVE | 0 | 5 |
| C10 | 金木交战（极端对冲） | REJECT | LIG_RETRY_EXHAUSTED | 1 | 7 |

## 结论

- 全链路已跑通：`AnalyzeClash -> FinalVerdict -> BrainHub Audit -> AssertionTree`。
- 本报表可作为 V12.1 稳定核心的内测基线输入。

## 原始 JSON

```json
[
  {
    "case_id": "C01",
    "label": "从强倾向（金水寒凝）",
    "audit_state": "REJECT",
    "reason_code": "LIG_RETRY_EXHAUSTED",
    "reject_count": 1,
    "assertion_nodes": 7
  },
  {
    "case_id": "C02",
    "label": "从弱倾向（木火重压）",
    "audit_state": "PASS",
    "reason_code": "PASS",
    "reject_count": 0,
    "assertion_nodes": 4
  },
  {
    "case_id": "C03",
    "label": "五行中和（平衡盘）",
    "audit_state": "REJECT",
    "reason_code": "LIG_RETRY_EXHAUSTED",
    "reject_count": 1,
    "assertion_nodes": 5
  },
  {
    "case_id": "C04",
    "label": "官杀混杂（高冲突）",
    "audit_state": "REJECT",
    "reason_code": "LIG_RETRY_EXHAUSTED",
    "reject_count": 1,
    "assertion_nodes": 5
  },
  {
    "case_id": "C05",
    "label": "财多身弱（负载测试）",
    "audit_state": "REJECT",
    "reason_code": "LIG_RETRY_EXHAUSTED",
    "reject_count": 1,
    "assertion_nodes": 6
  },
  {
    "case_id": "C06",
    "label": "印旺比劫（守成偏好）",
    "audit_state": "FLAG",
    "reason_code": "LIG_AMBIGUOUS_NARRATIVE",
    "reject_count": 0,
    "assertion_nodes": 7
  },
  {
    "case_id": "C07",
    "label": "子午冲显性（情感宫波动）",
    "audit_state": "FLAG",
    "reason_code": "LIG_AMBIGUOUS_NARRATIVE",
    "reject_count": 0,
    "assertion_nodes": 7
  },
  {
    "case_id": "C08",
    "label": "辰戌冲（土库冲开）",
    "audit_state": "REJECT",
    "reason_code": "LIG_RETRY_EXHAUSTED",
    "reject_count": 1,
    "assertion_nodes": 5
  },
  {
    "case_id": "C09",
    "label": "三合趋向（木局候选）",
    "audit_state": "FLAG",
    "reason_code": "LIG_AMBIGUOUS_NARRATIVE",
    "reject_count": 0,
    "assertion_nodes": 5
  },
  {
    "case_id": "C10",
    "label": "金木交战（极端对冲）",
    "audit_state": "REJECT",
    "reason_code": "LIG_RETRY_EXHAUSTED",
    "reject_count": 1,
    "assertion_nodes": 7
  }
]
```
