import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

import { buildRelationEffectAdmissionFixture } from "./relation-effect-admission-contract-fixture.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(here, "..");
const vite = await createServer({
  root: webRoot,
  appType: "custom",
  logLevel: "silent",
  server: { middlewareMode: true },
});

const failures = [];
let unsafeMutationCount = 0;
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

try {
  const { RelationEffectAdmissionReview } = await vite.ssrLoadModule(
    "/src/components/RelationEffectAdmissionReview.tsx",
  );
  const render = (fixture, mode) =>
    renderToStaticMarkup(
      React.createElement(RelationEffectAdmissionReview, {
        home: {
          mingli: {
            reading: fixture.bindings.reading,
            relation_effect_frontier: fixture.bindings.frontier,
            relation_effect_admission_review: fixture.review,
          },
          lab: fixture.bindings.lab,
        },
        mode,
      }),
    );

  const fixture = buildRelationEffectAdmissionFixture();
  const summary = render(fixture, "summary");
  const detailed = render(fixture, "detailed");

  for (const [mode, markup] of [
    ["summary", summary],
    ["detailed", detailed],
  ]) {
    for (const expected of [
      'data-review-status="AVAILABLE"',
      `data-mode="${mode}"`,
      'data-disposition="REJECTED_PRE_ADMISSION"',
      `data-review-ref="${fixture.review.review_ref}"`,
      `data-review-hash="${fixture.review.review_hash}"`,
      `data-frontier-ref="${fixture.bindings.frontier.frontier_ref}"`,
      `data-frontier-hash="${fixture.bindings.frontier.frontier_hash}"`,
      'data-provider-invoked="false"',
      'data-owner-professional-review-invoked="false"',
      'data-knowledge-promotion-request-created="false"',
      'data-gate-invoked="false"',
      'data-decision-created="false"',
      'data-selection-authority="false"',
      'data-professional-verdict-allowed="false"',
      'data-probability-claim-allowed="false"',
      'data-canonical-write-allowed="false"',
      'data-read-only="true"',
      "自动受损捷径审查",
      "<b>1</b>审查",
      "<b>0</b>准入",
      "<b>2</b>等待口径",
      "拒绝的是捷径，不是否定关系作用",
      "作用状态 · UNRESOLVED",
      "来源可用性 · UNRESOLVED",
      "未创建 Decision",
    ]) {
      assertIncludes(`${mode}-available`, markup, expected);
    }
    for (const forbidden of [
      "关系作用已确认",
      "来源已可用",
      "来源不可用已确认",
      "有效做功已确认",
      "概率结论",
      "吉凶",
    ]) {
      assertExcludes(`${mode}-authority`, markup, forbidden);
    }
  }

  assertExcludes("summary-proposal-hidden", summary, fixture.proposalClaim);
  assertExcludes("summary-assessment-hidden", summary, "data-assessment-ref=");
  for (const expected of [
    fixture.proposalClaim,
    "具体捷径",
    "拒绝预准入",
    "候选的真假没有被判定",
    "三种竞争解释",
    "全部 HELD · 没有选择",
    "六维准入状态",
    "0 / 6 满足",
    fixture.review.review_ref,
    fixture.review.review_hash,
    fixture.review.assessments[0].assessment_ref,
    fixture.review.assessments[0].assessment_hash,
    fixture.review.policy_ref,
    fixture.review.policy_hash,
    fixture.review.proposal_ref,
    fixture.review.proposal_hash,
    "没有创建作用原子",
  ]) {
    assertIncludes("detailed-proof", detailed, expected);
  }
  assertEqual(
    "detailed-held-count",
    (detailed.match(/data-status="HELD"/g) ?? []).length,
    3,
  );
  assertEqual(
    "detailed-held-selected-count",
    (detailed.match(/data-selected="false"/g) ?? []).length,
    3,
  );
  assertEqual(
    "detailed-dimension-count",
    (detailed.match(/data-dimension-id=/g) ?? []).length,
    6,
  );
  assertEqual(
    "detailed-satisfied-count",
    (detailed.match(/data-satisfied="false"/g) ?? []).length,
    6,
  );
  for (const dimension of fixture.dimensions) {
    assertIncludes("detailed-dimension-order", detailed, dimension);
  }

  const notTriggered = buildRelationEffectAdmissionFixture();
  notTriggered.review.review_ref = "review-ref-not-triggered";
  notTriggered.review.review_hash = "a".repeat(64);
  notTriggered.review.assessments = [];
  notTriggered.review.reviewed_demand_count = 0;
  notTriggered.review.rejected_pre_admission_count = 0;
  notTriggered.review.unreviewed_scope_invariant_demand_refs = [
    notTriggered.targetDemandRef,
  ];
  notTriggered.review.disposition = "NOT_TRIGGERED";
  notTriggered.bindings.lab.relation_effect_admission_review_ref =
    notTriggered.review.review_ref;
  notTriggered.bindings.lab.relation_effect_admission_review_hash =
    notTriggered.review.review_hash;
  const notTriggeredDetailed = render(notTriggered, "detailed");
  assertIncludes(
    "not-triggered-available",
    notTriggeredDetailed,
    'data-review-status="AVAILABLE"',
  );
  assertIncludes("not-triggered-copy", notTriggeredDetailed, "未触发");
  assertIncludes(
    "not-triggered-empty",
    notTriggeredDetailed,
    "没有适用坐标",
  );
  assertExcludes(
    "not-triggered-proposal-hidden",
    notTriggeredDetailed,
    fixture.proposalClaim,
  );

  const unsafeCases = [
    ["review-version", ({ review }) => {
      review.review_version = "v60.mingli-relation-rule-admission-review.999";
    }],
    ["review-frontier-ref", ({ review }) => {
      review.frontier_ref = "frontier-ref-drift";
    }],
    ["review-reading-hash", ({ review }) => {
      review.reading_hash = "b".repeat(64);
    }],
    ["review-case-ref", ({ review }) => {
      review.case_ref = "case-ref-drift";
    }],
    ["review-count", ({ review }) => {
      review.reviewed_demand_count = 2;
    }],
    ["review-disposition", ({ review }) => {
      review.disposition = "NOT_TRIGGERED";
    }],
    ["deferred-order", ({ review }) => {
      review.deferred_match_scope_demand_refs.reverse();
    }],
    ["frontier-match-demand-order", ({ review }) => {
      review.frontier_match_scope_demand_refs.reverse();
    }],
    ["frontier-scope-demand-drift", ({ review }) => {
      review.frontier_scope_invariant_demand_refs = ["demand-ref-drift"];
    }],
    ["classification-overlap", ({ review }) => {
      review.unreviewed_scope_invariant_demand_refs = [
        review.deferred_match_scope_demand_refs[0],
      ];
    }],
    ["lab-review-ref", ({ bindings }) => {
      bindings.lab.relation_effect_admission_review_ref = "review-ref-drift";
    }],
    ["lab-review-hash", ({ bindings }) => {
      bindings.lab.relation_effect_admission_review_hash = "c".repeat(64);
    }],
    ["lab-frontier-ref", ({ bindings }) => {
      bindings.lab.relation_effect_frontier_ref = "frontier-ref-drift";
    }],
    ["lab-reading-ref", ({ bindings }) => {
      bindings.lab.reading_ref = "reading-ref-drift";
    }],
    ["reading-read-only", ({ bindings }) => {
      bindings.reading.read_only = false;
    }],
    ["frontier-admitted-count", ({ bindings }) => {
      bindings.frontier.admitted_effect_rule_count = 1;
    }],
    ["frontier-demand-count", ({ bindings }) => {
      bindings.frontier.demand_count = 4;
    }],
    ["frontier-source-discussion", ({ bindings }) => {
      bindings.frontier.source_discussion_disposition = "ALLOW";
    }],
    ["frontier-version", ({ bindings }) => {
      bindings.frontier.frontier_version =
        "v60.mingli-relation-effect-research-frontier.999";
    }],
    ["frontier-semantics", ({ bindings }) => {
      bindings.frontier.research_semantics = "EFFECT_CONCLUSION";
    }],
    ["assessment-proposal-ref", ({ review }) => {
      review.assessments[0].proposal_ref = "proposal-ref-drift";
    }],
    ["assessment-demand-ref", ({ review }) => {
      review.assessments[0].demand_ref = "demand-ref-drift";
    }],
    ["assessment-effect-atom", ({ review }) => {
      review.assessments[0].admitted_effect_atom_refs = ["effect-atom-secret"];
    }],
    ["interpretation-selected", ({ review }) => {
      review.assessments[0].interpretations[0].selected = true;
    }],
    ["interpretation-effect-atom", ({ review }) => {
      review.assessments[0].interpretations[1].effect_atom_created = true;
    }],
    ["dimension-satisfied", ({ review }) => {
      review.assessments[0].dimension_assessments[0].satisfied = true;
    }],
    ["reverse-zi-wu-demand", ({ bindings }) => {
      const demand = bindings.frontier.demands[0];
      [demand.source_branch, demand.peer_branch] = [
        demand.peer_branch,
        demand.source_branch,
      ];
    }],
    ["unknown-assessment-field", ({ review }) => {
      review.assessments[0].provider_confidence_secret = "0.999";
    }],
  ];
  const reviewFalseBoundaries = [
    "provider_invoked",
    "owner_professional_review_invoked",
    "knowledge_promotion_request_created",
    "gate_invoked",
    "decision_created",
    "selection_authority",
    "professional_verdict_allowed",
    "probability_claim_allowed",
    "canonical_write_allowed",
  ];
  for (const field of reviewFalseBoundaries) {
    unsafeCases.push([`review-boundary-${field}`, ({ review }) => {
      review[field] = true;
    }]);
  }
  unsafeCases.push(["review-boundary-read-only", ({ review }) => {
    review.read_only = false;
  }]);
  const frontierFalseBoundaries = [
    "provider_invoked",
    "decision_created",
    "gate_invoked",
    "selection_authority",
    "professional_verdict_allowed",
    "probability_claim_allowed",
    "canonical_write_allowed",
  ];
  for (const field of frontierFalseBoundaries) {
    unsafeCases.push([`frontier-boundary-${field}`, ({ bindings }) => {
      bindings.frontier[field] = true;
    }]);
  }
  unsafeCases.push(["frontier-boundary-read-only", ({ bindings }) => {
    bindings.frontier.read_only = false;
  }]);
  unsafeMutationCount = unsafeCases.length;

  for (const [label, mutate] of unsafeCases) {
    const unsafe = structuredClone(buildRelationEffectAdmissionFixture());
    const secretProposal = `SECRET-PROPOSAL-${label}`;
    unsafe.review.assessments[0].proposal_claim = secretProposal;
    mutate(unsafe);
    const markup = render(unsafe, "detailed");
    assertIncludes(
      `${label}-withheld`,
      markup,
      'data-review-status="WITHHELD"',
    );
    assertIncludes(`${label}-boundary`, markup, "权限边界不完整");
    assertExcludes(`${label}-secret-hidden`, markup, secretProposal);
    assertExcludes(
      `${label}-identity-hidden`,
      markup,
      unsafe.review.assessments[0].assessment_ref,
    );
  }

  const styles = await readFile(
    path.join(webRoot, "src/styles/relation-effect-admission-review.css"),
    "utf8",
  );
  for (const expected of [
    ".relation-effect-admission-review",
    ".relation-effect-admission-counts",
    ".relation-effect-held-interpretations",
    ".relation-effect-admission-dimensions",
    ".relation-effect-admission-identity",
    ".relation-effect-admission-review.is-withheld",
  ]) {
    assertIncludes("styles", styles, expected);
  }
} finally {
  await vite.close();
}

const report = {
  summary: { reviewed: 1, admitted: 0, deferredMatchScope: 2 },
  interpretations: { held: 3, selected: 0, effectAtoms: 0 },
  dimensions: { reviewed: 6, satisfied: 0 },
  displayStates: ["AVAILABLE", "NOT_TRIGGERED", "WITHHELD"],
  unsafeMutationCount,
  proposalLeakageOnWithheld: "NONE",
  failures,
};

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (failures.length > 0) process.exitCode = 1;
