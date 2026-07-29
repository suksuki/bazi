import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(
  here,
  "../../.artifacts/mechanism-qualification",
);
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience";
const sessionToken = process.env.V60_AUDIT_SESSION_TOKEN;

if (!sessionToken) throw new Error("V60_AUDIT_SESSION_TOKEN is required");
await mkdir(artifactDirectory, { recursive: true });

const browser = await chromium.launch({ executablePath: chromePath, headless: true });
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
  failures.push(`request:${request.method()} ${request.url()} ${request.failure()?.errorText}`);
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
const mingliMatrix = page.locator(".mechanism-qualification");
await mingliMatrix.waitFor({ state: "visible" });
const qualificationRef = await mingliMatrix.getAttribute("data-qualification-ref");
const mingliCandidate = mingliMatrix.locator("details").first();
await mingliCandidate.locator("summary").click();
const mingliText = await mingliCandidate.innerText();
for (const expected of ["结构角色", "根源与显化", "专业准入"]) {
  if (!mingliText.includes(expected)) failures.push(`mingli:missing:${expected}`);
}
const homeSnapshot = await page.evaluate(async () => {
  const response = await fetch("/api/v60/experience/home");
  if (!response.ok) throw new Error(`home:${response.status}`);
  return response.json();
});
const qualification = homeSnapshot.mingli?.mechanism_qualification;
if (qualification?.qualification_ref !== qualificationRef) {
  failures.push("mingli:dom-api-qualification-ref-mismatch");
}
if (
  homeSnapshot.lab?.mechanism_qualification_ref !== qualificationRef ||
  homeSnapshot.mingli?.abu_expression?.qualification_ref !== qualificationRef
) {
  failures.push("mingli:shared-qualification-identity-mismatch");
}
for (const candidate of qualification?.candidates ?? []) {
  const professional = candidate.checks.find(
    (item) => item.dimension === "PROFESSIONAL_ADMISSION",
  );
  if (professional?.status !== "NOT_ADMITTED" || candidate.professional_admission) {
    failures.push(`mingli:professional-overreach:${candidate.candidate_ref}`);
  }
}
const mingliScreenshot = await screenshot("01-mingli-evidence-completeness");

await openView("lab");
const labMatrix = page.locator(".mechanism-qualification");
await labMatrix.waitFor({ state: "visible" });
if ((await labMatrix.getAttribute("data-qualification-ref")) !== qualificationRef) {
  failures.push("lab:qualification-ref-mismatch");
}
const labCandidate = labMatrix.locator("details").first();
await labCandidate.locator("summary").click();
const labText = await labMatrix.innerText();
for (const expected of ["还需要", "什么会推翻", "不计算分数"]) {
  if (!labText.includes(expected)) failures.push(`lab:missing:${expected}`);
}
const labScreenshot = await screenshot("02-lab-gap-and-falsifier-matrix");

await openView("abu");
const abuText = await page.locator(".home-abu-notes").innerText();
if (
  !abuText.includes("证据还缺什么") ||
  !abuText.includes("根源承接") ||
  !abuText.includes("反证")
) {
  failures.push("abu:qualification-summary-missing");
}
const abuScreenshot = await screenshot("03-abu-shared-gap-summary");

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
  qualificationRef,
  readingRef: qualification?.reading_ref,
  mechanismVectorRef: qualification?.mechanism_vector_ref,
  candidateCount: qualification?.candidates?.length,
  professionalVerdictAllowed: qualification?.professional_verdict_allowed,
  canonicalWriteAllowed: qualification?.canonical_write_allowed,
  screenshots: {
    mingliScreenshot,
    labScreenshot,
    abuScreenshot,
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
