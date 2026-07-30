import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(
  here,
  "../../.artifacts/dream-return-echo",
);
const chromePath =
  process.env.V60_AUDIT_CHROME_PATH ??
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience";
const sessionToken = process.env.V60_AUDIT_SESSION_TOKEN;

if (!sessionToken) throw new Error("V60_AUDIT_SESSION_TOKEN is required");
await mkdir(artifactDirectory, { recursive: true });

const browser = await chromium.launch({
  executablePath: chromePath,
  headless: true,
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
});
await context.addCookies([
  {
    name: "abu_v60_session",
    value: sessionToken,
    url: new URL(targetUrl).origin,
    httpOnly: true,
    sameSite: "Lax",
  },
]);

const page = await context.newPage();
const failures = [];
const observedRequests = [];
const screenshots = {};
const stageMetrics = {};

const fail = (message) => failures.push(message);
const sameJson = (left, right) => JSON.stringify(left) === JSON.stringify(right);

page.on("console", (message) => {
  if (message.type() === "error") fail(`console:${message.text()}`);
});
page.on("pageerror", (error) => fail(`page:${error.message}`));
page.on("request", (request) => {
  let pathname = request.url();
  try {
    pathname = new URL(request.url()).pathname;
  } catch {
    // Preserve the full URL for non-HTTP browser-internal requests.
  }
  observedRequests.push({
    method: request.method(),
    pathname,
    url: request.url(),
  });
});
page.on("requestfailed", (request) => {
  fail(
    `request:${request.method()} ${request.url()} ${request.failure()?.errorText}`,
  );
});
page.on("response", (response) => {
  if (response.status() >= 400) {
    fail(`response:${response.status()} ${response.url()}`);
  }
});

const readJson = async (pathname) =>
  page.evaluate(async (url) => {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${url}:${response.status}`);
    return response.json();
  }, pathname);

const capture = async (name) => {
  const screenshotPath = path.join(artifactDirectory, `${name}.png`);
  await page.screenshot({ path: screenshotPath });
  screenshots[name] = screenshotPath;
};

const inspectDocument = async (stage) => {
  const metrics = await page.evaluate(() => ({
    bodyScrollHeight: document.body.scrollHeight,
    bodyScrollWidth: document.body.scrollWidth,
    documentScrollHeight: document.documentElement.scrollHeight,
    documentScrollWidth: document.documentElement.scrollWidth,
    viewportHeight: window.innerHeight,
    viewportWidth: window.innerWidth,
  }));
  stageMetrics[stage] = metrics;
  if (
    metrics.bodyScrollHeight > metrics.viewportHeight + 1 ||
    metrics.documentScrollHeight > metrics.viewportHeight + 1 ||
    metrics.bodyScrollWidth > metrics.viewportWidth + 1 ||
    metrics.documentScrollWidth > metrics.viewportWidth + 1
  ) {
    fail(`${stage}:document-overflow`);
  }
};

const homeIdentity = (home) => ({
  contextRef: home.context_ref,
  contextHash: home.context_hash,
  caseRef: home.case.case_ref,
  caseVersion: home.case.case_version,
  chartVersionRef: home.chart.chart_version_ref,
  chartHash: home.chart.chart_hash,
  lifeCaseRevisionRef: home.life_case.life_case_revision_ref,
  lifeCaseRevisionHash: home.life_case.revision_hash,
  treeRef: home.tree.tree_ref,
  treeProjectionVersion: home.tree.projection_version,
  readingRef: home.mingli.reading.reading_ref,
  readingHash: home.mingli.reading.reading_hash,
  readingDecisionRefs: home.mingli.reading.decision_refs,
  labReadingRef: home.lab.reading_ref,
  labReadingHash: home.lab.reading_hash,
  comparisonDecisionRef:
    home.lab.mechanism_comparison?.decision_ref ?? null,
  comparisonDecisionHash:
    home.lab.mechanism_comparison?.decision_hash ?? null,
});

const candidateProjection = (entry) =>
  (entry.grove?.candidates ?? []).map(
    ({ candidate_ref, display_order, domain }) => ({
      candidateRef: candidate_ref,
      displayOrder: display_order,
      domain,
    }),
  );

const echoProjection = (echo) => ({
  contractVersion: echo.contract_version,
  echoRef: echo.echo_ref,
  echoHash: echo.echo_hash,
  encounterRef: echo.encounter_ref,
  publicAlias: echo.public_alias,
  episodeTitle: echo.episode_title,
  judgment: {
    choiceLabel: echo.judgment?.choice_label,
    summary: echo.judgment?.summary,
  },
  worldResponse: {
    summary: echo.world_response?.summary,
    evidenceSummaries: echo.world_response?.evidence_summaries ?? [],
  },
  stillToObserve: {
    summary: echo.still_to_observe?.summary,
  },
  abuRecap: {
    meaning: echo.abu_recap?.meaning,
    boundary: echo.abu_recap?.boundary,
    nextAttention: echo.abu_recap?.next_attention,
  },
  boundaries: {
    semantics: echo.semantics,
    ownerMingliEvidenceAllowed: echo.owner_mingli_evidence_allowed,
    dreamOutcomeAdmittedAsOwnerEvidence:
      echo.dream_outcome_admitted_as_owner_evidence,
    treeCandidateSetOrOrderChanged:
      echo.tree_candidate_set_or_order_changed,
    readOnly: echo.read_only,
    decisionWriteAllowed: echo.decision_write_allowed,
    knowledgeWriteAllowed: echo.knowledge_write_allowed,
    mingliWriteAllowed: echo.mingli_write_allowed,
    canonicalWriteAllowed: echo.canonical_write_allowed,
  },
});

const readCandidateDom = async () =>
  page.locator(".grove-tree-choice").evaluateAll((nodes) =>
    nodes.map((node) => ({
      candidateRef: node.getAttribute("data-candidate-ref"),
      domain: node.getAttribute("data-domain"),
    })),
  );

const readEchoDom = async () => {
  const card = page.locator(
    '.dream-return-echo[data-return-echo-status="AVAILABLE"]',
  );
  await card.waitFor({ state: "visible" });
  return card.evaluate((node) => {
    const text = (selector) =>
      node.querySelector(selector)?.textContent?.trim() ?? "";
    const texts = (selector) =>
      [...node.querySelectorAll(selector)].map(
        (item) => item.textContent?.trim() ?? "",
      );
    const details = node.querySelector(".dream-return-echo-recap");
    const rect = node.getBoundingClientRect();
    return {
      contractVersion: node.getAttribute("data-return-echo-version"),
      echoRef: node.getAttribute("data-return-echo-ref"),
      echoHash: node.getAttribute("data-return-echo-hash"),
      publicAlias: text("header strong"),
      episodeTitle: text("header small"),
      judgment: {
        label: text('[data-return-echo-section="judgment"] small'),
        choiceLabel: text('[data-return-echo-section="judgment"] strong'),
        summary: text('[data-return-echo-section="judgment"] p'),
      },
      worldResponse: {
        label: text('[data-return-echo-section="world-response"] small'),
        summary: text('[data-return-echo-section="world-response"] p'),
        evidenceSummaries: texts(
          '[data-return-echo-section="world-response"] li',
        ),
      },
      stillToObserve: {
        label: text('[data-return-echo-section="still-to-observe"] small'),
        summary: text('[data-return-echo-section="still-to-observe"] p'),
      },
      abuRecap: {
        open: details instanceof HTMLDetailsElement ? details.open : false,
        summary: text(".dream-return-echo-recap summary"),
        meaning: text('[data-abu-recap-question="meaning"] dd'),
        boundary: text('[data-abu-recap-question="boundary"] dd'),
        nextAttention: text('[data-abu-recap-question="next"] dd'),
        questionCount: node.querySelectorAll("[data-abu-recap-question]")
          .length,
      },
      boundaryCopy: text(".dream-return-echo-boundary"),
      boundaries: {
        semantics: node.getAttribute("data-semantics"),
        ownerMingliEvidenceAllowed:
          node.getAttribute("data-owner-mingli-evidence-allowed") === "true",
        dreamOutcomeAdmittedAsOwnerEvidence:
          node.getAttribute(
            "data-dream-outcome-admitted-as-owner-evidence",
          ) === "true",
        treeCandidateSetOrOrderChanged:
          node.getAttribute("data-tree-candidate-set-or-order-changed") ===
          "true",
        readOnly: node.getAttribute("data-read-only") === "true",
        decisionWriteAllowed:
          node.getAttribute("data-decision-write-allowed") === "true",
        knowledgeWriteAllowed:
          node.getAttribute("data-knowledge-write-allowed") === "true",
        mingliWriteAllowed:
          node.getAttribute("data-mingli-write-allowed") === "true",
        canonicalWriteAllowed:
          node.getAttribute("data-canonical-write-allowed") === "true",
      },
      layout: {
        horizontalOverflow: node.scrollWidth > node.clientWidth + 1,
        insideViewport:
          rect.left >= -1 &&
          rect.top >= -1 &&
          rect.right <= window.innerWidth + 1 &&
          rect.bottom <= window.innerHeight + 1,
      },
    };
  });
};

const assertEntryContract = (stage, entry) => {
  if (entry.kind !== "GROVE") {
    fail(`${stage}:entry-is-not-grove`);
    return null;
  }
  if (
    entry.grove.hidden_outcome_included !== false ||
    entry.grove.hidden_npc_choice_included !== false
  ) {
    fail(`${stage}:grove-hidden-information-boundary-invalid`);
  }
  const candidates = candidateProjection(entry);
  if (
    candidates.length !== 3 ||
    new Set(candidates.map(({ candidateRef }) => candidateRef)).size !== 3 ||
    !sameJson(
      candidates.map(({ displayOrder }) => displayOrder),
      [1, 2, 3],
    )
  ) {
    fail(`${stage}:candidate-ref-or-order-contract-invalid`);
  }
  const echo = entry.grove.return_echo;
  if (!echo || typeof echo !== "object") {
    fail(`${stage}:return-echo-missing`);
    return null;
  }
  const projection = echoProjection(echo);
  if (
    projection.contractVersion !== "v60.dream-return-echo.001" ||
    !projection.echoRef ||
    !projection.echoHash ||
    !projection.encounterRef ||
    projection.boundaries.semantics !== "DREAM_LIFE_RETURN_ECHO_ONLY" ||
    projection.boundaries.ownerMingliEvidenceAllowed !== false ||
    projection.boundaries.dreamOutcomeAdmittedAsOwnerEvidence !== false ||
    projection.boundaries.treeCandidateSetOrOrderChanged !== false ||
    projection.boundaries.readOnly !== true ||
    projection.boundaries.decisionWriteAllowed !== false ||
    projection.boundaries.knowledgeWriteAllowed !== false ||
    projection.boundaries.mingliWriteAllowed !== false ||
    projection.boundaries.canonicalWriteAllowed !== false
  ) {
    fail(`${stage}:return-echo-boundary-contract-invalid`);
  }
  for (const [field, value] of [
    ["judgment.choice-label", projection.judgment.choiceLabel],
    ["judgment.summary", projection.judgment.summary],
    ["world-response.summary", projection.worldResponse.summary],
    ["still-to-observe.summary", projection.stillToObserve.summary],
    ["abu-recap.meaning", projection.abuRecap.meaning],
    ["abu-recap.boundary", projection.abuRecap.boundary],
    ["abu-recap.next-attention", projection.abuRecap.nextAttention],
  ]) {
    if (typeof value !== "string" || value.trim().length === 0) {
      fail(`${stage}:${field}-missing`);
    }
  }
  return projection;
};

const assertDomMatchesEcho = (stage, dom, echo) => {
  if (
    dom.contractVersion !== echo.contractVersion ||
    dom.echoRef !== echo.echoRef ||
    dom.echoHash !== echo.echoHash
  ) {
    fail(`${stage}:dom-api-echo-identity-mismatch`);
  }
  if (
    dom.publicAlias !== echo.publicAlias ||
    dom.episodeTitle !== echo.episodeTitle ||
    dom.judgment.choiceLabel !== echo.judgment.choiceLabel ||
    dom.judgment.summary !== echo.judgment.summary ||
    dom.worldResponse.summary !== echo.worldResponse.summary ||
    !sameJson(
      dom.worldResponse.evidenceSummaries,
      echo.worldResponse.evidenceSummaries,
    ) ||
    dom.stillToObserve.summary !== echo.stillToObserve.summary
  ) {
    fail(`${stage}:dom-api-three-part-copy-mismatch`);
  }
  if (
    dom.judgment.label !== "当时的判断" ||
    dom.worldResponse.label !== "世界的回应" ||
    dom.stillToObserve.label !== "仍值得观察"
  ) {
    fail(`${stage}:three-part-label-contract-invalid`);
  }
  if (
    dom.abuRecap.summary !== "听阿布复盘这一次" ||
    dom.abuRecap.meaning !== echo.abuRecap.meaning ||
    dom.abuRecap.boundary !== echo.abuRecap.boundary ||
    dom.abuRecap.nextAttention !== echo.abuRecap.nextAttention ||
    dom.abuRecap.questionCount !== 3
  ) {
    fail(`${stage}:abu-recap-contract-mismatch`);
  }
  if (!sameJson(dom.boundaries, echo.boundaries)) {
    fail(`${stage}:dom-api-boundary-attributes-mismatch`);
  }
  if (
    !dom.boundaryCopy.includes("只属于这条梦中生命") ||
    !dom.boundaryCopy.includes("不得作为主人的命理证据") ||
    !dom.boundaryCopy.includes("不改变三棵树的候选或顺序")
  ) {
    fail(`${stage}:visible-boundary-copy-missing`);
  }
  if (dom.layout.horizontalOverflow || !dom.layout.insideViewport) {
    fail(`${stage}:return-echo-layout-overflow`);
  }
};

const assertCandidatesMatchDom = async (stage, candidates) => {
  const domCandidates = await readCandidateDom();
  const expectedDom = candidates.map(({ candidateRef, domain }) => ({
    candidateRef,
    domain,
  }));
  if (!sameJson(domCandidates, expectedDom)) {
    fail(`${stage}:api-dom-candidate-ref-or-order-mismatch`);
  }
  return domCandidates;
};

const dreamUrl = new URL(targetUrl);
dreamUrl.searchParams.set("scope", "dream");
dreamUrl.searchParams.delete("view");
dreamUrl.searchParams.delete("focus");

let initialEntry;
let initialEcho;
let initialCandidates = [];
let refreshedEntry;
let refreshedEcho;
let refreshedCandidates = [];
let initialHomeIdentity = null;
let refreshedHomeIdentity = null;
let homeNavigationIdentity = null;
let finalHomeIdentity = null;
let isolationSentinels = [];
let initialEchoDom = null;
let expandedEchoDom = null;
let refreshedEchoDom = null;

try {
  await page.goto(dreamUrl.toString(), { waitUntil: "networkidle" });
  await page
    .locator('main[data-experience-scope="dream"] .dream-grove-scene')
    .waitFor({ state: "visible" });

  initialEntry = await readJson("/api/v60/dream/entry");
  initialEcho = assertEntryContract("initial", initialEntry);
  if (!initialEcho) throw new Error("initial-return-echo-contract-unavailable");
  initialCandidates = candidateProjection(initialEntry);
  await assertCandidatesMatchDom("initial", initialCandidates);
  initialEchoDom = await readEchoDom();
  assertDomMatchesEcho("initial", initialEchoDom, initialEcho);

  const homeBefore = await readJson("/api/v60/experience/home");
  initialHomeIdentity = homeIdentity(homeBefore);
  await inspectDocument("initial-grove");
  await capture("01-grove-return-echo");

  await page.locator(".dream-return-echo-recap summary").click();
  await page
    .locator(".dream-return-echo-recap[open]")
    .waitFor({ state: "visible" });
  expandedEchoDom = await readEchoDom();
  if (!expandedEchoDom.abuRecap.open) {
    fail("expanded:abu-recap-did-not-open");
  }
  assertDomMatchesEcho("expanded", expandedEchoDom, initialEcho);
  await inspectDocument("expanded-recap");
  await capture("02-expanded-abu-recap");

  await page.reload({ waitUntil: "networkidle" });
  await page
    .locator('main[data-experience-scope="dream"] .dream-grove-scene')
    .waitFor({ state: "visible" });
  refreshedEntry = await readJson("/api/v60/dream/entry");
  refreshedEcho = assertEntryContract("refresh", refreshedEntry);
  if (!refreshedEcho) throw new Error("refreshed-return-echo-contract-unavailable");
  refreshedCandidates = candidateProjection(refreshedEntry);
  if (!sameJson(refreshedCandidates, initialCandidates)) {
    fail("refresh:candidate-refs-or-order-changed");
  }
  if (!sameJson(refreshedEcho, initialEcho)) {
    fail("refresh:return-echo-projection-changed");
  }
  await assertCandidatesMatchDom("refresh", refreshedCandidates);
  refreshedEchoDom = await readEchoDom();
  assertDomMatchesEcho("refresh", refreshedEchoDom, refreshedEcho);

  const homeAfterDreamRefresh = await readJson("/api/v60/experience/home");
  refreshedHomeIdentity = homeIdentity(homeAfterDreamRefresh);
  if (!sameJson(refreshedHomeIdentity, initialHomeIdentity)) {
    fail("dream-refresh:owner-home-mingli-identity-changed");
  }
  await inspectDocument("refreshed-grove");
  await capture("03-refreshed-grove-return-echo");

  const sentinelCandidates = [
    ["echo_ref", initialEcho.echoRef],
    ["echo_hash", initialEcho.echoHash],
    ["encounter_ref", initialEcho.encounterRef],
    ["episode_title", initialEcho.episodeTitle],
    ["judgment.summary", initialEcho.judgment.summary],
    ["world_response.summary", initialEcho.worldResponse.summary],
    ...initialEcho.worldResponse.evidenceSummaries.map((value, index) => [
      `world_response.evidence_summaries[${index}]`,
      value,
    ]),
    ["still_to_observe.summary", initialEcho.stillToObserve.summary],
    ["abu_recap.meaning", initialEcho.abuRecap.meaning],
    ["abu_recap.boundary", initialEcho.abuRecap.boundary],
    ["abu_recap.next_attention", initialEcho.abuRecap.nextAttention],
  ];
  isolationSentinels = sentinelCandidates.filter(
    ([, value]) => typeof value === "string" && value.trim().length >= 8,
  );

  const homeUrl = new URL(targetUrl);
  homeUrl.searchParams.delete("scope");
  homeUrl.searchParams.delete("focus");
  homeUrl.searchParams.set("view", "mingli");
  await page.goto(homeUrl.toString(), { waitUntil: "networkidle" });
  await page
    .locator('main[data-experience-scope="home"]')
    .waitFor({ state: "visible" });
  if ((await page.locator(".dream-return-echo").count()) !== 0) {
    fail("home:dream-return-echo-node-present");
  }
  const homeAtNavigation = await readJson("/api/v60/experience/home");
  homeNavigationIdentity = homeIdentity(homeAtNavigation);
  if (!sameJson(homeNavigationIdentity, initialHomeIdentity)) {
    fail("home:owner-mingli-identity-changed");
  }
  const homeApiMarkup = JSON.stringify(homeAtNavigation);
  const homeDomMarkup = await page
    .locator("main")
    .evaluate((node) => node.outerHTML);
  for (const [label, value] of isolationSentinels) {
    if (homeApiMarkup.includes(value)) {
      fail(`home-api:dream-echo-value-leaked:${label}`);
    }
    if (homeDomMarkup.includes(value)) {
      fail(`home-dom:dream-echo-value-leaked:${label}`);
    }
  }
  await inspectDocument("home-mingli");
  await capture("04-home-mingli-isolation");

  await page.reload({ waitUntil: "networkidle" });
  await page
    .locator('main[data-experience-scope="home"]')
    .waitFor({ state: "visible" });
  if ((await page.locator(".dream-return-echo").count()) !== 0) {
    fail("home-refresh:dream-return-echo-node-present");
  }
  const finalHome = await readJson("/api/v60/experience/home");
  finalHomeIdentity = homeIdentity(finalHome);
  if (
    !sameJson(finalHomeIdentity, initialHomeIdentity) ||
    !sameJson(finalHomeIdentity, homeNavigationIdentity)
  ) {
    fail("home-refresh:owner-mingli-identity-changed");
  }
  const refreshedHomeApiMarkup = JSON.stringify(finalHome);
  const refreshedHomeDomMarkup = await page
    .locator("main")
    .evaluate((node) => node.outerHTML);
  for (const [label, value] of isolationSentinels) {
    if (refreshedHomeApiMarkup.includes(value)) {
      fail(`home-refresh-api:dream-echo-value-leaked:${label}`);
    }
    if (refreshedHomeDomMarkup.includes(value)) {
      fail(`home-refresh-dom:dream-echo-value-leaked:${label}`);
    }
  }
  await inspectDocument("home-mingli-refresh");
  await capture("05-home-mingli-refresh");
} catch (error) {
  fail(
    `fatal:${
      error instanceof Error ? `${error.message}\n${error.stack ?? ""}` : String(error)
    }`,
  );
}

const postRequests = observedRequests.filter(
  ({ method }) => method === "POST",
);
if (postRequests.length !== 0) {
  fail(
    `network:unexpected-post:${postRequests
      .map(({ pathname }) => pathname)
      .join(",")}`,
  );
}

const audit = {
  targetUrl: dreamUrl.toString(),
  initialEcho,
  refreshedEcho,
  refreshStable:
    initialEcho !== undefined &&
    refreshedEcho !== undefined &&
    sameJson(initialEcho, refreshedEcho),
  initialCandidates,
  refreshedCandidates,
  candidateOrderStable: sameJson(initialCandidates, refreshedCandidates),
  initialEchoDom,
  expandedEchoDom,
  refreshedEchoDom,
  detailExpanded: expandedEchoDom?.abuRecap.open === true,
  initialHomeIdentity,
  refreshedHomeIdentity,
  homeNavigationIdentity,
  finalHomeIdentity,
  homeIdentityStable:
    initialHomeIdentity !== null &&
    sameJson(initialHomeIdentity, refreshedHomeIdentity) &&
    sameJson(initialHomeIdentity, homeNavigationIdentity) &&
    sameJson(initialHomeIdentity, finalHomeIdentity),
  homeIsolationSentinelLabels: isolationSentinels.map(([label]) => label),
  postRequestCount: postRequests.length,
  requests: observedRequests.map(({ method, pathname }) => ({
    method,
    pathname,
  })),
  stageMetrics,
  screenshots,
  failures,
};
await writeFile(
  path.join(artifactDirectory, "runtime-audit.json"),
  `${JSON.stringify(audit, null, 2)}\n`,
  "utf8",
);

await context.close();
await browser.close();
if (failures.length) throw new Error(failures.join("\n"));
console.log(JSON.stringify(audit, null, 2));
