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

    @app.get(f"{ADMIN_PREFIX}/api/project-status")
    def project_status() -> dict[str, object]:
        return _fetch_json("/api/v40/project/status")

    @app.get(f"{ADMIN_PREFIX}/api/mingli-depth-index")
    def mingli_depth_index() -> dict[str, object]:
        return _fetch_json("/api/v40/project/mingli-depth-index")

    @app.get(f"{ADMIN_PREFIX}/api/module-migration-status")
    def module_migration_status() -> dict[str, object]:
        return _fetch_json("/api/v40/project/module-migration-status")

    @app.get(f"{ADMIN_PREFIX}/api/trainable-runtime-spine")
    def trainable_runtime_spine() -> dict[str, object]:
        return _fetch_json("/api/v40/project/trainable-runtime-spine")

    @app.get(f"{ADMIN_PREFIX}/api/horizontal-runtime-context")
    def horizontal_runtime_context() -> dict[str, object]:
        return _fetch_json("/api/v40/project/horizontal-runtime-context")

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

    @app.get(f"{ADMIN_PREFIX}/api/weight-risk")
    def weight_risk() -> dict[str, object]:
        weights = _fetch_json("/api/v40/weights/candidates?limit=20")
        readiness = _fetch_json("/api/v40/release-readiness?limit=20")
        return {
            "version": "v40.admin_weight_risk_response.v1",
            "summary": _build_weight_risk_summary(weights, readiness),
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "admin_weight_risk_reads_candidate_weight_and_readiness_without_activation",
        }

    @app.get(f"{ADMIN_PREFIX}/api/llm")
    def llm_status() -> dict[str, object]:
        return _fetch_json("/api/v40/expression/provider/ollama")

    @app.get(f"{ADMIN_PREFIX}/api/llm-models")
    def llm_models() -> dict[str, object]:
        return _fetch_json("/api/v40/expression/provider/ollama/models")

    return app


def _api_base() -> str:
    return os.getenv("V40_API_BASE", "http://127.0.0.1:9040").rstrip("/")


def _fetch_json(path: str) -> dict[str, object]:
    try:
        with urlopen(f"{_api_base()}{path}", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=502, detail="V40 runtime API is unavailable") from exc


def _build_weight_risk_summary(weights_payload: dict[str, object], readiness_payload: dict[str, object]) -> dict[str, object]:
    weights = [item for item in weights_payload.get("weights", []) if isinstance(item, dict)]
    readiness_rows = [item for item in readiness_payload.get("readiness", []) if isinstance(item, dict)]
    readiness_by_id = {str(item.get("readiness_id", "")): item for item in readiness_rows}
    records = [_weight_risk_record(weight, readiness_by_id) for weight in weights]
    return {
        "candidate_count": len(records),
        "ready_count": sum(1 for record in records if record["risk_level"] == "ready"),
        "review_count": sum(1 for record in records if record["risk_level"] == "review"),
        "blocked_count": sum(1 for record in records if record["risk_level"] == "blocked"),
        "records": records,
    }


def _weight_risk_record(weight: dict[str, object], readiness_by_id: dict[str, dict[str, object]]) -> dict[str, object]:
    weight_json = weight.get("weight_json")
    if not isinstance(weight_json, dict):
        weight_json = {}
    weight_id = str(weight.get("weight_version_id") or weight_json.get("weight_version_id") or "")
    release_gate_id = str(weight.get("release_gate_id") or weight_json.get("release_gate_id") or "")
    rollback_version_id = str(weight.get("rollback_version_id") or weight_json.get("rollback_version_id") or "")
    active = bool(weight.get("active") or weight_json.get("active"))
    linked_readiness = readiness_by_id.get(release_gate_id)
    recommendation = str(linked_readiness.get("recommendation", "")) if linked_readiness else ""
    reasons: list[str] = []
    risk_level = "ready"
    if not linked_readiness:
        reasons.append("release_gate_id 未匹配 release_readiness")
        risk_level = "review"
    elif recommendation in {"reject", "rollback"}:
        reasons.append("release readiness 已拒绝")
        risk_level = "blocked"
    elif recommendation != "approve":
        reasons.append("release readiness 仍需复核")
        risk_level = "review"
    if not rollback_version_id:
        reasons.append("缺少 rollback_version_id")
        if risk_level == "ready":
            risk_level = "review"
    if active:
        reasons.append("当前版本已激活，继续保留回滚审计")
    next_action = "可进入显式激活审核" if risk_level == "ready" else "补齐 readiness 关联、风险说明或 rollback 后再审核"
    if risk_level == "blocked":
        next_action = "停止激活，回到 evaluation/replay 修复"
    return {
        "weight_version_id": weight_id,
        "source_training_run_id": str(weight.get("source_training_run_id") or weight_json.get("source_training_run_id") or ""),
        "release_gate_id": release_gate_id,
        "active": active,
        "rollback_version_id": rollback_version_id,
        "readiness_id": str(linked_readiness.get("readiness_id", "")) if linked_readiness else "",
        "readiness_recommendation": recommendation,
        "risk_level": risk_level,
        "reasons": reasons,
        "next_action": next_action,
    }


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
    .progress-grid { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 14px; margin-bottom: 14px; }
    .metric, section {
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: 0 18px 45px rgba(0,0,0,0.22);
    }
    .metric { border-radius: 7px; padding: 14px; }
    .metric span { display: block; color: var(--muted); font-size: 12px; }
    .metric strong { display: block; margin-top: 6px; font-size: 24px; }
    .completion { border-radius: 8px; padding: 16px; }
    .completion strong { display: block; font-size: 42px; line-height: 1; margin: 10px 0 8px; }
    .completion span { color: var(--muted); font-size: 12px; }
    .bars { display: grid; gap: 9px; }
    .bar-row { display: grid; gap: 5px; }
    .bar-meta { display: flex; justify-content: space-between; gap: 8px; color: var(--muted); font-size: 12px; }
    .bar-track { height: 8px; border-radius: 999px; background: rgba(255,255,255,.07); overflow: hidden; }
    .bar-fill { height: 100%; border-radius: inherit; background: linear-gradient(90deg, #4b9f88, #8be0c4); }
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
      .grid, .sections, .progress-grid { grid-template-columns: 1fr; }
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
    <div class="progress-grid">
      <section class="completion" id="completion"></section>
      <section><div class="section-head"><h2>V40 Completion</h2><span class="pill" id="phase"></span></div><div class="list" id="progress"></div></section>
      <section><div class="section-head"><h2>Mingli Depth</h2><span class="pill">RC2</span></div><div class="list" id="mingli-depth"></div></section>
      <section><div class="section-head"><h2>Module Map</h2><span class="pill">migration</span></div><div class="list" id="module-map"></div></section>
      <section><div class="section-head"><h2>Trainable Spine</h2><span class="pill">policy</span></div><div class="list" id="trainable-spine"></div></section>
      <section><div class="section-head"><h2>Runtime Context</h2><span class="pill">platform</span></div><div class="list" id="runtime-context"></div></section>
    </div>
    <div class="grid" id="metrics"></div>
    <div class="sections">
      <section><div class="section-head"><h2>Batch</h2><span class="pill">latest</span></div><div class="list" id="batches"></div></section>
      <section><div class="section-head"><h2>Readiness</h2><span class="pill">release</span></div><div class="list" id="readiness"></div></section>
      <section><div class="section-head"><h2>Candidate Risk</h2><span class="pill">source · rollback</span></div><div class="list" id="weight-risk"></div></section>
      <section><div class="section-head"><h2>Training Feedback</h2><span class="pill">closed loop</span></div><div class="list" id="training"></div></section>
      <section><div class="section-head"><h2>Weight</h2><span class="pill">candidate</span></div><div class="list" id="weights"></div></section>
      <section><div class="section-head"><h2>Activation</h2><span class="pill">review</span></div><div class="list" id="activation"></div></section>
      <section><div class="section-head"><h2>LLM</h2><span class="pill">ollama</span></div><div class="list" id="llm"></div></section>
    </div>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    const get = (path) => fetch(path).then((r) => r.json());
    const cls = (value) => value === "approve" || value === "ready" || value === true ? "ok" : value === "reject" || value === "blocked" ? "bad" : "review";
    function row(title, meta, value) {
      return `<div class="row"><strong>${title || "-"}</strong><span>${meta || ""}</span><span class="${cls(value)}">${value ?? ""}</span></div>`;
    }
    async function load() {
      const [project, depth, modules, trainable, context, summary, batches, readiness, risk, weights, reviews, executions, llm, models] = await Promise.all([
        get("/admin/v40/api/project-status"),
        get("/admin/v40/api/mingli-depth-index"),
        get("/admin/v40/api/module-migration-status"),
        get("/admin/v40/api/trainable-runtime-spine"),
        get("/admin/v40/api/horizontal-runtime-context"),
        get("/admin/v40/api/summary"),
        get("/admin/v40/api/batches"),
        get("/admin/v40/api/readiness"),
        get("/admin/v40/api/weight-risk"),
        get("/admin/v40/api/weights"),
        get("/admin/v40/api/activation-reviews"),
        get("/admin/v40/api/activation-executions"),
        get("/admin/v40/api/llm"),
        get("/admin/v40/api/llm-models"),
      ]);
      const status = project.status || {};
      const domains = status.domains || [];
      $("phase").textContent = `Phase ${status.current_phase || "-"}`;
      $("completion").innerHTML = `<span>overall</span><strong>${status.overall_completion_percent ?? 0}%</strong><span>${status.current_phase_name || ""}</span>`;
      $("progress").innerHTML = domains.map((item) => `
        <div class="row bar-row">
          <div class="bar-meta"><span>${item.label}</span><span>${item.completion_percent}% · ${item.status}</span></div>
          <div class="bar-track"><div class="bar-fill" style="width:${Math.max(0, Math.min(100, item.completion_percent || 0))}%"></div></div>
          <span>${item.next_step || ""}</span>
        </div>
      `).join("") || row("暂无完成度数据", "", "review");
      const depthIndex = depth.index || {};
      $("mingli-depth").innerHTML = [
        row(`命理纵深 ${depthIndex.mingli_depth_percent ?? 0}%`, `架构参考 ${depthIndex.architecture_completion_reference ?? 0}%`, depthIndex.status || "review"),
        ...(depthIndex.domains || []).map((item) => row(`${item.label} ${item.completion_percent}%`, item.next_step, item.status))
      ].join("");
      const moduleStatus = modules.status || {};
      const moduleSummary = moduleStatus.summary || {};
      $("module-map").innerHTML = [
        row("V40 原生模块", `${moduleSummary.v40_native_or_ready_groups ?? 0}/${moduleSummary.module_groups_total ?? 0}`, "ready"),
        row("V30 直接复用", "runtime import allowed", moduleSummary.v30_direct_runtime_reuse_allowed ?? 0),
        row("V30 资产可萃取", `${moduleSummary.reusable_v30_asset_groups ?? 0} groups`, "review"),
        row("RC2 必须新建", `${moduleSummary.new_required_groups ?? 0} groups`, "review"),
      ].join("");
      const trainableStatus = trainable.status || {};
      $("trainable-spine").innerHTML = [
        row("事实模块", `${(trainableStatus.immutable_fact_modules || []).length} validation only`, "ready"),
        row("可训练单元", `${(trainableStatus.trainable_unit_types || []).length} policy unit types`, "review"),
        row("反馈链路", `${(trainableStatus.feedback_flow || []).length} steps`, "review"),
        row("边界", trainableStatus.principle || "", trainableStatus.boundary || "review"),
      ].join("");
      const contextStatus = context.status || {};
      $("runtime-context").innerHTML = [
        row("Locale / Role / Client / Engine", `${(contextStatus.contexts || []).length} contexts`, "ready"),
        row("Engine Capability", `${(contextStatus.engine_capabilities || []).length} engines`, "review"),
        row("Term Dictionary", `${contextStatus.term_dictionary?.entries?.length || 0} terms`, "review"),
        row("Admin", "独立控制台和端口", "ready"),
      ].join("");
      const counts = summary.summary?.counts || {};
      $("metrics").innerHTML = ["training_label_events", "local_overlays", "training_examples", "training_example_replays", "training_replay_batches", "evaluation_batches", "release_readiness", "global_weight_versions", "weight_activation_executions"]
        .map((key) => `<div class="metric"><span>${key}</span><strong>${counts[key] ?? 0}</strong></div>`).join("");
      $("batches").innerHTML = (batches.batches || []).map((item) => row(item.batch_id, item.candidate_version, item.recommendation)).join("") || row("暂无数据", "", "");
      $("readiness").innerHTML = (readiness.readiness || []).map((item) => row(item.readiness_id, item.candidate_version, item.recommendation)).join("") || row("暂无数据", "", "");
      $("weight-risk").innerHTML = (risk.summary?.records || []).map((item) => row(item.weight_version_id, `${item.release_gate_id || "未关联"} · ${item.next_action}`, item.risk_level)).join("") || row("暂无候选权重", "", "review");
      const latestExamples = summary.summary?.latest_training_examples || [];
      const latestOverlays = summary.summary?.latest_local_overlays || [];
      const latestReplays = summary.summary?.latest_training_example_replays || [];
      const latestReplayBatches = summary.summary?.latest_training_replay_batches || [];
      const latestTraining = [
        ...latestReplayBatches.map((item) => row(item.batch_id, `${item.candidate_version || ""}`, item.recommendation || "batch")),
        ...latestReplays.map((item) => row(item.replay_id, `${item.status || ""} · ${item.recommendation || ""}`, "replay")),
        ...latestExamples.map((item) => row(item.example_id, `${item.topic || ""} · ${item.reading_id || ""}`, "example")),
        ...latestOverlays.map((item) => row(item.overlay_id, item.reading_id || "", "overlay")),
      ];
      $("training").innerHTML = latestTraining.join("") || row("暂无训练反馈", "等待命理师校准或用户反馈", "review");
      $("weights").innerHTML = (weights.weights || []).map((item) => row(item.weight_version_id, item.rollback_version_id || item.release_gate_id, item.active)).join("") || row("暂无数据", "", "");
      const combined = [...(reviews.reviews || []), ...(executions.executions || [])];
      $("activation").innerHTML = combined.map((item) => row(item.review_id || item.execution_id, item.weight_version_id, item.decision || item.activation_applied)).join("") || row("暂无数据", "", "");
      const modelRows = (models.models || []).slice(0, 6).map((name) => row(name, name === llm.model ? "当前模型" : "", name === llm.model ? "ready" : ""));
      $("llm").innerHTML = [
        row(llm.model || "未配置模型", `${llm.base_url || ""} · think ${llm.effective_thinking_max_tokens || 0}/${llm.effective_thinking_timeout_seconds || 0}s`, llm.enabled && llm.execute ? "ready" : "disabled"),
        row("模型发现", `${models.model_count || 0} models`, models.configured_model_available ? "ready" : "review"),
        ...modelRows
      ].join("");
    }
    $("refresh").addEventListener("click", load);
    setInterval(load, 15000);
    load().catch((error) => {
      $("metrics").innerHTML = `<div class="metric"><span>error</span><strong>API</strong></div>`;
      $("batches").innerHTML = row("V40 runtime unavailable", error.message, "reject");
    });
  </script>
</body>
</html>"""


app = create_admin_app()
