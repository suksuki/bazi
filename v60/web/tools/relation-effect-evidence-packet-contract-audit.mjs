import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

import {
  buildRelationEffectEvidencePacketFixture,
  evidenceDecisionPath,
  evidenceDimensions,
  makeNotTriggeredEvidencePacketFixture,
  requiredProfessionalPath,
} from "./relation-effect-evidence-packet-contract-fixture.mjs";

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

let unsafeMutationCount = 0;
try {
  const { RelationEffectEvidencePacket } = await vite.ssrLoadModule(
    "/src/components/RelationEffectEvidencePacket.tsx",
  );
  const render = (fixture, mode) =>
    renderToStaticMarkup(
      React.createElement(RelationEffectEvidencePacket, {
        home: {
          mingli: {
            reading: fixture.bindings.reading,
            relation_effect_frontier: fixture.bindings.frontier,
            relation_effect_admission_review: fixture.review,
            relation_effect_evidence_packet: fixture.packet,
          },
          lab: fixture.bindings.lab,
        },
        mode,
      }),
    );

  const fixture = buildRelationEffectEvidencePacketFixture();
  const summary = render(fixture, "summary");
  const detailed = render(fixture, "detailed");

  for (const [mode, markup] of [
    ["summary", summary],
    ["detailed", detailed],
  ]) {
    for (const expected of [
      'data-packet-status="AVAILABLE"',
      `data-mode="${mode}"`,
      `data-packet-ref="${fixture.packet.packet_ref}"`,
      `data-packet-hash="${fixture.packet.packet_hash}"`,
      'data-llm-allowed="false"',
      'data-provider-invoked="false"',
      'data-reasoner-invoked="false"',
      'data-decision-request-created="false"',
      'data-owner-professional-review-invoked="false"',
      'data-knowledge-promotion-request-created="false"',
      'data-knowledge-admission-eligible="false"',
      'data-gate-invoked="false"',
      'data-ledger-invoked="false"',
      'data-decision-created="false"',
      'data-selection-authority="false"',
      'data-professional-verdict-allowed="false"',
      'data-canonical-write-allowed="false"',
      'data-read-only="true"',
      "规则证据包",
      "作用决策暂缓",
      "<b>0 / 6</b>规则证据",
      "<b>0</b>专业材料",
      "当前运行基底只能定位事实与缺口，不是专业证据",
      "Readiness projection · 不是 Decision",
      "LLM／Provider／Gate 均未调用",
      "作用与来源可用性 · UNRESOLVED",
    ]) {
      assertIncludes(`${mode}-available`, markup, expected);
    }
    for (const step of evidenceDecisionPath) {
      assertIncludes(`${mode}-decision-path`, markup, step);
    }
    for (const forbidden of [
      fixture.proposalClaim,
      "关系作用已确认",
      "来源已可用",
      "来源不可用已确认",
      "有效做功已确认",
      "专业规则已准入",
      "概率结论",
      "吉凶",
    ]) {
      assertExcludes(`${mode}-authority`, markup, forbidden);
    }
  }

  assertExcludes("summary-demand-hidden", summary, "data-demand-packet-ref=");
  assertExcludes("summary-slot-hidden", summary, "data-slot-ref=");
  assertExcludes(
    "summary-future-path-hidden",
    summary,
    "data-professional-path-step=",
  );
  assertEqual(
    "detailed-demand-count",
    (detailed.match(/data-demand-packet-ref=/g) ?? []).length,
    1,
  );
  assertEqual(
    "detailed-slot-count",
    (detailed.match(/data-slot-ref=/g) ?? []).length,
    6,
  );
  assertEqual(
    "detailed-ready-count",
    (detailed.match(/data-ready="false"/g) ?? []).length,
    6,
  );
  assertEqual(
    "detailed-professional-evidence-zero-count",
    (detailed.match(/data-professional-evidence-count="0"/g) ?? []).length,
    6,
  );
  for (const dimension of evidenceDimensions) {
    assertIncludes("detailed-dimension-order", detailed, dimension);
  }
  for (const step of requiredProfessionalPath) {
    assertIncludes("detailed-future-path", detailed, step);
  }
  for (const expected of [
    "未来专业权威路径",
    "尚未执行",
    "当前运行基底",
    "不是专业证据材料",
    "建议提交的材料类型",
    "已绑定专业材料",
    "0 项 · 尚无 professional evidence ref",
    "材料请求指南，不代表 Knowledge 已接受或准入",
    "当前 0 项专业材料",
    "新 Reading 资格化",
    "当前机制关注顺序",
  ]) {
    assertIncludes("detailed-proof", detailed, expected);
  }

  const clearFixture = makeNotTriggeredEvidencePacketFixture();
  const clearDetailed = render(clearFixture, "detailed");
  for (const expected of [
    'data-packet-status="AVAILABLE"',
    'data-effect-decision-status="NOT_TRIGGERED"',
    "当前未触发",
    "<b>0 / 0</b>规则证据",
    "<b>0</b>关系需求",
    "没有伪造空候选或作用结论",
  ]) {
    assertIncludes("not-triggered", clearDetailed, expected);
  }
  for (const forbidden of [
    "data-demand-packet-ref=",
    "data-slot-ref=",
    "专业规则维度",
    clearFixture.proposalClaim,
  ]) {
    assertExcludes("not-triggered-empty", clearDetailed, forbidden);
  }

  const unsafeCases = [
    ["packet-version", ({ packet }) => {
      packet.packet_version =
        "v60.mingli-relation-effect-evidence-packet.999";
    }],
    ["packet-ref", ({ packet }) => {
      packet.packet_ref = "packet-ref-drift";
    }],
    ["packet-hash-format", ({ packet }) => {
      packet.packet_hash = "not-a-hash";
    }],
    ["case-ref", ({ packet }) => {
      packet.case_ref = "case-ref-drift";
    }],
    ["chart-ref", ({ packet }) => {
      packet.chart_version_ref = "chart-ref-drift";
    }],
    ["reading-ref", ({ packet }) => {
      packet.reading_ref = "reading-ref-drift";
    }],
    ["reading-hash", ({ packet }) => {
      packet.reading_hash = "e".repeat(64);
    }],
    ["frontier-ref", ({ packet }) => {
      packet.frontier_ref = "frontier-ref-drift";
    }],
    ["frontier-hash", ({ packet }) => {
      packet.frontier_hash = "e".repeat(64);
    }],
    ["review-ref", ({ packet }) => {
      packet.admission_review_ref = "review-ref-drift";
    }],
    ["review-hash", ({ packet }) => {
      packet.admission_review_hash = "e".repeat(64);
    }],
    ["policy-ref", ({ packet }) => {
      packet.policy_ref = "policy-ref-drift";
    }],
    ["proposal-hash", ({ packet }) => {
      packet.proposal_hash = "e".repeat(64);
    }],
    ["lab-packet-ref", ({ bindings }) => {
      bindings.lab.relation_effect_evidence_packet_ref = "packet-ref-drift";
    }],
    ["lab-packet-hash", ({ bindings }) => {
      bindings.lab.relation_effect_evidence_packet_hash = "e".repeat(64);
    }],
    ["demand-count", ({ packet }) => {
      packet.demand_packet_count = 2;
    }],
    ["slot-count", ({ packet }) => {
      packet.required_dimension_slot_count = 5;
    }],
    ["ready-count", ({ packet }) => {
      packet.ready_dimension_slot_count = 1;
    }],
    ["professional-count", ({ packet }) => {
      packet.professional_evidence_count = 1;
    }],
    ["status", ({ packet }) => {
      packet.status = "NOT_TRIGGERED";
    }],
    ["decision-path-order", ({ packet }) => {
      packet.decision_path.reverse();
    }],
    ["decision-path-semantics", ({ packet }) => {
      packet.decision_path_semantics = "EFFECT_DECISION";
    }],
    ["future-path-order", ({ packet }) => {
      packet.required_professional_path.reverse();
    }],
    ["future-path-semantics", ({ packet }) => {
      packet.required_professional_path_semantics = "EXECUTED";
    }],
    ["effect-decision", ({ packet }) => {
      packet.effect_decision_status = "APPROVED";
    }],
    ["demand-hash", ({ packet }) => {
      packet.demand_packets[0].demand_packet_hash = "not-a-hash";
    }],
    ["assessment-ref", ({ packet }) => {
      packet.demand_packets[0].assessment_ref = "assessment-ref-drift";
    }],
    ["relation-fact-ref", ({ packet }) => {
      packet.demand_packets[0].relation_fact_ref = "relation-ref-drift";
    }],
    ["source-branch", ({ packet }) => {
      packet.demand_packets[0].source_branch = "子";
    }],
    ["dimension-order", ({ packet }) => {
      packet.demand_packets[0].dimension_slots.reverse();
    }],
    ["basis-drift", ({ packet }) => {
      packet.demand_packets[0].dimension_slots[0].current_basis_refs = [
        "professional-evidence-ref-forged",
      ];
    }],
    ["basis-as-professional", ({ packet }) => {
      const slot = packet.demand_packets[0].dimension_slots[0];
      slot.professional_evidence_refs = [...slot.current_basis_refs];
    }],
    ["professional-slot-count", ({ packet }) => {
      packet.demand_packets[0].dimension_slots[0].professional_evidence_count =
        1;
    }],
    ["slot-ready", ({ packet }) => {
      packet.demand_packets[0].dimension_slots[0].ready = true;
    }],
    ["basis-status", ({ packet }) => {
      packet.demand_packets[0].dimension_slots[0].current_basis_status =
        "PROFESSIONAL_EVIDENCE";
    }],
    ["requested-artifact", ({ packet }) => {
      packet.demand_packets[0].dimension_slots[0].requested_artifact_kinds = [
        "LLM_OUTPUT",
        "PROFESSIONAL_SOURCE_CITATION",
      ];
    }],
    ["guidance-semantics", ({ packet }) => {
      packet.demand_packets[0].dimension_slots[0].guidance_semantics =
        "KNOWLEDGE_ADMISSION";
    }],
    ["requirement", ({ packet }) => {
      packet.demand_packets[0].dimension_slots[0].requirement =
        "系统已确认关系作用。";
    }],
    ["next-action", ({ packet }) => {
      packet.demand_packets[0].dimension_slots[0].next_action =
        "自动创建 Decision。";
    }],
    ["unknown-packet-field", ({ packet }) => {
      packet.professional_effect_conclusion_secret =
        "SECRET-EFFECT-CONCLUSION";
    }],
    ["unknown-slot-field", ({ packet }) => {
      packet.demand_packets[0].dimension_slots[0].provider_confidence_secret =
        "SECRET-PROVIDER-CONFIDENCE";
    }],
  ];
  for (const field of [
    "knowledge_admission_eligible",
    "llm_allowed",
    "provider_invoked",
    "reasoner_invoked",
    "decision_request_created",
    "owner_professional_review_invoked",
    "knowledge_promotion_request_created",
    "gate_invoked",
    "ledger_invoked",
    "decision_created",
    "selection_authority",
    "professional_verdict_allowed",
    "probability_claim_allowed",
    "canonical_write_allowed",
  ]) {
    unsafeCases.push([`authority-${field}`, ({ packet }) => {
      packet[field] = true;
    }]);
  }
  unsafeCases.push(["read-only", ({ packet }) => {
    packet.read_only = false;
  }]);
  unsafeMutationCount = unsafeCases.length;

  for (const [label, mutate] of unsafeCases) {
    const unsafe = structuredClone(
      buildRelationEffectEvidencePacketFixture(),
    );
    mutate(unsafe);
    const markup = render(unsafe, "detailed");
    assertIncludes(
      `${label}-withheld`,
      markup,
      'data-packet-status="WITHHELD"',
    );
    assertIncludes(`${label}-boundary`, markup, "权限边界不完整");
    assertExcludes(
      `${label}-packet-identity-hidden`,
      markup,
      unsafe.packet.packet_ref,
    );
    assertExcludes(
      `${label}-demand-identity-hidden`,
      markup,
      unsafe.packet.demand_packets[0].demand_packet_ref,
    );
    assertExcludes(
      `${label}-secret-effect-hidden`,
      markup,
      "SECRET-EFFECT-CONCLUSION",
    );
    assertExcludes(
      `${label}-secret-provider-hidden`,
      markup,
      "SECRET-PROVIDER-CONFIDENCE",
    );
  }

  const styles = await readFile(
    path.join(
      webRoot,
      "src/styles/relation-effect-evidence-packet.css",
    ),
    "utf8",
  );
  for (const expected of [
    ".relation-effect-evidence-packet",
    ".relation-effect-evidence-counts",
    ".relation-effect-decision-path",
    ".relation-effect-future-path",
    ".relation-effect-evidence-slot",
    ".relation-effect-evidence-context-basis",
    ".relation-effect-evidence-packet.is-withheld",
  ]) {
    assertIncludes("styles", styles, expected);
  }

  const rail = await readFile(
    path.join(webRoot, "src/components/HomeCompanionRail.tsx"),
    "utf8",
  );
  assertIncludes("rail-stack", rail, "RelationEffectReviewStack");
  assertEqual("rail-line-budget", rail.split("\n").length - 1 <= 500, true);
} finally {
  await vite.close();
}

const report = {
  packet: {
    demandPackets: 1,
    readyDimensions: 0,
    requiredDimensions: 6,
    professionalEvidence: 0,
  },
  paths: {
    currentReadinessSteps: evidenceDecisionPath.length,
    futureAuthoritySteps: requiredProfessionalPath.length,
  },
  clearCaseDemandPackets: 0,
  unsafeMutationCount,
  authorityLeakage: failures.length ? "FAILED" : "NONE",
  failures,
};

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (failures.length > 0) process.exitCode = 1;
