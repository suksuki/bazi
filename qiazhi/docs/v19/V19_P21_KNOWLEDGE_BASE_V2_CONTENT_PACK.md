# V19 P21 Knowledge Base v2 Content Pack

## Decision

Yes, the knowledge base now needs new content, but the next content should not be patched into the old monolithic seed file. P21 opens a new pack-based path:

```text
docs/bazi_knowledge/packs/*_knowledge_draft_seeds_*.json
```

The existing seed file remains supported. New packs are loaded alongside it by the source archive seeder, then grouped into review batches.

## Pack

```text
docs/bazi_knowledge/packs/p21_guided_question_collision_knowledge_draft_seeds_v1.json
```

The pack contains 10 draft knowledge units:

- 6 R1 structure/question boundary drafts
- 4 R2 income/wealth collision drafts

The pack is based on:

- P11 synthetic collision matrix
- P19 chart-specific question ranking
- P20 guided question diversity audit

## Coverage

R1 drafts cover:

- guided-question diversity as an audit signal
- composite branch relation reading order
- natal/time layer disambiguation
- visible vs hidden ten-god evidence layers
- time relations as context only
- vault location before interpretation

R2 drafts cover:

- visible wealth signal under clash
- visible wealth signal under combination/binding
- output-to-wealth conversion path
- competition/constraint attribution in income stability

## Review Batches

P21 adds two batch seeds:

```text
p21.r1_guided_question_structure_boundaries
p21.r2_income_collision_review
```

The R1 batch can enter fast analyst review before proposal drafting. The R2 batch stays blocked before source/version review.

## Guardrails

- Draft only
- No active rule creation
- No runtime inference change
- No automatic question library change
- R2 remains blocked before analyst/source review
- Synthetic cases are test fixtures, not domain truth

## Analyst Need

No analyst is needed for the engineering step. Analyst review is needed before:

- marking drafts `proposal_ready`
- turning R2 content into rule proposals
- adding any P21 content to runtime reviewed evidence templates
- creating a governance release record
