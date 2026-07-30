import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

import {
  buildClearRelationEffectEvidenceRequestFixture,
  buildEmptyRelationEffectEvidenceRequestFixture,
  buildRecordedRelationEffectEvidenceRequestFixture,
} from "./relation-effect-evidence-request-contract-fixture.mjs";

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
  const {
    RelationEffectEvidenceRequestControl,
    RelationEffectEvidenceRequestSummary,
  } = await vite.ssrLoadModule(
    "/src/components/RelationEffectEvidenceRequest.tsx",
  );
  const { RelationEffectEvidencePacket } = await vite.ssrLoadModule(
    "/src/components/RelationEffectEvidencePacket.tsx",
  );
  const { buildRelationEffectEvidenceRequestPayload } =
    await vite.ssrLoadModule(
      "/src/relationEffectEvidenceRequestApi.ts",
    );

  const homeFor = (fixture) => ({
    mingli: {
      reading: fixture.bindings.reading,
      relation_effect_frontier: fixture.bindings.frontier,
      relation_effect_admission_review: fixture.review,
      relation_effect_evidence_packet: fixture.packet,
      relation_effect_evidence_request_receipt:
        fixture.requestReceipt,
      relation_effect_evidence_materials: fixture.materials,
    },
    lab: fixture.bindings.lab,
  });
  const renderSummary = (fixture) =>
    renderToStaticMarkup(
      React.createElement(RelationEffectEvidenceRequestSummary, {
        home: homeFor(fixture),
      }),
    );
  const renderControl = (fixture) =>
    renderToStaticMarkup(
      React.createElement(RelationEffectEvidenceRequestControl, {
        home: homeFor(fixture),
        onChanged: async () => {},
      }),
    );
  const renderPacket = (fixture, mode) =>
    renderToStaticMarkup(
      React.createElement(RelationEffectEvidencePacket, {
        home: homeFor(fixture),
        mode,
        onEvidenceRequestChanged: async () => {},
      }),
    );

  const empty = buildEmptyRelationEffectEvidenceRequestFixture();
  const emptySummary = renderSummary(empty);
  const emptyDetailed = renderControl(empty);
  assertEqual("empty-summary-hidden", emptySummary, "");
  for (const expected of [
    'data-request-state="NOT_RECORDED"',
    'data-request-command="CREATE"',
    "登记补证准备请求",
    "0 材料 · 0 / 6",
    "不接收或生成任何材料",
    "不会启动专业审阅、Knowledge 准入、Gate",
  ]) {
    assertIncludes("empty-detailed", emptyDetailed, expected);
  }
  assertEqual(
    "empty-single-command",
    (emptyDetailed.match(/data-request-command=/g) ?? []).length,
    1,
  );
  for (const forbidden of [
    "<form",
    "<input",
    "<textarea",
    'type="file"',
    'type="url"',
  ]) {
    assertExcludes("empty-no-material-intake", emptyDetailed, forbidden);
  }

  const payload = buildRelationEffectEvidenceRequestPayload(
    empty.packet,
  );
  assertEqual(
    "payload-keys",
    JSON.stringify(Object.keys(payload)),
    JSON.stringify([
      "request_version",
      "expected_packet_ref",
      "expected_packet_hash",
      "idempotency_key",
    ]),
  );
  assertEqual(
    "payload-version",
    payload.request_version,
    "v60.mingli-relation-effect-evidence-request.001",
  );
  assertEqual(
    "payload-packet-ref",
    payload.expected_packet_ref,
    empty.packet.packet_ref,
  );
  assertEqual(
    "payload-packet-hash",
    payload.expected_packet_hash,
    empty.packet.packet_hash,
  );
  assertEqual(
    "payload-idempotency-deterministic",
    payload.idempotency_key,
    buildRelationEffectEvidenceRequestPayload(empty.packet)
      .idempotency_key,
  );
  assertEqual(
    "payload-idempotency-bounded",
    payload.idempotency_key.length <= 180,
    true,
  );

  const recorded = buildRecordedRelationEffectEvidenceRequestFixture();
  const recordedSummary = renderSummary(recorded);
  const recordedDetailed = renderControl(recorded);
  const integratedSummary = renderPacket(recorded, "summary");
  const integratedDetailed = renderPacket(recorded, "detailed");
  for (const markup of [recordedSummary, integratedSummary]) {
    for (const expected of [
      'data-request-state="RECORDED"',
      `data-receipt-ref="${recorded.requestReceipt.receipt_ref}"`,
      `data-receipt-hash="${recorded.requestReceipt.receipt_hash}"`,
      "补证准备请求已登记",
      "<b>0</b> 份未核验候选元数据",
      "<b>0 / 6</b> 就绪",
      "不是专业材料、专业证据、专业审阅或作用 Decision",
    ]) {
      assertIncludes("recorded-summary", markup, expected);
    }
  }
  for (const markup of [recordedDetailed, integratedDetailed]) {
    for (const expected of [
      'data-request-state="RECORDED"',
      'data-request-status="REQUEST_RECORDED_NOT_EVIDENCE"',
      'data-evidence-role="NOT_EVIDENCE"',
      'data-professional-material-count="0"',
      'data-professional-evidence-count="0"',
      'data-ready-dimension-slot-count="0"',
      "精确需求",
      "年柱 己 · 时柱午／月柱子",
      "0 专业材料、0 专业证据",
      "Owner 专业审阅、Knowledge 准入",
      "UNRESOLVED 状态",
    ]) {
      assertIncludes("recorded-detailed", markup, expected);
    }
    assertEqual(
      "recorded-six-slots",
      (markup.match(/data-requested-slot-ref=/g) ?? []).length,
      6,
    );
    assertEqual(
      "recorded-zero-ready-slots",
      (markup.match(/data-ready="false"/g) ?? []).length >= 6,
      true,
    );
    assertExcludes(
      "recorded-no-create-command",
      markup,
      'data-request-command="CREATE"',
    );
  }
  for (const slot of recorded.requestReceipt.request_items[0]
    .dimension_slots) {
    assertIncludes(
      `slot-${slot.dimension_id}-dimension`,
      recordedDetailed,
      `data-dimension-id="${slot.dimension_id}"`,
    );
    assertIncludes(
      `slot-${slot.dimension_id}-requirement`,
      recordedDetailed,
      slot.requirement,
    );
    assertIncludes(
      `slot-${slot.dimension_id}-action`,
      recordedDetailed,
      slot.next_action,
    );
  }
  for (const expected of [
    "<b>0 / 6</b>规则证据",
    "<b>0</b>专业材料",
    "作用与来源可用性 · UNRESOLVED",
  ]) {
    assertIncludes("packet-still-unresolved", integratedDetailed, expected);
  }

  const clear = buildClearRelationEffectEvidenceRequestFixture();
  assertEqual("clear-summary-hidden", renderSummary(clear), "");
  assertEqual("clear-control-hidden", renderControl(clear), "");
  const clearPacket = renderPacket(clear, "detailed");
  assertExcludes(
    "clear-no-request-command",
    clearPacket,
    'data-request-command="CREATE"',
  );
  assertExcludes(
    "clear-no-request-receipt",
    clearPacket,
    "补证准备请求已登记",
  );

  const unsafeCases = [
    ["receipt-version", (value) => {
      value.requestReceipt.receipt_version = "v60.invalid.999";
    }],
    ["receipt-hash", (value) => {
      value.requestReceipt.receipt_hash = "not-a-hash";
    }],
    ["case-ref", (value) => {
      value.requestReceipt.case_ref = "case-ref-drift";
    }],
    ["packet-ref", (value) => {
      value.requestReceipt.packet_ref = "packet-ref-drift";
    }],
    ["lab-ref", (value) => {
      value.bindings.lab.relation_effect_evidence_request_receipt_ref =
        "receipt-ref-drift";
    }],
    ["item-demand", (value) => {
      value.requestReceipt.request_items[0].demand_packet_ref =
        "demand-ref-drift";
    }],
    ["dimension-order", (value) => {
      value.requestReceipt.request_items[0].dimension_slots.reverse();
    }],
    ["requirement", (value) => {
      value.requestReceipt.request_items[0].dimension_slots[0].requirement =
        "SECRET-EFFECT-CONCLUSION";
    }],
    ["material-count", (value) => {
      value.requestReceipt.professional_material_count = 1;
    }],
    ["slot-ready", (value) => {
      value.requestReceipt.request_items[0].dimension_slots[0].ready =
        true;
    }],
    ["material-intake", (value) => {
      value.requestReceipt.material_intake_open = true;
    }],
    ["file-upload", (value) => {
      value.requestReceipt.file_upload_allowed = true;
    }],
    ["url-submission", (value) => {
      value.requestReceipt.url_submission_allowed = true;
    }],
    ["free-text", (value) => {
      value.requestReceipt.free_text_submission_allowed = true;
    }],
    ["unknown-field", (value) => {
      value.requestReceipt.secret_professional_verdict =
        "SECRET-PROFESSIONAL-VERDICT";
    }],
  ];
  for (const field of [
    "llm_allowed",
    "provider_invoked",
    "reasoner_invoked",
    "owner_professional_review_invoked",
    "knowledge_admission_eligible",
    "knowledge_write_allowed",
    "gate_invoked",
    "decision_request_created",
    "decision_created",
    "professional_verdict_allowed",
    "probability_claim_allowed",
    "effect_or_usability_write_allowed",
  ]) {
    unsafeCases.push([`authority-${field}`, (value) => {
      value.requestReceipt[field] = true;
    }]);
  }
  unsafeMutationCount = unsafeCases.length;
  for (const [label, mutate] of unsafeCases) {
    const unsafe = structuredClone(
      buildRecordedRelationEffectEvidenceRequestFixture(),
    );
    mutate(unsafe);
    const summary = renderSummary(unsafe);
    const detailed = renderControl(unsafe);
    for (const markup of [summary, detailed]) {
      assertIncludes(
        `${label}-withheld`,
        markup,
        'data-request-state="WITHHELD"',
      );
      assertIncludes(
        `${label}-boundary`,
        markup,
        "同源身份或权限边界不完整",
      );
      assertExcludes(
        `${label}-receipt-hidden`,
        markup,
        unsafe.requestReceipt.receipt_ref,
      );
      assertExcludes(
        `${label}-secret-conclusion-hidden`,
        markup,
        "SECRET-EFFECT-CONCLUSION",
      );
      assertExcludes(
        `${label}-secret-verdict-hidden`,
        markup,
        "SECRET-PROFESSIONAL-VERDICT",
      );
      assertExcludes(
        `${label}-no-command`,
        markup,
        'data-request-command="CREATE"',
      );
    }
  }

  const missingWithForgedLab =
    buildEmptyRelationEffectEvidenceRequestFixture();
  missingWithForgedLab.bindings.lab
    .relation_effect_evidence_request_receipt_ref = "forged-ref";
  const forgedMissing = renderControl(missingWithForgedLab);
  assertIncludes(
    "missing-forged-lab-withheld",
    forgedMissing,
    'data-request-state="WITHHELD"',
  );
  assertExcludes(
    "missing-forged-lab-no-command",
    forgedMissing,
    'data-request-command="CREATE"',
  );

  const componentSource = await readFile(
    path.join(
      webRoot,
      "src/components/RelationEffectEvidenceRequest.tsx",
    ),
    "utf8",
  );
  for (const forbidden of [
    "<form",
    "<input",
    "<textarea",
    'type="file"',
    'type="url"',
  ]) {
    assertExcludes("component-no-intake-control", componentSource, forbidden);
  }
  const styles = await readFile(
    path.join(
      webRoot,
      "src/styles/relation-effect-evidence-request.css",
    ),
    "utf8",
  );
  for (const expected of [
    ".relation-effect-evidence-request-summary",
    ".relation-effect-evidence-request",
    ".relation-effect-evidence-request-counts",
    ".relation-effect-evidence-request-items",
    ".relation-effect-evidence-request.is-withheld",
  ]) {
    assertIncludes("styles", styles, expected);
  }
  const rail = await readFile(
    path.join(webRoot, "src/components/HomeCompanionRail.tsx"),
    "utf8",
  );
  assertEqual("rail-line-budget", rail.split("\n").length - 1 <= 500, true);
} finally {
  await vite.close();
}

const report = {
  request: {
    emptyCommandCount: 1,
    recordedRequestItems: 1,
    requestedDimensions: 6,
    professionalMaterials: 0,
    readyDimensions: 0,
  },
  clearCaseCommandCount: 0,
  unsafeMutationCount,
  authorityLeakage: failures.length ? "FAILED" : "NONE",
  failures,
};

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (failures.length > 0) process.exitCode = 1;
