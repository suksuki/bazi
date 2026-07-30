import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

import {
  buildClearRelationEffectEvidenceMaterialFixture,
  buildEmptyRelationEffectEvidenceMaterialFixture,
  buildNoRequestRelationEffectEvidenceMaterialFixture,
  buildRecordedRelationEffectEvidenceMaterialFixture,
} from "./relation-effect-evidence-material-contract-fixture.mjs";

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
const expectThrow = (label, callback) => {
  try {
    callback();
    fail(`${label}:did-not-throw`);
  } catch {
    // Expected fail-closed rejection.
  }
};

let unsafeMutationCount = 0;
try {
  const { RelationEffectEvidenceMaterialControl } =
    await vite.ssrLoadModule(
      "/src/components/RelationEffectEvidenceMaterial.tsx",
    );
  const { RelationEffectEvidenceRequestSummary } =
    await vite.ssrLoadModule(
      "/src/components/RelationEffectEvidenceRequest.tsx",
    );
  const {
    buildRelationEffectEvidenceMaterialPayload,
  } = await vite.ssrLoadModule(
    "/src/relationEffectEvidenceMaterialApi.ts",
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
  const renderControl = (fixture) =>
    renderToStaticMarkup(
      React.createElement(RelationEffectEvidenceMaterialControl, {
        home: homeFor(fixture),
        onChanged: async () => {},
      }),
    );
  const renderSummary = (fixture) =>
    renderToStaticMarkup(
      React.createElement(RelationEffectEvidenceRequestSummary, {
        home: homeFor(fixture),
      }),
    );

  const empty = buildEmptyRelationEffectEvidenceMaterialFixture();
  const emptyMarkup = renderControl(empty);
  for (const expected of [
    'data-candidate-material-count="0"',
    'data-effect-decision-status="WITHHELD"',
    'data-evidence-role="NOT_EVIDENCE"',
    'data-professional-material-count="0"',
    'data-professional-evidence-count="0"',
    'data-ready-dimension-slot-count="0"',
    'data-candidate-kind="BIBLIOGRAPHIC_COORDINATE_CANDIDATE"',
    'data-target-artifact-kind="PROFESSIONAL_SOURCE_MANIFEST"',
    'data-material-command="CREATE"',
    'name="title"',
    'name="responsible_party"',
    'name="edition_or_publication_identity"',
    'name="locator"',
    "未核验候选书目元数据",
    "0</b>专业材料",
    "0 / 6</b>专业证据就绪",
    "不接收文件、URL、引文正文、非结构化备注或专业结论",
    "不产生该产物",
    "作用 Decision 继续 WITHHELD",
  ]) {
    assertIncludes("empty-recorded-receipt", emptyMarkup, expected);
  }
  assertEqual(
    "one-provenance-form",
    (emptyMarkup.match(/data-material-command=/g) ?? []).length,
    1,
  );
  assertEqual(
    "four-structured-inputs",
    (emptyMarkup.match(/<input/g) ?? []).length,
    4,
  );
  for (const forbidden of [
    "<textarea",
    "<select",
    'type="file"',
    'type="url"',
    "content_sha256",
    "declared_content_sha256",
    'name="artifact_kind"',
    'name="target_artifact_kind"',
  ]) {
    assertExcludes("structured-only-form", emptyMarkup, forbidden);
  }

  const bibliography = {
    title: "  候选书目题名  ",
    responsible_party: "示例责任者",
    edition_or_publication_identity: "第一版 · 示例出版方",
    locator: "卷一 · 第 20 页",
  };
  const payload = buildRelationEffectEvidenceMaterialPayload(
    empty.requestReceipt,
    empty.requestReceipt.request_items[0],
    empty.requestReceipt.request_items[0].dimension_slots.find(
      (slot) => slot.dimension_id === "PROFESSIONAL_PROVENANCE",
    ),
    bibliography,
  );
  assertEqual(
    "payload-keys",
    JSON.stringify(Object.keys(payload)),
    JSON.stringify([
      "material_request_version",
      "expected_receipt_ref",
      "expected_receipt_hash",
      "expected_packet_ref",
      "expected_packet_hash",
      "expected_request_item_ref",
      "expected_demand_packet_ref",
      "expected_demand_packet_hash",
      "expected_slot_ref",
      "candidate_kind",
      "target_artifact_kind",
      "bibliography",
      "idempotency_key",
    ]),
  );
  assertEqual(
    "bibliography-keys",
    JSON.stringify(Object.keys(payload.bibliography)),
    JSON.stringify([
      "title",
      "responsible_party",
      "edition_or_publication_identity",
      "locator",
    ]),
  );
  assertEqual(
    "payload-version",
    payload.material_request_version,
    "v60.mingli-relation-effect-evidence-material-request.001",
  );
  assertEqual(
    "payload-request-item",
    payload.expected_request_item_ref,
    empty.requestReceipt.request_items[0].request_item_ref,
  );
  assertEqual(
    "payload-demand-ref",
    payload.expected_demand_packet_ref,
    empty.requestReceipt.request_items[0].demand_packet_ref,
  );
  assertEqual(
    "payload-demand-hash",
    payload.expected_demand_packet_hash,
    empty.requestReceipt.request_items[0].demand_packet_hash,
  );
  assertEqual(
    "payload-candidate-kind",
    payload.candidate_kind,
    "BIBLIOGRAPHIC_COORDINATE_CANDIDATE",
  );
  assertEqual(
    "payload-target-only",
    payload.target_artifact_kind,
    "PROFESSIONAL_SOURCE_MANIFEST",
  );
  assertEqual("payload-title-normalized", payload.bibliography.title, "候选书目题名");
  assertEqual(
    "payload-idempotency-deterministic",
    payload.idempotency_key,
    buildRelationEffectEvidenceMaterialPayload(
      empty.requestReceipt,
      empty.requestReceipt.request_items[0],
      empty.requestReceipt.request_items[0].dimension_slots.find(
        (slot) => slot.dimension_id === "PROFESSIONAL_PROVENANCE",
      ),
      bibliography,
    ).idempotency_key,
  );
  assertEqual(
    "payload-idempotency-bounded",
    payload.idempotency_key.length <= 180,
    true,
  );

  for (const [label, invalidBibliography] of [
    ["url", { ...bibliography, locator: "https://example.test/source" }],
    ["newline", { ...bibliography, title: "题名\n附带正文" }],
    ["blank", { ...bibliography, responsible_party: " " }],
  ]) {
    expectThrow(`payload-${label}-rejected`, () =>
      buildRelationEffectEvidenceMaterialPayload(
        empty.requestReceipt,
        empty.requestReceipt.request_items[0],
        empty.requestReceipt.request_items[0].dimension_slots.find(
          (slot) => slot.dimension_id === "PROFESSIONAL_PROVENANCE",
        ),
        invalidBibliography,
      ),
    );
  }
  expectThrow("payload-non-provenance-slot-rejected", () =>
    buildRelationEffectEvidenceMaterialPayload(
      empty.requestReceipt,
      empty.requestReceipt.request_items[0],
      empty.requestReceipt.request_items[0].dimension_slots[0],
      bibliography,
    ),
  );
  const driftedItem = structuredClone(
    empty.requestReceipt.request_items[0],
  );
  driftedItem.demand_packet_hash = "0".repeat(64);
  expectThrow("payload-demand-chain-drift-rejected", () =>
    buildRelationEffectEvidenceMaterialPayload(
      empty.requestReceipt,
      driftedItem,
      driftedItem.dimension_slots.find(
        (slot) => slot.dimension_id === "PROFESSIONAL_PROVENANCE",
      ),
      bibliography,
    ),
  );

  const recorded =
    buildRecordedRelationEffectEvidenceMaterialFixture();
  const recordedMarkup = renderControl(recorded);
  const recordedSummary = renderSummary(recorded);
  for (const expected of [
    'data-candidate-material-count="1"',
    `data-material-ref="${recorded.material.material_ref}"`,
    `data-material-hash="${recorded.material.material_hash}"`,
    'data-material-status="CANDIDATE_METADATA_RECORDED_NOT_REQUESTED_ARTIFACT"',
    recorded.material.bibliography.title,
    recorded.material.bibliography.responsible_party,
    recorded.material.bibliography.edition_or_publication_identity,
    recorded.material.bibliography.locator,
    "未核验候选",
    "NOT_EVIDENCE · 未满足 PROFESSIONAL_SOURCE_MANIFEST",
  ]) {
    assertIncludes("recorded-material", recordedMarkup, expected);
  }
  for (const expected of [
    "<b>1</b> 份未核验候选元数据",
    "<b>0 / 6</b> 就绪",
    "不是专业材料、专业证据、专业审阅或作用 Decision",
  ]) {
    assertIncludes("mingli-count-only", recordedSummary, expected);
  }
  for (const hidden of [
    recorded.material.bibliography.title,
    recorded.material.bibliography.responsible_party,
    recorded.material.material_ref,
    recorded.material.material_hash,
  ]) {
    assertExcludes("mingli-no-material-detail", recordedSummary, hidden);
  }

  const noRequest =
    buildNoRequestRelationEffectEvidenceMaterialFixture();
  assertEqual("no-receipt-no-form", renderControl(noRequest), "");
  const clear = buildClearRelationEffectEvidenceMaterialFixture();
  assertEqual("clear-no-form", renderControl(clear), "");

  const unsafeCases = [
    ["version", (value) => {
      value.material.material_version = "v60.invalid.999";
    }],
    ["material-hash", (value) => {
      value.material.material_hash = "not-a-hash";
    }],
    ["receipt-ref", (value) => {
      value.material.request_receipt_ref = "receipt-drift";
    }],
    ["request-item", (value) => {
      value.material.request_item_ref = "item-drift";
    }],
    ["demand-hash", (value) => {
      value.material.demand_packet_hash = "0".repeat(64);
    }],
    ["slot", (value) => {
      value.material.slot_ref = "slot-drift";
    }],
    ["dimension", (value) => {
      value.material.dimension_id = "EFFECT_DIRECTION";
    }],
    ["candidate-kind", (value) => {
      value.material.candidate_kind = "PROFESSIONAL_SOURCE_MANIFEST";
    }],
    ["target-kind", (value) => {
      value.material.target_artifact_kind =
        "PROFESSIONAL_SOURCE_CITATION";
    }],
    ["status", (value) => {
      value.material.status = "PROFESSIONAL_EVIDENCE";
    }],
    ["evidence-role", (value) => {
      value.material.evidence_role = "PROFESSIONAL_EVIDENCE";
    }],
    ["bibliography-url", (value) => {
      value.material.bibliography.locator =
        "https://secret.test/claim";
    }],
    ["bibliography-hash", (value) => {
      value.material.bibliography_hash = "not-a-hash";
    }],
    ["bibliography-extra", (value) => {
      value.material.bibliography.professional_conclusion =
        "SECRET-PROFESSIONAL-CONCLUSION";
    }],
    ["lab-ref-order", (value) => {
      value.bindings.lab.relation_effect_evidence_material_refs = [
        "material-ref-drift",
      ];
    }],
    ["unknown-field", (value) => {
      value.material.secret_professional_verdict =
        "SECRET-PROFESSIONAL-VERDICT";
    }],
  ];
  for (const field of [
    "requested_artifact_satisfied",
    "material_truth_verified",
    "source_authenticity_verified",
    "artifact_content_present",
    "citation_body_present",
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
    "file_upload_allowed",
    "url_submission_allowed",
    "quotation_body_submission_allowed",
    "conclusion_submission_allowed",
    "unstructured_notes_submission_allowed",
  ]) {
    unsafeCases.push([`authority-${field}`, (value) => {
      value.material[field] = true;
    }]);
  }
  unsafeMutationCount = unsafeCases.length;
  for (const [label, mutate] of unsafeCases) {
    const unsafe = structuredClone(
      buildRecordedRelationEffectEvidenceMaterialFixture(),
    );
    mutate(unsafe);
    unsafe.materials = [unsafe.material];
    const markup = renderControl(unsafe);
    assertIncludes(
      `${label}-withheld`,
      markup,
      'data-material-state="WITHHELD"',
    );
    assertExcludes(
      `${label}-no-form`,
      markup,
      'data-material-command="CREATE"',
    );
    assertExcludes(
      `${label}-secret-conclusion-hidden`,
      markup,
      "SECRET-PROFESSIONAL-CONCLUSION",
    );
    assertExcludes(
      `${label}-secret-verdict-hidden`,
      markup,
      "SECRET-PROFESSIONAL-VERDICT",
    );
  }

  const componentSource = await readFile(
    path.join(
      webRoot,
      "src/components/RelationEffectEvidenceMaterial.tsx",
    ),
    "utf8",
  );
  for (const forbidden of [
    "<textarea",
    'type="file"',
    'type="url"',
    "content_sha256",
    "declared_content_sha256",
  ]) {
    assertExcludes("component-source-boundary", componentSource, forbidden);
  }
  const styles = await readFile(
    path.join(
      webRoot,
      "src/styles/relation-effect-evidence-material.css",
    ),
    "utf8",
  );
  for (const expected of [
    ".relation-effect-evidence-material",
    ".relation-effect-evidence-material-counts",
    ".relation-effect-evidence-material-list",
    ".relation-effect-evidence-material.is-withheld",
  ]) {
    assertIncludes("styles", styles, expected);
  }
} finally {
  await vite.close();
}

const report = {
  material: {
    candidateKind: "BIBLIOGRAPHIC_COORDINATE_CANDIDATE",
    targetArtifactKind: "PROFESSIONAL_SOURCE_MANIFEST",
    structuredFields: 4,
    recordedCandidateMaterials: 1,
    professionalMaterials: 0,
    professionalEvidence: 0,
    readyDimensions: 0,
    effectDecision: "WITHHELD",
  },
  noReceiptFormCount: 0,
  clearCaseFormCount: 0,
  unsafeMutationCount,
  authorityLeakage: failures.length ? "FAILED" : "NONE",
  failures,
};

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (failures.length > 0) process.exitCode = 1;
