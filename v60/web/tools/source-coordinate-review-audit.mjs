import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(
  here,
  "../../.artifacts/source-coordinate-review",
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
const summaryPanel = page.locator(
  '.source-coordinate-review[data-mode="summary"]',
);
await summaryPanel.waitFor({ state: "visible" });
await summaryPanel.scrollIntoViewIfNeeded();
const vectorRef = await summaryPanel.getAttribute("data-vector-ref");
const summaryText = await summaryPanel.innerText();
for (const expected of ["来源坐标复核", "不判旺衰", "关系作用仍待定"]) {
  if (!summaryText.includes(expected)) failures.push(`mingli:missing:${expected}`);
}

const homeSnapshot = await page.evaluate(async () => {
  const response = await fetch("/api/v60/experience/home");
  if (!response.ok) throw new Error(`home:${response.status}`);
  return response.json();
});
const vector = homeSnapshot.mingli?.source_coordinate_review;
if (vector?.vector_ref !== vectorRef) {
  failures.push("mingli:dom-api-vector-ref-mismatch");
}
if (
  homeSnapshot.mingli?.reading?.source_review_vector_ref !== vectorRef ||
  homeSnapshot.mingli?.reading?.source_review_vector_hash !== vector?.vector_hash ||
  homeSnapshot.lab?.source_review_vector_ref !== vectorRef ||
  homeSnapshot.lab?.source_review_vector_hash !== vector?.vector_hash
) {
  failures.push("mingli:shared-source-review-identity-mismatch");
}
if (
  vector?.professional_verdict_allowed !== false ||
  vector?.probability_claim_allowed !== false ||
  vector?.canonical_write_allowed !== false
) {
  failures.push("mingli:forbidden-authority-enabled");
}
if (
  (vector?.reviews ?? []).some(
    (item) =>
      item.root_usability_status !== "UNRESOLVED" ||
      item.relation_effect_status !== "UNRESOLVED",
  )
) {
  failures.push("mingli:unadmitted-conclusion-present");
}
const mingliScreenshot = await screenshot("01-mingli-source-coordinate-review");

await openView("lab");
const detailedPanel = page.locator(
  '.source-coordinate-review[data-mode="detailed"]',
);
await detailedPanel.waitFor({ state: "visible" });
await detailedPanel.scrollIntoViewIfNeeded();
if ((await detailedPanel.getAttribute("data-vector-ref")) !== vectorRef) {
  failures.push("lab:vector-ref-mismatch");
}
const detailedText = await detailedPanel.innerText();
for (const expected of ["来源候选", "需要复核", "关系作用仍待定"]) {
  if (!detailedText.includes(expected)) failures.push(`lab:missing:${expected}`);
}
const renderedReviewCount = await detailedPanel
  .locator(".source-review-detail-list article")
  .count();
const expectedReviewCount = vector?.review_required_count
  ? vector.review_required_count
  : Math.min(vector?.reviews?.length ?? 0, 4);
if (renderedReviewCount !== expectedReviewCount) {
  failures.push("lab:rendered-review-count-mismatch");
}
const labScreenshot = await screenshot("02-lab-source-coordinate-review");

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
  vectorRef,
  vectorHash: vector?.vector_hash,
  readingRef: homeSnapshot.mingli?.reading?.reading_ref,
  caseRef: vector?.case_ref,
  sourceEvidenceCount: vector?.source_evidence_count,
  clearCoordinateCount: vector?.clear_coordinate_count,
  reviewRequiredCount: vector?.review_required_count,
  clashIntersectionCount: vector?.six_clash_intersection_count,
  harmonyIntersectionCount: vector?.six_harmony_intersection_count,
  professionalVerdictAllowed: vector?.professional_verdict_allowed,
  probabilityClaimAllowed: vector?.probability_claim_allowed,
  canonicalWriteAllowed: vector?.canonical_write_allowed,
  screenshots: { mingliScreenshot, labScreenshot },
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
