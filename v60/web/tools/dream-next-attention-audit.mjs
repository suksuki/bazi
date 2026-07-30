import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const v60Root = path.resolve(here, "../..");
const artifactDirectory = path.join(
  v60Root,
  ".artifacts/dream-next-attention",
);
const chromePath =
  process.env.V60_AUDIT_CHROME_PATH ??
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience";
const sessionToken = process.env.V60_AUDIT_SESSION_TOKEN;
const otherSessionToken = process.env.V60_AUDIT_OTHER_SESSION_TOKEN;
const restartRuntime =
  process.env.V60_AUDIT_RESTART_RUNTIME?.toLowerCase() !== "false";

if (!sessionToken) throw new Error("V60_AUDIT_SESSION_TOKEN is required");
if (!otherSessionToken) {
  throw new Error("V60_AUDIT_OTHER_SESSION_TOKEN is required");
}
await mkdir(artifactDirectory, { recursive: true });

const target = new URL(targetUrl);
if (
  restartRuntime &&
  !["127.0.0.1", "localhost"].includes(target.hostname)
) {
  throw new Error("runtime restart audit is restricted to localhost");
}

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
    url: target.origin,
    httpOnly: true,
    sameSite: "Lax",
  },
]);

const failures = [];
const requests = [];
const screenshots = {};
const stageMetrics = {};
let page;
let otherContext = null;

const fail = (message) => failures.push(message);
const sameJson = (left, right) => JSON.stringify(left) === JSON.stringify(right);

const attachPageObservers = (nextPage) => {
  nextPage.on("console", (message) => {
    if (message.type() === "error") fail(`console:${message.text()}`);
  });
  nextPage.on("pageerror", (error) => fail(`page:${error.message}`));
  nextPage.on("requestfailed", (request) => {
    fail(
      `request:${request.method()} ${request.url()} ${
        request.failure()?.errorText
      }`,
    );
  });
  nextPage.on("request", (request) => {
    let body = null;
    if (request.method() === "POST") {
      try {
        body = request.postDataJSON();
      } catch {
        body = request.postData();
      }
    }
    requests.push({
      body,
      method: request.method(),
      pathname: new URL(request.url()).pathname,
    });
  });
  nextPage.on("response", (response) => {
    if (response.status() >= 400) {
      fail(`response:${response.status()} ${response.url()}`);
    }
  });
};

const newPage = async () => {
  const nextPage = await context.newPage();
  attachPageObservers(nextPage);
  return nextPage;
};

const dreamUrl = new URL(targetUrl);
dreamUrl.searchParams.set("scope", "dream");
dreamUrl.searchParams.delete("view");
dreamUrl.searchParams.delete("focus");

const homeUrl = new URL(targetUrl);
homeUrl.searchParams.delete("scope");
homeUrl.searchParams.delete("focus");
homeUrl.searchParams.set("view", "mingli");

const readJson = async (pathname) =>
  page.evaluate(async (url) => {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${url}:${response.status}`);
    return response.json();
  }, pathname);

const readJsonOnPage = async (activePage, pathname) =>
  activePage.evaluate(async (url) => {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${url}:${response.status}`);
    return response.json();
  }, pathname);

const capture = async (stage) => {
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
  const screenshotPath = path.join(artifactDirectory, `${stage}.png`);
  await page.screenshot({ path: screenshotPath });
  screenshots[stage] = screenshotPath;
};

const candidateIdentity = (entry) =>
  (entry.grove?.candidates ?? []).map(
    ({ candidate_ref, display_order, domain }) => ({
      candidateRef: candidate_ref,
      displayOrder: display_order,
      domain,
    }),
  );

const homeIdentity = (home) => ({
  contextRef: home.context_ref,
  contextHash: home.context_hash,
  caseRef: home.case.case_ref,
  caseVersion: home.case.case_version,
  chartVersionRef: home.chart.chart_version_ref,
  chartHash: home.chart.chart_hash,
  lifeCaseRevisionRef: home.life_case.life_case_revision_ref,
  lifeCaseRevisionHash: home.life_case.revision_hash,
  readingRef: home.mingli.reading.reading_ref,
  readingHash: home.mingli.reading.reading_hash,
  readingDecisionRefs: home.mingli.reading.decision_refs,
  comparisonDecisionRef:
    home.lab.mechanism_comparison?.decision_ref ?? null,
  comparisonDecisionHash:
    home.lab.mechanism_comparison?.decision_hash ?? null,
});

const knowledgeIdentity = (manifest) => ({
  knowledgeProfiles: manifest.knowledge_profiles,
  candidateRuleProfiles: manifest.candidate_rule_profiles,
  quantFoundationProfiles: manifest.quant_foundation_profiles,
  sourceReviewProfiles: manifest.source_review_profiles,
  mechanismEvidenceProfiles: manifest.mechanism_evidence_profiles,
  timingEvidenceProfiles: manifest.timing_evidence_profiles,
  relationEffectRuleAdmission: manifest.relation_effect_rule_admission,
  knowledgeProfileSelection: manifest.knowledge_profile_selection,
});

const assertPrompt = (stage, entry, expectedStatus = null) => {
  if (entry.kind !== "GROVE") {
    fail(`${stage}:entry-is-not-grove`);
    return null;
  }
  const candidates = candidateIdentity(entry);
  if (
    candidates.length !== 3 ||
    new Set(candidates.map(({ candidateRef }) => candidateRef)).size !== 3 ||
    !sameJson(
      candidates.map(({ displayOrder }) => displayOrder),
      [1, 2, 3],
    )
  ) {
    fail(`${stage}:candidate-contract-invalid`);
  }
  const prompt = entry.grove.next_attention;
  const echo = entry.grove.return_echo;
  if (!prompt || !echo) {
    fail(`${stage}:attention-or-echo-missing`);
    return null;
  }
  if (
    prompt.contract_version !== "v60.dream-return-attention.001" ||
    prompt.source_echo_ref !== echo.echo_ref ||
    prompt.source_echo_hash !== echo.echo_hash ||
    prompt.source_encounter_ref !== echo.encounter_ref ||
    !candidates.some(
      ({ candidateRef }) => candidateRef === prompt.source_candidate_ref,
    ) ||
    typeof prompt.source_candidate_hash !== "string" ||
    prompt.source_candidate_hash.length !== 64 ||
    !Array.isArray(prompt.options) ||
    prompt.options.length < 2 ||
    prompt.options.length > 3 ||
    new Set(prompt.options.map(({ observation_ref }) => observation_ref))
      .size !== prompt.options.length ||
    prompt.semantics !== "DREAM_RETURN_ATTENTION_ONLY" ||
    prompt.evidence_role !== "NOT_EVIDENCE" ||
    prompt.tree_candidate_set_or_order_changed !== false ||
    prompt.question_changed !== false ||
    prompt.answer_changed !== false ||
    prompt.npc_choice_changed !== false ||
    prompt.outcome_changed !== false ||
    prompt.mingli_write_allowed !== false ||
    prompt.decision_write_allowed !== false ||
    prompt.knowledge_write_allowed !== false
  ) {
    fail(`${stage}:attention-contract-invalid`);
  }
  if (expectedStatus !== null && prompt.status !== expectedStatus) {
    fail(`${stage}:attention-status:${prompt.status}`);
  }
  if (
    (prompt.status === "AWAITING_SELECTION" && prompt.selection !== null) ||
    (prompt.status === "SELECTED" && !prompt.selection)
  ) {
    fail(`${stage}:attention-selection-status-mismatch`);
  }
  return { candidates, echo, prompt };
};

const readAttentionDom = async (status) => {
  const node = page.locator(
    `.dream-next-attention[data-next-attention-status="${status}"]`,
  );
  await node.waitFor({ state: "visible" });
  return node.evaluate((element) => ({
    attentionRef: element.getAttribute("data-attention-ref"),
    attentionHash: element.getAttribute("data-attention-hash"),
    observationRef: element.getAttribute("data-observation-ref"),
    sourceCandidateRef: element.getAttribute("data-source-candidate-ref"),
    sourceCandidateHash: element.getAttribute("data-source-candidate-hash"),
    treeRef: element.getAttribute("data-tree-ref"),
    optionRefs: [...element.querySelectorAll("[data-observation-ref]")].map(
      (option) => option.getAttribute("data-observation-ref"),
    ),
    semantics: element.getAttribute("data-semantics"),
    evidenceRole: element.getAttribute("data-evidence-role"),
    treeCandidateSetOrOrderChanged:
      element.getAttribute("data-tree-candidate-set-or-order-changed"),
    questionChanged: element.getAttribute("data-question-changed"),
    answerChanged: element.getAttribute("data-answer-changed"),
    npcChoiceChanged: element.getAttribute("data-npc-choice-changed"),
    outcomeChanged: element.getAttribute("data-outcome-changed"),
    mingliWriteAllowed: element.getAttribute("data-mingli-write-allowed"),
    decisionWriteAllowed: element.getAttribute("data-decision-write-allowed"),
    knowledgeWriteAllowed: element.getAttribute("data-knowledge-write-allowed"),
  }));
};

const assertDomBoundary = (stage, dom) => {
  if (
    dom.semantics !== "DREAM_RETURN_ATTENTION_ONLY" ||
    dom.evidenceRole !== "NOT_EVIDENCE" ||
    dom.treeCandidateSetOrOrderChanged !== "false" ||
    dom.questionChanged !== "false" ||
    dom.answerChanged !== "false" ||
    dom.npcChoiceChanged !== "false" ||
    dom.outcomeChanged !== "false" ||
    dom.mingliWriteAllowed !== "false" ||
    dom.decisionWriteAllowed !== "false" ||
    dom.knowledgeWriteAllowed !== "false"
  ) {
    fail(`${stage}:dom-boundary-invalid`);
  }
};

const restartManagedRuntime = async (stage) => {
  if (!restartRuntime) return { skipped: true };
  await page.close();
  const python =
    process.env.V60_AUDIT_PYTHON ?? path.join(v60Root, ".venv/bin/python");
  const port = Number(target.port || (target.protocol === "https:" ? 443 : 80));
  let output = "";
  try {
    output = execFileSync(
      python,
      [
        path.join(v60Root, "tools/local_runtime.py"),
        "restart",
        "--host",
        target.hostname,
        "--port",
        String(port),
      ],
      {
        cwd: v60Root,
        encoding: "utf8",
        maxBuffer: 2 * 1024 * 1024,
      },
    );
  } catch (error) {
    throw new Error(
      `${stage}:runtime-restart-failed:${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }
  page = await newPage();
  const result = {
    skipped: false,
    ready: output.includes('"status": "READY"'),
  };
  if (!result.ready) fail(`${stage}:runtime-restart-not-ready`);
  return result;
};

let initial;
let selected;
let restartedSelected;
let opening;
let restartedOpening;
let initialHome;
let finalHome;
let initialKnowledge;
let finalKnowledge;
let initialDecisionCount = null;
let selectedDecisionCount = null;
let finalDecisionCount = null;
let initialAttentionCounts = null;
let selectedAttentionCounts = null;
let finalAttentionCounts = null;
let primaryAccountRef = null;
let otherAccountRef = null;
const restartResults = {};

try {
  page = await newPage();
  await page.goto(dreamUrl.toString(), { waitUntil: "networkidle" });
  await page.locator(".dream-grove-scene").waitFor({ state: "visible" });
  const primarySession = await readJson("/api/v60/auth/me");
  primaryAccountRef = primarySession.account.account_ref;

  const initialEntry = await readJson("/api/v60/dream/entry");
  initial = assertPrompt("initial", initialEntry, "AWAITING_SELECTION");
  if (!initial) throw new Error("initial-attention-contract-unavailable");
  const awaitingDom = await readAttentionDom("AWAITING_SELECTION");
  assertDomBoundary("initial", awaitingDom);
  if (
    awaitingDom.sourceCandidateRef !== initial.prompt.source_candidate_ref ||
    awaitingDom.sourceCandidateHash !== initial.prompt.source_candidate_hash ||
    awaitingDom.treeRef !== initial.prompt.tree_ref ||
    !sameJson(
      awaitingDom.optionRefs,
      initial.prompt.options.map(({ observation_ref }) => observation_ref),
    )
  ) {
    fail("initial:dom-api-option-order-mismatch");
  }

  initialHome = homeIdentity(await readJson("/api/v60/experience/home"));
  const initialManifest = await readJson("/api/v60/system/manifest");
  initialKnowledge = knowledgeIdentity(initialManifest);
  const initialRuntime = await readJson("/api/v60/system/runtime-status");
  initialDecisionCount = initialRuntime.counts.decisions;
  initialAttentionCounts = {
    selections: initialRuntime.counts.return_attention_selections,
    applications: initialRuntime.counts.return_attention_applications,
  };
  await capture("01-awaiting-selection");

  const selectedOption = initial.prompt.options[0];
  const selectionResponse = page.waitForResponse((response) => {
    const request = response.request();
    if (
      request.method() !== "POST" ||
      new URL(response.url()).pathname !== "/api/v60/dream/command"
    ) {
      return false;
    }
    try {
      return request.postDataJSON()?.command === "SELECT_NEXT_ATTENTION";
    } catch {
      return false;
    }
  });
  await page
    .locator(
      `.dream-next-attention [data-observation-ref="${selectedOption.observation_ref}"]`,
    )
    .click();
  const selectedResponse = await selectionResponse;
  if (!selectedResponse.ok()) {
    fail(`selection-response:${selectedResponse.status()}`);
  }
  const selectedEntry = await selectedResponse.json();
  const selectionRequestBody = selectedResponse.request().postDataJSON();
  selected = assertPrompt("selected", selectedEntry, "SELECTED");
  if (!selected?.prompt.selection) {
    throw new Error("selected-attention-contract-unavailable");
  }
  const selectedDom = await readAttentionDom("SELECTED");
  assertDomBoundary("selected", selectedDom);
  if (
    selectedDom.attentionRef !== selected.prompt.selection.attention_ref ||
    selectedDom.attentionHash !== selected.prompt.selection.attention_hash ||
    selectedDom.observationRef !== selectedOption.observation_ref
  ) {
    fail("selected:dom-api-selection-identity-mismatch");
  }
  if (!sameJson(selected.candidates, initial.candidates)) {
    fail("selected:candidate-order-changed");
  }
  const selectedRuntime = await readJson("/api/v60/system/runtime-status");
  selectedDecisionCount = selectedRuntime.counts.decisions;
  selectedAttentionCounts = {
    selections: selectedRuntime.counts.return_attention_selections,
    applications: selectedRuntime.counts.return_attention_applications,
  };
  if (selectedDecisionCount !== initialDecisionCount) {
    fail("selected:cognition-decision-count-changed");
  }
  if (
    selectedAttentionCounts.selections !== initialAttentionCounts.selections + 1 ||
    selectedAttentionCounts.applications !== initialAttentionCounts.applications
  ) {
    fail("selected:attention-row-count-invalid");
  }

  const replayedEntry = await page.evaluate(async (body) => {
    const response = await fetch("/api/v60/dream/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`selection-replay:${response.status}`);
    }
    return response.json();
  }, selectionRequestBody);
  if (!sameJson(replayedEntry, selectedEntry)) {
    fail("selected:exact-replay-changed-result");
  }
  const replayRuntime = await readJson("/api/v60/system/runtime-status");
  if (
    replayRuntime.counts.return_attention_selections !==
      selectedAttentionCounts.selections ||
    replayRuntime.counts.return_attention_applications !==
      selectedAttentionCounts.applications ||
    replayRuntime.counts.decisions !== initialDecisionCount
  ) {
    fail("selected:exact-replay-created-write");
  }
  await capture("02-selected");

  await page.reload({ waitUntil: "networkidle" });
  await page.locator(".dream-grove-scene").waitFor({ state: "visible" });
  const refreshedSelected = assertPrompt(
    "selected-refresh",
    await readJson("/api/v60/dream/entry"),
    "SELECTED",
  );
  if (
    !refreshedSelected ||
    !sameJson(refreshedSelected.prompt, selected.prompt) ||
    !sameJson(refreshedSelected.candidates, initial.candidates)
  ) {
    fail("selected-refresh:projection-changed");
  }
  await capture("03-selected-refresh");

  restartResults.selected = await restartManagedRuntime("selected");
  await page.goto(dreamUrl.toString(), { waitUntil: "networkidle" });
  await page.locator(".dream-grove-scene").waitFor({ state: "visible" });
  restartedSelected = assertPrompt(
    "selected-restart",
    await readJson("/api/v60/dream/entry"),
    "SELECTED",
  );
  if (
    !restartedSelected ||
    !sameJson(restartedSelected.prompt, selected.prompt) ||
    !sameJson(restartedSelected.candidates, initial.candidates)
  ) {
    fail("selected-restart:projection-changed");
  }
  await capture("04-selected-restart");

  const sourceCandidate = page.locator(
    `.grove-tree-choice[data-candidate-ref="${selected.prompt.source_candidate_ref}"]`,
  );
  await sourceCandidate.waitFor({ state: "visible" });
  const encounterResponsePromise = page.waitForResponse((response) => {
    const request = response.request();
    return (
      request.method() === "POST" &&
      new URL(response.url()).pathname ===
        `/api/v60/dream/grove/${encodeURIComponent(
          selected.prompt.source_candidate_ref,
        )}`
    );
  });
  await sourceCandidate.click();
  const encounterResponse = await encounterResponsePromise;
  if (!encounterResponse.ok()) {
    fail(`same-tree-response:${encounterResponse.status()}`);
  }
  const encounter = await encounterResponse.json();
  opening = encounter.opening_attention;
  if (
    !opening ||
    opening.contract_version !== "v60.dream-opening-attention.001" ||
    opening.attention_ref !== selected.prompt.selection.attention_ref ||
    opening.attention_hash !== selected.prompt.selection.attention_hash ||
    opening.source_tree_ref !== selected.prompt.tree_ref ||
    opening.target_tree_ref !== selected.prompt.tree_ref ||
    opening.target_encounter_ref !== encounter.encounter.encounter_ref ||
    opening.observation_ref !== selectedOption.observation_ref ||
    opening.semantics !== "DREAM_RETURN_ATTENTION_ONLY" ||
    opening.evidence_role !== "NOT_EVIDENCE" ||
    opening.tree_candidate_set_or_order_changed !== false ||
    opening.question_changed !== false ||
    opening.answer_changed !== false ||
    opening.npc_choice_changed !== false ||
    opening.outcome_changed !== false ||
    opening.mingli_write_allowed !== false ||
    opening.decision_write_allowed !== false ||
    opening.knowledge_write_allowed !== false ||
    opening.read_only !== true
  ) {
    fail("opening:contract-invalid");
  }
  const openingNode = page.locator(
    '.dream-opening-attention[data-opening-attention-status="REMEMBERED"]',
  );
  await openingNode.waitFor({ state: "visible" });
  const openingDom = await openingNode.evaluate((node) => ({
    applicationRef: node.getAttribute("data-application-ref"),
    applicationHash: node.getAttribute("data-application-hash"),
    attentionRef: node.getAttribute("data-attention-ref"),
    attentionHash: node.getAttribute("data-attention-hash"),
    sourceTreeRef: node.getAttribute("data-source-tree-ref"),
    targetTreeRef: node.getAttribute("data-target-tree-ref"),
    targetEncounterRef: node.getAttribute("data-target-encounter-ref"),
    observationRef: node.getAttribute("data-observation-ref"),
    semantics: node.getAttribute("data-semantics"),
    evidenceRole: node.getAttribute("data-evidence-role"),
    treeCandidateSetOrOrderChanged:
      node.getAttribute("data-tree-candidate-set-or-order-changed"),
    questionChanged: node.getAttribute("data-question-changed"),
    answerChanged: node.getAttribute("data-answer-changed"),
    npcChoiceChanged: node.getAttribute("data-npc-choice-changed"),
    outcomeChanged: node.getAttribute("data-outcome-changed"),
    mingliWriteAllowed: node.getAttribute("data-mingli-write-allowed"),
    decisionWriteAllowed: node.getAttribute("data-decision-write-allowed"),
    knowledgeWriteAllowed: node.getAttribute("data-knowledge-write-allowed"),
    readOnly: node.getAttribute("data-read-only"),
    label: node.querySelector("strong")?.textContent?.trim() ?? null,
    summary: node.querySelector("p")?.textContent?.trim() ?? null,
    remembered:
      node.querySelector("small")?.textContent?.includes("世界已记住") ?? false,
  }));
  if (
    openingDom.applicationRef !== opening.application_ref ||
    openingDom.applicationHash !== opening.application_hash ||
    openingDom.attentionRef !== opening.attention_ref ||
    openingDom.attentionHash !== opening.attention_hash ||
    openingDom.sourceTreeRef !== opening.source_tree_ref ||
    openingDom.targetTreeRef !== opening.target_tree_ref ||
    openingDom.targetEncounterRef !== opening.target_encounter_ref ||
    openingDom.observationRef !== opening.observation_ref ||
    openingDom.semantics !== "DREAM_RETURN_ATTENTION_ONLY" ||
    openingDom.evidenceRole !== "NOT_EVIDENCE" ||
    openingDom.treeCandidateSetOrOrderChanged !== "false" ||
    openingDom.questionChanged !== "false" ||
    openingDom.answerChanged !== "false" ||
    openingDom.npcChoiceChanged !== "false" ||
    openingDom.outcomeChanged !== "false" ||
    openingDom.mingliWriteAllowed !== "false" ||
    openingDom.decisionWriteAllowed !== "false" ||
    openingDom.knowledgeWriteAllowed !== "false" ||
    openingDom.readOnly !== "true" ||
    openingDom.label !== opening.label ||
    openingDom.summary !== opening.summary ||
    !openingDom.remembered
  ) {
    fail("opening:dom-api-identity-mismatch");
  }
  const encounterWithoutOpening = {
    ...encounter,
    opening_attention: null,
  };
  const encounterWithoutOpeningJson = JSON.stringify(encounterWithoutOpening);
  for (const value of [
    opening.application_ref,
    opening.application_hash,
    opening.attention_ref,
    opening.attention_hash,
    opening.observation_ref,
  ]) {
    if (encounterWithoutOpeningJson.includes(value)) {
      fail("opening:attention-identity-leaked-outside-projection");
    }
  }
  await capture("05-same-tree-opening");

  await page.reload({ waitUntil: "networkidle" });
  await page
    .locator('.dream-opening-attention[data-opening-attention-status="REMEMBERED"]')
    .waitFor({ state: "visible" });
  const refreshedEncounter = await readJson("/api/v60/dream/encounter");
  if (!sameJson(refreshedEncounter.opening_attention, opening)) {
    fail("opening-refresh:projection-changed");
  }
  await capture("06-opening-refresh");

  restartResults.opening = await restartManagedRuntime("opening");
  await page.goto(dreamUrl.toString(), { waitUntil: "networkidle" });
  await page
    .locator('.dream-opening-attention[data-opening-attention-status="REMEMBERED"]')
    .waitFor({ state: "visible" });
  const restartedEncounter = await readJson("/api/v60/dream/encounter");
  restartedOpening = restartedEncounter.opening_attention;
  if (!sameJson(restartedOpening, opening)) {
    fail("opening-restart:projection-changed");
  }
  await capture("07-opening-restart");

  await page.goto(homeUrl.toString(), { waitUntil: "networkidle" });
  await page
    .locator('main[data-experience-scope="home"]')
    .waitFor({ state: "visible" });
  finalHome = homeIdentity(await readJson("/api/v60/experience/home"));
  finalKnowledge = knowledgeIdentity(
    await readJson("/api/v60/system/manifest"),
  );
  const finalRuntime = await readJson("/api/v60/system/runtime-status");
  finalDecisionCount = finalRuntime.counts.decisions;
  finalAttentionCounts = {
    selections: finalRuntime.counts.return_attention_selections,
    applications: finalRuntime.counts.return_attention_applications,
  };
  if (!sameJson(finalHome, initialHome)) {
    fail("home:mingli-identity-changed");
  }
  if (!sameJson(finalKnowledge, initialKnowledge)) {
    fail("home:knowledge-manifest-changed");
  }
  if (finalDecisionCount !== initialDecisionCount) {
    fail("home:cognition-decision-count-changed");
  }
  if (
    finalAttentionCounts.selections !== initialAttentionCounts.selections + 1 ||
    finalAttentionCounts.applications !== initialAttentionCounts.applications + 1
  ) {
    fail("home:attention-row-count-invalid");
  }
  if (
    finalRuntime.integrity.invalid_dream_return_attention_selections !== 0 ||
    finalRuntime.integrity.invalid_dream_return_attention_applications !== 0
  ) {
    fail("home:return-attention-runtime-integrity-invalid");
  }
  const homeApi = JSON.stringify(await readJson("/api/v60/experience/home"));
  const homeDom = await page.locator("main").evaluate((node) => node.outerHTML);
  for (const [label, value] of [
    ["attention_ref", opening?.attention_ref],
    ["attention_hash", opening?.attention_hash],
    ["application_ref", opening?.application_ref],
    ["application_hash", opening?.application_hash],
    ["observation_ref", opening?.observation_ref],
  ]) {
    if (value && homeApi.includes(value)) {
      fail(`home-api:attention-leak:${label}`);
    }
    if (value && homeDom.includes(value)) {
      fail(`home-dom:attention-leak:${label}`);
    }
  }
  if (
    (await page.locator(".dream-next-attention").count()) !== 0 ||
    (await page.locator(".dream-opening-attention").count()) !== 0
  ) {
    fail("home:dream-attention-node-present");
  }
  await capture("08-home-isolation");

  otherContext = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  await otherContext.addCookies([
    {
      name: "abu_v60_session",
      value: otherSessionToken,
      url: target.origin,
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
  const otherPage = await otherContext.newPage();
  await otherPage.goto(dreamUrl.toString(), { waitUntil: "networkidle" });
  const otherSession = await readJsonOnPage(otherPage, "/api/v60/auth/me");
  otherAccountRef = otherSession.account.account_ref;
  if (otherAccountRef === primaryAccountRef) {
    fail("other-account:same-account-session");
  }
  const otherEntryJson = JSON.stringify(
    await readJsonOnPage(otherPage, "/api/v60/dream/entry"),
  );
  const otherDom = await otherPage.locator("main").evaluate((node) => node.outerHTML);
  for (const [label, value] of [
    ["attention_ref", opening?.attention_ref],
    ["attention_hash", opening?.attention_hash],
    ["application_ref", opening?.application_ref],
    ["application_hash", opening?.application_hash],
  ]) {
    if (value && otherEntryJson.includes(value)) {
      fail(`other-account-api:attention-leak:${label}`);
    }
    if (value && otherDom.includes(value)) {
      fail(`other-account-dom:attention-leak:${label}`);
    }
  }
  await otherPage.screenshot({
    path: path.join(artifactDirectory, "09-other-account-isolation.png"),
  });
  screenshots["09-other-account-isolation"] = path.join(
    artifactDirectory,
    "09-other-account-isolation.png",
  );
  await otherContext.close();
  otherContext = null;
} catch (error) {
  fail(
    `fatal:${
      error instanceof Error
        ? `${error.message}\n${error.stack ?? ""}`
        : String(error)
    }`,
  );
}

const postRequests = requests.filter(({ method }) => method === "POST");
const dreamCommands = postRequests
  .filter(({ pathname }) => pathname === "/api/v60/dream/command")
  .map(({ body }) =>
    typeof body === "object" && body !== null ? body.command : null,
  );
const groveSelections = postRequests.filter(({ pathname }) =>
  pathname.startsWith("/api/v60/dream/grove/"),
);
const nonDreamPosts = postRequests.filter(
  ({ pathname }) =>
    pathname !== "/api/v60/dream/command" &&
    !pathname.startsWith("/api/v60/dream/grove/"),
);
if (
  !sameJson(dreamCommands, [
    "SELECT_NEXT_ATTENTION",
    "SELECT_NEXT_ATTENTION",
  ])
) {
  fail(`network:dream-command-sequence:${JSON.stringify(dreamCommands)}`);
}
if (
  groveSelections.length !== 1 ||
  groveSelections[0].pathname !==
    `/api/v60/dream/grove/${encodeURIComponent(
      selected?.prompt.source_candidate_ref ?? "",
    )}`
) {
  fail("network:same-tree-selection-invalid");
}
if (nonDreamPosts.length !== 0) {
  fail(
    `network:non-dream-post:${nonDreamPosts
      .map(({ pathname }) => pathname)
      .join(",")}`,
  );
}

const audit = {
  targetUrl: dreamUrl.toString(),
  restartRuntime,
  restartResults,
  initialPrompt: initial?.prompt ?? null,
  selectedPrompt: selected?.prompt ?? null,
  restartedSelectedPrompt: restartedSelected?.prompt ?? null,
  opening,
  restartedOpening,
  initialCandidates: initial?.candidates ?? null,
  initialHome,
  finalHome,
  initialKnowledge,
  finalKnowledge,
  initialDecisionCount,
  selectedDecisionCount,
  finalDecisionCount,
  initialAttentionCounts,
  selectedAttentionCounts,
  finalAttentionCounts,
  primaryAccountRef,
  otherAccountRef,
  requests,
  screenshots,
  stageMetrics,
  failures,
};
await writeFile(
  path.join(artifactDirectory, "runtime-audit.json"),
  `${JSON.stringify(audit, null, 2)}\n`,
  "utf8",
);

if (page && !page.isClosed()) await page.close();
if (otherContext) await otherContext.close();
await context.close();
await browser.close();
if (failures.length) throw new Error(failures.join("\n"));
console.log(JSON.stringify(audit, null, 2));
