/** 盲派 Skill 与 physics_tensor / work_vector 的运行时对齐（徽章、终审存证） */

export type BlindSkillBadge = {
  id: string;
  shortLabel: string;
  armed: boolean;
  hit: boolean;
};

const BLIND_PLUGIN = "classical.blind_school.v1";

function blindPayloadFromTensor(pt: Record<string, unknown> | undefined): Record<string, unknown> {
  if (!pt) return {};
  const po = (pt.plugin_outputs || {}) as Record<string, unknown>;
  const plug = (po[BLIND_PLUGIN] || {}) as Record<string, unknown>;
  return (plug.payload || {}) as Record<string, unknown>;
}

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

/**
 * 实验室徽章：armed = 子开关开启；hit = 当前局面上物理层已产出对应信号。
 */
export function computeBlindSkillBadges(
  physicsTensor: Record<string, unknown> | null | undefined,
  workVector: Record<string, unknown> | null | undefined,
): BlindSkillBadge[] {
  const pt = physicsTensor || undefined;
  const meta = (pt?.meta || {}) as Record<string, unknown>;
  const plugins = meta.enabled_plugins;
  const blindOn = Array.isArray(plugins) && plugins.includes(BLIND_PLUGIN);
  if (!blindOn) return [];

  const flags = (meta.blind_school_features || {}) as Record<string, unknown>;
  const chips = (meta.mangpai_chip_logs as string[]) || [];
  const chipText = chips.map((c) => String(c));
  const wv = Array.isArray(workVector?.work_vectors)
    ? (workVector!.work_vectors as Record<string, unknown>[])
    : [];
  const payload = blindPayloadFromTensor(pt);

  const pierceArmed = flags.enable_pierce_harm !== false;
  const pierceHit =
    pierceArmed &&
    wv.some((v) => String(v?.type || "") === "穿");

  const tombArmed = flags.enable_tomb_vault !== false;
  const tombHit =
    tombArmed &&
    chipText.some((line) => line.includes("墓库闭锁"));

  const hostArmed = flags.enable_host_guest_bonus !== false;
  const div = Number(payload.causal_dividend_index);
  const hostHit =
    hostArmed &&
    (chipText.some((line) => line.includes("宾主")) ||
      (Number.isFinite(div) && div >= 0.08));

  return [
    { id: "mp_pierce_01", shortLabel: "穿", armed: pierceArmed, hit: pierceHit },
    { id: "mp_tomb_01", shortLabel: "库", armed: tombArmed, hit: tombHit },
    { id: "mp_host_guest_01", shortLabel: "宾主", armed: hostArmed, hit: hostHit },
  ];
}
