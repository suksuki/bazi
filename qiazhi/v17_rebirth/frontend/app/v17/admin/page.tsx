"use client";

import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { V17_ClassicalPatternAtlas } from "@/components/V17_ClassicalPatternAtlas";

type TabKey = "llm" | "db" | "plugins" | "physics" | "evolution";

type LlmNode = {
  provider: string;
  host: string;
  port: number;
  model: string;
  httpTimeoutSec: number;
  fuseWaitSec: number;
};

type DbBridge = {
  driver: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  sslmode: string;
  url: string;
  enabled: boolean;
};

type PluginAdminRow = {
  layer: string;
  layer_dir: string;
  module: string;
  plugin_id: string;
  display_name?: string;
  display_definition?: string;
  display_description?: string;
  technical_label?: string;
  family_label?: string;
  causal_tier: number;
  power_tier?: number;
  execution_order?: number;
  registry_priority?: number;
  kind: string;
  last_facts?: string[];
  last_at?: string;
  activated?: boolean;
  causal_active_path?: boolean;
  function_summary?: string;
  design_rationale?: string;
  causal_trace_text?: string;
  executed_before_plugin_ids?: string[];
  module_doc?: string;
  spec_doc?: string;
  definition_text?: string;
  trigger_condition_text?: string;
  detail_description?: string;
  declared_params?: Record<string, unknown>;
  skill_manifest?: Record<string, unknown>;
  is_standard_skill?: boolean;
  policy_valid?: boolean;
  policy_errors?: string[];
  config_required?: boolean;
  config_exists?: boolean;
  config_file?: string;
};

function pluginCardTitle(row: PluginAdminRow): string {
  return String(row.display_name || row.definition_text || row.plugin_id || "未命名插件").trim();
}

function pluginCardDefinition(row: PluginAdminRow): string {
  return String(row.display_definition || row.definition_text || row.function_summary || row.plugin_id || "").trim();
}

function pluginCardDescription(row: PluginAdminRow): string {
  return String(row.display_description || row.detail_description || row.design_rationale || "暂无补充说明。").trim();
}

type PluginRuntimeStatus = {
  plugin_id: string;
  fact_count?: number;
  proposal_count?: number;
  decision_count?: number;
  status?: string;
  target_god?: string;
  reason?: string;
};

type PluginClaim = {
  claim_id: string;
  plugin_id: string;
  target_god?: string;
  projection_share?: number;
  cluster_projection?: Record<string, unknown>;
  logic_level?: string;
  claim_type?: string;
  source_event?: string;
  match_ratio?: number;
};

type RecomputeContribution = {
  target_god?: string;
  before?: number;
  after?: number;
  ratio_total?: number;
  delta_abs?: number;
};

type PluginConflict = {
  conflict_id: string;
  conflict_type?: string;
  severity?: string;
  conflict_score?: number;
  confidence_band?: string;
  source_event?: string;
  claims?: string[];
  plugins?: string[];
  target_god?: string;
  why_conflict?: string;
  recommended_arbiter?: string;
  resolution_status?: string;
  routing_reason?: string;
  routing_policy?: string;
  routing_scores?: Record<string, number>;
  meta?: LooseObject;
};

type PluginConflictResolution = {
  conflict_id: string;
  resolved_by?: string;
  policy?: string;
  winner_claim_id?: string;
  applied_to_settlement?: boolean;
  next_queue?: string;
  reason?: string;
  status?: string;
};

type KnowledgeSnapshot = {
  claim_history?: {
    total_claims?: number;
    by_type?: Record<string, number>;
    top_targets?: Array<{ target_god?: string; count?: number }>;
  };
  conflict_history?: {
    total_conflicts?: number;
    by_type?: Record<string, number>;
    recommended_arbiters?: Record<string, number>;
    feedback_arbiters?: Record<string, number>;
    feedback_arbiter_scores?: Record<string, number>;
  };
  resolution_preview?: {
    total_suggestions?: number;
    resolved_by?: Record<string, number>;
  };
};

type BrainAction = {
  action_id?: string;
  conflict_id?: string;
  action_type?: string;
  queue?: string;
  confidence?: number;
  reason?: string;
  source_plugins?: string[];
};

type PluginPanelRow = {
  plugin: PluginAdminRow;
  runtime?: PluginRuntimeStatus;
  relatedClaims: PluginClaim[];
  relatedConflicts: PluginConflict[];
};

type PhysicsL0Foundation = {
  STEM_BASE?: number;
  BRANCH_BASE?: number;
};
type EvolutionLogEntry = {
  id?: string;
  timestamp?: string;
  ten_god?: string;
  delta?: number;
  plugin_id?: string;
  step?: string;
  reason?: string;
};

type ActionKey = "loadModels" | "testLlm" | "testLlmChat" | "saveLlm" | "testDb" | "saveDb" | "loadPlugins" | "savePhysics" | "loadEvolution" | null;
type LooseObject = Record<string, unknown>;
const ORACLE_SESSION_STORAGE_KEY = "v17.oracle.current_session_id";

function asLooseObject(value: unknown): LooseObject {
  return typeof value === "object" && value !== null ? (value as LooseObject) : {};
}

function asLooseRecord<T>(value: unknown, fallback: T[] = [] as T[]): T[] {
  return Array.isArray(value) ? (value as T[]) : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  const raw = Number(value);
  return Number.isFinite(raw) ? raw : fallback;
}

function asString(value: unknown, fallback = ""): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

async function requestJson(url: string, init?: RequestInit) {
  const resp = await fetch(url, init);
  const text = await resp.text();
  let data: unknown = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { ok: false, error: text.slice(0, 200) || "non-json response" };
  }
  return { resp, data };
}

function applyLlmNodeToState(llmNode: LooseObject | null, setLlm: Dispatch<SetStateAction<LlmNode>>) {
  if (!llmNode) return;
  const baseUrl = String(llmNode.base_url || "");
  let host = "127.0.0.1";
  let port = 11434;
  try {
    const parsed = new URL(baseUrl);
    host = parsed.hostname || host;
    port = Number(parsed.port || (parsed.protocol === "https:" ? 443 : 11434));
  } catch {}
  const httpRaw = Number(llmNode.http_timeout_sec);
  const fuseRaw = Number(llmNode.fuse_wait_timeout_sec);
  setLlm({
    provider: String(llmNode.provider || "ollama"),
    host,
    port,
    model: String(llmNode.model || ""),
    httpTimeoutSec: Number.isFinite(httpRaw) && httpRaw > 0 ? httpRaw : 15,
    fuseWaitSec: Number.isFinite(fuseRaw) && fuseRaw > 0 ? fuseRaw : 30,
  });
}

function normalizePluginKey(value: string | undefined): string {
  return String(value || "").trim().toLowerCase();
}

function conflictTone(severity: string | undefined): string {
  const value = String(severity || "").trim().toUpperCase();
  if (value === "P1") return "bg-rose-900/40 text-rose-300";
  if (value === "P2") return "bg-amber-900/40 text-amber-300";
  return "bg-cyan-900/40 text-cyan-300";
}

function compactRoutingScores(scores: Record<string, number> | undefined): string {
  if (!scores) return "";
  return Object.entries(scores)
    .map(([name, value]) => `${name} ${(Number(value) || 0).toFixed(2)}`)
    .filter(Boolean)
    .sort()
    .join(" · ");
}

function resolveRoutingPolicy(conflict: PluginConflict): string {
  const policy = String(conflict.routing_policy || "").trim();
  if (policy) return policy;
  const reason = String(conflict.routing_reason || "").trim();
  if (reason) return "explicit";
  return "severity_plus_policy";
}

function brainStepTone(kind: string | undefined): string {
  const value = String(kind || "").trim().toLowerCase();
  if (value.includes("manual") || value === "user") return "text-violet-300";
  if (value.includes("system")) return "text-amber-300";
  if (value.includes("llm")) return "text-cyan-300";
  return "text-zinc-400";
}

type ConflictMergeGroup = {
  key: string;
  conflict_type: string;
  severity: string;
  target_god: string;
  recommended_arbiter: string;
  conflicts: PluginConflict[];
  conflict_ids: string[];
  max_conflict_score: number;
};

function isConflictPending(
  conflict: PluginConflict,
  resolution?: PluginConflictResolution | undefined,
) {
  const status = String(conflict.resolution_status || "").trim().toLowerCase();
  if (status) {
    if (status === "approved" || status === "resolved_system") return false;
    if (status.startsWith("queued_")) return false;
  }

  const resolutionStatus = String(resolution?.status || "").trim().toLowerCase();
  if (resolutionStatus) {
    if (resolutionStatus === "approved" || resolutionStatus === "resolved_system") return false;
    if (resolutionStatus.startsWith("queued_")) return false;
  }
  return true;
}

function conflictMergeKey(row: PluginConflict) {
  const target = String(row.target_god || "未定目标").trim();
  const severity = String(row.severity || "P3").trim().toUpperCase();
  const type = String(row.conflict_type || "unknown").trim().toLowerCase();
  const arbiter = String(row.recommended_arbiter || "system").trim().toLowerCase();
  return `${type}#${target}#${severity}#${arbiter}`;
}

function buildConflictGroups(
  conflicts: PluginConflict[],
  resolutions: PluginConflictResolution[],
): ConflictMergeGroup[] {
  const resolutionByConflict = new Map<string, PluginConflictResolution>();
  for (const resolution of resolutions || []) {
    const conflictId = String(resolution.conflict_id || "").trim();
    if (conflictId) resolutionByConflict.set(conflictId, resolution);
  }

  const bucket: Record<string, ConflictMergeGroup> = {};
  for (const row of conflicts || []) {
    const conflictId = String(row.conflict_id || "").trim();
    if (!conflictId) continue;
    const resolution = resolutionByConflict.get(conflictId);
    if (!isConflictPending(row, resolution)) {
      continue;
    }
    const key = conflictMergeKey(row);
    if (!bucket[key]) {
      bucket[key] = {
        key,
        conflict_type: String(row.conflict_type || "unknown").trim(),
        severity: String(row.severity || "P3").trim(),
        target_god: String(row.target_god || "未定目标").trim(),
        recommended_arbiter: String(row.recommended_arbiter || "system").trim().toLowerCase(),
        conflicts: [],
        conflict_ids: [],
        max_conflict_score: 0,
      };
    }
    bucket[key].conflicts.push(row);
    bucket[key].conflict_ids.push(conflictId);
    bucket[key].max_conflict_score = Math.max(
      bucket[key].max_conflict_score,
      Number(row.conflict_score || 0),
    );
  }

  const grouped = Object.values(bucket).sort((a, b) => {
    const sevA = String(a.severity || "P3").toUpperCase();
    const sevB = String(b.severity || "P3").toUpperCase();
    const severityValue = { P1: 3, P2: 2, P3: 1 };
    const score = (value: string) => severityValue[value as keyof typeof severityValue] || 0;
    return (
      score(sevB) - score(sevA) ||
      b.max_conflict_score - a.max_conflict_score ||
      b.conflict_ids.length - a.conflict_ids.length ||
      b.target_god.localeCompare(a.target_god)
    );
  });

  return grouped;
}

function isInboxRuntimeStatus(status: string | undefined): boolean {
  const value = String(status || "").trim().toLowerCase();
  return new Set([
    "manual_pending",
    "manual_committed",
    "manual_rejected",
    "await_review",
    "context_pending",
    "context_consumed",
    "proposal_pending",
    "auto_applied",
  ]).has(value);
}

function isHitRuntimeStatus(status: string | undefined): boolean {
  const value = String(status || "").trim().toLowerCase();
  return value !== "" && value !== "unknown";
}

function runtimeStatusTone(status: string | undefined): string {
  const value = String(status || "").trim().toLowerCase();
  if (value === "auto_applied") return "bg-emerald-900/40 text-emerald-300";
  if (value === "manual_committed") return "bg-cyan-900/40 text-cyan-300";
  if (value === "manual_pending" || value === "await_review" || value === "proposal_pending") return "bg-amber-900/40 text-amber-300";
  if (value === "context_pending" || value === "context_consumed") return "bg-sky-900/40 text-sky-300";
  if (value === "manual_rejected") return "bg-rose-900/40 text-rose-300";
  if (value === "clamped") return "bg-fuchsia-900/40 text-fuchsia-300";
  if (value.startsWith("skipped")) return "bg-rose-900/40 text-rose-300";
  return "bg-zinc-800 text-zinc-400";
}

function compactProjection(projection: unknown): string {
  if (!projection || typeof projection !== "object") return "";
  const entries = Object.entries(projection as Record<string, unknown>)
    .map(([key, value]) => [key, Number(value || 0)] as const)
    .filter(([, value]) => Number.isFinite(value) && value > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);
  return entries.map(([key, value]) => `${key} ${Math.round(value * 100)}%`).join(" · ");
}

function runtimeStatusLabel(status: string | undefined): string {
  const value = String(status || "").trim().toLowerCase();
  if (value === "manual_pending") return "待手动处理";
  if (value === "manual_committed") return "已人工结算";
  if (value === "manual_rejected") return "已人工否决";
  if (value === "await_review") return "等待复核";
  if (value === "context_pending") return "上下文待消化";
  if (value === "context_consumed") return "上下文已消化";
  if (value === "proposal_pending") return "Proposal 待裁决";
  if (value === "auto_applied") return "自动已结算";
  if (value === "fact_only") return "仅命中事实";
  if (value === "clamped") return "护栏钳制";
  if (value === "skipped_dedup") return "重复跳过";
  if (value === "skipped_no_target") return "无目标跳过";
  return String(status || "unknown");
}

export default function V17AdminPage() {
  const [tab, setTab] = useState<TabKey>("llm");
  const [llm, setLlm] = useState<LlmNode>({ provider: "ollama", host: "192.168.0.12", port: 11434, model: "", httpTimeoutSec: 15, fuseWaitSec: 30 });
  const [db, setDb] = useState<DbBridge>({ driver: "postgres", host: "127.0.0.1", port: 5432, database: "v17_rebirth", username: "postgres", password: "", sslmode: "prefer", url: "", enabled: false });
  const [msg, setMsg] = useState("");
  const [llmModels, setLlmModels] = useState<string[]>([]);
  const [llmPrompt, setLlmPrompt] = useState("你好，请简单自我介绍。");
  const [llmTestReply, setLlmTestReply] = useState("");
  const [llmProbeMeta, setLlmProbeMeta] = useState("");
  const [dbProbeMeta, setDbProbeMeta] = useState("");
  const [busy, setBusy] = useState<ActionKey>(null);
  const [plugins, setPlugins] = useState<PluginAdminRow[]>([]);
  const [pluginStatuses, setPluginStatuses] = useState<PluginRuntimeStatus[]>([]);
  const [pluginClaims, setPluginClaims] = useState<PluginClaim[]>([]);
  const [pluginConflicts, setPluginConflicts] = useState<PluginConflict[]>([]);
  const [pluginConflictResolutions, setPluginConflictResolutions] = useState<PluginConflictResolution[]>([]);
  const [knowledgeSnapshot, setKnowledgeSnapshot] = useState<KnowledgeSnapshot>({});
  const [brainActionQueue, setBrainActionQueue] = useState<BrainAction[]>([]);
  const [recomputeContributions, setRecomputeContributions] = useState<RecomputeContribution[]>([]);
  const [pluginRuntimeSessionId, setPluginRuntimeSessionId] = useState("default");
  const [resolvedPluginRuntimeSessionId, setResolvedPluginRuntimeSessionId] = useState("default");
  const [physicsConstants, setPhysicsConstants] = useState<LooseObject>({});
  const [evolutionLogs, setEvolutionLogs] = useState<EvolutionLogEntry[]>([]);
  const [l0Locked, setL0Locked] = useState(true);
  const [resolveBusyKeys, setResolveBusyKeys] = useState<string[]>([]);
  const [pluginPolicyFilter, setPluginPolicyFilter] = useState<"all" | "warn">("all");

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(ORACLE_SESSION_STORAGE_KEY);
      if (stored && stored.trim()) {
        setPluginRuntimeSessionId(stored.trim());
      }
    } catch {}

    const syncFromStorage = () => {
      try {
        const stored = window.localStorage.getItem(ORACLE_SESSION_STORAGE_KEY);
        if (stored && stored.trim()) {
          setPluginRuntimeSessionId(stored.trim());
        }
      } catch {}
    };

    window.addEventListener("storage", syncFromStorage);
    return () => window.removeEventListener("storage", syncFromStorage);
  }, []);

  const llmBaseUrl = `http://${llm.host}:${llm.port}/v1`;
  const ghostBtn = "cursor-pointer rounded-md border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-semibold text-zinc-200 transition hover:border-zinc-500 hover:bg-zinc-800 disabled:opacity-50";
  const solidBtn = "cursor-pointer rounded-md bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 transition hover:bg-white disabled:opacity-60";

  const loadPlugins = useCallback(async () => {
    setBusy("loadPlugins");
    try {
      const [{ data }, { data: statusData }] = await Promise.all([
        requestJson("/api/v17-admin/plugins?v17_origin=v17_rebirth"),
        requestJson(`/api/v17-admin/plugin-runtime-status?v17_origin=v17_rebirth&session_id=${encodeURIComponent(pluginRuntimeSessionId || "default")}`),
      ]);
      const statusPayload = asLooseObject(statusData);
      const list = asLooseRecord<PluginAdminRow>(asLooseObject(data).plugins, []);
      const statusList = asLooseRecord<PluginRuntimeStatus>(statusPayload.statuses, []);
      const claimList = asLooseRecord<PluginClaim>(statusPayload.claims, []);
      const conflictList = asLooseRecord<PluginConflict>(statusPayload.conflicts, []);
      const resolutionList = asLooseRecord<PluginConflictResolution>(statusPayload.conflict_resolutions, []);
      const knowledge = (statusPayload.knowledge_snapshot as KnowledgeSnapshot) || {};
      const actions = asLooseRecord<BrainAction>(statusPayload.brain_action_queue, []);
      const contributions = asLooseRecord<RecomputeContribution>(statusPayload.recompute_contributions, []);
      setPlugins(list);
      setPluginStatuses(statusList);
      setPluginClaims(claimList);
      setPluginConflicts(conflictList);
      setPluginConflictResolutions(resolutionList);
      setKnowledgeSnapshot(knowledge);
      setBrainActionQueue(actions);
      setRecomputeContributions(contributions);
      setResolvedPluginRuntimeSessionId(asString(statusPayload.session_id, pluginRuntimeSessionId || "default"));
    } finally { setBusy(null); }
  }, [pluginRuntimeSessionId]);

  async function resolveConflictBatch(
    conflictIds: string[],
    arbiter: "system" | "llm" | "user",
    batchKey: string,
  ) {
    const ids = [...new Set((conflictIds || []).map((value) => String(value || "").trim()).filter(Boolean))];
    if (!ids.length || resolveBusyKeys.includes(batchKey)) return;
    setResolveBusyKeys((prev) => [...prev, batchKey]);
    try {
      const body: Record<string, unknown> = {
        session_id: resolvedPluginRuntimeSessionId || pluginRuntimeSessionId || "default",
        arbiter,
        v17_origin: "v17_rebirth",
      };
      if (ids.length === 1) {
        body.conflict_id = ids[0];
      } else {
        body.conflict_ids = ids;
      }

      const { resp, data } = await requestJson("/api/v17-admin/conflict-resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!resp.ok || !(data as { ok?: boolean }).ok) {
        setMsg(`冲突裁决失败：${String((data as { detail?: string }).detail || "unknown error")}`);
        return;
      }
      setMsg(`已提交 ${ids.length} 条冲突给 ${arbiter.toUpperCase()}。`);
      await loadPlugins();
    } finally {
      setResolveBusyKeys((prev) => prev.filter((item) => item !== batchKey));
    }
  }

  const loadEvolution = useCallback(async () => {
    setBusy("loadEvolution");
    try {
      const { data } = await requestJson("/api/v17/admin/evolution-logs?v17_origin=v17_rebirth&limit=50");
      const payload = asLooseObject(data);
      if (payload.ok) {
        setEvolutionLogs(asLooseRecord<EvolutionLogEntry>(payload.logs, []));
      }
    } finally { setBusy(null); }
  }, []);

  useEffect(() => {
    void (async () => {
      const [{ data: llmData }, { data: dbData }, { data: physicsData }] = await Promise.all([
        requestJson("/api/v17-admin/llm-node?v17_origin=v17_rebirth"),
        requestJson("/api/v17-admin/db-bridge?v17_origin=v17_rebirth"),
        requestJson("/api/v17-admin/physics-constants?v17_origin=v17_rebirth"),
      ]);
      const llmNode = asLooseObject(llmData).node;
      applyLlmNodeToState(typeof llmNode === "object" && llmNode !== null ? (llmNode as LooseObject) : null, setLlm);
      const bridge = asLooseObject(dbData).bridge;
      if (typeof bridge === "object" && bridge !== null) {
        setDb(bridge as DbBridge);
      }
      const constants = asLooseObject(physicsData).constants;
      if (typeof constants === "object" && constants !== null) {
        setPhysicsConstants(asLooseObject(constants));
      }
    })();
  }, []);

  useEffect(() => {
    if (tab === "plugins") loadPlugins();
    if (tab === "evolution") loadEvolution();
  }, [tab, loadPlugins, loadEvolution]);

  async function saveLlm() {
    setBusy("saveLlm");
    try {
      const { resp } = await requestJson("/api/v17-admin/llm-node", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...llm, base_url: llmBaseUrl, v17_origin: "v17_rebirth" }),
      });
      setMsg(resp.ok ? "LLM 配置已保存" : "保存失败");
    } finally { setBusy(null); }
  }

  async function loadModels() {
    setBusy("loadModels");
    try {
      const { data } = await requestJson("/api/v17-admin/llm-node/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: llmBaseUrl, v17_origin: "v17_rebirth" }),
      });
      const payload = asLooseObject(data);
      const result = asLooseObject(payload.result);
      const models = asLooseRecord<string>(result.models, []);
      if (payload.ok) {
        setLlmModels(models);
        setLlmProbeMeta(`模型列表：${asString(result.models_url, llmBaseUrl)}`);
        if (!llm.model && models.length) {
          setLlm((prev) => ({ ...prev, model: String(models[0] || "") }));
        }
        setMsg(`已加载 ${models.length} 个模型`);
      } else {
        setMsg(`加载模型失败：${asString(payload.error, "unknown error")}`);
      }
    } finally { setBusy(null); }
  }

  async function testLlm() {
    setBusy("testLlm");
    try {
      const { data } = await requestJson("/api/v17-admin/llm-node/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: llmBaseUrl, v17_origin: "v17_rebirth" }),
      });
      const payload = asLooseObject(data);
      const result = asLooseObject(payload.result);
      if (payload.ok) {
        setLlmProbeMeta(`连通成功 · ${asString(result.probe_url, llmBaseUrl)} · HTTP ${asString(result.http_status, "")}`);
        setMsg("LLM 节点连通成功");
      } else {
        setLlmProbeMeta("");
        setMsg(`LLM 连通失败：${asString(payload.error, "unknown error")}`);
      }
    } finally { setBusy(null); }
  }

  async function testLlmChat() {
    setBusy("testLlmChat");
    try {
      const { data } = await requestJson("/api/v17-admin/llm-node/chat-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_url: llmBaseUrl,
        model: llm.model,
        prompt: llmPrompt,
        v17_origin: "v17_rebirth",
      }),
      });
      const payload = asLooseObject(data);
      const result = asLooseObject(payload.result);
      if (payload.ok) {
        const reply = asString(result.reply, "");
        setLlmTestReply(reply.trim());
        setMsg("LLM 对话测试完成");
      } else {
        setLlmTestReply("");
        setMsg(`LLM 对话测试失败：${asString(payload.error, "unknown error")}`);
      }
    } finally { setBusy(null); }
  }

  async function saveDb() {
    setBusy("saveDb");
    try {
      const { resp, data } = await requestJson("/api/v17-admin/db-bridge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...db, v17_origin: "v17_rebirth" }),
      });
      const payload = asLooseObject(data);
      const bridge = asLooseObject(payload.bridge);
      if (resp.ok && payload.ok) {
        if (Object.keys(bridge).length) {
          setDb(bridge as DbBridge);
        }
        setMsg("数据库桥接配置已保存");
      } else {
        setMsg(`数据库桥接保存失败：${asString(payload.detail || payload.error, "unknown error")}`);
      }
    } finally { setBusy(null); }
  }

  async function testDb() {
    setBusy("testDb");
    try {
      const { data } = await requestJson("/api/v17-admin/db-bridge/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ host: db.host, port: db.port, v17_origin: "v17_rebirth" }),
      });
      const payload = asLooseObject(data);
      if (payload.ok) {
        setDbProbeMeta(`连通成功 · ${db.host}:${db.port}`);
        setMsg("数据库桥接连通成功");
      } else {
        setDbProbeMeta("");
        setMsg(`数据库桥接测试失败：${asString(payload.error, "unknown error")}`);
      }
    } finally { setBusy(null); }
  }

  async function savePhysics() {
    setBusy("savePhysics");
    try {
      await requestJson("/api/v17-admin/physics-constants", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ constants: physicsConstants, v17_origin: "v17_rebirth" }),
      });
      setMsg("物理定律已同步");
    } finally { setBusy(null); }
  }

  const brainTimeline = pluginConflicts.slice(0, 10).map((conflict) => {
    const conflictId = String(conflict.conflict_id || "").trim();
    const resolution = pluginConflictResolutions.find((item) => item.conflict_id === conflictId);
    const action = brainActionQueue.find((item) => String(item.conflict_id || "").trim() === conflictId);
    return { conflict, resolution, action };
  }).filter((row) => String(row.conflict.conflict_id || "").trim());

  const pluginPanelRows: PluginPanelRow[] = plugins.map((plugin) => {
    const pluginKey = normalizePluginKey(plugin.plugin_id);
    const moduleKey = normalizePluginKey(plugin.module);
    const runtime = pluginStatuses.find((row) => {
      const statusKey = normalizePluginKey(row.plugin_id);
      return statusKey === pluginKey || (statusKey && moduleKey && (statusKey === moduleKey || statusKey.endsWith(`.${moduleKey}`) || moduleKey.endsWith(`.${statusKey}`)));
    });
    const relatedClaims = pluginClaims.filter((row) => {
      const rowKey = normalizePluginKey(row.plugin_id);
      return rowKey === pluginKey || (rowKey && moduleKey && (rowKey === moduleKey || rowKey.endsWith(`.${moduleKey}`) || moduleKey.endsWith(`.${rowKey}`)));
    });
    const relatedConflicts = pluginConflicts.filter((row) => {
      const rows = Array.isArray(row.plugins) ? row.plugins : [];
      return rows.some((item) => {
        const itemKey = normalizePluginKey(item);
        return itemKey === pluginKey || (itemKey && moduleKey && (itemKey === moduleKey || itemKey.endsWith(`.${moduleKey}`) || moduleKey.endsWith(`.${itemKey}`)));
      });
    });
    return { plugin, runtime, relatedClaims, relatedConflicts };
  });
  const visiblePluginRows = pluginPanelRows.filter((row) =>
    pluginPolicyFilter === "warn" ? row.plugin.policy_valid === false : true,
  );
  const l2PatternRows = visiblePluginRows.filter((row) => {
    const pluginId = String(row.plugin.plugin_id || "").trim();
    return row.plugin.causal_tier === 3 && (pluginId.startsWith("classical.pattern.") || pluginId === "ten_god_pattern");
  });
  const scannedPluginCount = visiblePluginRows.length;
  const hitPluginRows = visiblePluginRows.filter((row) => {
    const factCount = Number(row.runtime?.fact_count || 0);
    return factCount > 0 || isHitRuntimeStatus(row.runtime?.status) || row.plugin.activated;
  });
  const inboxPluginRows = visiblePluginRows.filter((row) => {
    const decisionCount = Number(row.runtime?.decision_count || 0);
    return decisionCount > 0 || isInboxRuntimeStatus(row.runtime?.status);
  });
  const policyWarnCount = pluginPanelRows.filter((row) => row.plugin.policy_valid === false).length;

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 font-sans p-6 text-sm">
      <div className="mx-auto max-w-7xl grid grid-cols-1 md:grid-cols-[240px_1fr] gap-6">
        <aside className="space-y-2">
          <h1 className="text-sm font-bold text-zinc-500 mb-6 px-4">V17 CEREBRUM ADMIN</h1>
          {[
            { id: "llm", label: "LLM 节点", icon: "🧠" },
            { id: "db", label: "数据库桥接", icon: "💎" },
            { id: "plugins", label: "插件链", icon: "🧬" },
            { id: "physics", label: "宇宙常数", icon: "⚛️" },
            { id: "evolution", label: "演化审计", icon: "📜" },
          ].map((t) => (
            <button key={t.id} onClick={() => setTab(t.id as TabKey)} className={`w-full text-left px-4 py-2.5 rounded-xl transition ${tab === t.id ? "bg-zinc-100 text-black font-bold" : "text-zinc-400 hover:bg-zinc-900"}`}>
              {t.icon} <span className="ml-2">{t.label}</span>
            </button>
          ))}
        </aside>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6 min-h-[600px]">
          {tab === "llm" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold border-b border-zinc-800 pb-2">LLM Node Config</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <label className="text-xs text-zinc-400">
                      Provider
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.provider} onChange={e => setLlm(s => ({...s, provider: e.target.value}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      Model
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.model} onChange={e => setLlm(s => ({...s, model: e.target.value}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      Host
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.host} onChange={e => setLlm(s => ({...s, host: e.target.value}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      Port
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.port} onChange={e => setLlm(s => ({...s, port: Number(e.target.value)}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      HTTP Timeout
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.httpTimeoutSec} onChange={e => setLlm(s => ({...s, httpTimeoutSec: Number(e.target.value)}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      Fuse Wait
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.fuseWaitSec} onChange={e => setLlm(s => ({...s, fuseWaitSec: Number(e.target.value)}))} />
                    </label>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-[11px] text-zinc-400">
                    Base URL: <span className="text-zinc-200">{llmBaseUrl}</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button onClick={saveLlm} className={solidBtn} disabled={busy === "saveLlm"}>保存配置</button>
                    <button onClick={testLlm} className={ghostBtn} disabled={busy === "testLlm"}>连通测试</button>
                    <button onClick={loadModels} className={ghostBtn} disabled={busy === "loadModels"}>加载模型</button>
                  </div>
                  {llmProbeMeta ? <div className="text-xs text-emerald-300">{llmProbeMeta}</div> : null}
                </div>
                <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                  <div>
                    <div className="mb-2 text-xs text-zinc-400">模型测试</div>
                    <textarea
                      className="min-h-[120px] w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm"
                      value={llmPrompt}
                      onChange={e => setLlmPrompt(e.target.value)}
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button onClick={testLlmChat} className={solidBtn} disabled={busy === "testLlmChat" || !llm.model}>测试对话</button>
                  </div>
                  {llmModels.length ? (
                    <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
                      <div className="mb-2 text-[11px] uppercase tracking-wide text-zinc-500">Models</div>
                      <div className="flex max-h-40 flex-wrap gap-2 overflow-auto">
                        {llmModels.map((model) => (
                          <button
                            key={model}
                            type="button"
                            onClick={() => setLlm(s => ({ ...s, model }))}
                            className={`rounded-full border px-2 py-1 text-[11px] ${llm.model === model ? "border-cyan-400 bg-cyan-950/40 text-cyan-100" : "border-zinc-700 bg-zinc-950 text-zinc-300"}`}
                          >
                            {model}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
                    <div className="mb-2 text-[11px] uppercase tracking-wide text-zinc-500">Test Reply</div>
                    <div className="min-h-[120px] whitespace-pre-wrap text-sm text-zinc-200">
                      {llmTestReply || "尚未执行测试。"}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {tab === "db" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold border-b border-zinc-800 pb-2">Database Bridge</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <label className="text-xs text-zinc-400">
                      Driver
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.driver} onChange={e => setDb(s => ({...s, driver: e.target.value}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      Host
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.host} onChange={e => setDb(s => ({...s, host: e.target.value}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      Port
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.port} onChange={e => setDb(s => ({...s, port: Number(e.target.value)}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      Database
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.database} onChange={e => setDb(s => ({...s, database: e.target.value}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      Username
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.username} onChange={e => setDb(s => ({...s, username: e.target.value}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      Password
                      <input type="password" className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.password} onChange={e => setDb(s => ({...s, password: e.target.value}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      SSL Mode
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.sslmode} onChange={e => setDb(s => ({...s, sslmode: e.target.value}))} />
                    </label>
                    <label className="text-xs text-zinc-400">
                      URL
                      <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.url} onChange={e => setDb(s => ({...s, url: e.target.value}))} />
                    </label>
                  </div>
                  <label className="flex items-center gap-2 text-sm text-zinc-300">
                    <input type="checkbox" checked={db.enabled} onChange={e => setDb(s => ({...s, enabled: e.target.checked}))} />
                    启用数据库桥接
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button onClick={saveDb} className={solidBtn} disabled={busy === "saveDb"}>保存配置</button>
                    <button onClick={testDb} className={ghostBtn} disabled={busy === "testDb"}>连通测试</button>
                  </div>
                  {dbProbeMeta ? <div className="text-xs text-emerald-300">{dbProbeMeta}</div> : null}
                </div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                  <div className="mb-2 text-[11px] uppercase tracking-wide text-zinc-500">Bridge State</div>
                  <pre className="overflow-auto rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-xs text-zinc-300">
                    {JSON.stringify(db, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {tab === "physics" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold border-b border-zinc-800 pb-2">V17 Physics Constants</h2>
              <button onClick={() => setL0Locked(!l0Locked)} className="text-xs text-red-500 underline mb-4">{l0Locked ? "Unlock L0 Matrix" : "Lock L0 Matrix"}</button>
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-zinc-950/40 p-4 border border-zinc-800 rounded-xl">
                    <h3 className="text-xs text-zinc-500 font-bold mb-4">L0 FOUNDATION</h3>
                    {(() => {
                      const l0Foundation = asLooseObject(physicsConstants.L0_FOUNDATION) as PhysicsL0Foundation;
                      return (
                      <>
                    <label className="block text-xs mb-1">STEM_BASE</label>
                    <input
                      type="number"
                      disabled={l0Locked}
                      className="w-full bg-zinc-900 border border-zinc-800 p-2 rounded mb-3"
                      value={asNumber(l0Foundation.STEM_BASE, 0)}
                      onChange={e =>
                        setPhysicsConstants((s) => {
                          const updatedFoundation = { ...asLooseObject(s.L0_FOUNDATION), STEM_BASE: asNumber(e.target.value, 0) };
                          return { ...s, L0_FOUNDATION: updatedFoundation };
                        })}
                    />
                    <label className="block text-xs mb-1">BRANCH_BASE</label>
                    <input
                      type="number"
                      disabled={l0Locked}
                      className="w-full bg-zinc-900 border border-zinc-800 p-2 rounded mb-3"
                      value={asNumber(l0Foundation.BRANCH_BASE, 0)}
                      onChange={e =>
                        setPhysicsConstants((s) => {
                          const updatedFoundation = { ...asLooseObject(s.L0_FOUNDATION), BRANCH_BASE: asNumber(e.target.value, 0) };
                          return { ...s, L0_FOUNDATION: updatedFoundation };
                        })}
                    />
                      </>
                      );
                    })()}
                </div>
              </div>
              <button onClick={savePhysics} className={solidBtn}>Apply Universal Laws</button>
            </div>
          )}

          {tab === "evolution" && (
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-zinc-800 pb-2">
                <h2 className="text-lg font-bold">Evolution Ledger (The Causal Trace)</h2>
                <button onClick={loadEvolution} className="text-sky-500 text-xs">REFRESH</button>
              </div>
              <div className="bg-zinc-950 rounded-xl overflow-hidden border border-zinc-800">
                <table className="w-full text-xs text-left">
                  <thead className="bg-zinc-900/80 text-zinc-500 uppercase font-bold text-[10px]">
                    <tr>
                      <th className="px-4 py-3">Time</th>
                      <th className="px-4 py-3">God</th>
                      <th className="px-4 py-3">Delta</th>
                      <th className="px-4 py-3">Plugin / Step</th>
                      <th className="px-4 py-3">Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900">
                    {evolutionLogs.map((log) => {
                      const evolutionTime = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "—";
                      const deltaValue = asNumber(log.delta, 0);
                      const deltaText = `${deltaValue > 0 ? "+" : ""}${deltaValue.toFixed(2)}`;
                      return (
                        <tr key={log.id} className="hover:bg-zinc-800/20">
                          <td className="px-4 py-3 text-zinc-500">{evolutionTime}</td>
                          <td className="px-4 py-3 font-bold text-zinc-200">{log.ten_god}</td>
                          <td className={`px-4 py-3 font-mono ${deltaValue > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                            {deltaText}
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sky-400">{log.plugin_id}</span>
                            <div className="text-[9px] text-zinc-600">{log.step}</div>
                          </td>
                          <td className="px-4 py-3 text-zinc-400 whitespace-nowrap overflow-hidden text-ellipsis max-w-[200px]">{log.reason}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === "plugins" && (
            <div className="space-y-4">
               <div className="border-b border-zinc-800 pb-2">
                 <h2 className="text-lg font-bold">Plugin Runtime Atlas</h2>
                 <p className="mt-1 text-[11px] text-zinc-500">统一查看插件家族、命中层、决策入口、冲突层与重算贡献。</p>
               </div>
               <div className="flex items-center gap-2">
                  <input
                    className="bg-zinc-950 border border-zinc-800 p-2 rounded text-xs w-72"
                    placeholder="session_id（留 default 自动回退最近活跃会话）"
                    value={pluginRuntimeSessionId}
                    onChange={e => setPluginRuntimeSessionId(e.target.value)}
                  />
                  <button onClick={() => void loadPlugins()} className={solidBtn}>刷新运行态</button>
                  <span className="text-[10px] text-zinc-500">当前解析会话：{resolvedPluginRuntimeSessionId || "default"}</span>
               </div>
               <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3 text-[11px] text-zinc-400">
                 <div className="flex flex-wrap items-center gap-4">
                   <span>scanned {scannedPluginCount}</span>
                   <span>hit {hitPluginRows.length}</span>
                   <span>inbox {inboxPluginRows.length}</span>
                   <span>policy warn {policyWarnCount}</span>
                   <span>claims {Number(knowledgeSnapshot.claim_history?.total_claims || 0)}</span>
                   <span>conflicts {Number(knowledgeSnapshot.conflict_history?.total_conflicts || 0)}</span>
                  <span>suggestions {Number(knowledgeSnapshot.resolution_preview?.total_suggestions || 0)}</span>
                  <span>brain actions {brainActionQueue.length}</span>
                  <span>recompute {recomputeContributions.length}</span>
                </div>
                 <div className="mt-1 flex flex-wrap items-center gap-3 text-[10px] text-zinc-500">
                   <span>arbiter bias: system {Number(knowledgeSnapshot.conflict_history?.recommended_arbiters?.system || 0)}</span>
                   <span>llm {Number(knowledgeSnapshot.conflict_history?.recommended_arbiters?.llm || 0)}</span>
                   <span>user {Number(knowledgeSnapshot.conflict_history?.recommended_arbiters?.user || 0)}</span>
                 </div>
                 <div className="mt-1 flex flex-wrap items-center gap-3 text-[10px] text-zinc-400">
                   <span>feedback system {Number((knowledgeSnapshot.conflict_history?.feedback_arbiters || {}).system || 0)}</span>
                   <span>llm {Number((knowledgeSnapshot.conflict_history?.feedback_arbiters || {}).llm || 0)}</span>
                   <span>user {Number((knowledgeSnapshot.conflict_history?.feedback_arbiters || {}).user || 0)}</span>
                   <span>score system {Number((knowledgeSnapshot.conflict_history?.feedback_arbiter_scores || {}).system || 0).toFixed(2)}</span>
                   <span>llm {Number((knowledgeSnapshot.conflict_history?.feedback_arbiter_scores || {}).llm || 0).toFixed(2)}</span>
                   <span>user {Number((knowledgeSnapshot.conflict_history?.feedback_arbiter_scores || {}).user || 0).toFixed(2)}</span>
                 </div>
                </div>
               <div className="flex items-center gap-2">
                 <button
                   type="button"
                   onClick={() => setPluginPolicyFilter("all")}
                   className={`rounded border px-3 py-1 text-xs ${pluginPolicyFilter === "all" ? "border-zinc-300 bg-zinc-100 text-zinc-900" : "border-zinc-700 bg-zinc-950 text-zinc-300"}`}
                 >
                   全部插件
                 </button>
                 <button
                   type="button"
                   onClick={() => setPluginPolicyFilter("warn")}
                   className={`rounded border px-3 py-1 text-xs ${pluginPolicyFilter === "warn" ? "border-rose-300 bg-rose-100 text-rose-900" : "border-zinc-700 bg-zinc-950 text-zinc-300"}`}
                 >
                   只看 Policy Warn
                 </button>
                 <span className="text-[10px] text-zinc-500">
                   当前视图：{pluginPolicyFilter === "warn" ? "仅显示制度告警插件" : "显示全部插件"}
                 </span>
               </div>
               {brainActionQueue.length ? (
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="mb-2 text-[11px] font-semibold text-zinc-300">Brain Action Queue</div>
                   <div className="space-y-2">
                     {brainActionQueue.slice(0, 6).map((row, idx) => (
                       <div key={row.action_id || `brain_${idx}`} className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-2">
                         <div className="flex items-center justify-between gap-2">
                           <span className="text-[10px] uppercase text-sky-300">{row.action_type || "brain_action"}</span>
                           <span className="text-[10px] uppercase text-zinc-500">{row.queue || "llm"}</span>
                         </div>
                         <div className="mt-1 text-[10px] text-zinc-300">{row.reason || "—"}</div>
                         <div className="mt-1 text-[10px] text-zinc-500">
                           conflict {row.conflict_id || "—"} / confidence {Number(row.confidence || 0).toFixed(2)}
                         </div>
                       </div>
                     ))}
                   </div>
                 </div>
               ) : null}
               {brainTimeline.length ? (
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="mb-2 text-[11px] font-semibold text-zinc-300">Brain Flow Timeline</div>
                   <div className="space-y-2">
                     {brainTimeline.map((row, idx) => (
                       <div key={row.conflict.conflict_id || `timeline_${idx}`} className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-2">
                         <div className="text-[10px] uppercase text-zinc-400">
                           {row.conflict.conflict_type || "conflict"} · {row.conflict.conflict_id || "—"}
                         </div>
                         <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px]">
                           <span className="rounded border border-zinc-700 px-2 py-1 text-rose-300">
                             Conflict · {row.conflict.severity || "P?"}
                           </span>
                           <span className={`rounded border border-zinc-700 px-2 py-1 ${brainStepTone(row.resolution?.resolved_by || row.conflict.recommended_arbiter)}`}>
                             Resolution · {row.resolution?.resolved_by || row.conflict.recommended_arbiter || "pending"}
                           </span>
                           <span className={`rounded border border-zinc-700 px-2 py-1 ${brainStepTone(row.action?.action_type || row.resolution?.policy)}`}>
                             Brain Action · {row.action?.action_type || row.resolution?.policy || "waiting"}
                           </span>
                           <span className={`rounded border border-zinc-700 px-2 py-1 ${brainStepTone(row.action?.queue || row.resolution?.resolved_by)}`}>
                             Queue · {row.action?.queue || row.resolution?.next_queue || "pending"}
                           </span>
                         </div>
                         <div className="mt-2 text-[10px] text-zinc-400">
                            {row.action?.reason || row.resolution?.reason || row.conflict.why_conflict || "—"}
                         </div>
                          <div className="mt-1 text-[10px] text-zinc-500">
                            policy {resolveRoutingPolicy(row.conflict)} · {row.conflict.routing_policy || row.conflict.routing_reason || "routing reason pending"}
                          </div>
                          {compactRoutingScores(row.conflict.routing_scores || undefined) ? (
                            <div className="mt-1 text-[10px] text-zinc-500">
                              路由候选分数 {compactRoutingScores(row.conflict.routing_scores || undefined)}
                            </div>
                          ) : null}
                       </div>
                     ))}
                   </div>
                </div>
               ) : null}
               <div className="grid gap-3 md:grid-cols-3">
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="text-[11px] font-semibold text-zinc-300">扫描层</div>
                   <div className="mt-1 text-[10px] text-zinc-500">插件注册表中被扫描到的总量。</div>
                   <div className="mt-3 text-2xl font-semibold text-zinc-100">{scannedPluginCount}</div>
                 </div>
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="text-[11px] font-semibold text-zinc-300">命中层</div>
                   <div className="mt-1 text-[10px] text-zinc-500">本轮确实产出 facts / proposal / claim 的插件。</div>
                   <div className="mt-3 text-2xl font-semibold text-emerald-300">{hitPluginRows.length}</div>
                 </div>
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="text-[11px] font-semibold text-zinc-300">Inbox 层</div>
                   <div className="mt-1 text-[10px] text-zinc-500">已经进入手动、自动或上下文队列的插件。</div>
                   <div className="mt-3 text-2xl font-semibold text-amber-300">{inboxPluginRows.length}</div>
                 </div>
               </div>
               <div className="grid gap-3 lg:grid-cols-3">
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="mb-2 text-[11px] font-semibold text-zinc-300">扫描到的插件</div>
                   <div className="space-y-1 text-[10px] text-zinc-500">
                     {visiblePluginRows.slice(0, 12).map((row) => (
                       <div key={`scan_${row.plugin.plugin_id}`} className="flex items-center justify-between gap-2">
                         <span className="truncate">{pluginCardTitle(row.plugin)}</span>
                         <span className="text-zinc-700">L{row.plugin.causal_tier}</span>
                       </div>
                     ))}
                   </div>
                 </div>
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="mb-2 text-[11px] font-semibold text-zinc-300">命中并产出事实</div>
                   <div className="space-y-1 text-[10px] text-zinc-500">
                     {hitPluginRows.slice(0, 12).map((row) => (
                       <div key={`hit_${row.plugin.plugin_id}`} className="flex items-center justify-between gap-2">
                         <span className="truncate">{pluginCardTitle(row.plugin)}</span>
                         <span>{Number(row.runtime?.fact_count || 0)} facts</span>
                       </div>
                     ))}
                   </div>
                 </div>
                 <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                   <div className="mb-2 text-[11px] font-semibold text-zinc-300">已进入 Inbox</div>
                   <div className="space-y-1 text-[10px] text-zinc-500">
                     {inboxPluginRows.slice(0, 12).map((row) => (
                       <div key={`inbox_${row.plugin.plugin_id}`} className="flex items-center justify-between gap-2">
                         <span className="truncate">{pluginCardTitle(row.plugin)}</span>
                         <span>{runtimeStatusLabel(row.runtime?.status)}</span>
                       </div>
                     ))}
                   </div>
                 </div>
               </div>
               <div className="rounded-2xl border border-zinc-800 bg-zinc-950/30 p-3">
                 <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                   <div>
                     <h3 className="text-sm font-semibold text-zinc-100">L2 Classical Pattern System</h3>
                     <p className="mt-1 text-[11px] text-zinc-500">古典格局全集目录应归属于 admin 插件页中的 L2 结构层，而不是 Oracle 主页面。</p>
                   </div>
                   <div className="rounded-full border border-cyan-500/20 bg-cyan-950/20 px-3 py-1 text-[10px] text-cyan-200">
                     L2 插件 {l2PatternRows.length}
                   </div>
                 </div>
                 <V17_ClassicalPatternAtlas
                   title="L2 Classical Pattern Atlas"
                   subtitle="L2 古典格局全集目录、定义条件与系统挂接状态"
                   compact
                 />
               </div>
               <div className="space-y-2">
                  {visiblePluginRows.map(({ plugin: p, runtime, relatedClaims, relatedConflicts }) => {
                    const runtimeStatus = String(runtime?.status || "unknown");
                    const runtimeTone = runtimeStatusTone(runtimeStatus);
                    const matchValues = relatedClaims
                      .map((row) => Number(row.match_ratio || 0))
                      .filter((value) => Number.isFinite(value) && value > 0);
                    const avgMatch = matchValues.length
                      ? matchValues.reduce((sum, value) => sum + value, 0) / matchValues.length
                      : null;
                    const pluginTargets = Array.from(new Set([
                      String(runtime?.target_god || "").trim(),
                      ...relatedClaims.map((row) => String(row.target_god || "").trim()),
                    ].filter(Boolean)));
                    const relatedContribution = recomputeContributions.find((row) => pluginTargets.includes(String(row.target_god || "").trim()));
                    const topClaim = [...relatedClaims]
                      .sort((a, b) => Number(b.match_ratio || 0) - Number(a.match_ratio || 0))[0];
                    const projectionText = compactProjection(topClaim?.cluster_projection);
                    return (
                    <div key={p.plugin_id} className="p-3 bg-zinc-950/40 border border-zinc-800 rounded-xl">
                      <div className="flex justify-between items-center">
                       <div>
                          <div className="font-bold text-zinc-200">{pluginCardTitle(p)}</div>
                          <div className="text-[10px] text-zinc-500">Tier: {p.causal_tier} · Order: {p.execution_order}</div>
                          <div className="mt-1 text-[10px] text-zinc-400">{p.technical_label || p.plugin_id}</div>
                       </div>
                       <div className={`px-2 py-0.5 rounded text-[10px] ${p.activated ? "bg-emerald-900/40 text-emerald-400" : "bg-zinc-800 text-zinc-500"}`}>
                          {p.activated ? "ACTIVE" : "IDLE"}
                       </div>
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-[10px]">
                        <span className={`rounded px-2 py-0.5 uppercase ${runtimeTone}`}>{runtimeStatusLabel(runtimeStatus)}</span>
                        <span className={`rounded px-2 py-0.5 ${p.policy_valid === false ? "bg-rose-950/40 text-rose-300" : "bg-emerald-950/30 text-emerald-300"}`}>
                          {p.policy_valid === false ? "policy_warn" : "policy_ok"}
                        </span>
                        {runtime?.target_god ? <span className="text-zinc-500">target {runtime.target_god}</span> : null}
                        {typeof runtime?.fact_count === "number" ? <span className="text-zinc-600">facts {runtime.fact_count}</span> : null}
                        {typeof runtime?.proposal_count === "number" ? <span className="text-zinc-600">proposals {runtime.proposal_count}</span> : null}
                        {typeof runtime?.decision_count === "number" ? <span className="text-zinc-600">decisions {runtime.decision_count}</span> : null}
                        <span className="text-zinc-600">claims {relatedClaims.length}</span>
                        <span className="text-zinc-600">conflicts {relatedConflicts.length}</span>
                        {avgMatch !== null ? <span className="text-emerald-300">match {(avgMatch * 100).toFixed(0)}%</span> : null}
                        {relatedContribution ? <span className="text-sky-300">delta {Number(relatedContribution.delta_abs || 0).toFixed(2)}</span> : null}
                      </div>
                      <div className="mt-1 text-[10px] text-zinc-300">{pluginCardDefinition(p)}</div>
                      <div className="mt-1 text-[10px] text-zinc-500">{runtime?.reason || pluginCardDescription(p)}</div>
                      {topClaim ? (
                        <div className="mt-2 rounded-lg border border-zinc-800 bg-zinc-950/60 p-2 text-[10px] text-zinc-300">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="text-fuchsia-200">主落点 {String(topClaim.target_god || "未定目标")}</span>
                            <span className="text-fuchsia-300">match {Math.round(Number(topClaim.match_ratio || 0) * 100)}%</span>
                          </div>
                          <div className="mt-1 text-zinc-500">
                            占比 {Math.round(Number(topClaim.projection_share || 0) * 100)}%
                            {projectionText ? ` · ${projectionText}` : ""}
                          </div>
                        </div>
                      ) : null}
                      {relatedContribution ? (
                        <div className="mt-1 text-[10px] text-zinc-400">
                          重算贡献：{String(relatedContribution.target_god || "—")} {Number(relatedContribution.before || 0).toFixed(2)} → {Number(relatedContribution.after || 0).toFixed(2)}
                          {" · "}ratio {Number(relatedContribution.ratio_total || 0).toFixed(3)}
                          {" · "}delta {Number(relatedContribution.delta_abs || 0).toFixed(2)}
                        </div>
                      ) : null}
                      {p.config_required ? (
                        <div className="mt-1 text-[10px] text-zinc-500">
                          config: {p.config_exists ? (p.config_file || "present") : "missing"}
                        </div>
                      ) : null}
                      {Array.isArray(p.policy_errors) && p.policy_errors.length ? (
                        <div className="mt-1 space-y-1 text-[10px] text-rose-300">
                          {p.policy_errors.slice(0, 3).map((msg) => (
                            <div key={`${p.plugin_id}_${msg}`}>policy: {msg}</div>
                          ))}
                        </div>
                      ) : null}
                      {(() => {
                        const relatedGroups = buildConflictGroups(relatedConflicts, pluginConflictResolutions);
                        return relatedGroups.length ? (
                          <div className="mt-2 space-y-2">
                            {relatedGroups.slice(0, 5).map((group) => {
                              const sample = group.conflicts[0];
                              const firstConflictId = String(sample.conflict_id || "").trim();
                              const busyKey = `${p.plugin_id}|${group.key}`;
                              const isBusy = resolveBusyKeys.includes(busyKey);
                              return (
                                <div key={group.key} className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-2">
                                  <div className="flex items-center justify-between gap-2">
                                    <span className={`rounded px-2 py-0.5 text-[10px] uppercase ${conflictTone(group.severity)}`}>
                                      {group.severity || "P3"} · {group.recommended_arbiter || "system"}
                                    </span>
                                    <span className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-500">
                                      {group.conflict_type || "conflict"}
                                    </span>
                                  </div>
                                  <div className="mt-1 text-[10px] text-zinc-300">
                                    target {group.target_god} · {group.conflict_ids.length} 条
                                    · 评分 {group.max_conflict_score.toFixed(3)}
                                  </div>
                                  <div className="mt-1 text-[10px] text-zinc-500">
                                    policy {resolveRoutingPolicy(sample)} · {sample.routing_policy || sample.routing_reason || "routing reason pending"}
                                  </div>
                                  {compactRoutingScores(sample.routing_scores || undefined) ? (
                                    <div className="mt-1 text-[10px] text-zinc-500">
                                      路由候选分数 {compactRoutingScores(sample.routing_scores || undefined)}
                                    </div>
                                  ) : null}
                                  <div className="mt-1 text-[10px] text-zinc-500">
                                    {sample?.why_conflict || "—"}
                                  </div>
                                  {firstConflictId ? (
                                    <div className="mt-1 text-[10px] text-zinc-500">
                                      示例冲突 {firstConflictId}
                                    </div>
                                  ) : null}
                                  {group.conflicts.slice(0, 2).map((conflict) => {
                                    const plugins = Array.isArray(conflict.plugins) ? conflict.plugins : [];
                                    return (
                                      <div key={conflict.conflict_id} className="mt-1 text-[10px] text-zinc-400">
                                        · {conflict.why_conflict || conflict.conflict_id || "—"}
                                        {plugins.length ? `（来源插件 ${plugins.length} 个）` : ""}
                                      </div>
                                    );
                                  })}
                                  <div className="mt-2 flex items-center gap-2">
                                    <button
                                      type="button"
                                      disabled={isBusy}
                                      onClick={() => void resolveConflictBatch(group.conflict_ids, "system", busyKey)}
                                      className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-300 disabled:opacity-40"
                                    >
                                      System 批裁
                                    </button>
                                    <button
                                      type="button"
                                      disabled={isBusy}
                                      onClick={() => void resolveConflictBatch(group.conflict_ids, "llm", busyKey)}
                                      className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-300 disabled:opacity-40"
                                      title="按冲突批量提交给 LLM"
                                    >
                                      LLM 批裁
                                    </button>
                                    <button
                                      type="button"
                                      disabled={isBusy}
                                      onClick={() => void resolveConflictBatch(group.conflict_ids, "user", busyKey)}
                                      className="rounded border border-zinc-700 px-2 py-1 text-[10px] text-zinc-300 disabled:opacity-40"
                                    >
                                      用户批裁
                                    </button>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        ) : null;
                      })()}
                    </div>
                  )})}
               </div>
            </div>
          )}

          <p className="mt-8 text-xs text-zinc-600 italic">{msg || "Waiting for command..."}</p>
        </div>
      </div>
    </main>
  );
}
