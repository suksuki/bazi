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
const assertIncludes = (label, markup, expected) => {
  if (!markup.includes(expected)) failures.push(`${label}:missing:${expected}`);
};
const assertExcludes = (label, markup, forbidden) => {
  if (markup.includes(forbidden)) failures.push(`${label}:forbidden:${forbidden}`);
};

try {
  const { MechanismDecisionTrace } = await vite.ssrLoadModule(
    "/src/components/MechanismDecisionTrace.tsx",
  );
  const reading = {
    reading_ref: "reading:contract",
    decision_refs: [],
  };
  const qualification = {
    candidates: [],
  };
  const pendingExpectations = [
    {
      count: 0,
      kind: "NO_CANDIDATE",
      title: "当前没有可比较候选",
      copy: "当前真实命盘没有达到本版结构候选门槛",
    },
    {
      count: 1,
      kind: "SINGLE_CANDIDATE",
      title: "单条候选尚未记录顺序",
      copy: "尚未形成规则引擎 Decision",
    },
    {
      count: 2,
      kind: "MULTIPLE_CANDIDATES",
      title: "候选仍在并列核查",
      copy: "系统不会在页面里自行挑选",
    },
  ];

  for (const expectation of pendingExpectations) {
    const markup = renderToStaticMarkup(
      React.createElement(MechanismDecisionTrace, {
        comparison: {
          candidate_count: expectation.count,
          decision_ref: null,
          decision_hash: null,
          selected_candidate_ref: null,
          authority: null,
          status: "NOT_RUN",
          rationale_summary: null,
          evidence_refs_used: [],
          decision_trace: null,
        },
        mode: "mingli",
        qualification,
        reading,
      }),
    );
    const label = `pending-${expectation.count}`;
    assertIncludes(
      label,
      markup,
      `data-candidate-count="${expectation.count}"`,
    );
    assertIncludes(label, markup, `data-pending-kind="${expectation.kind}"`);
    assertIncludes(label, markup, expectation.title);
    assertIncludes(label, markup, expectation.copy);
  }

  const decisionRef = "decision:rule";
  const selectedCandidateRef = "candidate:rule";
  const ruleTrace = {
    trace_version: "v60.mingli-decision-trace.001",
    trace_integrity_status: "VERIFIED",
    decision_ref: decisionRef,
    decision_hash: "a".repeat(64),
    kernel_version: "v60.cognitive-decision-kernel.004",
    request_id: "request:rule",
    subject_ref: "vector:rule",
    authority: "RULE_ENGINE",
    status: "RESOLVED",
    route_reason: "one_qualified_candidate_remains",
    selected_candidate_ref: selectedCandidateRef,
    attention_candidate_refs: [selectedCandidateRef],
    reviewed_candidate_refs: [selectedCandidateRef],
    candidate_coverage_complete: true,
    candidate_coverage_semantics: "RULE_ENGINE_SINGLE_ATTENTION_CANDIDATE",
    bound_evidence_refs: ["evidence:rule"],
    evidence_refs_used: [],
    evidence_use_semantics: "REQUEST_BOUND_NOT_PROVIDER_USED",
    selected_evidence_bound: true,
    selected_evidence_use_semantics:
      "REQUEST_BOUND_RULE_NOT_PROVIDER_CITED",
    provider_counter_evidence_refs: [],
    proposal_ref: null,
    gate_receipt_ref: null,
    gate_version: null,
    gate_disposition: "NOT_REQUIRED",
    gate_reason: "single_attention_candidate_selected_by_rule_engine",
    decision_record_allowed: true,
    canonical_domain_write_allowed: false,
    reasoner_runtime_ref: null,
    provider_id: null,
    model_ref: null,
    model_profile_ref: null,
    model_profile_hash: null,
    prompt_ref: null,
    provider_response_ref: null,
    context_hash: null,
    attention_scope: "STATIC_NATAL_MECHANISM_CANDIDATE_PRIORITY_ONLY",
    admitted_input_scopes: ["MECHANISM_CANDIDATE_EVIDENCE"],
    unbound_input_scopes: [
      "SOURCE_USABILITY",
      "TIMING_ACTIVATION",
      "MECHANISM_QUALIFICATION",
      "PROFESSIONAL_ADMISSION",
      "CALIBRATION",
    ],
    counter_evidence_semantics:
      "BOUND_REF_ONLY_NOT_PROFESSIONALLY_ADMITTED",
    selection_rationale_contract:
      "DETERMINISTIC_SINGLE_CANDIDATE_ROUTE_REASON_ONLY",
    provider_confidence_semantics: "NOT_RECORDED_RULE_ENGINE_ROUTE",
    professional_selection_qualified: false,
    professional_verdict_allowed: false,
    probability_claim_allowed: false,
    read_only: true,
  };
  const ruleMarkup = renderToStaticMarkup(
    React.createElement(MechanismDecisionTrace, {
      comparison: {
        candidate_count: 1,
        decision_ref: decisionRef,
        decision_hash: ruleTrace.decision_hash,
        selected_candidate_ref: selectedCandidateRef,
        authority: "RULE_ENGINE",
        status: "RESOLVED",
        rationale_summary: null,
        evidence_refs_used: [],
        decision_trace: ruleTrace,
      },
      mode: "lab",
      qualification: {
        candidates: [
          {
            candidate_ref: selectedCandidateRef,
            pattern_label: "单候选结构",
            checks: [
              {
                dimension: "PROFESSIONAL_ADMISSION",
                label: "专业准入",
                status: "NOT_ADMITTED",
                meaning: "尚未准入。",
                next_evidence: "专业规则。",
              },
            ],
          },
        ],
      },
      reading: {
        reading_ref: "reading:rule",
        decision_refs: [decisionRef],
      },
    }),
  );
  for (const expected of [
    "规则引擎",
    "规则唯一候选",
    "规则未引用 Provider 证据",
    "所选证据已绑定 · 规则未引用",
    "固定的单候选路由原因",
    "规则引擎路线没有调用 Provider",
    "规则 Decision 已记录（无需 Gate）",
    "专业裁决未授权",
  ]) {
    assertIncludes("rule", ruleMarkup, expected);
  }
  for (const forbidden of [
    "Provider confidence 仅是未校准的原始记录",
    "Reasoner Decision 已通过 Gate 准入",
    "候选覆核",
    "所选证据已绑定并由 Provider 引用",
  ]) {
    assertExcludes("rule", ruleMarkup, forbidden);
  }
} finally {
  await vite.close();
}

if (failures.length) throw new Error(failures.join("\n"));
console.log(
  JSON.stringify(
    {
      pendingCandidateCounts: [0, 1, 2],
      ruleEngineRoute: "PASS",
      failures,
    },
    null,
    2,
  ),
);
