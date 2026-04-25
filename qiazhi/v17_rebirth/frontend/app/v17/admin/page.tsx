"use client";

import { useCallback, useEffect, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";
import {
  Activity,
  ArrowRight,
  BrainCircuit,
  Database,
  FlaskConical,
  Gauge,
  PlugZap,
  Users,
} from "lucide-react";
import { V17_AppShell } from "@/components/V17_AppShell";
import { V17_PageGuard } from "@/components/V17_PageGuard";
import { V17_AdminPluginOverview } from "@/components/V17_AdminPluginOverview";
import { V17_AdminPluginTierPanel } from "@/components/V17_AdminPluginTierPanel";
import { V17_AdminPluginRuntimePanel } from "@/components/V17_AdminPluginRuntimePanel";
import { V17_AdminPhysicsPanel } from "@/components/V17_AdminPhysicsPanel";
import { V17_AdminEvolutionPanel } from "@/components/V17_AdminEvolutionPanel";
import { V17_AdminLlmPanel } from "@/components/V17_AdminLlmPanel";
import { V17_AdminDbPanel } from "@/components/V17_AdminDbPanel";
import { V17_AdminCoreEnginePanel } from "@/components/V17_AdminCoreEnginePanel";
import {
  V17_AdminLearningPanel,
  type LearningCampaignRuntime,
  type LearningCampaignUiConfig,
} from "@/components/V17_AdminLearningPanel";
import { V17_AdminUsersPanel, type AdminAuthUser } from "@/components/V17_AdminUsersPanel";
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
import { V17_FeatureOutlet, type V17FeatureRenderers } from "@/components/V17_FeatureOutlet";
import { requestJson, jsonPostInit } from "@/lib/apiClient";
import type { AdminFeatureTabKey } from "@/lib/featureRegistry";
import { useV17Runtime } from "@/hooks/useV17Runtime";

type TabKey = AdminFeatureTabKey;

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

type AdminConsoleCard = {
  id: TabKey;
  title: string;
  desc: string;
  badge: ReactNode;
  icon: ReactNode;
  tone: string;
};

function AdminConsoleDeck({
  cards,
  activeId,
  onSelect,
}: {
  cards: AdminConsoleCard[];
  activeId: TabKey;
  onSelect: (id: TabKey) => void;
}) {
  return (
    <section className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const active = card.id === activeId;
        return (
          <button
            key={card.id}
            type="button"
            onClick={() => onSelect(card.id)}
            className={`group min-w-0 rounded-2xl border p-3 text-left transition active:scale-[0.99] sm:p-4 ${
              active
                ? "border-cyan-400/45 bg-cyan-500/10 shadow-[0_0_24px_rgba(34,211,238,0.12)]"
                : "border-white/10 bg-white/[0.035] hover:border-white/20 hover:bg-white/[0.055]"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <span className={`rounded-xl border p-2 ${card.tone}`}>{card.icon}</span>
              <span className="inline-flex min-h-8 max-w-[42%] items-center justify-center rounded-full border border-white/10 bg-black/20 px-2 text-[10px] text-zinc-300">
                <span className="truncate">{card.badge}</span>
              </span>
            </div>
            <div className="mt-3 flex items-end justify-between gap-3">
              <div className="min-w-0">
                <h3 className="truncate text-sm font-semibold text-zinc-50">{card.title}</h3>
                <p className="mt-1 line-clamp-2 text-[11px] leading-5 text-zinc-400">{card.desc}</p>
              </div>
              <ArrowRight className={`h-4 w-4 shrink-0 transition ${active ? "text-cyan-200" : "text-zinc-500 group-hover:text-zinc-200"}`} />
            </div>
          </button>
        );
      })}
    </section>
  );
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
  const { language, user, authLoading, logout, access, ui } = useV17Runtime();
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
  const [relationDynamicsSummary, setRelationDynamicsSummary] = useState<LooseObject[]>([]);
  const [climateField, setClimateField] = useState<LooseObject>({});
  const [climateModifierLayer, setClimateModifierLayer] = useState<LooseObject>({});
  const [climateTheme, setClimateTheme] = useState<LooseObject>({});
  const [xiangfaTheme, setXiangfaTheme] = useState<LooseObject>({});
  const [tenGodDecomposition, setTenGodDecomposition] = useState<Record<string, TenGodDecompositionRow>>({});
  const [recomputeContributions, setRecomputeContributions] = useState<RecomputeContribution[]>([]);
  const [pluginRuntimeSessionId, setPluginRuntimeSessionId] = useState("default");
  const [resolvedPluginRuntimeSessionId, setResolvedPluginRuntimeSessionId] = useState("default");
  const [physicsConstants, setPhysicsConstants] = useState<LooseObject>({});
  const [evolutionLogs, setEvolutionLogs] = useState<EvolutionLogEntry[]>([]);
  const [l0Locked, setL0Locked] = useState(true);
  const [resolveBusyKeys, setResolveBusyKeys] = useState<string[]>([]);
  const [pluginPolicyFilter, setPluginPolicyFilter] = useState<"all" | "warn">("all");
  const [learningCampaign, setLearningCampaign] = useState<LearningCampaignRuntime>({});
  const [learningConfig, setLearningConfig] = useState<LearningCampaignUiConfig>({
    maxMinutes: 180,
    maxExtendedCases: "",
    requestLlmReview: false,
  });
  const [learningBusy, setLearningBusy] = useState(false);
  const [authUsers, setAuthUsers] = useState<AdminAuthUser[]>([]);
  const [authUsersLoading, setAuthUsersLoading] = useState(false);

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
  const selectAdminTab = (nextTab: TabKey) => {
    setTab(nextTab);
    requestAnimationFrame(() => {
      document.getElementById("v17-admin-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  const canManageSystem = access.canAccessAdmin && access.role === "admin";

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
      const relationDynamics = asLooseRecord<LooseObject>(statusPayload.relation_dynamics_summary, []);
      const climate = asLooseObject(statusPayload.climate_field);
      const climateModifier = asLooseObject(statusPayload.climate_modifier_layer);
      const climateTopic = asLooseObject(statusPayload.climate_theme);
      const xiangfaTopic = asLooseObject(statusPayload.xiangfa_theme);
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
      setRelationDynamicsSummary(relationDynamics);
      setClimateField(climate);
      setClimateModifierLayer(climateModifier);
      setClimateTheme(climateTopic);
      setXiangfaTheme(xiangfaTopic);
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

      const { resp, data } = await requestJson("/api/v17-admin/conflict-resolve", jsonPostInit(body));
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

  const loadLearningCampaign = useCallback(async () => {
    setLearningBusy(true);
    try {
      const { data } = await requestJson("/api/v17-admin/learning-campaign?v17_origin=v17_rebirth");
      const payload = asLooseObject(data);
      const campaign = asLooseObject(payload.campaign);
      if (Object.keys(campaign).length) {
        setLearningCampaign(campaign as LearningCampaignRuntime);
      }
    } finally {
      setLearningBusy(false);
    }
  }, []);

  const loadAuthUsers = useCallback(async () => {
    setAuthUsersLoading(true);
    try {
      const { data } = await requestJson("/api/auth/users");
      const payload = asLooseObject(data);
      const rows = Array.isArray(payload.users) ? payload.users : [];
      setAuthUsers(
        rows.map((row) => {
          const item = asLooseObject(row);
          return {
            id: Number(item.id || 0),
            username: asString(item.username),
            display_name: asString(item.display_name),
            email: asString(item.email),
            role: (asString(item.role, "user") as AdminAuthUser["role"]),
            is_active: Boolean(item.is_active),
            created_at: asString(item.created_at),
            last_login_at: asString(item.last_login_at),
	            latest_ip_address: asString(item.latest_ip_address),
	            latest_user_agent: asString(item.latest_user_agent),
	            latest_seen_at: asString(item.latest_seen_at),
	            role_request_id: Number(item.role_request_id || 0),
	            role_request_status: asString(item.role_request_status) as AdminAuthUser["role_request_status"],
	            role_request_role: asString(item.role_request_role) as AdminAuthUser["role_request_role"],
	            role_request_reason: asString(item.role_request_reason),
	            role_request_created_at: asString(item.role_request_created_at),
	            role_request_updated_at: asString(item.role_request_updated_at),
	          };
	        }),
	      );
    } finally {
      setAuthUsersLoading(false);
    }
  }, []);

	  async function updateAuthUserRole(userId: number, role: AdminAuthUser["role"]) {
    const { resp, data } = await requestJson(`/api/auth/users/${userId}/role`, jsonPostInit({ role }));
    const payload = asLooseObject(data);
    if (!resp.ok || payload.ok === false) {
      setMsg(`角色更新失败：${asString(payload.detail || payload.error, "未知错误")}`);
      return;
    }
    setMsg(`用户角色已更新为 ${role}`);
	    await loadAuthUsers();
	  }

	  async function decideAuthRoleRequest(requestId: number, decision: "approved" | "rejected") {
	    const { resp, data } = await requestJson(
	      `/api/auth/role-requests/${requestId}/decision`,
	      jsonPostInit({ status: decision }),
	    );
	    const payload = asLooseObject(data);
	    if (!resp.ok || payload.ok === false) {
	      setMsg(`命理师申请审核失败：${asString(payload.detail || payload.error, "未知错误")}`);
	      return;
	    }
	    setMsg(decision === "approved" ? "命理师申请已批准。" : "命理师申请已驳回。");
	    await loadAuthUsers();
	  }

  async function startLearningCampaign() {
    setLearningBusy(true);
    try {
      const maxCases = learningConfig.maxExtendedCases.trim();
      const { data } = await requestJson("/api/v17-admin/learning-campaign/start", jsonPostInit({
          v17_origin: "v17_rebirth",
          max_minutes: learningConfig.maxMinutes,
          max_extended_cases: maxCases ? Number(maxCases) : null,
          request_llm_review: learningConfig.requestLlmReview,
        }));
      const payload = asLooseObject(data);
      const campaign = asLooseObject(payload.campaign);
      if (Object.keys(campaign).length) {
        setLearningCampaign(campaign as LearningCampaignRuntime);
      }
      setMsg(payload.ok === false ? asString(payload.detail, "学习 Campaign 启动失败") : "学习 Campaign 已启动");
    } finally {
      setLearningBusy(false);
    }
  }

  async function pauseLearningCampaign() {
    setLearningBusy(true);
    try {
      const { data } = await requestJson("/api/v17-admin/learning-campaign/pause", jsonPostInit({ v17_origin: "v17_rebirth" }));
      const payload = asLooseObject(data);
      const campaign = asLooseObject(payload.campaign);
      if (Object.keys(campaign).length) {
        setLearningCampaign(campaign as LearningCampaignRuntime);
      }
      setMsg("学习 Campaign 已请求暂停");
    } finally {
      setLearningBusy(false);
    }
  }

  useEffect(() => {
    if (!canManageSystem) return;
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
  }, [canManageSystem]);

  useEffect(() => {
    if (!canManageSystem) return;
    if (tab === "plugins") loadPlugins();
    if (tab === "evolution") loadEvolution();
    if (tab === "learning") loadLearningCampaign();
    if (tab === "users") loadAuthUsers();
  }, [tab, canManageSystem, loadPlugins, loadEvolution, loadLearningCampaign, loadAuthUsers]);

  useEffect(() => {
    if (!canManageSystem) return;
    if (tab !== "learning") return;
    const status = String(learningCampaign.status || "");
    if (status !== "running" && status !== "pause_requested") return;
    const timer = window.setInterval(() => {
      void loadLearningCampaign();
    }, 1200);
    return () => window.clearInterval(timer);
  }, [tab, canManageSystem, learningCampaign.status, loadLearningCampaign]);

  async function saveLlm() {
    setBusy("saveLlm");
    try {
      const { resp } = await requestJson("/api/v17-admin/llm-node", jsonPostInit({ ...llm, base_url: llmBaseUrl, v17_origin: "v17_rebirth" }));
      setMsg(resp.ok ? "LLM 配置已保存" : "保存失败");
    } finally { setBusy(null); }
  }

  async function loadModels() {
    setBusy("loadModels");
    try {
      const { data } = await requestJson("/api/v17-admin/llm-node/models", jsonPostInit({ base_url: llmBaseUrl, v17_origin: "v17_rebirth" }));
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
      const { data } = await requestJson("/api/v17-admin/llm-node/test", jsonPostInit({ base_url: llmBaseUrl, v17_origin: "v17_rebirth" }));
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
      const { data } = await requestJson("/api/v17-admin/llm-node/chat-test", jsonPostInit({
          base_url: llmBaseUrl,
          model: llm.model,
          prompt: llmPrompt,
          v17_origin: "v17_rebirth",
        }));
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
      const { resp, data } = await requestJson("/api/v17-admin/db-bridge", jsonPostInit({ ...db, v17_origin: "v17_rebirth" }));
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
      const { data } = await requestJson("/api/v17-admin/db-bridge/test", jsonPostInit({ host: db.host, port: db.port, v17_origin: "v17_rebirth" }));
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
      await requestJson("/api/v17-admin/physics-constants", jsonPostInit({ constants: physicsConstants, v17_origin: "v17_rebirth" }));
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
  const adminConsoleCards: AdminConsoleCard[] = [
    {
      id: "llm",
      title: ui("模型引擎", "Model Engine", "모델 엔진"),
      desc: ui("配置模型、节点、超时与连通测试。", "Configure model, endpoint, timeout, and tests.", "모델, 노드, 제한시간, 연결 테스트를 설정합니다."),
      badge: llm.model || "model",
      icon: <BrainCircuit className="h-4 w-4" />,
      tone: "border-violet-400/25 bg-violet-500/10 text-violet-100",
    },
    {
      id: "db",
      title: ui("数据库", "Database", "데이터베이스"),
      desc: ui("Postgres 桥接、保存配置与连通测试。", "Postgres bridge, saved config, and connectivity.", "Postgres 브리지, 저장 설정, 연결 상태입니다."),
      badge: db.enabled ? "on" : "off",
      icon: <Database className="h-4 w-4" />,
      tone: "border-cyan-400/25 bg-cyan-500/10 text-cyan-100",
    },
    {
      id: "plugins",
      title: ui("规则引擎", "Rule Engine", "규칙 엔진"),
      desc: ui("插件运行态、冲突裁决与核心推理链。", "Plugin runtime, conflict arbitration, and reasoning chain.", "플러그인 런타임, 충돌 중재, 추론 체인입니다."),
      badge: plugins.length,
      icon: <PlugZap className="h-4 w-4" />,
      tone: "border-amber-400/25 bg-amber-500/10 text-amber-100",
    },
    {
      id: "physics",
      title: ui("参数中心", "Parameters", "파라미터"),
      desc: ui("L0 常数、冻结状态与基础权重。", "L0 constants, lock state, and base weights.", "L0 상수, 잠금 상태, 기본 가중치입니다."),
      badge: l0Locked ? "locked" : "edit",
      icon: <Gauge className="h-4 w-4" />,
      tone: "border-emerald-400/25 bg-emerald-500/10 text-emerald-100",
    },
    {
      id: "evolution",
      title: ui("审计日志", "Audit Logs", "감사 로그"),
      desc: ui("演化账本与每次十神位移记录。", "Evolution ledger and deity-shift records.", "진화 장부와 십신 이동 기록입니다."),
      badge: evolutionLogs.length,
      icon: <Activity className="h-4 w-4" />,
      tone: "border-sky-400/25 bg-sky-500/10 text-sky-100",
    },
    {
      id: "learning",
      title: ui("学习任务", "Learning", "학습 작업"),
      desc: ui("批量学习、LLM 复核与质量分数。", "Batch learning, LLM review, and quality score.", "일괄 학습, LLM 검토, 품질 점수입니다."),
      badge: asString(learningCampaign.status, "idle"),
      icon: <FlaskConical className="h-4 w-4" />,
      tone: "border-fuchsia-400/25 bg-fuchsia-500/10 text-fuchsia-100",
    },
    {
      id: "users",
      title: ui("成员权限", "Members", "멤버 권한"),
      desc: ui("账号、角色与协作权限维护。", "Accounts, roles, and collaboration access.", "계정, 역할, 협업 권한을 관리합니다."),
      badge: authUsers.length,
      icon: <Users className="h-4 w-4" />,
      tone: "border-zinc-400/25 bg-zinc-500/10 text-zinc-100",
    },
  ];
  const adminRenderers: V17FeatureRenderers<TabKey> = {
    llm: () => (
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
    ),
    db: () => (
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
    ),
    physics: () => (
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
    ),
    evolution: () => (
      <V17_AdminEvolutionPanel
        evolutionLogs={evolutionLogs}
        asNumber={asNumber}
        loadEvolution={loadEvolution}
      />
    ),
    plugins: () => (
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
          climateField={climateField}
          climateModifierLayer={climateModifierLayer}
          climateTheme={climateTheme}
          xiangfaTheme={xiangfaTheme}
          projectionBridgeProtocol={projectionBridgeProtocol}
          relationFormationSummary={relationFormationSummary}
          relationDynamicsSummary={relationDynamicsSummary}
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
    ),
    learning: () => (
      <V17_AdminLearningPanel
        campaign={learningCampaign}
        config={learningConfig}
        setConfig={setLearningConfig}
        loading={learningBusy}
        onStart={startLearningCampaign}
        onPause={pauseLearningCampaign}
        onRefresh={loadLearningCampaign}
      />
    ),
    users: () => (
      <V17_AdminUsersPanel
        users={authUsers}
        loading={authUsersLoading}
	        onRefresh={loadAuthUsers}
	        onUpdateRole={updateAuthUserRole}
	        onDecideRoleRequest={decideAuthRoleRequest}
	        operatorRole="admin"
	      />
    ),
  };

  return (
    <V17_PageGuard
      language={language}
      user={user}
      loading={authLoading}
      onLogout={() => void logout()}
      allowed={canManageSystem}
      forbiddenRedirectTo="/v17/oracle"
      forbiddenContent={(
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5 text-center sm:rounded-3xl sm:p-8">
          <div className="text-[11px] uppercase tracking-[0.28em] text-cyan-300/80">Admin Guard</div>
          <h1 className="mt-3 text-2xl font-semibold text-zinc-50">{ui("正在校验权限", "Checking access", "권한 확인 중")}</h1>
          <p className="mt-3 text-sm text-zinc-400">
            {ui("当前账号无管理员权限，正在返回主页面。", "This account does not have admin access. Returning to the main page.", "현재 계정에는 관리자 권한이 없어 메인 화면으로 돌아갑니다.")}
          </p>
        </div>
      )}
    >
      <V17_AppShell
        language={language}
        user={user}
        loading={authLoading}
        onLogout={() => void logout()}
        maxWidthClassName="max-w-[1500px]"
      >
        <div className="space-y-4 text-sm sm:space-y-6">
          <header className="rounded-2xl border border-zinc-800/80 bg-[linear-gradient(135deg,rgba(17,24,39,0.88),rgba(9,9,11,0.96))] p-4 shadow-[0_20px_80px_rgba(0,0,0,0.35)] sm:rounded-3xl sm:p-5">
            <div className="flex flex-col items-start justify-between gap-4 sm:flex-row">
              <div className="min-w-0">
                <div className="text-[11px] uppercase tracking-[0.28em] text-cyan-300/80">V17 Admin</div>
                <h1 className="mt-2 text-xl font-semibold tracking-tight text-zinc-50 sm:text-2xl">{ui("管理中枢", "Admin Console", "관리 콘솔")}</h1>
                <p className="mt-2 max-w-3xl text-[12px] leading-6 text-zinc-400">
                  {ui(
                    "对齐 L0-L4 插件体系、运行态、冲突裁决与演化账本。这里应该像控制台，而不是杂糅的配置页。",
                    "Operate L0-L4 plugins, runtime status, conflict arbitration, and evolution ledgers from one console.",
                    "L0-L4 플러그인, 런타임 상태, 충돌 중재, 진화 장부를 하나의 콘솔에서 다룹니다.",
                  )}
                </p>
              </div>
              <div className="flex max-w-full flex-wrap gap-2">
                <span className="rounded-full border border-zinc-700 bg-zinc-950/60 px-3 py-1 text-[10px] text-zinc-400">
                  {ui("当前标签", "Current tab", "현재 탭")} · {tab.toUpperCase()}
                </span>
                <span className="rounded-full border border-cyan-500/20 bg-cyan-950/20 px-3 py-1 text-[10px] text-cyan-200">
                  {ui("插件", "Plugins", "플러그인")} {plugins.length}
                </span>
                <span className="rounded-full border border-emerald-500/20 bg-emerald-950/20 px-3 py-1 text-[10px] text-emerald-200">
                  {ui("管理员", "Admin", "관리자")} {user?.display_name || user?.username || ""}
                </span>
              </div>
            </div>
          </header>

          <AdminConsoleDeck cards={adminConsoleCards} activeId={tab} onSelect={selectAdminTab} />

          <div id="v17-admin-panel" className="scroll-mt-20 min-h-[60vh] min-w-0 rounded-2xl border border-zinc-800/80 bg-[linear-gradient(180deg,rgba(24,24,27,0.72),rgba(9,9,11,0.92))] p-3 shadow-[0_20px_80px_rgba(0,0,0,0.28)] sm:scroll-mt-6 sm:rounded-3xl sm:p-6 md:min-h-[700px]">
            <V17_FeatureOutlet activeId={tab} renderers={adminRenderers} />

            <p className="mt-8 text-xs italic text-zinc-600">{msg || "等待指令..."}</p>
          </div>
        </div>
      </V17_AppShell>
    </V17_PageGuard>
  );
}
