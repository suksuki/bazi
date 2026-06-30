from __future__ import annotations

import json
import os
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from v40 import __version__


ADMIN_PREFIX = "/admin/v40"


def create_admin_app() -> FastAPI:
    app = FastAPI(title="Qiazhi V40 Admin Console", version=__version__)

    @app.get(f"{ADMIN_PREFIX}/health")
    def health() -> dict[str, object]:
        return {
            "ok": True,
            "package": "v40-admin",
            "version": __version__,
            "admin_prefix": ADMIN_PREFIX,
            "api_base": _api_base(),
            "boundary": "v40_admin_console_is_independent_read_model_surface",
        }

    @app.get(ADMIN_PREFIX, response_class=HTMLResponse)
    def console() -> HTMLResponse:
        return HTMLResponse(_console_html())

    @app.get(f"{ADMIN_PREFIX}/api/summary")
    def summary() -> dict[str, object]:
        return _fetch_json("/api/v40/lab/summary")

    @app.get(f"{ADMIN_PREFIX}/api/batches")
    def batches() -> dict[str, object]:
        return _fetch_json("/api/v40/evaluation/batches?limit=8")

    @app.get(f"{ADMIN_PREFIX}/api/readiness")
    def readiness() -> dict[str, object]:
        return _fetch_json("/api/v40/release-readiness?limit=8")

    @app.get(f"{ADMIN_PREFIX}/api/weights")
    def weights() -> dict[str, object]:
        return _fetch_json("/api/v40/weights/candidates?limit=8")

    @app.get(f"{ADMIN_PREFIX}/api/activation-reviews")
    def activation_reviews() -> dict[str, object]:
        return _fetch_json("/api/v40/weights/activation-reviews?limit=8")

    @app.get(f"{ADMIN_PREFIX}/api/activation-executions")
    def activation_executions() -> dict[str, object]:
        return _fetch_json("/api/v40/weights/activation-executions?limit=8")

    return app


def _api_base() -> str:
    return os.getenv("V40_API_BASE", "http://127.0.0.1:9040").rstrip("/")


def _fetch_json(path: str) -> dict[str, object]:
    try:
        with urlopen(f"{_api_base()}{path}", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=502, detail="V40 runtime API is unavailable") from exc


def _console_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>掐指一算 V40 Admin</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #080d0d;
      --panel: rgba(20, 29, 29, 0.84);
      --panel-soft: rgba(255, 255, 255, 0.045);
      --line: rgba(190, 206, 198, 0.12);
      --text: #eef5ef;
      --muted: #94a39b;
      --accent: #64d6b5;
      --warn: #f2c879;
      --bad: #ff8f8a;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: radial-gradient(circle at top right, rgba(79, 168, 139, 0.16), transparent 34%), var(--bg);
      color: var(--text);
      font: 14px/1.55 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    main { max-width: 1180px; margin: 0 auto; padding: 28px 22px 44px; }
    header { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 22px; }
    h1 { margin: 0; font-size: 24px; font-weight: 720; }
    .sub { margin-top: 5px; color: var(--muted); }
    button {
      appearance: none;
      border: 0;
      border-radius: 7px;
      background: #1f6f5c;
      color: white;
      padding: 9px 13px;
      font-weight: 680;
      cursor: pointer;
    }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
    .metric, section {
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: 0 18px 45px rgba(0,0,0,0.22);
    }
    .metric { border-radius: 7px; padding: 14px; }
    .metric span { display: block; color: var(--muted); font-size: 12px; }
    .metric strong { display: block; margin-top: 6px; font-size: 24px; }
    .sections { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    section { border-radius: 8px; overflow: hidden; }
    .section-head { display: flex; justify-content: space-between; align-items: center; padding: 13px 14px; border-bottom: 1px solid var(--line); }
    h2 { margin: 0; font-size: 15px; }
    .pill { color: var(--accent); font-size: 12px; }
    .list { display: grid; gap: 1px; background: rgba(255,255,255,0.035); }
    .row { padding: 12px 14px; background: rgba(10, 15, 15, 0.88); min-height: 62px; }
    .row strong { display: block; font-size: 13px; overflow-wrap: anywhere; }
    .row span { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .ok { color: var(--accent); }
    .review { color: var(--warn); }
    .bad { color: var(--bad); }
    @media (max-width: 880px) {
      .grid, .sections { grid-template-columns: 1fr; }
      header { flex-direction: column; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>掐指一算 V40 Control Plane</h1>
        <div class="sub">Evaluation · Training · Release</div>
      </div>
      <button id="refresh">刷新</button>
    </header>
    <div class="grid" id="metrics"></div>
    <div class="sections">
      <section><div class="section-head"><h2>Batch</h2><span class="pill">latest</span></div><div class="list" id="batches"></div></section>
      <section><div class="section-head"><h2>Readiness</h2><span class="pill">release</span></div><div class="list" id="readiness"></div></section>
      <section><div class="section-head"><h2>Weight</h2><span class="pill">candidate</span></div><div class="list" id="weights"></div></section>
      <section><div class="section-head"><h2>Activation</h2><span class="pill">review</span></div><div class="list" id="activation"></div></section>
    </div>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    const get = (path) => fetch(path).then((r) => r.json());
    const cls = (value) => value === "approve" || value === true ? "ok" : value === "reject" ? "bad" : "review";
    function row(title, meta, value) {
      return `<div class="row"><strong>${title || "-"}</strong><span>${meta || ""}</span><span class="${cls(value)}">${value ?? ""}</span></div>`;
    }
    async function load() {
      const [summary, batches, readiness, weights, reviews, executions] = await Promise.all([
        get("/admin/v40/api/summary"),
        get("/admin/v40/api/batches"),
        get("/admin/v40/api/readiness"),
        get("/admin/v40/api/weights"),
        get("/admin/v40/api/activation-reviews"),
        get("/admin/v40/api/activation-executions"),
      ]);
      const counts = summary.summary?.counts || {};
      $("metrics").innerHTML = ["evaluation_batches", "release_readiness", "global_weight_versions", "weight_activation_executions"]
        .map((key) => `<div class="metric"><span>${key}</span><strong>${counts[key] ?? 0}</strong></div>`).join("");
      $("batches").innerHTML = (batches.batches || []).map((item) => row(item.batch_id, item.candidate_version, item.recommendation)).join("") || row("暂无数据", "", "");
      $("readiness").innerHTML = (readiness.readiness || []).map((item) => row(item.readiness_id, item.candidate_version, item.recommendation)).join("") || row("暂无数据", "", "");
      $("weights").innerHTML = (weights.weights || []).map((item) => row(item.weight_version_id, item.rollback_version_id || item.release_gate_id, item.active)).join("") || row("暂无数据", "", "");
      const combined = [...(reviews.reviews || []), ...(executions.executions || [])];
      $("activation").innerHTML = combined.map((item) => row(item.review_id || item.execution_id, item.weight_version_id, item.decision || item.activation_applied)).join("") || row("暂无数据", "", "");
    }
    $("refresh").addEventListener("click", load);
    load().catch((error) => {
      $("metrics").innerHTML = `<div class="metric"><span>error</span><strong>API</strong></div>`;
      $("batches").innerHTML = row("V40 runtime unavailable", error.message, "reject");
    });
  </script>
</body>
</html>"""


app = create_admin_app()
