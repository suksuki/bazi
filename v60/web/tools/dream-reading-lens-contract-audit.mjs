import { readFile } from "node:fs/promises";
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
const assertEqual = (label, actual, expected) => {
  if (actual !== expected) {
    fail(`${label}:expected:${JSON.stringify(expected)}:actual:${JSON.stringify(actual)}`);
  }
};
const assertIncludes = (label, value, expected) => {
  if (!value.includes(expected)) fail(`${label}:missing:${expected}`);
};
const assertExcludes = (label, value, forbidden) => {
  if (value.includes(forbidden)) fail(`${label}:forbidden:${forbidden}`);
};
const assertThrows = (label, callback, expectedMessage) => {
  try {
    callback();
    fail(`${label}:did-not-throw`);
  } catch (error) {
    if (!(error instanceof Error) || error.message !== expectedMessage) {
      fail(`${label}:wrong-error:${String(error)}`);
    }
  }
};

const domainRows = [
  {
    domain: "career",
    label: "事业与职责",
    question: "事业观察问题？",
    statement: "statement-secret-career",
    signal_status: "TIMING_ONLY",
    evidence_count: 91,
  },
  {
    domain: "wealth",
    label: "成果与交换",
    question: "成果观察问题？",
    statement: "statement-secret-wealth",
    signal_status: "MECHANISM_ONLY",
    evidence_count: 92,
  },
  {
    domain: "relationship",
    label: "关系与边界",
    question: "关系观察问题？",
    statement: "statement-secret-relationship",
    signal_status: "NO_BOUNDED_EVIDENCE",
    evidence_count: 93,
  },
];

const source = {
  reading_brief: {
    life_domains: domainRows,
    brief_ref: "brief-ref-secret",
    brief_hash: "brief-hash-secret",
    rationale: "rationale-secret",
    timing_coordinate: "timing-coordinate-secret",
  },
  mechanism_comparison: {
    status: "RESOLVED",
    decision_ref: "decision-ref-secret",
    decision_hash: "decision-hash-secret",
    selected_candidate_ref: "candidate-ref-secret",
    selected_candidate_label: "candidate-label-secret",
    rationale_summary: "decision-rationale-secret",
    evidence_refs_used: ["evidence-ref-secret"],
    provider_confidence: 0.97,
  },
};
const domainSequence = (markup) =>
  [...markup.matchAll(/data-domain="([^"]+)"/g)]
    .map((match) => match[1])
    .join(",");
const observationListMarkup = (markup) =>
  markup.match(
    /<div class="dream-reading-observation-list">.*?<\/div>/s,
  )?.[0] ?? "";

try {
  const { buildDreamReadingObservationLens } = await vite.ssrLoadModule(
    "/src/homeDreamObservationLens.ts",
  );
  const { DreamReadingObservationLens } = await vite.ssrLoadModule(
    "/src/components/DreamReadingObservationLens.tsx",
  );

  const lens = buildDreamReadingObservationLens(source);
  assertEqual(
    "lens-keys",
    Object.keys(lens).sort().join(","),
    [
      "attention_order_recorded",
      "canonical_write_allowed",
      "decision_role",
      "future_evidence_included",
      "observations",
      "semantics",
      "tree_candidate_set_or_order_changed",
    ]
      .sort()
      .join(","),
  );
  assertEqual("semantics", lens.semantics, "ATTENTION_WINDOW_ONLY");
  assertEqual(
    "decision-role",
    lens.decision_role,
    "NOT_APPLIED_TO_TREE_CANDIDATES_OR_ORDER",
  );
  assertEqual("attention-recorded", lens.attention_order_recorded, true);
  assertEqual(
    "tree-candidates-or-order",
    lens.tree_candidate_set_or_order_changed,
    false,
  );
  assertEqual("future-evidence", lens.future_evidence_included, false);
  assertEqual("canonical-write", lens.canonical_write_allowed, false);
  assertEqual("domain-count", lens.observations.length, 3);
  assertEqual(
    "domain-order",
    lens.observations.map(({ domain }) => domain).join(","),
    "career,wealth,relationship",
  );
  for (const [index, observation] of lens.observations.entries()) {
    assertEqual(
      `observation-${index}-keys`,
      Object.keys(observation).sort().join(","),
      "domain,label,question",
    );
    assertEqual(`observation-${index}-label`, observation.label, domainRows[index].label);
    assertEqual(
      `observation-${index}-question`,
      observation.question,
      domainRows[index].question,
    );
  }

  const notRunLens = buildDreamReadingObservationLens({
    ...source,
    mechanism_comparison: {
      ...source.mechanism_comparison,
      status: "NOT_RUN",
      decision_ref: null,
    },
  });
  assertEqual(
    "attention-not-recorded",
    notRunLens.attention_order_recorded,
    false,
  );
  const inconsistentLens = buildDreamReadingObservationLens({
    ...source,
    mechanism_comparison: {
      ...source.mechanism_comparison,
      decision_ref: null,
    },
  });
  assertEqual(
    "attention-inconsistent-fails-closed",
    inconsistentLens.attention_order_recorded,
    false,
  );

  assertThrows(
    "missing-domain",
    () =>
      buildDreamReadingObservationLens({
        ...source,
        reading_brief: { life_domains: domainRows.slice(0, 2) },
      }),
    "dream_observation_domain_contract_invalid",
  );
  assertThrows(
    "duplicate-domain",
    () =>
      buildDreamReadingObservationLens({
        ...source,
        reading_brief: {
          life_domains: [...domainRows, { ...domainRows[0] }],
        },
      }),
    "dream_observation_domain_contract_invalid",
  );

  const serializedLens = JSON.stringify(lens);
  const groveMarkup = renderToStaticMarkup(
    React.createElement(DreamReadingObservationLens, {
      lens,
      mode: "grove",
    }),
  );
  const encounterMarkup = renderToStaticMarkup(
    React.createElement(DreamReadingObservationLens, {
      lens,
      mode: "encounter",
    }),
  );
  const markups = [
    ["grove", groveMarkup],
    ["encounter", encounterMarkup],
  ];
  for (const secret of [
    "brief-ref-secret",
    "brief-hash-secret",
    "rationale-secret",
    "timing-coordinate-secret",
    "decision-ref-secret",
    "decision-hash-secret",
    "candidate-ref-secret",
    "candidate-label-secret",
    "evidence-ref-secret",
    "0.97",
    "91",
    "92",
    "93",
    "statement-secret",
  ]) {
    assertExcludes("serialized-lens", serializedLens, secret);
    for (const [mode, markup] of markups) {
      assertExcludes(`rendered-${mode}`, markup, secret);
    }
  }
  for (const forbiddenAttribute of [
    "data-decision-ref",
    "data-decision-hash",
    "data-candidate",
    "data-rationale",
    "data-evidence-count",
    "data-timing",
    "data-confidence",
  ]) {
    for (const [mode, markup] of markups) {
      assertExcludes(`rendered-${mode}-attributes`, markup, forbiddenAttribute);
    }
  }
  for (const expected of [
    'data-semantics="ATTENTION_WINDOW_ONLY"',
    'data-decision-role="NOT_APPLIED_TO_TREE_CANDIDATES_OR_ORDER"',
    'data-attention-order-recorded="true"',
    'data-tree-candidate-set-or-order-changed="false"',
    'data-dream-answer-or-outcome-input="false"',
    'data-dream-outcome-admitted-as-owner-evidence="false"',
    'data-future-evidence-included="false"',
    'data-canonical-write-allowed="false"',
    'data-domain="career"',
    'data-domain="wealth"',
    'data-domain="relationship"',
    "三条等权",
  ]) {
    for (const [mode, markup] of markups) {
      assertIncludes(`rendered-${mode}-contract`, markup, expected);
    }
  }
  assertIncludes("grove-mode", groveMarkup, 'data-mode="grove"');
  assertIncludes(
    "grove-boundary",
    groveMarkup,
    "系统不会据此改动三棵树的候选或顺序，也不预测结果、不回写命理。",
  );
  assertIncludes("encounter-mode", encounterMarkup, 'data-mode="encounter"');
  for (const expected of [
    "把三个现实问题留在树边",
    "系统不把它们写入树中问题、封印或结果",
    "不用梦中结果验证你的命理",
    "不预测、不回写",
  ]) {
    assertIncludes("encounter-boundary", encounterMarkup, expected);
  }
  assertEqual(
    "grove-encounter-domain-order",
    domainSequence(groveMarkup),
    domainSequence(encounterMarkup),
  );
  assertEqual(
    "grove-encounter-observation-copy",
    observationListMarkup(groveMarkup),
    observationListMarkup(encounterMarkup),
  );
  for (const [mode, markup] of markups) {
    assertEqual(
      `${mode}-rendered-domain-count`,
      (markup.match(/data-domain=/g) ?? []).length,
      3,
    );
    assertEqual(
      `${mode}-rendered-domain-order`,
      domainSequence(markup),
      "career,wealth,relationship",
    );
    assertExcludes(`${mode}-rendered-ranking`, markup, "selected");
    assertExcludes(`${mode}-rendered-ranking`, markup, "primary");
    assertExcludes(`${mode}-rendered-ranking`, markup, "rank");
  }

  const styles = await readFile(
    path.join(webRoot, "src/styles/dream-reading-observation-lens.css"),
    "utf8",
  );
  if (
    !/\.dream-reading-observation-lens\s*\{[^}]*pointer-events:\s*none;/s.test(
      styles,
    )
  ) {
    fail("styles:pointer-events-not-none");
  }
  assertIncludes(
    "styles",
    styles,
    '.dream-reading-observation-lens[data-mode="encounter"]',
  );
} finally {
  await vite.close();
}

if (failures.length) throw new Error(failures.join("\n"));
console.log(
  JSON.stringify(
    {
      domains: ["career", "wealth", "relationship"],
      missingDomain: "FAIL_CLOSED",
      duplicateDomain: "FAIL_CLOSED",
      decisionProjection: "BOOLEAN_ONLY",
      presentationModes: ["grove", "encounter"],
      renderLeakage: "NONE",
      failures,
    },
    null,
    2,
  ),
);
