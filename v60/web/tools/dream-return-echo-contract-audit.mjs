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

const returnEcho = {
  contract_version: "v60.dream-return-echo.001",
  echo_ref: "v60-dream-return-echo-contract-test",
  echo_hash: "echo-hash-must-not-render",
  encounter_ref: "encounter-ref-must-not-render",
  public_alias: "闻溪",
  episode_title: "共同修复，共同署名",
  judgment: {
    choice_label: "保留试案",
    summary: "你当时把共同职责放在单独署名之前。",
  },
  world_response: {
    summary: "后来抵达的是两条已经提交的梦中事实。",
    evidence_summaries: [
      "馆方把修复安排交给共同小组。",
      "完成记录同时留下两个人的名字。",
    ],
  },
  still_to_observe: {
    summary: "下一次仍要看职责如何被承认，而不是把这一幕解释成命理结果。",
  },
  abu_recap: {
    meaning: "这次只说明共同职责后来得到了可核验的回应。",
    boundary: "它不能证明主人的命盘关系已经有效做功。",
    next_attention: "回到林中时，继续看另一段人生怎样留下自己的证据。",
  },
  semantics: "DREAM_LIFE_RETURN_ECHO_ONLY",
  owner_mingli_evidence_allowed: false,
  dream_outcome_admitted_as_owner_evidence: false,
  tree_candidate_set_or_order_changed: false,
  read_only: true,
  decision_write_allowed: false,
  knowledge_write_allowed: false,
  mingli_write_allowed: false,
  canonical_write_allowed: false,
};

const candidate = (candidateRef, domain, alias, displayOrder) => ({
  candidate_ref: candidateRef,
  domain,
  public_alias: alias,
  premise: `${alias}的独立梦中问题`,
  display_order: displayOrder,
  tree: {
    state: "READY",
    version: 1,
    phenotype: {
      profile_version: "phenotype.001",
      fact_basis: "contract fixture",
      element_membership_ratios: {
        wood: 0.2,
        fire: 0.2,
        earth: 0.2,
        metal: 0.2,
        water: 0.2,
      },
      crown_spread: 1,
      branch_lift: 0.84,
      root_spread: 1,
      bark_definition: 0.86,
      surface_moisture: 0.9,
      semantic_status: "VISUAL_METAPHOR_ONLY",
    },
    scene_hash: `${candidateRef}-scene-hash`,
  },
});

const candidates = Object.freeze([
  Object.freeze(candidate("candidate-career", "career", "闻溪", 1)),
  Object.freeze(candidate("candidate-wealth", "wealth", "禾央", 2)),
  Object.freeze(candidate("candidate-relationship", "relationship", "照宁", 3)),
]);

const baseGrove = {
  grove_version: "v60.dream-grove.002",
  selection_status: "AWAITING_TREE_SELECTION",
  candidates,
  hidden_outcome_included: false,
  hidden_npc_choice_included: false,
};

const delivery = (ref, mediaType) => ({
  asset_ref: ref,
  asset_version: "asset.001",
  url: `/${ref}`,
  media_type: mediaType,
  sha256: `${ref}-sha256`,
});
const media = {
  registry_version: "registry.001",
  catalog_version: "catalog.001",
  assets: {
    brand_logo: delivery("brand", "image/svg+xml"),
    grove_background: delivery("grove-background", "image/png"),
    life_world_background: delivery("life-background", "image/png"),
  },
  cues: {
    abu_idle: {
      cue_ref: "abu-idle",
      version: "cue.001",
      trigger: "IDLE",
      playback: "LOOP",
      interruptible: true,
      deliveries: {
        VP9_ALPHA_WEBM: delivery("abu-idle-video", "video/webm"),
        REDUCED_MOTION_POSTER: delivery("abu-idle-poster", "image/png"),
      },
    },
    abu_guide_left: {
      cue_ref: "abu-guide",
      version: "cue.001",
      trigger: "GUIDE_LEFT",
      playback: "PLAY_ONCE",
      interruptible: true,
      deliveries: {
        VP9_ALPHA_WEBM: delivery("abu-guide-video", "video/webm"),
        REDUCED_MOTION_POSTER: delivery("abu-guide-poster", "image/png"),
      },
    },
  },
};
const lens = {
  semantics: "ATTENTION_WINDOW_ONLY",
  decision_role: "NOT_APPLIED_TO_TREE_CANDIDATES_OR_ORDER",
  attention_order_recorded: false,
  tree_candidate_set_or_order_changed: false,
  future_evidence_included: false,
  canonical_write_allowed: false,
  observations: [
    { domain: "career", label: "事业与职责", question: "事业观察？" },
    { domain: "wealth", label: "成果与交换", question: "成果观察？" },
    { domain: "relationship", label: "关系与边界", question: "关系观察？" },
  ],
};

const candidateOrder = (markup) =>
  [...markup.matchAll(/data-candidate-ref="([^"]+)"/g)]
    .map((match) => match[1])
    .join(",");

try {
  const { DreamReturnEchoCard } = await vite.ssrLoadModule(
    "/src/components/DreamReturnEchoCard.tsx",
  );
  const { DreamGroveScene } = await vite.ssrLoadModule(
    "/src/DreamGroveScene.tsx",
  );

  const emptyMarkup = renderToStaticMarkup(
    React.createElement(DreamReturnEchoCard, { echo: null }),
  );
  assertEqual("empty-echo", emptyMarkup, "");
  const absentMarkup = renderToStaticMarkup(
    React.createElement(DreamReturnEchoCard, { echo: undefined }),
  );
  assertEqual("absent-echo", absentMarkup, "");

  const echoMarkup = renderToStaticMarkup(
    React.createElement(DreamReturnEchoCard, { echo: returnEcho }),
  );
  for (const expected of [
    'data-return-echo-status="AVAILABLE"',
    `data-return-echo-ref="${returnEcho.echo_ref}"`,
    `data-return-echo-hash="${returnEcho.echo_hash}"`,
    'data-return-echo-version="v60.dream-return-echo.001"',
    'data-semantics="DREAM_LIFE_RETURN_ECHO_ONLY"',
    'data-owner-mingli-evidence-allowed="false"',
    'data-dream-outcome-admitted-as-owner-evidence="false"',
    'data-tree-candidate-set-or-order-changed="false"',
    'data-read-only="true"',
    'data-decision-write-allowed="false"',
    'data-knowledge-write-allowed="false"',
    'data-mingli-write-allowed="false"',
    'data-canonical-write-allowed="false"',
    "当时的判断",
    "世界的回应",
    "仍值得观察",
    "听阿布复盘这一次",
    "它说明了什么",
    "它还不能说明什么",
    "接下来该看什么",
    "只属于这条梦中生命",
    "不得作为主人的命理证据",
    "不改变三棵树的候选或顺序",
  ]) {
    assertIncludes("available-echo", echoMarkup, expected);
  }
  assertEqual(
    "section-count",
    (echoMarkup.match(/data-return-echo-section=/g) ?? []).length,
    3,
  );
  assertEqual(
    "abu-question-count",
    (echoMarkup.match(/data-abu-recap-question=/g) ?? []).length,
    3,
  );
  assertEqual(
    "single-recap-disclosure",
    (echoMarkup.match(/<details/g) ?? []).length,
    1,
  );
  assertExcludes("encounter-ref-hidden", echoMarkup, returnEcho.encounter_ref);

  const unsafeOverrides = {
    contract_version: "v60.dream-return-echo.999",
    semantics: "DREAM_OUTCOME_AS_OWNER_READING",
    owner_mingli_evidence_allowed: true,
    dream_outcome_admitted_as_owner_evidence: true,
    tree_candidate_set_or_order_changed: true,
    read_only: false,
    decision_write_allowed: true,
    knowledge_write_allowed: true,
    mingli_write_allowed: true,
    canonical_write_allowed: true,
  };
  for (const [field, value] of Object.entries(unsafeOverrides)) {
    const withheldMarkup = renderToStaticMarkup(
      React.createElement(DreamReturnEchoCard, {
        echo: { ...returnEcho, [field]: value },
      }),
    );
    assertIncludes(
      `unsafe-${field}-withheld`,
      withheldMarkup,
      'data-return-echo-status="WITHHELD"',
    );
    assertIncludes(
      `unsafe-${field}-boundary`,
      withheldMarkup,
      "边界凭据不完整",
    );
    assertExcludes(
      `unsafe-${field}-content-hidden`,
      withheldMarkup,
      returnEcho.judgment.summary,
    );
    assertExcludes(
      `unsafe-${field}-content-hidden`,
      withheldMarkup,
      returnEcho.abu_recap.meaning,
    );
  }

  const noEchoGroveMarkup = renderToStaticMarkup(
    React.createElement(DreamGroveScene, {
      background: media.assets.grove_background,
      busy: false,
      grove: { ...baseGrove, return_echo: null },
      lens,
      media,
      onSelect: () => {},
    }),
  );
  const withEchoGroveMarkup = renderToStaticMarkup(
    React.createElement(DreamGroveScene, {
      background: media.assets.grove_background,
      busy: false,
      grove: { ...baseGrove, return_echo: returnEcho },
      lens,
      media,
      onSelect: () => {},
    }),
  );
  assertIncludes("grove-empty-state", noEchoGroveMarkup, 'data-return-echo="false"');
  assertIncludes("grove-echo-state", withEchoGroveMarkup, 'data-return-echo="true"');
  assertEqual(
    "candidate-count-without-echo",
    (noEchoGroveMarkup.match(/class="grove-tree-choice"/g) ?? []).length,
    3,
  );
  assertEqual(
    "candidate-count-with-echo",
    (withEchoGroveMarkup.match(/class="grove-tree-choice"/g) ?? []).length,
    3,
  );
  assertEqual(
    "candidate-order-without-echo",
    candidateOrder(noEchoGroveMarkup),
    "candidate-career,candidate-wealth,candidate-relationship",
  );
  assertEqual(
    "candidate-order-with-echo",
    candidateOrder(withEchoGroveMarkup),
    candidateOrder(noEchoGroveMarkup),
  );
  assertEqual(
    "input-candidate-order-not-mutated",
    candidates.map(({ candidate_ref }) => candidate_ref).join(","),
    "candidate-career,candidate-wealth,candidate-relationship",
  );

  const styles = await readFile(
    path.join(webRoot, "src/styles/dream-return-echo.css"),
    "utf8",
  );
  for (const expected of [
    ".dream-return-echo",
    ".dream-return-echo-sections",
    ".dream-return-echo-recap",
    '.dream-grove-scene[data-return-echo="true"] .dream-grove-trees',
  ]) {
    assertIncludes("styles", styles, expected);
  }
} finally {
  await vite.close();
}

const report = {
  groveVersion: baseGrove.grove_version,
  states: ["EMPTY", "AVAILABLE", "WITHHELD"],
  sections: ["judgment", "world-response", "still-to-observe"],
  abuRecapQuestions: ["meaning", "boundary", "next"],
  candidateCount: candidates.length,
  candidateOrderStable: true,
  ownerMingliEvidenceAllowed: false,
  readOnly: true,
  decisionWriteAllowed: false,
  knowledgeWriteAllowed: false,
  mingliWriteAllowed: false,
  failures,
};

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (failures.length > 0) process.exitCode = 1;
