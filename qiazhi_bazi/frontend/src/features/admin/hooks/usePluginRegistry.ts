"use client";

import useSWR from "swr";

export type PluginManifestItem = {
  id: string;
  layer: "L1" | "L2" | "L3" | "L4";
  category: string;
  status: "HEALTHY" | "IDLE" | "ERROR";
  dependencies: string[];
  metadata: { label: string; doc_path: string; priority: number; hook: string };
  performance_snapshot?: { last_latency_ms?: number | null; p50_ms?: number | null; p95_ms?: number | null; error_rate?: number | null };
};

export type PluginManifest = {
  plugins: PluginManifestItem[];
  dependency_links: Array<{ from: string; to: string }>;
  performance_snapshot?: { plugin_count?: number; max_last_latency_ms?: number | null };
  global_conflict_tension?: number;
  refreshed_at?: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";

const fetcher = async (url: string): Promise<PluginManifest> => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`manifest fetch failed: ${res.status}`);
  return res.json();
};

export function usePluginRegistry() {
  const { data, error, isLoading, mutate } = useSWR<PluginManifest>(`${API_BASE}/api/v1/plugins/manifest`, fetcher, {
    refreshInterval: 8000,
    revalidateOnFocus: true,
  });
  return { manifest: data, error, isLoading, refresh: () => mutate() };
}

