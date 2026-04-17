/** 从最近一次 analyze 快照的 physics_tensor 中解析某物理键的数值（与 PluginManagementPanel 原逻辑一致）。 */
export function runtimePhysicsNumber(
  pt: Record<string, unknown> | undefined,
  key: string,
): number | null {
  if (!pt) return null;
  const meta = (pt.meta || {}) as Record<string, unknown>;
  const rcfg = (meta.runtime_physics_config || {}) as Record<string, unknown>;
  const v = rcfg[key];
  if (typeof v === "number" && Number.isFinite(v)) return v;
  const plugins = (pt.plugin_outputs || {}) as Record<string, unknown>;
  const blind = (plugins["classical.blind_school.v1"] || {}) as Record<string, unknown>;
  const payload = (blind.payload || {}) as Record<string, unknown>;
  const wvCfg = (payload.runtime_physics_config || {}) as Record<string, unknown>;
  const w = wvCfg[key];
  if (typeof w === "number" && Number.isFinite(w)) return w;
  return null;
}
