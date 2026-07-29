import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(here, "../../.artifacts/semantic-focus");
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience?scope=dream";
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
  if (
    request.failure()?.errorText === "net::ERR_ABORTED" &&
    request.url().endsWith("/abu-v60-seated-idle-loop-v1/poster.png")
  ) {
    return;
  }
  failures.push(`request:${request.url()}:${request.failure()?.errorText}`);
});
page.on("response", (response) => {
  if (response.status() >= 400) {
    failures.push(`response:${response.status()}:${response.url()}`);
  }
});

await page.goto(targetUrl, { waitUntil: "domcontentloaded" });
await page.locator(".tree-base").waitFor({ state: "visible" });

const worldLeaf = page.locator(
  '[data-content-key="dream.organ.evidence_leaf_world"]',
);
const structureLeaf = page.locator(
  '[data-content-key="dream.organ.evidence_leaf_structure"]',
);
await worldLeaf.click();
const versionAfterObservation = await page
  .locator(".tree-state-key p")
  .textContent();

await page
  .locator('[data-content-key="navigation.perspective.theater"]')
  .click();
const theaterText = await page.locator(".companion-content").innerText();
if (!theaterText.includes("砚舟已把引水草放回旧水渠的石缝")) {
  failures.push("theater-did-not-project-focused-evidence");
}

await page.locator('[data-content-key="navigation.perspective.lab"]').click();
const labWorldText = await page.locator(".companion-content").innerText();
if (!labWorldText.includes("不会被 Lab 伪装成命盘事实")) {
  failures.push("world-evidence-was-not-kept-out-of-chart-facts");
}

await structureLeaf.click();
const labStructureText = await page.locator(".companion-content").innerText();
if (!labStructureText.includes("申与巳具备六合成员关系")) {
  failures.push("structure-focus-did-not-project-formal-fact");
}

await worldLeaf.click();
await page.reload({ waitUntil: "domcontentloaded" });
await page.locator(".tree-base").waitFor({ state: "visible" });
if (!(await worldLeaf.getAttribute("data-focused"))) {
  failures.push("focus-not-restored-after-refresh");
}

const metrics = await page.evaluate(() => ({
  bodyScrollHeight: document.body.scrollHeight,
  bodyScrollWidth: document.body.scrollWidth,
  viewportHeight: window.innerHeight,
  viewportWidth: window.innerWidth,
  url: window.location.href,
}));
if (
  metrics.bodyScrollHeight > metrics.viewportHeight ||
  metrics.bodyScrollWidth > metrics.viewportWidth
) {
  failures.push("document-scroll");
}
if (!metrics.url.includes("focus=v60-organ-yanzhou-leaf-world-v1")) {
  failures.push("focus-url-not-restored");
}
if (!metrics.url.includes("view=lab")) failures.push("perspective-url-not-restored");

await page.screenshot({
  path: path.join(artifactDirectory, "automated-desktop-semantic-focus.png"),
});
const audit = {
  targetUrl,
  versionAfterObservation,
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
