/** 盲派 Skill 与 physics_tensor 的运行时对齐（终审存证等） */

const BLIND_PLUGIN = "classical.blind_school.v1";

/** 终审时固化：盲派插件开启且子开关开启的 Skill ID（与后端 skill_manifest.json 一致） */
export function computeVerdictEffectiveBlindSkillIds(snapshot: {
  physics_tensor?: Record<string, unknown>;
} | null): string[] {
  const pt = snapshot?.physics_tensor;
  if (!pt) return [];
  const meta = (pt.meta || {}) as Record<string, unknown>;
  const plugins = meta.enabled_plugins;
  const blindOn = Array.isArray(plugins) && plugins.includes(BLIND_PLUGIN);
  if (!blindOn) return [];
  const flags = (meta.blind_school_features || {}) as Record<string, unknown>;
  const ids: string[] = [];
  if (flags.enable_pierce_harm !== false) ids.push("mp_pierce_01");
  if (flags.enable_tomb_vault !== false) ids.push("mp_tomb_01");
  if (flags.enable_host_guest_bonus !== false) ids.push("mp_host_guest_01");
  return ids;
}
