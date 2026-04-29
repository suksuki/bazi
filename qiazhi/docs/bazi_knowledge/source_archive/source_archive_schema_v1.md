# V19 八字资料来源库 Schema v1

日期：2026-04-29

状态：draft

用途：定义八字资料来源入库格式。该 Schema 只记录资料来源，不生成知识单元，不生成规则，不影响推理。

## 1. Source Record

```ts
interface BaziSourceRecord {
  source_id: string
  title: string
  source_type:
    | 'classical_text'
    | 'classical_commentary'
    | 'legacy_v17_v18'
    | 'modern_reference'
    | 'practitioner_note'
    | 'web_reference'
    | 'library_record'
    | 'pdf_scan'
  author_or_compiler?: string
  period?: string
  language: 'zh' | 'en' | 'ko' | 'mixed'
  url?: string
  local_path?: string
  access_note?: string
  license_note?: string
  reliability: 'high' | 'medium' | 'low' | 'unknown'
  source_priority: 'primary' | 'secondary' | 'tertiary'
  knowledge_scope: string[]
  risk_level: 'R0' | 'R1' | 'R2' | 'R3' | 'R4'
  allowed_usage: string[]
  forbidden_usage: string[]
  ingestion_status: 'cataloged' | 'queued' | 'excerpting' | 'draft_units_created' | 'deprecated'
  notes?: string
}
```

## 2. 风险等级

```text
R0：基础事实
R1：结构关系
R2：机制解释
R3：格局 / 用神 / 综合判断
R4：象义 / 盲派 / 神煞 / 断语 / 案例
```

## 3. 入库边界

允许：

```text
记录来源
记录目录
记录知识范围
记录风险等级
记录可用/禁用范围
```

禁止：

```text
直接生成 active rule
直接改变 inference
直接输出 fortune
直接复制现代版权书籍全文
未经审核将网络文章作为权威
```

## 4. Source 到 Rule 的唯一合法链路

```text
Source Record
→ Excerpt Record
→ Knowledge Unit Draft
→ Rule Knowledge Proposal
→ Schema Validation
→ Analyst/Admin Review
→ Version Record
→ Future Active Rule
```
