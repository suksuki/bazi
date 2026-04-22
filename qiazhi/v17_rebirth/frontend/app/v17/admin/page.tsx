"use client";

import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { V17_AdminPluginOverview } from "@/components/V17_AdminPluginOverview";
import { V17_AdminPluginTierPanel } from "@/components/V17_AdminPluginTierPanel";
import { V17_AdminPluginRuntimePanel } from "@/components/V17_AdminPluginRuntimePanel";
import { V17_AdminPhysicsPanel } from "@/components/V17_AdminPhysicsPanel";
import { V17_AdminEvolutionPanel } from "@/components/V17_AdminEvolutionPanel";
import { V17_AdminLlmPanel } from "@/components/V17_AdminLlmPanel";
import { V17_AdminDbPanel } from "@/components/V17_AdminDbPanel";
import { V17_AdminCoreEnginePanel } from "@/components/V17_AdminCoreEnginePanel";
import {
  ADMIN_GHOST_BTN,
  ADMIN_SOLID_BTN,
  asLooseObject,
  asLooseRecord,
  asNumber,
  asString,
  brainStepTone,
  buildConflictGroups,
  buildPluginTierBuckets,
  compactProjection,
  compactRoutingScores,
  conflictTone,
  formatArbiterLabel,
  formatQueueLabel,
  isHitRuntimeStatus,
  isInboxRuntimeStatus,
  normalizePluginKey,
  pickAutoArbiter,
  pluginCardDefinition,
  pluginCardDescription,
  pluginCardTitle,
  resolveRoutingPolicy,
  runtimeStatusLabel,
  runtimeStatusTone,
  type ArbiterRole,
  type ConflictMergeGroupLike,
  type LooseObject,
  type PluginTierBucketLike,
} from "@/components/adminShared";

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

type CoreEngineAuthority = LooseObject;
type TenGodDecompositionRow = {
  manifest?: number;
  root?: number;
  momentum?: number;
  momentum_month_order?: number;
  momentum_stage?: number;
  momentum_stage_lu?: number;
  momentum_stage_blade?: number;
  momentum_stage_general?: number;
  momentum_structure?: number;
  momentum_auxiliary?: number;
  momentum_other?: number;
  hidden?: number;
  total?: number;
};

type PluginPanelRow = {
  plugin: PluginAdminRow;
  runtime?: PluginRuntimeStatus;
  relatedClaims: PluginClaim[];
  relatedConflicts: PluginConflict[];
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
const ORACLE_SESSION_STORAGE_KEY = "v17.oracle.current_session_id";

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
  const [coreEngineAuthority, setCoreEngineAuthority] = useState<CoreEngineAuthority>({});
  const [projectionBridgeProtocol, setProjectionBridgeProtocol] = useState<LooseObject>({});
  const [relationFormationSummary, setRelationFormationSummary] = useState<LooseObject[]>([]);
  const [tenGodDecomposition, setTenGodDecomposition] = useState<Record<string, TenGodDecompositionRow>>({});
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
  const ghostBtn = ADMIN_GHOST_BTN;
  const solidBtn = ADMIN_SOLID_BTN;

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
      const authority = asLooseObject(statusPayload.core_engine_authority);
      const bridgeProtocol =
        asLooseObject(statusPayload.projection_bridge_protocol) ||
        asLooseObject(authority.projection_bridge_protocol);
      const relationSummary = asLooseRecord<LooseObject>(statusPayload.relation_formation_summary, []);
      const decomposition = asLooseObject(statusPayload.ten_gods_decomposition_l0) as Record<string, TenGodDecompositionRow>;
      const contributions = asLooseRecord<RecomputeContribution>(statusPayload.recompute_contributions, []);
      setPlugins(list);
      setPluginStatuses(statusList);
      setPluginClaims(claimList);
      setPluginConflicts(conflictList);
      setPluginConflictResolutions(resolutionList);
      setKnowledgeSnapshot(knowledge);
      setBrainActionQueue(actions);
      setCoreEngineAuthority(authority);
      setProjectionBridgeProtocol(bridgeProtocol);
      setRelationFormationSummary(relationSummary);
      setTenGodDecomposition(decomposition);
      setRecomputeContributions(contributions);
      setResolvedPluginRuntimeSessionId(asString(statusPayload.session_id, pluginRuntimeSessionId || "default"));
    } finally { setBusy(null); }
  }, [pluginRuntimeSessionId]);

  async function resolveConflictBatch(
    conflictIds: string[],
    arbiter: ArbiterRole,
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
        setMsg(`冲突裁决失败：${String((data as { detail?: string }).detail || "未知错误")}`);
        return;
      }
      setMsg(`已提交 ${ids.length} 条冲突给 ${formatArbiterLabel(arbiter)}。`);
      await loadPlugins();
    } finally {
      setResolveBusyKeys((prev) => prev.filter((item) => item !== batchKey));
    }
  }

  async function resolveConflictByRule(group: ConflictMergeGroupLike, busyKey?: string) {
    const ids = Array.from(new Set(group.conflict_ids || []));
    if (!ids.length) return;
    const autoArbiter = pickAutoArbiter(group.severity);
    const nextBusyKey = busyKey || `auto_rule_${group.key}`;
    await resolveConflictBatch(ids, autoArbiter, nextBusyKey);
  }

  async function resolveAllConflictByRule(groups: ConflictMergeGroupLike[]) {
    const allBusyKey = "auto_rule_all_conflicts";
    if (resolveBusyKeys.includes(allBusyKey)) return;
    if (!groups.length) {
      setMsg("当前无可处理冲突。");
      return;
    }
    setResolveBusyKeys((prev) => [...prev, allBusyKey]);
    try {
      await Promise.all(
        groups.map((group) => resolveConflictByRule(group, `auto_rule_${group.key}`)),
      );
    } finally {
      setResolveBusyKeys((prev) => prev.filter((item) => item !== allBusyKey));
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
        setMsg(`加载模型失败：${asString(payload.error, "未知错误")}`);
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
        setMsg(`LLM 连通失败：${asString(payload.error, "未知错误")}`);
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
        setMsg(`LLM 对话测试失败：${asString(payload.error, "未知错误")}`);
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
        setMsg(`数据库桥接保存失败：${asString(payload.detail || payload.error, "未知错误")}`);
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
        setMsg(`数据库桥接测试失败：${asString(payload.error, "未知错误")}`);
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

  const pendingConflictGroups = buildConflictGroups(pluginConflicts, pluginConflictResolutions);

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
  const pluginTierBuckets: PluginTierBucketLike<PluginAdminRow>[] = buildPluginTierBuckets(visiblePluginRows);
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
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.08),transparent_26%),linear-gradient(180deg,#09090b_0%,#111827_100%)] px-4 py-6 text-sm text-zinc-100 md:px-6">
      <div className="mx-auto max-w-[1500px] space-y-6">
        <header className="rounded-3xl border border-zinc-800/80 bg-[linear-gradient(135deg,rgba(17,24,39,0.88),rgba(9,9,11,0.96))] p-5 shadow-[0_20px_80px_rgba(0,0,0,0.35)]">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-[11px] uppercase tracking-[0.28em] text-cyan-300/80">V17 Admin</div>
              <h1 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-50">管理中枢</h1>
              <p className="mt-2 max-w-3xl text-[12px] leading-6 text-zinc-400">
                对齐 L0-L4 插件体系、运行态、冲突裁决与演化账本。这里应该像控制台，而不是杂糅的配置页。
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-zinc-700 bg-zinc-950/60 px-3 py-1 text-[10px] text-zinc-400">
                当前标签 · {tab.toUpperCase()}
              </span>
              <span className="rounded-full border border-cyan-500/20 bg-cyan-950/20 px-3 py-1 text-[10px] text-cyan-200">
                插件 {plugins.length}
              </span>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-[260px_1fr]">
        <aside className="rounded-3xl border border-zinc-800/70 bg-zinc-950/40 p-3 backdrop-blur">
          <h1 className="mb-4 px-3 text-[11px] font-bold uppercase tracking-[0.28em] text-zinc-500">V17 管理中枢</h1>
          <div className="space-y-2">
          {[
            { id: "llm", label: "LLM 节点", icon: "🧠" },
            { id: "db", label: "数据库桥接", icon: "💎" },
            { id: "plugins", label: "插件链", icon: "🧬" },
            { id: "physics", label: "宇宙常数", icon: "⚛️" },
            { id: "evolution", label: "演化审计", icon: "📜" },
          ].map((t) => (
            <button key={t.id} onClick={() => setTab(t.id as TabKey)} className={`w-full rounded-2xl px-4 py-3 text-left transition ${tab === t.id ? "border border-zinc-200/80 bg-zinc-100 text-black shadow-[0_10px_30px_rgba(255,255,255,0.08)]" : "border border-transparent text-zinc-400 hover:border-zinc-800 hover:bg-zinc-900/70 hover:text-zinc-100"}`}>
              {t.icon} <span className="ml-2">{t.label}</span>
            </button>
          ))}
          </div>
        </aside>

        <div className="min-h-[700px] rounded-3xl border border-zinc-800/80 bg-[linear-gradient(180deg,rgba(24,24,27,0.72),rgba(9,9,11,0.92))] p-6 shadow-[0_20px_80px_rgba(0,0,0,0.28)]">
          {tab === "llm" && (
            <V17_AdminLlmPanel
              llm={llm}
              setLlm={setLlm}
              llmBaseUrl={llmBaseUrl}
              llmProbeMeta={llmProbeMeta}
              llmPrompt={llmPrompt}
              setLlmPrompt={setLlmPrompt}
              llmModels={llmModels}
              llmTestReply={llmTestReply}
              busy={busy}
              saveLlm={saveLlm}
              testLlm={testLlm}
              loadModels={loadModels}
              testLlmChat={testLlmChat}
              solidBtn={solidBtn}
              ghostBtn={ghostBtn}
            />
          )}

          {tab === "db" && (
            <V17_AdminDbPanel
              db={db}
              setDb={setDb}
              dbProbeMeta={dbProbeMeta}
              busy={busy}
              saveDb={saveDb}
              testDb={testDb}
              solidBtn={solidBtn}
              ghostBtn={ghostBtn}
            />
          )}

          {tab === "physics" && (
            <V17_AdminPhysicsPanel
              l0Locked={l0Locked}
              setL0Locked={setL0Locked}
              physicsConstants={physicsConstants}
              setPhysicsConstants={setPhysicsConstants}
              asLooseObject={asLooseObject}
              asNumber={asNumber}
              savePhysics={savePhysics}
              solidBtn={solidBtn}
            />
          )}

          {tab === "evolution" && (
            <V17_AdminEvolutionPanel
              evolutionLogs={evolutionLogs}
              asNumber={asNumber}
              loadEvolution={loadEvolution}
            />
          )}

          {tab === "plugins" && (
            <div className="space-y-4">
               <V17_AdminPluginRuntimePanel
                 pluginRuntimeSessionId={pluginRuntimeSessionId}
                 setPluginRuntimeSessionId={setPluginRuntimeSessionId}
                 resolvedPluginRuntimeSessionId={resolvedPluginRuntimeSessionId}
                 loadPlugins={loadPlugins}
                 scannedPluginCount={scannedPluginCount}
                 hitPluginCount={hitPluginRows.length}
                 inboxPluginCount={inboxPluginRows.length}
                 policyWarnCount={policyWarnCount}
                 knowledgeSnapshot={knowledgeSnapshot}
                 brainActionQueue={brainActionQueue}
                 recomputeContributionCount={recomputeContributions.length}
                 pluginPolicyFilter={pluginPolicyFilter}
                 setPluginPolicyFilter={setPluginPolicyFilter}
                 resolveBusyKeys={resolveBusyKeys}
                 pendingConflictGroups={pendingConflictGroups}
                 resolveAllConflictByRule={resolveAllConflictByRule}
                 brainTimeline={brainTimeline}
                 formatQueueLabel={formatQueueLabel}
                 formatArbiterLabel={formatArbiterLabel}
                 conflictTone={conflictTone}
                 brainStepTone={brainStepTone}
                 resolveRoutingPolicy={resolveRoutingPolicy}
                 compactRoutingScores={compactRoutingScores}
               />
               <V17_AdminCoreEnginePanel
                 pluginCount={plugins.length}
                 hasAuthoritySource={pluginClaims.some((row) => String((row as Record<string, unknown>)?.plugin_id || "").includes("god_ring_resolver"))}
                 authority={coreEngineAuthority}
                 projectionBridgeProtocol={projectionBridgeProtocol}
                 relationFormationSummary={relationFormationSummary}
                 tenGodDecomposition={tenGodDecomposition}
               />
               <V17_AdminPluginOverview
                 scannedPluginCount={scannedPluginCount}
                 hitPluginRows={hitPluginRows}
                 inboxPluginRows={inboxPluginRows}
                 visiblePluginRows={visiblePluginRows}
                 l2PatternCount={l2PatternRows.length}
                 pluginCardTitle={(plugin) => pluginCardTitle(plugin as PluginAdminRow)}
                 runtimeStatusLabel={runtimeStatusLabel}
               />
               <V17_AdminPluginTierPanel
                 pluginTierBuckets={pluginTierBuckets}
                 recomputeContributions={recomputeContributions}
                 resolveBusyKeys={resolveBusyKeys}
                 pluginConflictResolutions={pluginConflictResolutions}
                 pluginCardTitle={pluginCardTitle}
                 pluginCardDefinition={pluginCardDefinition}
                 pluginCardDescription={pluginCardDescription}
                 runtimeStatusTone={runtimeStatusTone}
                 runtimeStatusLabel={runtimeStatusLabel}
                 compactProjection={compactProjection}
                 buildConflictGroups={buildConflictGroups}
                 conflictTone={conflictTone}
                 formatArbiterLabel={formatArbiterLabel}
                 resolveRoutingPolicy={resolveRoutingPolicy}
                 compactRoutingScores={compactRoutingScores}
                 resolveConflictByRule={resolveConflictByRule}
                 resolveConflictBatch={resolveConflictBatch}
               />
            </div>
          )}

                        <p className="mt-8 text-xs text-zinc-600 italic">{msg || "等待指令..."}</p>
        </div>
      </div>
      </div>
    </main>
  );
}
