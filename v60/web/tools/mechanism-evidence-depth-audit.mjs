import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(
  here,
  "../../.artifacts/mechanism-evidence-depth",
);
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience";
const sessionToken = process.env.V60_AUDIT_SESSION_TOKEN;

if (!sessionToken) throw new Error("V60_AUDIT_SESSION_TOKEN is required");
await mkdir(artifactDirectory, { recursive: true });

const browser = await chromium.launch({
  executablePath: chromePath,
  headless: true,
});
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
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

page.on("console", (message) => {
  if (message.type() === "error") failures.push(`console:${message.text()}`);
});
page.on("pageerror", (error) => failures.push(`page:${error.message}`));
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
const screenshot = async (name) => {
  const screenshotPath = path.join(artifactDirectory, `${name}.png`);
  await page.screenshot({ path: screenshotPath });
  return screenshotPath;
};

await openView("mingli");
const mingliDisclosure = page.locator(".mechanism-evidence-contrast-disclosure");
await mingliDisclosure.waitFor({ state: "visible" });
await mingliDisclosure.locator("summary").click();
const mingliDepth = mingliDisclosure.locator(".mechanism-evidence-contrast");
const depthRef = await mingliDepth.getAttribute("data-depth-ref");
const mingliText = await mingliDepth.innerText();
for (const expected of [
  "候选证据对照",
  "不计分 · 不判旺衰",
  "起点",
  "去向",
  "专业准入仍待证据",
]) {
  if (!mingliText.includes(expected)) failures.push(`mingli:missing:${expected}`);
}
const homeSnapshot = await page.evaluate(async () => {
  const response = await fetch("/api/v60/experience/home");
  if (!response.ok) throw new Error(`home:${response.status}`);
  return response.json();
});
const depth = homeSnapshot.mingli?.mechanism_evidence_depth;
if (depth?.depth_ref !== depthRef) {
  failures.push("mingli:dom-api-depth-ref-mismatch");
}
if (
  homeSnapshot.lab?.mechanism_evidence_depth_ref !== depthRef ||
  homeSnapshot.lab?.mechanism_evidence_depth_hash !== depth?.depth_hash
) {
  failures.push("mingli:shared-depth-identity-mismatch");
}
if (
  depth?.professional_verdict_allowed !== false ||
  depth?.probability_claim_allowed !== false ||
  depth?.canonical_write_allowed !== false
) {
  failures.push("mingli:forbidden-authority-enabled");
}
for (const candidate of depth?.candidates ?? []) {
  if (
    candidate.evidence_score_status !== "NOT_COMPUTED" ||
    candidate.professional_admission !== false
  ) {
    failures.push(`mingli:candidate-overreach:${candidate.candidate_ref}`);
  }
}
const candidateCount = await mingliDepth
  .locator(".mechanism-evidence-candidate")
  .count();
if (candidateCount !== depth?.candidates?.length) {
  failures.push("mingli:candidate-count-mismatch");
}
const mingliScreenshot = await screenshot("01-mingli-candidate-evidence-depth");

await openView("lab");
const labDepth = page.locator(".mechanism-evidence-contrast");
await labDepth.waitFor({ state: "visible" });
if ((await labDepth.getAttribute("data-depth-ref")) !== depthRef) {
  failures.push("lab:depth-ref-mismatch");
}
const labText = await labDepth.innerText();
for (const expected of ["时序", "关系", "竞争"]) {
  if (!labText.includes(expected)) failures.push(`lab:missing:${expected}`);
}
const labCandidateCount = await labDepth
  .locator(".mechanism-evidence-candidate")
  .count();
if (labCandidateCount !== candidateCount) {
  failures.push("lab:candidate-count-mismatch");
}
const labScreenshot = await screenshot("02-lab-candidate-evidence-depth");

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
  depthRef,
  readingRef: depth?.reading_ref,
  mechanismVectorRef: depth?.mechanism_vector_ref,
  timingVectorRef: depth?.timing_vector_ref,
  selectedAttentionCandidateRef: depth?.selected_attention_candidate_ref,
  candidateCount,
  evidenceChannelsByCandidate: Object.fromEntries(
    (depth?.candidates ?? []).map((candidate) => [
      candidate.candidate_ref,
      candidate.evidence_channels,
    ]),
  ),
  unresolvedDimensions: Array.from(
    new Set(
      (depth?.candidates ?? []).flatMap(
        (candidate) => candidate.unresolved_dimensions,
      ),
    ),
  ),
  canonicalWriteAllowed: depth?.canonical_write_allowed,
  professionalVerdictAllowed: depth?.professional_verdict_allowed,
  probabilityClaimAllowed: depth?.probability_claim_allowed,
  screenshots: {
    mingliScreenshot,
    labScreenshot,
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
