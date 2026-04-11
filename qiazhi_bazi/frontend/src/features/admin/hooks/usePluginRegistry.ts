"use client";

import useSWR from "swr";
import { useMemo } from "react";

export type BlindSchoolSkillItem = {
  id: string;
  name: string;
  description: string;
  impact_factor: string;
  assertion_template: string;
  physics_setting_key?: string;
  physics_weight?: number;
  /** 例如 `core_conflict`、`SHANG_GUAN_JIAN_GUAN`，供管理台路由分组 */
  description_tags?: string[];
};

export type BasePhysicsSkillRow = BlindSchoolSkillItem;

export type PluginManifestItem = {
  id: string;
  layer: "L1" | "L2" | "L3" | "L4";
  category: string;
  status: "HEALTHY" | "IDLE" | "ERROR";
  dependencies: string[];
  metadata: {
    label: string;
    doc_path: string;
    priority: number;
    hook: string;
    display_name?: string;
    use_case?: string;
    detailed_description?: string;
    physical_impact?: string;
    governance_notes?: string;
    description_tags?: string[];
    skills?: BlindSchoolSkillItem[];
    blueprint_markdown?: string;
    l1_physics_operator?: boolean;
    op_id?: string;
  };
  performance_snapshot?: { last_latency_ms?: number | null; p50_ms?: number | null; p95_ms?: number | null; error_rate?: number | null };
};

export type PluginManifest = {
  plugins: PluginManifestItem[];
  dependency_links: Array<{ from: string; to: string }>;
  performance_snapshot?: { plugin_count?: number; max_last_latency_ms?: number | null };
  global_conflict_tension?: number;
  /** 后端 `DEFAULT_PHYSICS_SETTINGS` 快照，供 Lab 与运行时 η 对齐校验 */
  default_physics_settings?: Record<string, number>;
  /** 与 `manifests/l1_physics_manifest.json` 同源，供蓝图 Modal 与 LLM 对齐 */
  l1_physics_manifest?: Record<string, unknown>;
  /**
   * `base_physics/skill_manifest.json` 全量 skills（扁平注册表，供 DNA/LLM/一致性校验）。
   * L1 算子卡片的 `metadata.skills` 仅含该算子映射的一行，二者数据源相同但用途不同，管理台勿合并为重复卡片。
   */
  base_physics_skills?: BasePhysicsSkillRow[];
  refreshed_at?: number;
};

const API_BASE_RAW = (process.env.NEXT_PUBLIC_QIAZHI_API ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");
const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "::1"]);
export const resolveQiazhiApiBasePrefix = () => {
  if (!API_BASE_RAW) return "";
  if (API_BASE_RAW === "/api") return "";
  if (API_BASE_RAW.startsWith("/")) return API_BASE_RAW;
  if (typeof window === "undefined") return API_BASE_RAW;
  try {
    const apiHost = new URL(API_BASE_RAW).hostname;
    const pageHost = window.location.hostname;
    if (LOOPBACK_HOSTS.has(apiHost) && !LOOPBACK_HOSTS.has(pageHost)) return "";
  } catch {
    return "";
  }
  return API_BASE_RAW;
};
const API_BASE = resolveQiazhiApiBasePrefix();

/** 单插件蓝图（GET `/api/v1/plugins/manifest?plugin_id=`） */
export function buildPluginManifestUrl(pluginId: string): string {
  return `${API_BASE}/api/v1/plugins/manifest?plugin_id=${encodeURIComponent(pluginId)}`;
}

const fetcher = async (url: string): Promise<PluginManifest> => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`manifest fetch failed: ${res.status}`);
  return res.json();
};

export function usePluginRegistry() {
  const shouldFetchManifest = useMemo(() => {
    if (typeof window === "undefined") return true;
    if (!API_BASE) return true;
    if (API_BASE.startsWith("/")) return true;
    let apiHost = "";
    try {
      apiHost = new URL(API_BASE).hostname;
    } catch {
      return true;
    }
    const pageHost = window.location.hostname;
    const apiIsLoopback = LOOPBACK_HOSTS.has(apiHost);
    const pageIsLoopback = LOOPBACK_HOSTS.has(pageHost);
    // 外域页面访问 loopback 地址会被浏览器私网策略拦截，直接停用拉取避免反复报错/重试。
    if (apiIsLoopback && !pageIsLoopback) return false;
    return true;
  }, []);

  const swrKey = shouldFetchManifest ? `${API_BASE}/api/v1/plugins/manifest` : null;
  const { data, error, isLoading, mutate } = useSWR<PluginManifest>(swrKey, fetcher, {
    refreshInterval: shouldFetchManifest ? 8000 : 0,
    revalidateOnFocus: shouldFetchManifest,
    shouldRetryOnError: false,
    revalidateOnReconnect: shouldFetchManifest,
  });

  const blockedError = !shouldFetchManifest
    ? new Error("Plugin manifest disabled: page origin cannot access loopback API.")
    : undefined;

  return {
    manifest: data,
    error: error || blockedError,
    isLoading: shouldFetchManifest ? isLoading : false,
    refresh: () => (shouldFetchManifest ? mutate() : Promise.resolve(undefined)),
  };
}

