import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(here, "../../.artifacts/guide-left-runtime");
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
await page.locator("[data-abu-motion=GUIDE_LEFT]").waitFor({ state: "visible" });

const capture = async (name) => {
  const actor = page.locator("[data-abu-motion]");
  const state = await actor.getAttribute("data-abu-motion");
  const box = await actor.boundingBox();
  const metrics = await page.evaluate(() => ({
    bodyScrollHeight: document.body.scrollHeight,
    bodyScrollWidth: document.body.scrollWidth,
    viewportHeight: window.innerHeight,
    viewportWidth: window.innerWidth,
  }));
  await page.screenshot({ path: path.join(artifactDirectory, `${name}.png`) });
  return { state, box, metrics };
};

const atStart = await capture("00-guide-start");
await page.waitForTimeout(1_200);
const atGesture = await capture("01-guide-gesture");
await page.waitForTimeout(4_200);
const returnedToIdle = await capture("02-return-idle");

if (atStart.state !== "GUIDE_LEFT") failures.push("guide-left-did-not-start");
if (atGesture.state !== "GUIDE_LEFT") failures.push("guide-left-ended-too-early");
if (returnedToIdle.state !== "IDLE") failures.push("guide-left-did-not-return-to-idle");

for (const [name, captureResult] of Object.entries({
  atStart,
  atGesture,
  returnedToIdle,
})) {
  if (!captureResult.box) failures.push(`${name}:actor-not-visible`);
  if (
    captureResult.metrics.bodyScrollHeight > captureResult.metrics.viewportHeight ||
    captureResult.metrics.bodyScrollWidth > captureResult.metrics.viewportWidth
  ) {
    failures.push(`${name}:document-scroll`);
  }
}

if (
  atStart.box &&
  atGesture.box &&
  JSON.stringify(atStart.box) !== JSON.stringify(atGesture.box)
) {
  failures.push("guide-left-layout-shift");
}
if (
  atStart.box &&
  returnedToIdle.box &&
  JSON.stringify(atStart.box) !== JSON.stringify(returnedToIdle.box)
) {
  failures.push("idle-return-layout-shift");
}

const audit = {
  targetUrl,
  atStart,
  atGesture,
  returnedToIdle,
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
