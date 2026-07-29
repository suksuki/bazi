import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(here, "../../.artifacts/first-slice");
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8061/experience?scope=dream";
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
let revealRequested = false;

page.on("console", (message) => {
  if (message.type() === "error") failures.push(`console:${message.text()}`);
});
page.on("pageerror", (error) => failures.push(`page:${error.message}`));
page.on("requestfailed", (request) => {
  failures.push(`request:${request.method()} ${request.url()} ${request.failure()?.errorText}`);
});
page.on("response", async (response) => {
  if (response.status() >= 400) failures.push(`response:${response.status()} ${response.url()}`);
  if (!response.url().includes("/api/v60/dream/")) return;
  const contentType = response.headers()["content-type"] ?? "";
  if (!contentType.includes("application/json")) return;
  const body = await response.text();
  const containsFutureEvidence =
    body.includes("三个夜晚后") || body.includes("少量新细根");
  if (containsFutureEvidence && !revealRequested) {
    failures.push(`future-evidence-leak:${response.url()}`);
  }
});

await page.goto(targetUrl, { waitUntil: "networkidle" });
await page.locator(".tree-base").waitFor({ state: "visible" });

const screenshot = async (name) => {
  const metrics = await page.evaluate(() => ({
    bodyScrollHeight: document.body.scrollHeight,
    bodyScrollWidth: document.body.scrollWidth,
    viewportHeight: window.innerHeight,
    viewportWidth: window.innerWidth,
  }));
  if (metrics.bodyScrollHeight > metrics.viewportHeight) {
    failures.push(`${name}:document-vertical-scroll`);
  }
  if (metrics.bodyScrollWidth > metrics.viewportWidth) {
    failures.push(`${name}:document-horizontal-scroll`);
  }
  const screenshotPath = path.join(artifactDirectory, `${name}.png`);
  await page.screenshot({ path: screenshotPath });
  return { screenshotPath, metrics };
};

const evidenceLeaf = page.locator(".tree-organ-evidence_leaf_world");
const structureLeaf = page.locator(".tree-organ-evidence_leaf_structure");
const treeReady = await screenshot("00-tree-ready");
await evidenceLeaf.click();
await structureLeaf.click();
await page.locator(".tree-organ-structure_branch").click();
await page.locator(".tree-organ-question_flower").click();
await page.locator(".answer-options").waitFor({ state: "visible" });

const initial = await screenshot("01-question-open");
const preSealText = await page.locator("body").innerText();
if (preSealText.includes("三个夜晚后") || preSealText.includes("少量新细根")) {
  failures.push("future-evidence-visible-before-seal");
}

await page.locator(".answer-options button").nth(1).click();
const sealed = await screenshot("02-answer-sealed");

await page
  .getByRole("button", { name: "打开旧渠回声果" })
  .waitFor({ state: "visible", timeout: 30_000 });
const matured = await screenshot("03-fruit-matured");

revealRequested = true;
await page.getByRole("button", { name: "打开旧渠回声果" }).click();
await page.getByText("判断得到支持").waitFor();
const revealed = await screenshot("04-revealed");

await page.getByRole("button", { name: "收下这次复盘" }).click();
await page.getByText("旧渠回声果已进入你的观察记录").waitFor();
const completed = await screenshot("05-reconciled");

await page.getByRole("button", { name: "命理 Lab" }).click();
await page.locator(".candidate-path").waitFor({ state: "visible" });
const lab = await screenshot("06-lab-same-case");

await page.reload({ waitUntil: "networkidle" });
await page.getByText("判断得到支持").waitFor();
await page.getByText("旧渠回声果已进入你的观察记录").waitFor();
const recovered = await screenshot("07-refresh-recovered");

const audit = {
  targetUrl,
  treeReady,
  initial,
  sealed,
  matured,
  revealed,
  completed,
  lab,
  recovered,
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
