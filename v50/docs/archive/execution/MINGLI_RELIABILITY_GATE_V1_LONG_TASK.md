# Mingli Reliability Gate v1

Status: implementation complete; professional blind test pending

Final audit:

- [Master report](../../../reports/mingli-reliability-gate-v1/MINGLI_RELIABILITY_GATE_V1_REPORT.md)
- [Machine-readable report](../../../reports/mingli-reliability-gate-v1/MINGLI_RELIABILITY_GATE_V1_REPORT.json)

## Product promise

DeepBazi may withhold a Mingli conclusion, but it must not submit a conclusion
that the system already knows conflicts with the chart, loses its baseline, or
collapses competing interpretations into false certainty.

This slice freezes new product features. It changes only the authority and
delivery rules for the existing whole-chart and on-demand domain experience.

## User-visible outcomes

Every cognition run ends in exactly one state:

1. `reliable`
   - The whole-chart center, primary path, conditions, counter-signals, and
     uncertainty passed fact and evidence review.
   - The result may be committed to the Life Case.
2. `competing`
   - Two interpretations remain professionally plausible.
   - Both explanations and the information needed to distinguish them remain
     visible, but no formal baseline is committed.
3. `blocked`
   - A hard fact, evidence, semantic consistency, or safety error remains.
   - Deterministic chart facts remain visible; no formal insight or cognitive
     belief is committed.

## Authority rules

- A Review error is commit-blocking. No downstream adapter may downgrade it.
- Deterministic locked-fact repair may correct a provable wording error before
  Review. The repaired output must be reviewed again and the repair must remain
  traceable.
- Completeness and expression issues may remain warnings. They cannot turn a
  blocked result into a reliable result.
- A competing interpretation is not an error and must not be flattened into a
  single confident answer.
- Legacy records without a reliability disposition are not eligible for new
  domain commits until their baseline is recomputed.

## Strategy dimensions

The public and professional contracts must not use one flat "useful god" list.
Each strategy statement declares one question it answers:

- `climate`: climate regulation / 调候
- `support_balance`: support and restraint / 扶抑
- `structure`: structure success or failure / 格局
- `transformation`: control and transformation / 制化与通关
- `work_path`: conditions required by the main work path / 做功
- `timing`: current temporal strategy / 岁运
- `domain`: a domain-specific condition, never a replacement for the baseline

`mixed` is never commit-eligible because it hides which question is being
answered.

## Domain inheritance

An on-demand domain result must carry:

- baseline insight id;
- baseline record id;
- case version;
- baseline semantic signature;
- request fingerprint.

A cache hit is valid only when all of these inputs and the normalized user
question match. A domain result may extend the baseline. It may not silently
replace its selected hypothesis or main work path.

If the domain output explicitly requires a different whole-chart baseline, the
result becomes a `case_revision_candidate`; it is not committed as a domain
insight until a new baseline is compared and reviewed.

## Verification matrix

### Machine tests

- A Review hard error cannot become `passed=true` downstream.
- Formal Insight validation rejects `blocked`, `competing`, and legacy review
  states.
- A reliable baseline can commit.
- A competing baseline remains recoverable but uncommitted.
- A blocked baseline preserves chart facts and retry actions.
- Domain insight commit requires the exact current baseline reference.
- Same baseline + domain + question reuses the result.
- A changed question, baseline, case version, or timing signature recomputes.
- Domain baseline override produces a revision candidate.

### Small professional stability run

Use four charts, including one deliberately disputed chart. Run each baseline
five independent times and compare:

- structural center;
- selected and competing hypotheses;
- primary work path;
- success and failure conditions;
- strategy by dimension;
- uncertainty and disposition.

Wording differences are ignored. Unexplained opposite direction within the
same dimension is a release blocker.

### Performance measurements

Record separately:

- chart-ready time;
- first meaningful preview time;
- full draft time;
- formal commit time;
- domain first preview time;
- domain completion time;
- exact-request cache reuse time.

## Non-goals

- No new life domain.
- No Daily, narrative theater, relative profiles, or new UI navigation.
- No large benchmark expansion.
- No relaxed validator to make pass rates look better.
- No replacement of specific Mingli reasoning with templates.

## Definition of done

The slice is complete only when real artifacts demonstrate all three states,
domain inheritance is visible, a known hard conflict cannot enter Life Case,
and the five-run comparison exposes rather than hides any remaining drift.
