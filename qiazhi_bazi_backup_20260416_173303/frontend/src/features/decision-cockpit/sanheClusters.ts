import { sysCorePhysicsPayload } from "@/features/stream-board/sysCorePhysics";

/** 与 cardBuilder 对齐：仅从 `plugin_outputs.sys.core.physics` 解析三合簇。 */
export type SanheClusterRow = {
  key: string;
  branches: string[];
  clusterAbs: number | null;
  status: string;
  nodeLine: string;
  detail: string;
};

export function extractSanheClusters(physics: Record<string, unknown> | null | undefined): SanheClusterRow[] {
  if (!physics || typeof physics !== "object") return [];
  const po = physics.plugin_outputs as Record<string, unknown> | undefined;
  const sysPayload = sysCorePhysicsPayload(po);
  const raw = sysPayload && Array.isArray(sysPayload.sanhe_clusters) ? sysPayload.sanhe_clusters : [];
  const clusters: unknown[] = Array.isArray(raw) ? raw : [];
  const out: SanheClusterRow[] = [];
  clusters.forEach((cl, idx) => {
    if (!cl || typeof cl !== "object") return;
    const row = cl as Record<string, unknown>;
    const brs = Array.isArray(row.branches) ? row.branches.map((x) => String(x)) : [];
    if (brs.length < 3) return;
    const nodes = Array.isArray(row.nodes) ? row.nodes : [];
    const nodeLine = nodes
      .map((n) => {
        if (!n || typeof n !== "object") return "";
        const o = n as Record<string, unknown>;
        const p = String(o.pillar || "");
        const b = String(o.branch || "");
        return p && b ? `${p}:${b}` : "";
      })
      .filter(Boolean)
      .join("，");
    const ca = row.cluster_abs;
    const clusterAbs = typeof ca === "number" && Number.isFinite(ca) ? ca : null;
    const detail = `合成场·三合局 [${brs.join("·")}]`;
    out.push({
      key: `sanhe-${idx}`,
      branches: brs,
      clusterAbs,
      status: String(row.energy_vault_status || "AGGREGATED"),
      nodeLine: nodeLine || "—",
      detail,
    });
  });
  return out;
}

export function clusterMatchesTopologyDetail(cluster: SanheClusterRow, topologyDetail: string): boolean {
  const d = String(topologyDetail || "");
  if (!d) return false;
  if (d.includes(cluster.branches.join("·"))) return true;
  return cluster.branches.every((b) => d.includes(b));
}
