import path from "node:path";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const here = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(here, "..");
const vite = await createServer({
  root: webRoot,
  appType: "custom",
  logLevel: "silent",
  server: { middlewareMode: true },
});

const failures = [];
const fail = (message) => failures.push(message);
const assertIncludes = (label, value, expected) => {
  if (!value.includes(expected)) fail(`${label}:missing:${expected}`);
};
const assertExcludes = (label, value, forbidden) => {
  if (value.includes(forbidden)) fail(`${label}:forbidden:${forbidden}`);
};
const assertEqual = (label, actual, expected) => {
  if (actual !== expected) {
    fail(
      `${label}:expected:${JSON.stringify(expected)}:actual:${JSON.stringify(actual)}`,
    );
  }
};

const requiredDimensions = [
  "APPLICABILITY_CONTEXT",
  "EFFECT_DIRECTION",
  "COMPLETION_CONDITIONS",
  "BLOCKING_CONDITIONS",
  "COUNTER_EVIDENCE",
  "PROFESSIONAL_PROVENANCE",
];
const demand = (index, dependencyStatus) => ({
  demand_ref: `demand-ref-${index}`,
  carrier_ref: `carrier-ref-${index}`,
  visible_slot: index === 1 ? "year" : "month",
  visible_stem: index === 1 ? "己" : "丙",
  source_review_ref: `source-review-ref-${index}`,
  source_evidence_ref: `source-evidence-ref-${index}`,
  intersection_ref: `intersection-ref-${index}`,
  relation_fact_ref: `relation-fact-ref-${index}`,
  relation_type: "six_clash_membership",
  source_match_kind:
    dependencyStatus === "SCOPE_INVARIANT_RULE_DEMAND"
      ? "EXACT_IDENTITY"
      : "SAME_ELEMENT_DIFFERENT_IDENTITY",
  source_slot: "year",
  source_branch: "巳",
  peer_slot: "month",
  peer_branch: "亥",
  scope_presence:
    dependencyStatus === "SCOPE_INVARIANT_RULE_DEMAND"
      ? ["EXACT_IDENTITY_ONLY", "ELEMENT_AFFINITY_INCLUDED"]
      : ["ELEMENT_AFFINITY_INCLUDED"],
  dependency_status: dependencyStatus,
  required_rule_dimensions: requiredDimensions,
  effect_status: "UNRESOLVED",
  usability_status: "UNRESOLVED",
  selection_authority: false,
});
const frontier = {
  frontier_ref: "frontier-ref-visible",
  frontier_hash: "a".repeat(64),
  frontier_version: "v60.mingli-relation-effect-research-frontier.001",
  case_ref: "case-ref-secret",
  chart_version_ref: "chart-ref-secret",
  reading_ref: "reading-ref-secret",
  reading_hash: "b".repeat(64),
  source_review_vector_ref: "source-vector-ref-secret",
  source_review_vector_hash: "c".repeat(64),
  prerequisite_ref: "prerequisite-ref-secret",
  prerequisite_hash: "d".repeat(64),
  refusal_receipt_ref: "refusal-ref-secret",
  refusal_receipt_hash: "e".repeat(64),
  demands: [
    demand(1, "SCOPE_INVARIANT_RULE_DEMAND"),
    demand(2, "MATCH_SCOPE_RULE_FIRST"),
    demand(3, "MATCH_SCOPE_RULE_FIRST"),
  ],
  demand_count: 3,
  scope_invariant_rule_demand_count: 1,
  match_scope_rule_first_count: 2,
  admitted_effect_rule_count: 0,
  research_semantics: "MEMBERSHIP_DEPENDENCY_AND_RULE_GAPS_ONLY",
  source_discussion_disposition: "ABSTAIN",
  effect_status: "UNRESOLVED",
  usability_status: "UNRESOLVED",
  provider_invoked: false,
  decision_created: false,
  gate_invoked: false,
  selection_authority: false,
  professional_verdict_allowed: false,
  probability_claim_allowed: false,
  canonical_write_allowed: false,
  read_only: true,
  reasoner_rationale_secret: "reasoner-rationale-secret",
  provider_confidence_secret: "0.999-provider-confidence-secret",
  professional_effect_conclusion_secret: "effect-conclusion-secret",
};

try {
  const { RelationEffectResearchFrontier } = await vite.ssrLoadModule(
    "/src/components/RelationEffectResearchFrontier.tsx",
  );
  const summary = renderToStaticMarkup(
    React.createElement(RelationEffectResearchFrontier, {
      frontier,
      mode: "summary",
    }),
  );
  const detailed = renderToStaticMarkup(
    React.createElement(RelationEffectResearchFrontier, {
      frontier,
      mode: "detailed",
    }),
  );

  for (const [mode, markup] of [
    ["summary", summary],
    ["detailed", detailed],
  ]) {
    for (const expected of [
      `data-mode="${mode}"`,
      'data-source-discussion="ABSTAIN"',
      'data-provider-invoked="false"',
      'data-decision-created="false"',
      'data-gate-invoked="false"',
      'data-selection-authority="false"',
      'data-professional-verdict-allowed="false"',
      'data-probability-claim-allowed="false"',
      'data-canonical-write-allowed="false"',
      "关系作用规则需求",
      "研究顺序，不是结论",
      "只决定先补哪类规则",
      "关系作用与来源可用性仍为",
      "UNRESOLVED",
      "未创建 Decision",
    ]) {
      assertIncludes(`${mode}-contract`, markup, expected);
    }
    for (const forbidden of [
      "reasoner-rationale-secret",
      "0.999-provider-confidence-secret",
      "effect-conclusion-secret",
      "可用根",
      "有效做功",
      "吉凶",
      "概率结论",
      "作用已成立",
      "专业结论已准入",
    ]) {
      assertExcludes(`${mode}-authority`, markup, forbidden);
    }
  }

  assertExcludes("summary-demand-details", summary, "demand-ref-1");
  assertEqual(
    "detailed-demand-count",
    (detailed.match(/data-demand-ref=/g) ?? []).length,
    3,
  );
  assertEqual(
    "scope-invariant-count",
    (detailed.match(/SCOPE_INVARIANT_RULE_DEMAND/g) ?? []).length,
    1,
  );
  assertEqual(
    "match-scope-first-count",
    (detailed.match(/MATCH_SCOPE_RULE_FIRST/g) ?? []).length,
    2,
  );
  for (const dimension of requiredDimensions) {
    assertIncludes("detailed-rule-dimension", detailed, dimension);
  }
  for (const expected of [
    "跨两种口径共现",
    "仅宽口径出现",
    "年柱 · 己",
    "六冲成员",
    "六维规则缺口",
  ]) {
    assertIncludes("detailed-visible-proof", detailed, expected);
  }
} finally {
  await vite.close();
}

if (failures.length) throw new Error(failures.join("\n"));
console.log(
  JSON.stringify(
    {
      counts: {
        scopeInvariant: 1,
        matchScopeFirst: 2,
        admittedEffectRule: 0,
      },
      ruleDimensions: requiredDimensions,
      authorityLeakage: "NONE",
      failures,
    },
    null,
    2,
  ),
);
