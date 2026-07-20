import {spawn} from "node:child_process";
import {mkdir, rm, writeFile} from "node:fs/promises";
import {join, resolve} from "node:path";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9238;
const FPS = Number(process.env.S0_FPS || 12);
const TOTAL = Number(process.env.S0_DURATION || 44.5);
const WIDTH = Number(process.env.S0_WIDTH || 1920);
const HEIGHT = Number(process.env.S0_HEIGHT || 1080);
const URL = process.env.S0_URL || "http://127.0.0.1:8053/experience-static/prototypes/abu-says-mingli-s0-v11/index.html?paused=1&capture=1";
const OUTPUT = resolve(process.env.S0_FRAME_DIR || "artifacts/s0-v11/frames");
const PROFILE = resolve(process.env.S0_CHROME_PROFILE || "/tmp/deepbazi-s0-v11-chrome");

const sleep = (milliseconds) => new Promise((resolveSleep) => setTimeout(resolveSleep, milliseconds));

async function waitForJson(url, attempts = 100) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) return response.json();
    } catch {
      // Chrome has not exposed its debugging endpoint yet.
    }
    await sleep(100);
  }
  throw new Error(`cdp_endpoint_unavailable:${url}`);
}

function createCdp(webSocketUrl) {
  const socket = new WebSocket(webSocketUrl);
  const pending = new Map();
  let sequence = 0;

  const opened = new Promise((resolveOpen, rejectOpen) => {
    socket.addEventListener("open", resolveOpen, {once: true});
    socket.addEventListener("error", rejectOpen, {once: true});
  });

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(String(event.data));
    if (!message.id || !pending.has(message.id)) return;
    const {resolveRequest, rejectRequest} = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) rejectRequest(new Error(`${message.error.code}:${message.error.message}`));
    else resolveRequest(message.result);
  });

  return {
    async send(method, params = {}) {
      await opened;
      sequence += 1;
      const id = sequence;
      return new Promise((resolveRequest, rejectRequest) => {
        pending.set(id, {resolveRequest, rejectRequest});
        socket.send(JSON.stringify({id, method, params}));
      });
    },
    close() {
      socket.close();
    },
  };
}

async function waitForTheater(cdp) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    const result = await cdp.send("Runtime.evaluate", {
      expression: "document.readyState === 'complete' && typeof window.setTheaterTime === 'function' && document.querySelectorAll('.pillar').length === 6",
      returnByValue: true,
    });
    if (result.result?.value === true) return;
    await sleep(100);
  }
  throw new Error("s0_v11_theater_not_ready");
}

async function main() {
  await rm(OUTPUT, {recursive: true, force: true});
  await mkdir(OUTPUT, {recursive: true});
  await rm(PROFILE, {recursive: true, force: true});

  const chrome = spawn(CHROME, [
    "--headless=new",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${PROFILE}`,
    `--window-size=${WIDTH},${HEIGHT}`,
    "--force-device-scale-factor=1",
    "--hide-scrollbars",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--autoplay-policy=no-user-gesture-required",
    "about:blank",
  ], {stdio: "ignore"});

  let cdp;
  try {
    await waitForJson(`http://127.0.0.1:${PORT}/json/version`);
    const page = await fetch(`http://127.0.0.1:${PORT}/json/new?${encodeURIComponent(URL)}`, {method: "PUT"}).then((response) => response.json());
    cdp = createCdp(page.webSocketDebuggerUrl);
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: WIDTH,
      height: HEIGHT,
      deviceScaleFactor: 1,
      mobile: false,
      screenWidth: WIDTH,
      screenHeight: HEIGHT,
    });
    await waitForTheater(cdp);

    const frameCount = Math.ceil(TOTAL * FPS);
    const startedAt = Date.now();
    for (let index = 0; index < frameCount; index += 1) {
      const targetElapsed = index * (1000 / FPS);
      const remaining = targetElapsed - (Date.now() - startedAt);
      if (remaining > 0) await sleep(remaining);
      const time = Math.min(TOTAL - .001, index / FPS);
      await cdp.send("Runtime.evaluate", {
        expression: `window.setTheaterTime(${time.toFixed(4)});`,
        returnByValue: true,
      });
      const screenshot = await cdp.send("Page.captureScreenshot", {
        format: "jpeg",
        quality: 94,
        fromSurface: true,
        captureBeyondViewport: false,
      });
      const filename = `frame-${String(index + 1).padStart(5, "0")}.jpg`;
      await writeFile(join(OUTPUT, filename), Buffer.from(screenshot.data, "base64"));
      if (index % FPS === 0) process.stdout.write(`\rRendered ${Math.floor(index / FPS)}s / ${TOTAL}s`);
    }
    process.stdout.write(`\rRendered ${TOTAL}s / ${TOTAL}s\n`);
  } finally {
    if (cdp) cdp.close();
    chrome.kill("SIGTERM");
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
