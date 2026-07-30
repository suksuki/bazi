import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(
  here,
  "../../.artifacts/mechanism-decision-trace",
);
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience";
const sessionToken = process.env.V60_AUDIT_SESSION_TOKEN;
const pendingSessionToken = process.env.V60_PENDING_AUDIT_SESSION_TOKEN;

if (!sessionToken) throw new Error("V60_AUDIT_SESSION_TOKEN is required");
if (!pendingSessionToken) {
  throw new Error("V60_PENDING_AUDIT_SESSION_TOKEN is required");
}
await mkdir(artifactDirectory, { recursive: true });

const browser = await chromium.launch({
  executablePath: chromePath,
  headless: true,
});
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const sessionCookie = (token) => ({
  name: "abu_v60_session",
  value: token,
  url: new URL(targetUrl).origin,
  httpOnly: true,
  sameSite: "Lax",
});
await context.addCookies([sessionCookie(sessionToken)]);
const page = await context.newPage();
const failures = [];
const comparisonMutations = [];

page.on("console", (message) => {
  if (message.type() === "error") failures.push(`console:${message.text()}`);
});
page.on("pageerror", (error) => failures.push(`page:${error.message}`));
page.on("request", (request) => {
  const url = new URL(request.url());
  if (
    request.method() !== "GET" &&
    url.pathname === "/api/v60/experience/home/mechanism-comparison"
  ) {
    comparisonMutations.push(`${request.method()} ${url.pathname}`);
  }
});
page.on("requestfailed", (request) => {
  failures.push(
    `request:${request.method()} ${request.url()} ${request.failure()?.errorText}`,
  );
});
page.on("response", (response) => {
  if (response.status() >= 400) {
    failures.push(`response:${response.status()} ${response.url()}`);
  }
});

const openView = async (view) => {
  const url = new URL(targetUrl);
  url.searchParams.set("view", view);
  await page.goto(url.toString(), { waitUntil: "networkidle" });
};
const screenshot = async (name, locator) => {
  await locator.scrollIntoViewIfNeeded();
  const screenshotPath = path.join(artifactDirectory, `${name}.png`);
  await page.screenshot({ path: screenshotPath });
  return screenshotPath;
};
const readTraceIdentity = async (locator) => ({
  decisionRef: await locator.getAttribute("data-decision-ref"),
  decisionHash: await locator.getAttribute("data-decision-hash"),
  selectedCandidateRef: await locator.getAttribute(
    "data-selected-candidate-ref",
  ),
  readingBound: await locator.getAttribute("data-reading-bound"),
  traceIntegrity: await locator.getAttribute("data-trace-integrity"),
  traceVersion: await locator.getAttribute("data-trace-version"),
});
const assertTraceCopy = async (view, locator, rationale) => {
  const text = await locator.innerText();
  for (const expected of [
    "同一份关注排序",
    "身份与覆盖已核验",
    "为什么先追查它",
    "为什么还不能裁决",
    "候选覆盖完整",
    "所选证据已绑定并由 Provider 引用",
    "Reading 已绑定",
    "本次纳入",
    "原局机制候选证据",
    "本次未绑定",
    "来源可用性",
    "时序激活",
    "机制资格",
    "专业准入",
    "校准与概率",
    "专业选择未合格",
    "专业裁决未授权",
    "概率主张未授权",
    "canonical 命理回写禁止",
  ]) {
    if (!text.includes(expected)) failures.push(`${view}:missing:${expected}`);
  }
  if (!text.includes(rationale)) failures.push(`${view}:rationale-mismatch`);
  if (/Provider confidence\s*[:：]?\s*[0-9]/.test(text)) {
    failures.push(`${view}:numeric-provider-confidence-exposed`);
  }
  const layout = await locator.evaluate((element) => {
    const quote = element.querySelector(".mechanism-decision-trace-grid blockquote");
    const style = quote ? getComputedStyle(quote) : null;
    return {
      quoteFound: Boolean(quote),
      fontSize: style?.fontSize ?? null,
      marginBottom: style?.marginBottom ?? null,
      paddingTop: style?.paddingTop ?? null,
      paddingLeft: style?.paddingLeft ?? null,
      horizontalOverflow: element.scrollWidth > element.clientWidth,
    };
  });
  if (
    !layout.quoteFound ||
    layout.fontSize !== "9px" ||
    layout.marginBottom !== "0px" ||
    layout.paddingTop !== "0px" ||
    layout.paddingLeft !== "8px" ||
    layout.horizontalOverflow
  ) {
    failures.push(`${view}:trace-layout-contract-drift`);
  }
  return text;
};

await openView("mingli");
const mingliTrace = page.locator(
  '.mechanism-decision-trace[data-mode="mingli"]',
);
await mingliTrace.waitFor({ state: "visible" });
const homeSnapshot = await page.evaluate(async () => {
  const response = await fetch("/api/v60/experience/home");
  if (!response.ok) throw new Error(`home:${response.status}`);
  return response.json();
});
const comparison = homeSnapshot.lab?.mechanism_comparison;
const trace = comparison?.decision_trace;
const reading = homeSnapshot.mingli?.reading;
const qualification = homeSnapshot.mingli?.mechanism_qualification;

if (!trace || trace.trace_integrity_status !== "VERIFIED") {
  failures.push("api:verified-decision-trace-missing");
}
if (
  trace?.decision_ref !== comparison?.decision_ref ||
  trace?.decision_hash !== comparison?.decision_hash ||
  trace?.selected_candidate_ref !== comparison?.selected_candidate_ref
) {
  failures.push("api:comparison-trace-identity-mismatch");
}
if (
  !reading?.decision_refs?.includes(trace?.decision_ref) ||
  reading?.decision_refs?.length !== 1
) {
  failures.push("api:reading-decision-binding-mismatch");
}
if (
  trace?.candidate_coverage_complete !== true ||
  trace?.selected_evidence_bound !== true ||
  trace?.selected_evidence_use_semantics !==
    "PROVIDER_CITED_BOUND_EVIDENCE" ||
  trace?.reviewed_candidate_refs?.length !==
    trace?.attention_candidate_refs?.length ||
  trace?.attention_candidate_refs?.length !== comparison?.candidate_count
) {
  failures.push("api:decision-coverage-invalid");
}
if (
  trace?.authority !== "LLM_REASONER" ||
  trace?.gate_disposition !== "ADMITTED" ||
  trace?.decision_record_allowed !== true
) {
  failures.push("api:expected-llm-gate-admission-missing");
}
if (
  trace?.canonical_domain_write_allowed !== false ||
  trace?.professional_selection_qualified !== false ||
  trace?.professional_verdict_allowed !== false ||
  trace?.probability_claim_allowed !== false ||
  trace?.read_only !== true
) {
  failures.push("api:forbidden-decision-authority-enabled");
}
if (
  JSON.stringify(trace?.admitted_input_scopes) !==
  JSON.stringify(["MECHANISM_CANDIDATE_EVIDENCE"])
) {
  failures.push("api:admitted-input-scope-mismatch");
}
const expectedUnboundScopes = [
  "SOURCE_USABILITY",
  "TIMING_ACTIVATION",
  "MECHANISM_QUALIFICATION",
  "PROFESSIONAL_ADMISSION",
  "CALIBRATION",
];
if (
  JSON.stringify(trace?.unbound_input_scopes) !==
  JSON.stringify(expectedUnboundScopes)
) {
  failures.push("api:unbound-input-scope-mismatch");
}
if (
  trace?.counter_evidence_semantics !==
    "BOUND_REF_ONLY_NOT_PROFESSIONALLY_ADMITTED" ||
  trace?.candidate_coverage_semantics !==
    "PROVIDER_REVIEWED_ATTENTION_CANDIDATES" ||
  trace?.evidence_use_semantics !== "PROVIDER_CITED_BOUND_EVIDENCE" ||
  trace?.provider_confidence_semantics !==
    "RECORDED_UNCALIBRATED_NOT_PRODUCT_AUTHORITY" ||
  trace?.selection_rationale_contract !==
    "FREE_TEXT_NO_DISTINCT_SELECTION_BASIS_FIELD"
) {
  failures.push("api:decision-semantics-mismatch");
}
const selectedQualification = qualification?.candidates?.find(
  (candidate) => candidate.candidate_ref === trace?.selected_candidate_ref,
);
if (
  !selectedQualification ||
  selectedQualification.professional_admission !== false ||
  selectedQualification.unresolved_or_unadmitted_count < 1
) {
  failures.push("api:selected-candidate-professional-gap-missing");
}

const mingliIdentity = await readTraceIdentity(mingliTrace);
await assertTraceCopy(
  "mingli",
  mingliTrace,
  comparison?.rationale_summary ?? trace?.route_reason,
);
const mingliScreenshot = await screenshot(
  "01-mingli-verified-decision-handoff",
  mingliTrace,
);

await openView("lab");
const labTrace = page.locator('.mechanism-decision-trace[data-mode="lab"]');
await labTrace.waitFor({ state: "visible" });
const labIdentity = await readTraceIdentity(labTrace);
await labTrace.locator(".mechanism-decision-identity summary").click();
const labText = await assertTraceCopy(
  "lab",
  labTrace,
  comparison?.rationale_summary ?? trace?.route_reason,
);
for (const expected of ["还需要", "Counter refs", "仅绑定引用，不是专业反证"]) {
  if (!labText.includes(expected)) failures.push(`lab:missing:${expected}`);
}
const selectedLabCandidate = page.locator(
  '.mechanism-qualification details[data-selected="true"]',
);
if ((await selectedLabCandidate.count()) !== 1) {
  failures.push("lab:selected-qualification-candidate-missing");
} else {
  const selectedLabel = await selectedLabCandidate.innerText();
  const selectedCandidateRef = await selectedLabCandidate.getAttribute(
    "data-candidate-ref",
  );
  if (!selectedLabel.includes("当前优先追查")) {
    failures.push("lab:selected-qualification-label-missing");
  }
  if (selectedCandidateRef !== trace?.selected_candidate_ref) {
    failures.push("lab:selected-qualification-candidate-mismatch");
  }
}
const labScreenshot = await screenshot(
  "02-lab-decision-gaps-and-identity",
  labTrace,
);

await openView("abu");
const abuTrace = page.locator('.mechanism-decision-trace[data-mode="abu"]');
await abuTrace.waitFor({ state: "visible" });
const abuIdentity = await readTraceIdentity(abuTrace);
await assertTraceCopy(
  "abu",
  abuTrace,
  comparison?.rationale_summary ?? trace?.route_reason,
);
const abuScreenshot = await screenshot(
  "03-abu-same-decision-boundary",
  abuTrace,
);

for (const [view, identity] of [
  ["mingli", mingliIdentity],
  ["lab", labIdentity],
  ["abu", abuIdentity],
]) {
  if (
    identity.decisionRef !== trace?.decision_ref ||
    identity.decisionHash !== trace?.decision_hash ||
    identity.selectedCandidateRef !== trace?.selected_candidate_ref ||
    identity.readingBound !== "true" ||
    identity.traceIntegrity !== "VERIFIED" ||
    identity.traceVersion !== trace?.trace_version
  ) {
    failures.push(`${view}:dom-api-decision-identity-mismatch`);
  }
}
if (
  JSON.stringify(mingliIdentity) !== JSON.stringify(labIdentity) ||
  JSON.stringify(mingliIdentity) !== JSON.stringify(abuIdentity)
) {
  failures.push("views:decision-identity-mismatch");
}

await page.reload({ waitUntil: "networkidle" });
const reloadedTrace = page.locator(
  '.mechanism-decision-trace[data-mode="abu"]',
);
await reloadedTrace.waitFor({ state: "visible" });
if (
  JSON.stringify(await readTraceIdentity(reloadedTrace)) !==
  JSON.stringify(abuIdentity)
) {
  failures.push("reload:decision-identity-drift");
}

await context.addCookies([sessionCookie(pendingSessionToken)]);
await openView("mingli");
const pendingTrace = page.locator(
  '.mechanism-decision-trace[data-mode="mingli"][data-status="NOT_RUN"]',
);
await pendingTrace.waitFor({ state: "visible" });
const pendingSnapshot = await page.evaluate(async () => {
  const response = await fetch("/api/v60/experience/home");
  if (!response.ok) throw new Error(`pending-home:${response.status}`);
  return response.json();
});
const pendingComparison = pendingSnapshot.lab?.mechanism_comparison;
const pendingCandidateCount = Number(
  await pendingTrace.getAttribute("data-candidate-count"),
);
if (
  pendingComparison?.decision_ref !== null ||
  pendingComparison?.decision_trace !== null ||
  pendingComparison?.status !== "NOT_RUN" ||
  pendingComparison?.candidate_count < 2 ||
  pendingCandidateCount !== pendingComparison?.candidate_count ||
  (await pendingTrace.getAttribute("data-pending-kind")) !==
    "MULTIPLE_CANDIDATES"
) {
  failures.push("pending:multiple-candidate-contract-mismatch");
}
const pendingText = await pendingTrace.innerText();
for (const expected of [
  "候选仍在并列核查",
  "尚无 Decision",
  `当前有 ${pendingCandidateCount} 条结构候选`,
  "系统不会在页面里自行挑选",
]) {
  if (!pendingText.includes(expected)) failures.push(`pending:missing:${expected}`);
}
const pendingScreenshot = await screenshot(
  "04-mingli-pending-candidate-boundary",
  pendingTrace,
);

if (comparisonMutations.length) {
  failures.push(`read-only:comparison-mutation:${comparisonMutations.join(",")}`);
}

const metrics = await page.evaluate(() => ({
  bodyScrollHeight: document.body.scrollHeight,
  bodyScrollWidth: document.body.scrollWidth,
  viewportHeight: window.innerHeight,
  viewportWidth: window.innerWidth,
}));
if (
  metrics.bodyScrollHeight > metrics.viewportHeight ||
  metrics.bodyScrollWidth > metrics.viewportWidth
) {
  failures.push("experience:document-scroll");
}

const audit = {
  targetUrl,
  decisionRef: trace?.decision_ref,
  decisionHash: trace?.decision_hash,
  readingRef: reading?.reading_ref,
  selectedCandidateRef: trace?.selected_candidate_ref,
  pendingCandidateCount,
  authority: trace?.authority,
  gateDisposition: trace?.gate_disposition,
  candidateCoverage: `${trace?.reviewed_candidate_refs?.length}/${trace?.attention_candidate_refs?.length}`,
  boundEvidenceCount: trace?.bound_evidence_refs?.length,
  evidenceUsedCount: trace?.evidence_refs_used?.length,
  admittedInputScopes: trace?.admitted_input_scopes,
  unboundInputScopes: trace?.unbound_input_scopes,
  permissions: {
    decisionRecordAllowed: trace?.decision_record_allowed,
    professionalSelectionQualified: trace?.professional_selection_qualified,
    professionalVerdictAllowed: trace?.professional_verdict_allowed,
    probabilityClaimAllowed: trace?.probability_claim_allowed,
    canonicalDomainWriteAllowed: trace?.canonical_domain_write_allowed,
  },
  comparisonMutations,
  screenshots: {
    mingliScreenshot,
    labScreenshot,
    abuScreenshot,
    pendingScreenshot,
  },
  metrics,
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
